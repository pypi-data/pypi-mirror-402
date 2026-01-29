from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from pyspark.sql import Column
from pyspark.sql import functions as F
from typing_extensions import override

from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.sdk.service.ml import Function as SDKFunction
from databricks.sdk.service.ml import FunctionExtraParameter, FunctionFunctionType


class Function(_FeatureStoreObject):
    """Abstract base class for all aggregation functions."""

    @abstractmethod
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        pass

    @abstractmethod
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the aggregation function."""
        pass

    def extra_parameters(self) -> Dict[str, Any]:
        """
        Return the extra parameters of the function.
        Only applicable to a few functions that require additional parameters.
        """
        return {}

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert the function to a dictionary that can be used to generate a YAML file."""
        result = {"operator": self.name}
        if extra_params := self.extra_parameters():
            result["extra_parameters"] = extra_params
        return result

    @classmethod
    def _from_yaml_dict(
        cls, operator: str, extra_params: Optional[Dict[str, Any]] = None
    ) -> "Function":
        """Create a Function from operator name and optional extra parameters."""
        # Map operator names to function classes
        if operator == "approx_count_distinct":
            return ApproxCountDistinct._from_yaml_dict(operator, extra_params)
        elif operator in ["percentile_approx", "approx_percentile"]:
            return ApproxPercentile._from_yaml_dict(operator, extra_params)
        elif operator in AGGREGATION_FUNCTION_BY_SHORTHAND:
            # For simple functions without parameters, use the mapping
            return AGGREGATION_FUNCTION_BY_SHORTHAND[operator]
        else:
            raise ValueError(f"Unknown function operator: {operator}")

    @classmethod
    def from_string(cls, function_str: str) -> "Function":
        """
        Create a Function instance from a string representation.

        :param function_str: String name of the aggregation function
        :return: Function instance
        :raises ValueError: If the function string is not recognized
        """
        if not isinstance(function_str, str):
            raise ValueError(f"Expected string, got {type(function_str)}")

        function_str = function_str.lower().strip()
        if function_str in AGGREGATION_FUNCTION_BY_SHORTHAND:
            return AGGREGATION_FUNCTION_BY_SHORTHAND[function_str]
        else:
            raise ValueError(
                f"Unknown function '{function_str}'. "
                f"Valid functions are: {list(AGGREGATION_FUNCTION_BY_SHORTHAND.keys())}"
            )

    @classmethod
    def _from_sdk_function(cls, sdk_function: SDKFunction) -> "Function":
        if sdk_function is None or sdk_function.function_type is None:
            raise ValueError("Function must include 'function_type'")

        operator = sdk_function.function_type.value.lower()

        # Extract extra parameters if present
        extra_params = None
        if sdk_function.extra_parameters:
            extra_params = {
                param.key: param.value for param in sdk_function.extra_parameters
            }

        # Delegate to _from_yaml_dict which handles type conversion
        return cls._from_yaml_dict(operator, extra_params)

    def _to_sdk_function(self) -> SDKFunction:
        extra_params = self.extra_parameters()
        sdk_extra_params = None
        if extra_params:
            sdk_extra_params = [
                FunctionExtraParameter(key=k, value=str(v))
                for k, v in extra_params.items()
                if v is not None
            ]
        return SDKFunction(
            function_type=FunctionFunctionType[self.name.upper()],
            extra_parameters=sdk_extra_params,
        )

    def __str__(self) -> str:
        """Return a string representation of the function."""
        extra_params = self.extra_parameters()
        if extra_params:
            params_str = ", ".join(f"{k}={v}" for k, v in extra_params.items())
            return f"{self.name}({params_str})"
        return self.name

    def __repr__(self) -> str:
        """Return a detailed string representation of the function."""
        extra_params = self.extra_parameters()
        if extra_params:
            params_str = ", ".join(f"{k}={v!r}" for k, v in extra_params.items())
            return f"{self.__class__.__name__}({params_str})"
        return f"{self.__class__.__name__}()"


class Avg(Function):
    """Class representing the average (avg) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"AVG(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"AVG({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.avg(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.avg(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "avg"


class Count(Function):
    """Class representing the count aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return (
                f"COUNT(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
            )
        return f"COUNT({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.count(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.count(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "count"


class ApproxCountDistinct(Function):
    """
    Class representing the approximate count distinct aggregation function.
    See https://docs.databricks.com/en/sql/language-manual/functions/approx_count_distinct.html

    :param relativeSD: The relative standard deviation allowed in the approximation.
    """

    # Field names used in the YAML serialization
    PARAM_RELATIVE_SD = "relativeSD"

    def __init__(self, relativeSD: Optional[float] = None):
        if relativeSD is not None and not isinstance(relativeSD, float):
            raise ValueError("relativeSD must be a float if supplied.")
        self._relativeSD = relativeSD

    @property
    def name(self) -> str:
        return "approx_count_distinct"

    @property
    def relativeSD(self) -> Optional[float]:
        return self._relativeSD

    @override
    def extra_parameters(self) -> Dict[str, Any]:
        return {
            self.PARAM_RELATIVE_SD: self._relativeSD,
        }

    @classmethod
    def _from_yaml_dict(
        cls, operator: str, extra_params: Optional[Dict[str, Any]] = None
    ) -> "ApproxCountDistinct":
        """Create ApproxCountDistinct from operator and parameters."""
        if extra_params is None:
            extra_params = {}
        relative_sd = extra_params.get(cls.PARAM_RELATIVE_SD)
        # Convert to float if it's a string (from SDK)
        if relative_sd is not None and isinstance(relative_sd, str):
            relative_sd = float(relative_sd)
        return cls(relativeSD=relative_sd)

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        column_expr = (
            f"CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END"
            if filter_condition
            else column_name
        )
        if self._relativeSD:
            return f"APPROX_COUNT_DISTINCT({column_expr}, {self._relativeSD})"
        return f"APPROX_COUNT_DISTINCT({column_expr})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            col_expr = F.when(
                F.expr(filter_condition), F.col(input_columns[0])
            ).otherwise(None)
        else:
            col_expr = F.col(input_columns[0])

        if self._relativeSD:
            return F.approx_count_distinct(col_expr, self._relativeSD)
        else:
            return F.approx_count_distinct(col_expr)


class ApproxPercentile(Function):
    """
    Class representing the percentile approximation aggregation function.
    See https://docs.databricks.com/en/sql/language-manual/functions/approx_percentile.html

    :param percentile: The percentile to approximate.
    :param accuracy: The accuracy of the approximation.
    """

    # Field names used in the YAML serialization
    PARAM_PERCENTILE = "percentile"
    PARAM_ACCURACY = "accuracy"

    def __init__(self, percentile: float, accuracy: Optional[int] = None):
        if not isinstance(percentile, float):
            raise ValueError("percentile must be a float.")
        if accuracy is not None and not isinstance(accuracy, int):
            raise ValueError("accuracy must be an integer if supplied.")
        self._percentile = percentile
        self._accuracy = accuracy

    @property
    def name(self) -> str:
        return "approx_percentile"

    @property
    def percentile(self) -> float:
        return self._percentile

    @property
    def accuracy(self) -> Optional[int]:
        return self._accuracy

    @override
    def extra_parameters(self) -> Dict[str, Any]:
        return {
            self.PARAM_PERCENTILE: self._percentile,
            self.PARAM_ACCURACY: self._accuracy,
        }

    @classmethod
    def _from_yaml_dict(
        cls, operator: str, extra_params: Optional[Dict[str, Any]] = None
    ) -> "ApproxPercentile":
        """Create ApproxPercentile from operator and parameters."""
        if extra_params is None:
            extra_params = {}
        percentile = extra_params.get(cls.PARAM_PERCENTILE)
        accuracy = extra_params.get(cls.PARAM_ACCURACY)
        # Convert to proper types if they're strings (from SDK)
        if percentile is not None and isinstance(percentile, str):
            percentile = float(percentile)
        if accuracy is not None and isinstance(accuracy, str):
            accuracy = int(accuracy)
        return cls(percentile=percentile, accuracy=accuracy)

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        column_expr = (
            f"CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END"
            if filter_condition
            else column_name
        )
        if self._accuracy:
            return f"PERCENTILE_APPROX({column_expr}, {self._percentile}, {self._accuracy})"
        return f"PERCENTILE_APPROX({column_expr}, {self._percentile})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            col_expr = F.when(
                F.expr(filter_condition), F.col(input_columns[0])
            ).otherwise(None)
        else:
            col_expr = F.col(input_columns[0])

        if self._accuracy:
            return F.percentile_approx(col_expr, self._percentile, self._accuracy)
        else:
            return F.percentile_approx(col_expr, self._percentile)


# Backward compatibility alias
PercentileApprox = ApproxPercentile


class First(Function):
    """Class representing the first aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if not timestamp_key:
            raise ValueError(
                "timestamp_key must be supplied for First aggregation function."
            )
        if filter_condition:
            return f"MIN_BY(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END, {timestamp_key})"
        return f"MIN_BY({column_name}, {timestamp_key})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.first(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                ),
                ignorenulls=True,
            )
        else:
            return F.first(F.col(input_columns[0]), ignorenulls=True)

    @property
    def name(self) -> str:
        return "first"


class Last(Function):
    """Class representing the last aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if not timestamp_key:
            raise ValueError(
                "timestamp_key must be supplied for Last aggregation function."
            )
        if filter_condition:
            return f"MAX_BY(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END, {timestamp_key})"
        return f"MAX_BY({column_name}, {timestamp_key})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.last(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                ),
                ignorenulls=True,
            )
        else:
            return F.last(F.col(input_columns[0]), ignorenulls=True)

    @property
    def name(self) -> str:
        return "last"


class Max(Function):
    """Class representing the maximum (max) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"MAX(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"MAX({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.max(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.max(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "max"


class Min(Function):
    """Class representing the minimum (min) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"MIN(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"MIN({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.min(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.min(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "min"


class StddevPop(Function):
    """Class representing the population standard deviation (stddev_pop) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"STDDEV_POP(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"STDDEV_POP({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.stddev_pop(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.stddev_pop(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "stddev_pop"


class StddevSamp(Function):
    """Class representing the sample standard deviation (stddev_samp) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"STDDEV_SAMP(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"STDDEV_SAMP({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.stddev_samp(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.stddev_samp(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "stddev_samp"


class Sum(Function):
    """Class representing the sum aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"SUM(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"SUM({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.sum(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.sum(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "sum"


class VarPop(Function):
    """Class representing the population variance (var_pop) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"VAR_POP(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"VAR_POP({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.var_pop(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.var_pop(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "var_pop"


class VarSamp(Function):
    """Class representing the sample variance (var_samp) aggregation function."""

    @override
    def to_sql(
        self,
        column_name: str,
        timestamp_key: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> str:
        if filter_condition:
            return f"VAR_SAMP(CASE WHEN {filter_condition} THEN {column_name} ELSE NULL END)"
        return f"VAR_SAMP({column_name})"

    @override
    def spark_function(
        self, input_columns: List[str], filter_condition: Optional[str] = None
    ) -> Column:
        if filter_condition:
            return F.var_samp(
                F.when(F.expr(filter_condition), F.col(input_columns[0])).otherwise(
                    None
                )
            )
        else:
            return F.var_samp(F.col(input_columns[0]))

    @property
    def name(self) -> str:
        return "var_samp"


# Mapping from shorthand strings to instances of corresponding classes
# Only include aggregations that don't require additional arguments
AGGREGATION_FUNCTION_BY_SHORTHAND = {
    "mean": Avg(),
    "avg": Avg(),
    "count": Count(),
    "first": First(),
    "last": Last(),
    "max": Max(),
    "min": Min(),
    "stddev_pop": StddevPop(),
    "stddev_samp": StddevSamp(),
    "sum": Sum(),
    "var_pop": VarPop(),
    "var_samp": VarSamp(),
    "approx_count_distinct": ApproxCountDistinct(),
}
