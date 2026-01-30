"""Warning catalog loader and registry.

Loads warning types from YAML and provides:
- WARNINGS: Dict[str, WarningType] - lookup by warning_id
- WarningIds: Class with constants for type-safe warning references
"""

import logging
import threading
from pathlib import Path
from typing import Dict, Optional

import yaml

from palisade.warnings.models import WarningType, SarifMetadata, Severity

logger = logging.getLogger(__name__)

# Path to the YAML catalog
CATALOG_PATH = Path(__file__).parent / "warning_catalog.yaml"


class WarningCatalog:
    """Warning catalog with lazy loading and validation.
    
    Thread-safe singleton with double-checked locking for efficient concurrent access.
    """
    
    _instance: Optional["WarningCatalog"] = None
    _warnings: Dict[str, WarningType] = {}
    _sarif_id_map: Dict[str, WarningType] = {}  # Reverse lookup: SARIF ID -> WarningType
    _loaded: bool = False
    _lock = threading.Lock()  # Thread-safe loading
    
    def __new__(cls) -> "WarningCatalog":
        """Singleton pattern for catalog."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> Dict[str, WarningType]:
        """Load warning types from YAML catalog.
        
        Thread-safe with double-checked locking for performance.
        
        Args:
            path: Optional path to YAML file. Uses default if not provided.
            
        Returns:
            Dictionary mapping warning_id to WarningType
        """
        # Fast path: already loaded, no lock needed for reads
        if cls._loaded and path is None:
            return cls._warnings
        
        # Slow path: need to load, acquire lock
        with cls._lock:
            # Double-check after acquiring lock (another thread might have loaded)
            if cls._loaded and path is None:
                return cls._warnings
            
            catalog_path = path or CATALOG_PATH
            
            if not catalog_path.exists():
                raise FileNotFoundError(
                    f"Warning catalog not found at {catalog_path}. "
                    "This should be included with the package."
                )
            
            try:
                with open(catalog_path) as f:
                    data = yaml.safe_load(f)
                
                warnings = {}
                for warning_id, warning_data in data.get("warnings", {}).items():
                    try:
                        warnings[warning_id] = WarningType.from_dict(warning_id, warning_data)
                    except Exception as e:
                        logger.warning(f"Failed to load warning {warning_id}: {e}")
                
                # Build reverse lookup map: SARIF ID -> WarningType (O(n) once, O(1) lookups)
                sarif_id_map = {}
                for warning in warnings.values():
                    if warning.sarif and warning.sarif.id:
                        sarif_id_map[warning.sarif.id] = warning
                
                cls._warnings = warnings
                cls._sarif_id_map = sarif_id_map
                cls._loaded = True
                logger.debug(f"Loaded {len(warnings)} warnings from {catalog_path}")
                return warnings
                
            except Exception as e:
                raise RuntimeError(f"Failed to load warning catalog: {e}") from e
    
    @classmethod
    def get(cls, warning_id: str) -> Optional[WarningType]:
        """Get a warning type by ID.
        
        Args:
            warning_id: The warning identifier
            
        Returns:
            WarningType if found, None otherwise
        """
        if not cls._loaded:
            cls.load()
        return cls._warnings.get(warning_id)
    
    @classmethod
    def find_by_sarif_id(cls, sarif_id: str) -> Optional[WarningType]:
        """Find a warning type by its SARIF ID using O(1) lookup.
        
        This is more efficient than iterating over all warnings.
        
        Args:
            sarif_id: The SARIF rule ID (e.g., "PALISADE-BO-001")
            
        Returns:
            WarningType if found, None otherwise
        """
        if not cls._loaded:
            cls.load()
        return cls._sarif_id_map.get(sarif_id)
    
    @classmethod
    def get_or_create(cls, warning_id: str, validator_name: str = "Unknown") -> WarningType:
        """Get a warning type by ID, raising an error if not found.
        
        All warnings must be explicitly defined in warning_catalog.yaml.
        This ensures consistent metadata and proper documentation.
        
        Args:
            warning_id: The warning identifier  
            validator_name: Name of the validator (unused, kept for compatibility)
            
        Returns:
            WarningType instance from the catalog
            
        Raises:
            KeyError: If warning_id is not found in warning_catalog.yaml
        """
        if not cls._loaded:
            cls.load()
        
        warning = cls._warnings.get(warning_id)
        if warning:
            return warning
        
        # Warning not found - fail fast to ensure proper documentation
        raise KeyError(
            f"Warning ID '{warning_id}' not found in warning_catalog.yaml. "
            f"All warnings must be explicitly defined in the catalog. "
            f"Please add this warning with proper SARIF metadata, descriptions, "
            f"and recommendations."
        )
    
    @classmethod
    def all_warnings(cls) -> Dict[str, WarningType]:
        """Get all loaded warning types from the YAML catalog.
        
        Returns:
            Dictionary of all warning types
        """
        if not cls._loaded:
            cls.load()
        return cls._warnings.copy()
    
    @classmethod
    def reload(cls, path: Optional[Path] = None) -> Dict[str, WarningType]:
        """Force reload the catalog (thread-safe).
        
        Args:
            path: Optional path to YAML file
            
        Returns:
            Reloaded warnings dictionary
        """
        with cls._lock:
            cls._loaded = False
            cls._warnings = {}
            cls._sarif_id_map = {}
        return cls.load(path)


class _WarningIdsMeta(type):
    """Metaclass that provides attribute access to warning IDs."""
    
    def __getattr__(cls, name: str) -> str:
        """Get warning ID by constant name.
        
        Allows: WarningIds.ROP_GADGETS_DETECTED -> "rop_gadgets_detected"
        """
        # Convert UPPER_CASE to lower_case
        warning_id = name.lower()
        
        # Verify warning exists (loads catalog if needed)
        if not WarningCatalog._loaded:
            WarningCatalog.load()
        
        if warning_id not in WarningCatalog._warnings:
            # Still return the ID but log a warning
            logger.debug(f"Warning ID {warning_id} not in catalog, using as-is")
        
        return warning_id


class WarningIds(metaclass=_WarningIdsMeta):
    """Type-safe constants for warning IDs.
    
    Usage:
        from palisade.warnings import WarningIds
        
        # IDE autocomplete works!
        warning_type = WarningIds.ROP_GADGETS_DETECTED
        # Returns: "rop_gadgets_detected"
    
    Note: Constants are dynamically resolved from the warning catalog.
    If you add a warning to warning_catalog.yaml, the constant is automatically available.
    """
    
    # Buffer Overflow warnings
    ROP_GADGETS_DETECTED = "rop_gadgets_detected"
    DANGEROUS_FUNCTIONS_DETECTED = "dangerous_functions_detected"
    FORMAT_STRING_VULNERABILITIES = "format_string_vulnerabilities"
    INTEGER_OVERFLOW_PATTERNS = "integer_overflow_patterns"
    NATIVE_EXECUTABLE_DETECTED = "native_executable_detected"
    NATIVE_LIBRARY_DETECTED = "native_library_detected"
    PE_MISSING_ASLR = "pe_missing_aslr"
    PE_MISSING_DEP = "pe_missing_dep"
    ELF_MISSING_NX_BIT = "elf_missing_nx_bit"
    ELF_MISSING_STACK_PROTECTION = "elf_missing_stack_protection"
    ARCHIVE_CONTAINS_NATIVE_CODE = "archive_contains_native_code"
    ARCHIVE_PATH_TRAVERSAL = "archive_path_traversal"
    
    # GGUF Safety rules
    GGUF_INVALID_MAGIC = "gguf_invalid_magic"
    GGUF_UNSUPPORTED_VERSION = "gguf_unsupported_version"
    GGUF_HEADER_CORRUPTION = "gguf_header_corruption"
    GGUF_TENSOR_MISMATCH = "gguf_tensor_mismatch"
    GGUF_SUSPICIOUS_METADATA = "gguf_suspicious_metadata"
    GGUF_CODE_INJECTION_PATTERNS = "gguf_code_injection_patterns"
    GGUF_NETWORK_ACCESS_PATTERNS = "gguf_network_access_patterns"
    
    # Pickle Security rules
    PICKLE_DANGEROUS_IMPORTS = "pickle_dangerous_imports"
    PICKLE_ARBITRARY_CODE = "pickle_arbitrary_code"
    PICKLE_SUSPICIOUS_GLOBALS = "pickle_suspicious_globals"
    PICKLE_REDUCE_EXPLOIT = "pickle_reduce_exploit"
    
    # SafeTensors Integrity rules
    SAFETENSORS_VALIDATION_ISSUE = "safetensors_validation_issue"
    SAFETENSORS_SUSPICIOUS_TENSOR_NAMES = "suspicious_tensor_names"
    SAFETENSORS_HEADER_CORRUPTION = "safetensors_header_corruption"
    
    # Backdoor Detection rules
    BACKDOOR_DETECTION_SIGNALS = "backdoor_detection_signals"
    BACKDOOR_SUSPICIOUS_HEADER_PATTERNS = "backdoor_suspicious_header_patterns"
    BACKDOOR_TEXTUAL_PATTERNS = "backdoor_textual_patterns_in_chunk"
    BACKDOOR_STEGANOGRAPHY = "backdoor_steganography_in_chunk"
    BACKDOOR_WEIGHT_ANOMALY = "backdoor_weight_anomaly_in_chunk"
    BACKDOOR_MEMORIZED_PAYLOADS = "backdoor_memorized_payloads"
    
    # Tokenizer Hygiene rules
    TOKENIZER_PROMPT_INJECTION = "tokenizer_prompt_injection"
    TOKENIZER_CODE_INJECTION = "tokenizer_code_injection"
    TOKENIZER_HIDDEN_TOKENS = "tokenizer_hidden_tokens"
    
    # Tool Call Security rules
    TOOL_HIJACKING = "tool_hijacking"
    COVERT_TOOL_INJECTION = "covert_tool_injection"
    UNEXPECTED_TOOL_CALLS = "unexpected_tool_calls"
    
    # Supply Chain rules
    SUPPLY_CHAIN_UNTRUSTED_SOURCE = "supply_chain_untrusted_source"
    SUPPLY_CHAIN_MISSING_SIGNATURE = "supply_chain_missing_signature"
    
    # Inference Behavior rules
    INFERENCE_UNAVAILABLE = "inference_unavailable"
    INFERENCE_ERROR = "inference_error"
    SUSPICIOUS_PERPLEXITY_PATTERNS = "suspicious_perplexity_patterns"
    
    # General
    VALIDATION_ERROR = "validation_error"
    STREAMING_VALIDATION_ERROR = "streaming_validation_error"


# Module-level WARNINGS dict (lazy loaded)
def _get_warnings() -> Dict[str, WarningType]:
    """Get the warnings dictionary, loading if necessary."""
    return WarningCatalog.load()


class _WarningsProxy:
    """Proxy object that lazy-loads warnings on first access."""
    
    def __getitem__(self, key: str) -> WarningType:
        return _get_warnings()[key]
    
    def __contains__(self, key: str) -> bool:
        return key in _get_warnings()
    
    def get(self, key: str, default: Optional[WarningType] = None) -> Optional[WarningType]:
        return _get_warnings().get(key, default)
    
    def keys(self):
        return _get_warnings().keys()
    
    def values(self):
        return _get_warnings().values()
    
    def items(self):
        return _get_warnings().items()
    
    def __iter__(self):
        return iter(_get_warnings())
    
    def __len__(self):
        return len(_get_warnings())


# Export as WARNINGS for convenient access
WARNINGS = _WarningsProxy()

