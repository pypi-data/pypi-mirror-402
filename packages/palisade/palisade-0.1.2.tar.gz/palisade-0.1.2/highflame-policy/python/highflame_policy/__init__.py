"""Highflame Policy Framework - Cedar-based policy engine for security decisions.

This package provides a high-performance, type-safe policy engine that can be used
for authorization decisions in security-focused applications.
"""

from highflame_policy._native import PyCedarPolicyEngine, PyPolicyEffect

# Export with cleaner names
PolicyEffect = PyPolicyEffect

__version__ = "0.1.0"
__all__ = ["PyCedarPolicyEngine", "PolicyEffect"]

