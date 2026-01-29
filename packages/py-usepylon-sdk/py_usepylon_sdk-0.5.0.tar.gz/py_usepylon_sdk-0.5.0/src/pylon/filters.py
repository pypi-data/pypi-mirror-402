"""Filter builder utilities for the Pylon SDK.

This module provides a fluent API for building query filters that can
be used with the Pylon API's search and list endpoints.

Note:
    The filter builder produces dictionary representations compatible with
    Pylon's API filter format. Use `filter.to_dict()` to get the serialized
    filter for API requests.

Example:
    from pylon import filters

    # Simple field filter
    filter = filters.Field("state").eq("open")

    # Compound filters
    filter = filters.And(
        filters.Field("state").in_(["open", "pending"]),
        filters.Field("created_at").after(datetime(2024, 1, 1))
    )

    # Serialize for API request
    filter_dict = filter.to_dict()
    # Use with your API calls as needed
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Filter(ABC):
    """Abstract base class for all filter types.

    Filters can be serialized to a dictionary format suitable for
    API requests.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the filter to a dictionary.

        Returns:
            Dictionary representation of the filter.
        """
        ...

    def __and__(self, other: Filter) -> And:
        """Combine filters with AND using & operator.

        Example:
            combined = filter1 & filter2
        """
        return And(self, other)

    def __or__(self, other: Filter) -> Or:
        """Combine filters with OR using | operator.

        Example:
            combined = filter1 | filter2
        """
        return Or(self, other)

    def __invert__(self) -> Not:
        """Negate a filter using ~ operator.

        Example:
            negated = ~filter
        """
        return Not(self)


class And(Filter):
    """Logical AND combination of multiple filters.

    All conditions must be true for the filter to match.

    Example:
        filter = And(
            Field("state").eq("open"),
            Field("priority").eq("high")
        )
    """

    def __init__(self, *filters: Filter) -> None:
        """Initialize an AND filter.

        Args:
            *filters: Two or more filters to combine with AND.
        """
        if len(filters) < 2:
            raise ValueError("And requires at least 2 filters")
        self._filters = filters

    def to_dict(self) -> dict[str, Any]:
        """Serialize the AND filter to a dictionary."""
        return {"and": [f.to_dict() for f in self._filters]}


class Or(Filter):
    """Logical OR combination of multiple filters.

    At least one condition must be true for the filter to match.

    Example:
        filter = Or(
            Field("state").eq("open"),
            Field("state").eq("pending")
        )
    """

    def __init__(self, *filters: Filter) -> None:
        """Initialize an OR filter.

        Args:
            *filters: Two or more filters to combine with OR.
        """
        if len(filters) < 2:
            raise ValueError("Or requires at least 2 filters")
        self._filters = filters

    def to_dict(self) -> dict[str, Any]:
        """Serialize the OR filter to a dictionary."""
        return {"or": [f.to_dict() for f in self._filters]}


class Not(Filter):
    """Logical NOT negation of a filter.

    The condition must be false for the filter to match.

    Example:
        filter = Not(Field("state").eq("closed"))
    """

    def __init__(self, filter_: Filter) -> None:
        """Initialize a NOT filter.

        Args:
            filter_: The filter to negate.
        """
        self._filter = filter_

    def to_dict(self) -> dict[str, Any]:
        """Serialize the NOT filter to a dictionary."""
        return {"not": self._filter.to_dict()}


class FieldFilter(Filter):
    """A filter condition on a specific field.

    Created by Field().eq(), Field().in_(), etc.
    """

    def __init__(
        self,
        field: str,
        operator: str,
        value: Any,
    ) -> None:
        """Initialize a field filter.

        Args:
            field: The field name to filter on.
            operator: The comparison operator.
            value: The value to compare against.
        """
        self._field = field
        self._operator = operator
        self._value = value

    def to_dict(self) -> dict[str, Any]:
        """Serialize the field filter to a dictionary."""
        return {
            "field": self._field,
            "operator": self._operator,
            "value": self._value,
        }


class Field:
    """Builder for field-based filters.

    Use this class to create filter conditions on specific fields.

    Example:
        # Equality
        Field("state").eq("open")

        # In list
        Field("status").in_(["open", "pending"])

        # Comparisons
        Field("created_at").after(datetime(2024, 1, 1))
        Field("priority").gte(3)

        # Contains
        Field("title").contains("urgent")
    """

    def __init__(self, name: str) -> None:
        """Initialize a field builder.

        Args:
            name: The field name to filter on.
        """
        self._name = name

    def eq(self, value: Any) -> FieldFilter:
        """Create an equality filter.

        Args:
            value: The value to match.

        Returns:
            A FieldFilter for the equality condition.
        """
        return FieldFilter(self._name, "equals", value)

    def neq(self, value: Any) -> FieldFilter:
        """Create a not-equal filter.

        Args:
            value: The value to not match.

        Returns:
            A FieldFilter for the inequality condition.
        """
        return FieldFilter(self._name, "not_equals", value)

    def in_(self, values: list[Any]) -> FieldFilter:
        """Create an 'in list' filter.

        Args:
            values: List of values to match.

        Returns:
            A FieldFilter for the in-list condition.
        """
        return FieldFilter(self._name, "in", values)

    def not_in(self, values: list[Any]) -> FieldFilter:
        """Create a 'not in list' filter.

        Args:
            values: List of values to exclude.

        Returns:
            A FieldFilter for the not-in-list condition.
        """
        return FieldFilter(self._name, "not_in", values)

    def gt(self, value: Any) -> FieldFilter:
        """Create a greater-than filter.

        Args:
            value: The value to compare against.

        Returns:
            A FieldFilter for the greater-than condition.
        """
        return FieldFilter(self._name, "greater_than", value)

    def gte(self, value: Any) -> FieldFilter:
        """Create a greater-than-or-equal filter.

        Args:
            value: The value to compare against.

        Returns:
            A FieldFilter for the greater-than-or-equal condition.
        """
        return FieldFilter(self._name, "greater_than_or_equals", value)

    def lt(self, value: Any) -> FieldFilter:
        """Create a less-than filter.

        Args:
            value: The value to compare against.

        Returns:
            A FieldFilter for the less-than condition.
        """
        return FieldFilter(self._name, "less_than", value)

    def lte(self, value: Any) -> FieldFilter:
        """Create a less-than-or-equal filter.

        Args:
            value: The value to compare against.

        Returns:
            A FieldFilter for the less-than-or-equal condition.
        """
        return FieldFilter(self._name, "less_than_or_equals", value)

    def contains(self, value: str) -> FieldFilter:
        """Create a contains filter (substring match).

        Args:
            value: The substring to search for.

        Returns:
            A FieldFilter for the contains condition.
        """
        return FieldFilter(self._name, "contains", value)

    def starts_with(self, value: str) -> FieldFilter:
        """Create a starts-with filter (prefix match).

        Args:
            value: The prefix to match.

        Returns:
            A FieldFilter for the starts-with condition.
        """
        return FieldFilter(self._name, "starts_with", value)

    def ends_with(self, value: str) -> FieldFilter:
        """Create an ends-with filter (suffix match).

        Args:
            value: The suffix to match.

        Returns:
            A FieldFilter for the ends-with condition.
        """
        return FieldFilter(self._name, "ends_with", value)

    def after(self, value: datetime) -> FieldFilter:
        """Create an 'after' filter for datetime fields.

        Args:
            value: The datetime to compare against.

        Returns:
            A FieldFilter for the after condition.
        """
        return FieldFilter(self._name, "greater_than", value.isoformat())

    def before(self, value: datetime) -> FieldFilter:
        """Create a 'before' filter for datetime fields.

        Args:
            value: The datetime to compare against.

        Returns:
            A FieldFilter for the before condition.
        """
        return FieldFilter(self._name, "less_than", value.isoformat())

    def between(self, start: datetime, end: datetime) -> And:
        """Create a 'between' filter for datetime fields.

        Args:
            start: The start datetime (inclusive).
            end: The end datetime (inclusive).

        Returns:
            An And filter combining greater_than_or_equals and less_than_or_equals conditions.
        """
        return And(
            FieldFilter(self._name, "greater_than_or_equals", start.isoformat()),
            FieldFilter(self._name, "less_than_or_equals", end.isoformat()),
        )

    def is_null(self) -> FieldFilter:
        """Create an 'is null' filter.

        Returns:
            A FieldFilter for the null check condition.
        """
        return FieldFilter(self._name, "is_null", True)

    def is_not_null(self) -> FieldFilter:
        """Create an 'is not null' filter.

        Returns:
            A FieldFilter for the not-null check condition.
        """
        return FieldFilter(self._name, "is_null", False)
