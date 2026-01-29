from __future__ import annotations

import operator
import re
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Sequence


def _get_by_path(data: Mapping[str, Any], path: str) -> Any:
	parts = path.split(".")
	current: Any = data
	for part in parts:
		if not isinstance(current, Mapping):
			return None
		current = current.get(part)
	return current


def _ensure_sequence(value: Any) -> Sequence[Any]:
	if isinstance(value, (list, tuple)):
		return value
	return [value]


OPS = {
	"eq": operator.eq,
	"ne": operator.ne,
	"gt": operator.gt,
	"ge": operator.ge,
	"lt": operator.lt,
	"le": operator.le,
}


def _coerce_types(actual: Any, value: Any) -> tuple:
	"""Try to coerce value to match actual's type for comparison."""
	if actual is None or value is None:
		return actual, value

	# If types already match, return as-is
	if type(actual) == type(value):
		return actual, value

	# Try to coerce value to actual's type
	try:
		# Handle Decimal type from MSSQL
		if isinstance(actual, Decimal):
			if isinstance(value, str):
				return float(actual), float(value)
			elif isinstance(value, (int, float)):
				return float(actual), float(value)
		if isinstance(actual, int) and isinstance(value, str):
			return actual, int(value)
		if isinstance(actual, float) and isinstance(value, str):
			return actual, float(value)
		if isinstance(actual, str) and isinstance(value, (int, float)):
			return actual, str(value)
		if isinstance(actual, bool) and isinstance(value, str):
			return actual, value.lower() in ('true', '1', 'yes')
	except (ValueError, TypeError):
		pass

	return actual, value


def _match_condition(cond: Dict[str, Any], event: Mapping[str, Any]) -> bool:
	if "all" in cond:
		return all(_match_condition(c, event) for c in _ensure_sequence(cond["all"]))
	if "any" in cond:
		return any(_match_condition(c, event) for c in _ensure_sequence(cond["any"]))
	if "not" in cond:
		return not _match_condition(cond["not"], event)

	op = cond.get("op")
	field = cond.get("field")
	value = cond.get("value")
	if not op or not field:
		return False

	actual = _get_by_path(event, field)

	# Coerce types for comparison
	actual, value = _coerce_types(actual, value)

	if op in OPS:
		try:
			return bool(OPS[op](actual, value))
		except Exception:
			return False
	if op == "in":
		return actual in _ensure_sequence(value)
	if op == "contains":
		try:
			return value in actual  # type: ignore[operator]
		except Exception:
			return False
	if op == "regex":
		try:
			return re.search(str(value), str(actual)) is not None
		except Exception:
			return False
	return False


class RuleEngine:
	@staticmethod
	def evaluate(rule_condition: Dict[str, Any], event: Mapping[str, Any]) -> bool:
		"""
		Evaluate rule condition against event data.
		Handles frontend format: {"rules": [{"field": ..., "operator": ..., "value": ...}]}
		"""
		if not rule_condition:
			return True

		# Handle frontend format with "rules" array
		if "rules" in rule_condition:
			rules = rule_condition.get("rules", [])
			if not rules:
				return True

			# All rules must pass (AND logic)
			for rule in rules:
				field = rule.get("field", "")
				op = rule.get("operator", "eq")
				value = rule.get("value")

				# Map frontend operators to internal ops
				op_map = {
					"equals": "eq",
					"not_equals": "ne",
					"greater_than": "gt",
					"less_than": "lt",
					"greater_than_or_equal": "ge",
					"less_than_or_equal": "le",
					"contains": "contains",
					"regex": "regex",
					"in": "in",
					"eq": "eq",
					"ne": "ne",
					"gt": "gt",
					"gte": "ge",  # Frontend shorthand
					"lt": "lt",
					"lte": "le",  # Frontend shorthand
					"ge": "ge",
					"le": "le",
				}
				internal_op = op_map.get(op, op)

				cond = {"field": field, "op": internal_op, "value": value}
				if not _match_condition(cond, event):
					return False

			return True

		# Handle legacy format
		return _match_condition(rule_condition, event)

	@staticmethod
	def evaluate_filters(filters: List[Dict[str, Any]], event: Mapping[str, Any]) -> bool:
		"""
		Evaluate a list of filters against event data.
		All filters must pass (AND logic).
		Each filter has: field, operator, value
		"""
		if not filters:
			return True

		for f in filters:
			field = f.get("field", "")
			op = f.get("operator", "eq")
			value = f.get("value")

			actual = _get_by_path(event, field)

			# Map filter operators to internal ops
			op_map = {
				"equals": "eq",
				"not_equals": "ne",
				"greater_than": "gt",
				"less_than": "lt",
				"contains": "contains",
				"regex": "regex",
				"in": "in",
				"eq": "eq",
				"ne": "ne",
				"gt": "gt",
				"lt": "lt",
				"ge": "ge",
				"le": "le",
			}
			internal_op = op_map.get(op, op)

			# Evaluate single filter
			cond = {"field": field, "op": internal_op, "value": value}
			if not _match_condition(cond, event):
				return False

		return True


