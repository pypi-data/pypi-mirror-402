"""Result Analyzers for Palisade CLI.

This package provides analysis tools for scan results:
- Threat analyzer (categorize and assess threats)
- Validator stats (performance and coverage analysis)
- Policy analyzer (policy enforcement results)
"""

from palisade.cli.analyzers.threat_analyzer import (
    analyze_threats,
    get_recommendations,
    group_warnings_by_file,
    group_warnings_by_severity,
)
from palisade.cli.analyzers.validator_stats import (
    analyze_validator_performance,
    get_validator_summary,
    infer_validator_name,
)
from palisade.cli.analyzers.policy_analyzer import (
    aggregate_policy_results,
    analyze_policy_result,
    get_exit_code_from_policy,
)

__all__ = [
    # Threat analysis
    "analyze_threats",
    "get_recommendations",
    "group_warnings_by_file",
    "group_warnings_by_severity",
    # Validator stats
    "analyze_validator_performance",
    "get_validator_summary",
    "infer_validator_name",
    # Policy analysis
    "aggregate_policy_results",
    "analyze_policy_result",
    "get_exit_code_from_policy",
]


