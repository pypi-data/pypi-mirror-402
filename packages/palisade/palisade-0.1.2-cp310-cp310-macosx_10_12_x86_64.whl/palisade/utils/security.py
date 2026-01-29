"""Security-related utilities for the scanner."""

import io
import pickle
import pickletools
from typing import Any, Dict, List

from palisade.core.config import SAFE_MODULES, UNSAFE_OPCODES


class SandboxUnpickler(pickle.Unpickler):
    """A restricted unpickler that prevents arbitrary imports and dangerous operations."""

    def find_class(self, module: str, name: str) -> Any:
        """Override to prevent arbitrary imports.

        Args:
        ----
            module: Module name
            name: Class name

        Raises:
        ------
            pickle.UnpicklingError: If import is blocked
        """
        if module in SAFE_MODULES and name in SAFE_MODULES[module]:
            return super().find_class(module, name)
        msg = f"Import blocked: {module}.{name}"
        raise pickle.UnpicklingError(msg)

def static_pickle_scan(data: bytes) -> List[Dict[str, Any]]:
    """Perform static analysis on pickle data to detect unsafe opcodes.

    Args:
    ----
        data: Raw pickle data to analyze

    Returns:
    -------
        List of warnings containing details about unsafe opcodes found
    """
    warnings = []
    for opcode, arg, pos in pickletools.genops(io.BytesIO(data)):
        if opcode.name.encode() in UNSAFE_OPCODES:
            warnings.append({
                "offset": pos,
                "opcode": opcode.name,
                "arg": arg,
                "message": "Unsafe opcode detected",
            })
    return warnings
