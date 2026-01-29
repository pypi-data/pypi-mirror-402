"""Buffer Overflow Detection Validator.

This validator detects potential buffer overflow vulnerabilities in compiled model components:
• Native extensions and shared libraries (.so, .dll, .dylib)
• ONNX operators with compiled custom kernels
• TensorRT engines and CUDA kernels
• Embedded native code in model archives
• Assembly code patterns and ROP gadgets
• Stack/heap buffer overflow patterns in binary data
• Format string vulnerabilities in error messages
• Integer overflow patterns in dimension calculations

Critical for preventing memory corruption attacks and RCE through buffer overflows.
"""

import gzip
import logging
import struct
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, cast

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine
    from palisade.models.model_file import ModelFile

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.models.types import ChunkInfo, StreamingContext

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)


def analysis_timeout(timeout_seconds: int = 30) -> Callable:
    """
    Thread-safe timeout decorator for analysis methods.

    Uses ThreadPoolExecutor with timeout instead of signals to work
    correctly when called from background threads.

    Args:
        timeout_seconds: Maximum time allowed for the operation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if we're in the main thread - if so, we could use signals, but
            # for consistency and thread-safety, always use ThreadPoolExecutor

            try:
                # Use ThreadPoolExecutor with timeout for thread-safe timeout handling
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    return future.result(timeout=timeout_seconds)

            except ConcurrentTimeoutError:
                logger.warning(f"Analysis timeout in {func.__name__} after {timeout_seconds}s")
                # Return timeout warning if called as method
                if args and hasattr(args[0], "create_standard_warning"):
                    return [args[0].create_standard_warning(
                        "analysis_timeout",
                        f"Analysis operation {func.__name__} timed out after {timeout_seconds} seconds",
                        Severity.MEDIUM,
                        "Analysis was aborted due to timeout - manual review recommended"
                    )]
                return []
            except Exception as e:
                # Re-raise other exceptions normally
                logger.debug(f"Error in {func.__name__}: {str(e)}")
                raise

        return wrapper
    return decorator


class BufferOverflowValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR for buffer overflow detection.

    Detects buffer overflow vulnerabilities in compiled model components:
    - Native libraries and extensions
    - ONNX custom operators with native code
    - TensorRT engines and GPU kernels
    - Embedded assembly and native code
    - Unsafe memory operations patterns
    - Integer overflow in calculations
    - Format string vulnerabilities
    """

    def __init__(self, metadata: Optional[ModelMetadata] = None, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Load policy configuration
        self._load_policy_configuration()

        # Native library file extensions to scan
        self.native_extensions = {
            ".so", ".dll", ".dylib", ".a", ".lib", ".o", ".obj"
        }

        # Compiled model formats that may contain native code
        self.compiled_formats = {
            ".onnx", ".trt", ".engine", ".tensorrt", ".openvino"
        }

        # Archive formats that may contain native code
        self.archive_formats = {
            ".zip", ".tar", ".gz", ".tgz", ".tar.gz"
        }

        # Dangerous function patterns (common buffer overflow sources)
        self.dangerous_functions = {
            # C/C++ unsafe functions
            b"strcpy", b"strcat", b"sprintf", b"gets", b"scanf",
            b"strncpy", b"strncat", b"snprintf", b"vsprintf", b"vsnprintf",
            # Memory operations that can overflow
            b"memcpy", b"memmove", b"memset", b"bcopy", b"bzero",
            # Allocation functions with size issues
            b"malloc", b"calloc", b"realloc", b"alloca",
            # Format string vulnerabilities
            b"printf", b"fprintf", b"dprintf", b"syslog"
        }

        # Binary patterns that may indicate compiled code vulnerabilities
        # These are more reliable than regex-based assembly detection
        self.suspicious_binary_patterns = [
            # x86 instruction sequences that commonly appear in ROP gadgets
            (b"\x58\xc3", "pop_eax_ret"),           # pop eax; ret
            (b"\x5d\xc3", "pop_ebp_ret"),           # pop ebp; ret
            (b"\xff\xe4", "jmp_esp"),               # jmp esp (direct)
            (b"\xff\x25", "jmp_indirect"),          # jmp [addr] (indirect)
            # Stack manipulation patterns
            (b"\x81\xc4", "add_esp_imm32"),         # add esp, imm32
            (b"\x81\xec", "sub_esp_imm32"),         # sub esp, imm32
            # String operation prefixes that could indicate buffer operations
            (b"\xf3\xa4", "rep_movsb"),             # rep movsb
            (b"\xf3\xa5", "rep_movsd"),             # rep movsd
            (b"\xf3\xaa", "rep_stosb"),             # rep stosb
        ]

        # PE/ELF binary signatures
        self.binary_signatures = {
            b"MZ": "pe_executable",  # Windows PE
            b"\x7fELF": "elf_executable",  # Linux/Unix ELF
            b"\xfe\xed\xfa\xce": "mach_o_32",  # macOS Mach-O 32-bit
            b"\xfe\xed\xfa\xcf": "mach_o_64",  # macOS Mach-O 64-bit
        }

    def _load_policy_configuration(self) -> None:
        """Load buffer overflow detection policy configuration."""
        # Default configuration
        policy_config = {}

        if (self.policy_engine and
            hasattr(self.policy_engine, "get_validator_config") and
            callable(self.policy_engine.get_validator_config)):
            policy_config = self.policy_engine.get_validator_config("buffer_overflow") or {}

        # Detection sensitivity levels
        self.detection_level = policy_config.get("detection_level", "high")  # low, medium, high, paranoid
        self.scan_native_libs = policy_config.get("scan_native_libs", True)
        self.scan_onnx_operators = policy_config.get("scan_onnx_operators", True)
        self.scan_gpu_kernels = policy_config.get("scan_gpu_kernels", True)
        self.deep_binary_analysis = policy_config.get("deep_binary_analysis", False)

        # Size limits for safe processing
        self.max_file_size_mb = policy_config.get("max_file_size_mb", 100)
        self.max_archive_entries = policy_config.get("max_archive_entries", 1000)

        # Timeout and rate limiting settings
        self.regex_timeout_seconds = policy_config.get("regex_timeout_seconds", 5)
        self.max_regex_scan_size = policy_config.get("max_regex_scan_size", 512 * 1024)  # 512KB limit for regex

    def can_validate(self, model_type: ModelType) -> bool:
        """Check if this validator can handle the given model type."""
        # Can validate most model types that might contain compiled components
        return model_type in {
            ModelType.PYTORCH,  # May contain C++ extensions
            ModelType.ONNX,  # May contain custom operators
            ModelType.TENSORFLOW,  # May contain compiled ops
            ModelType.HUGGINGFACE,  # May contain compiled components
            ModelType.UNKNOWN,  # Check everything unknown
        }

    def get_checks_performed(self) -> List[str]:
        """Return list of checks performed by this validator."""
        return [
            "binary_type_detection",
            "dangerous_function_scan",
            "integer_overflow_check",
            "format_string_scan",
            "native_library_detection",
            "archive_content_scan"
        ]
    
    def get_features_analyzed(self) -> List[str]:
        """Return list of features analyzed by this validator."""
        return [
            "native_code_presence",
            "compiled_components",
            "memory_operations",
            "function_calls",
            "assembly_patterns",
            "archive_contents",
            "custom_operators"
        ]

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate model data for buffer overflow vulnerabilities."""
        warnings = []

        try:
            # Quick signature check for known binary formats
            binary_type = self._detect_binary_type(data)
            if binary_type:
                warnings.extend(self._analyze_binary_content(data, binary_type))

                # For binaries, focus analysis on executable sections if available
                executable_sections = self._get_executable_sections(data, binary_type)
                if executable_sections:
                    # Analyze only executable sections for better accuracy
                    for section in executable_sections:
                        section_data = section["data"]
                        warnings.extend(self._scan_dangerous_functions(section_data, f"section:{section['name']}"))

                        if self.deep_binary_analysis:
                            warnings.extend(self._analyze_binary_patterns(section_data, f"section:{section['name']}"))

                        warnings.extend(self._check_integer_overflow_patterns(section_data, f"section:{section['name']}"))
                        warnings.extend(self._scan_format_string_vulns(section_data, f"section:{section['name']}"))
                else:
                    # Fall back to full binary analysis if section parsing fails
                    warnings.extend(self._scan_dangerous_functions(data))
                    if self.deep_binary_analysis:
                        warnings.extend(self._analyze_binary_patterns(data))
                    warnings.extend(self._check_integer_overflow_patterns(data))
                    warnings.extend(self._scan_format_string_vulns(data))
            else:
                # For non-binary data, be much more conservative to avoid false positives
                # Only scan for dangerous functions (which are more reliable indicators)
                warnings.extend(self._scan_dangerous_functions(data))
                
                # Skip integer overflow and format string checks for non-binary data
                # These patterns are too common in legitimate model data
                if self.deep_binary_analysis:
                    warnings.extend(self._analyze_binary_patterns(data))

        except Exception as e:
            logger.warning(f"Error during buffer overflow validation: {e}")
            warnings.append(self.create_standard_warning(
                "validation_error",
                f"Buffer overflow validation failed: {str(e)}",
                Severity.MEDIUM,
                "Manual security review recommended for this model component"
            ))

        return warnings

    def validate_file(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Validate file with enhanced archive and native library support."""
        warnings = []

        try:
            file_path = Path(model_file.file_info.path)
            file_ext = file_path.suffix.lower()

            # Handle archive files specially
            if file_ext in self.archive_formats:
                warnings.extend(self._scan_archive_file(file_path))

            # Handle native library files
            elif file_ext in self.native_extensions:
                warnings.extend(self._scan_native_library(model_file))

            # Handle compiled model formats
            elif file_ext in self.compiled_formats:
                warnings.extend(self._scan_compiled_model(model_file))

            # Default validation for other files
            else:
                warnings.extend(super().validate_file(model_file))

        except Exception as e:
            logger.warning(f"Error validating file {model_file.file_info.path}: {e}")
            warnings.append(self.create_standard_warning(
                "file_validation_error",
                f"File validation failed: {str(e)}",
                Severity.MEDIUM
            ))

        return warnings

    def _detect_binary_type(self, data: bytes) -> Optional[str]:
        """Detect binary executable type from data."""
        if len(data) < 4:
            return None

        for signature, binary_type in self.binary_signatures.items():
            if data.startswith(signature):
                return binary_type

        return None

    def _validate_section_boundaries(self, offset: int, size: int, data_len: int, max_size: int = 100 * 1024 * 1024) -> bool:
        """Common boundary validation for all binary formats."""
        return (offset > 0 and size > 0 and
                offset < data_len and size <= max_size and
                offset <= data_len - size)

    def _create_section_info(self, data: bytes, offset: int, size: int, name: str, **metadata: Any) -> Optional[Dict[str, Any]]:
        """Common section extraction logic."""
        if not self._validate_section_boundaries(offset, size, len(data)):
            return None
        return {
            "name": name,
            "offset": offset,
            "size": size,
            "data": data[offset:offset + size],
            **metadata
        }

    @analysis_timeout(timeout_seconds=20)
    def _analyze_binary_content(self, data: bytes, binary_type: str) -> List[Dict[str, Any]]:
        """Analyze binary executable content for buffer overflow patterns."""
        warnings = []

        if binary_type == "pe_executable":
            warnings.extend(self._analyze_pe_binary(data))
        elif binary_type == "elf_executable":
            warnings.extend(self._analyze_elf_binary(data))
        elif binary_type.startswith("mach_o"):
            warnings.extend(self._analyze_macho_binary(data))

        # Always flag presence of native executables as potential risk
        warnings.append(self.create_standard_warning(
            "native_executable_detected",
            f"Native executable detected: {binary_type}",
            Severity.HIGH,
            f"Native executables in ML models pose security risks. Type: {binary_type}",
            data=data,  # Pass data for comprehensive metadata including hashes
            binary_type=binary_type,
            analysis_performed=True
        ))

        return warnings

    @analysis_timeout(timeout_seconds=15)
    def _get_executable_sections(self, data: bytes, binary_type: str) -> List[Dict[str, Any]]:
        """Extract executable sections from binary for focused analysis."""
        sections: List[Dict[str, Any]] = []

        try:
            if binary_type == "pe_executable":
                sections = self._get_pe_executable_sections(data)
            elif binary_type == "elf_executable":
                sections = self._get_elf_executable_sections(data)
            elif binary_type.startswith("mach_o"):
                sections = self._get_macho_executable_sections(data)
        except Exception as e:
            logger.debug(f"Error extracting executable sections: {str(e)}")

        return sections

    def _get_pe_executable_sections(self, data: bytes) -> List[Dict[str, Any]]:
        """Get executable sections from PE binary."""
        sections: List[Dict[str, Any]] = []

        try:
            if len(data) < 64:
                return sections

            pe_offset = struct.unpack("<I", data[60:64])[0]

            # Validate PE offset for potential attacks
            if (pe_offset == 0 or pe_offset >= len(data) or
                pe_offset > 0x10000000 or  # Sanity check: PE offset shouldn't be > 256MB
                pe_offset + 24 > len(data)):
                logger.debug(f"Invalid PE offset: {pe_offset}")
                return sections

            # Skip PE signature and COFF header to get to Optional Header
            opt_header_offset = pe_offset + 24
            if opt_header_offset + 2 > len(data):
                return sections

            # Get number of sections from COFF header
            num_sections = struct.unpack("<H", data[pe_offset + 6:pe_offset + 8])[0]
            opt_header_size = struct.unpack("<H", data[pe_offset + 20:pe_offset + 22])[0]

            # Validate section count and optional header size
            if num_sections > 1000 or opt_header_size > 0x1000:  # Reasonable limits
                logger.debug(f"Suspicious PE header values: sections={num_sections}, opt_header_size={opt_header_size}")
                return sections

            # Section headers start after optional header
            section_table_offset = opt_header_offset + opt_header_size
            if section_table_offset >= len(data):
                logger.debug(f"Section table offset beyond file: {section_table_offset}")
                return sections

            for i in range(min(num_sections, 50)):  # Limit to prevent DoS
                section_offset = section_table_offset + (i * 40)  # Each section header is 40 bytes
                if section_offset + 40 > len(data):
                    break

                # Extract section characteristics (last 4 bytes of section header)
                characteristics = struct.unpack("<I", data[section_offset + 36:section_offset + 40])[0]

                # Check if section is executable (IMAGE_SCN_MEM_EXECUTE = 0x20000000)
                if characteristics & 0x20000000:
                    raw_data_ptr = struct.unpack("<I", data[section_offset + 20:section_offset + 24])[0]
                    raw_data_size = struct.unpack("<I", data[section_offset + 16:section_offset + 20])[0]

                    # Validate section boundaries with integer overflow protection
                    if (raw_data_ptr > 0 and raw_data_size > 0 and
                        raw_data_ptr < len(data) and
                        raw_data_size <= len(data) and  # Prevent size overflow
                        raw_data_ptr <= len(data) - raw_data_size):  # Prevent offset+size overflow

                        # Additional sanity check: don't process sections larger than 100MB
                        if raw_data_size <= 100 * 1024 * 1024:
                            section_data = data[raw_data_ptr:raw_data_ptr + raw_data_size]
                            sections.append({
                                "name": data[section_offset:section_offset + 8].rstrip(b"\x00").decode("ascii", errors="ignore"),
                                "offset": raw_data_ptr,
                                "size": raw_data_size,
                                "data": section_data,
                                "characteristics": hex(characteristics)
                            })
                        else:
                            logger.debug(f"Skipping oversized PE section: {raw_data_size} bytes")

        except (struct.error, IndexError, UnicodeDecodeError) as e:
            logger.debug(f"Error parsing PE sections: {str(e)}")

        return sections

    def _get_elf_executable_sections(self, data: bytes) -> List[Dict[str, Any]]:
        """Get executable sections from ELF binary."""
        sections: List[Dict[str, Any]] = []

        try:
            if len(data) < 52:  # Minimum for 32-bit ELF header
                return sections

            # Check ELF endianness (byte 5)
            endian = data[5]
            if endian == 1:  # ELFDATA2LSB (little-endian)
                endian_format = "<"
            elif endian == 2:  # ELFDATA2MSB (big-endian)
                endian_format = ">"
            else:
                logger.debug(f"Invalid ELF endianness: {endian}")
                return sections

            # Check ELF class (32/64 bit)
            elf_class = data[4]
            if elf_class == 1:  # 32-bit
                header_size = 52
                section_entry_size = 40
            elif elf_class == 2:  # 64-bit
                header_size = 64
                section_entry_size = 64
            else:
                return sections

            if len(data) < header_size:
                return sections

            # Parse ELF header for section information with correct endianness
            if elf_class == 1:  # 32-bit
                section_offset = struct.unpack(f"{endian_format}I", data[32:36])[0]
                section_count = struct.unpack(f"{endian_format}H", data[48:50])[0]
            else:  # 64-bit
                section_offset = struct.unpack(f"{endian_format}Q", data[40:48])[0]
                section_count = struct.unpack(f"{endian_format}H", data[60:62])[0]

            # Validate section offset and count for potential attacks
            if (section_offset == 0 or section_offset >= len(data) or
                section_count > 10000 or section_count == 0):  # Reasonable limits
                logger.debug(f"Invalid ELF section values: offset={section_offset}, count={section_count}")
                return sections

            # Limit section count to prevent DoS
            section_count = min(section_count, 100)

            for i in range(section_count):
                sect_hdr_offset = section_offset + (i * section_entry_size)
                if sect_hdr_offset + section_entry_size > len(data):
                    break

                if elf_class == 1:  # 32-bit
                    sect_flags = struct.unpack(f"{endian_format}I", data[sect_hdr_offset + 8:sect_hdr_offset + 12])[0]
                    sect_addr = struct.unpack(f"{endian_format}I", data[sect_hdr_offset + 12:sect_hdr_offset + 16])[0]
                    sect_file_offset = struct.unpack(f"{endian_format}I", data[sect_hdr_offset + 16:sect_hdr_offset + 20])[0]
                    sect_size = struct.unpack(f"{endian_format}I", data[sect_hdr_offset + 20:sect_hdr_offset + 24])[0]
                else:  # 64-bit
                    sect_flags = struct.unpack(f"{endian_format}Q", data[sect_hdr_offset + 8:sect_hdr_offset + 16])[0]
                    sect_addr = struct.unpack(f"{endian_format}Q", data[sect_hdr_offset + 16:sect_hdr_offset + 24])[0]
                    sect_file_offset = struct.unpack(f"{endian_format}Q", data[sect_hdr_offset + 24:sect_hdr_offset + 32])[0]
                    sect_size = struct.unpack(f"{endian_format}Q", data[sect_hdr_offset + 32:sect_hdr_offset + 40])[0]

                # Check if section is executable (SHF_EXECINSTR = 0x4)
                if sect_flags & 0x4 and sect_file_offset > 0 and sect_size > 0:
                    # Validate section boundaries with integer overflow protection
                    if (sect_file_offset < len(data) and
                        sect_size <= len(data) and  # Prevent size overflow
                        sect_file_offset <= len(data) - sect_size):  # Prevent offset+size overflow

                        # Additional sanity check: don't process sections larger than 100MB
                        if sect_size <= 100 * 1024 * 1024:
                            section_data = data[sect_file_offset:sect_file_offset + sect_size]
                            sections.append({
                                "name": f"section_{i}",
                                "offset": sect_file_offset,
                                "size": sect_size,
                                "data": section_data,
                                "flags": hex(sect_flags),
                                "address": hex(sect_addr)
                            })
                        else:
                            logger.debug(f"Skipping oversized ELF section: {sect_size} bytes")

        except (struct.error, IndexError) as e:
            logger.debug(f"Error parsing ELF sections: {str(e)}")

        return sections

    def _get_macho_executable_sections(self, data: bytes) -> List[Dict[str, Any]]:
        """Get executable sections from Mach-O binary."""
        sections: List[Dict[str, Any]] = []

        try:
            if len(data) < 28:  # Minimum Mach-O header size
                return sections

            # Read Mach-O magic and determine architecture
            magic = struct.unpack("<I", data[0:4])[0]
            if magic in [0xfeedface, 0xfeedfacf]:  # 32-bit and 64-bit
                is_64bit = (magic == 0xfeedfacf)
                header_size = 32 if is_64bit else 28

                if len(data) < header_size:
                    return sections

                ncmds = struct.unpack("<I", data[16:20])[0]

                # Validate number of commands for potential attacks
                if ncmds > 1000 or ncmds == 0:  # Reasonable limits
                    logger.debug(f"Invalid Mach-O ncmds: {ncmds}")
                    return sections

                # Parse load commands to find executable segments
                cmd_offset = header_size
                for _ in range(min(ncmds, 50)):  # Limit to prevent DoS
                    if cmd_offset + 8 > len(data):
                        break

                    cmd = struct.unpack("<I", data[cmd_offset:cmd_offset + 4])[0]
                    cmdsize = struct.unpack("<I", data[cmd_offset + 4:cmd_offset + 8])[0]

                    # LC_SEGMENT (32-bit) or LC_SEGMENT_64 (64-bit)
                    if cmd == 1 or cmd == 25:
                        seg_cmd_size = 56 if cmd == 1 else 72
                        if cmd_offset + seg_cmd_size <= len(data):
                            if cmd == 1:  # 32-bit segment
                                fileoff = struct.unpack("<I", data[cmd_offset + 32:cmd_offset + 36])[0]
                                filesize = struct.unpack("<I", data[cmd_offset + 36:cmd_offset + 40])[0]
                                maxprot = struct.unpack("<I", data[cmd_offset + 24:cmd_offset + 28])[0]
                            else:  # 64-bit segment
                                fileoff = struct.unpack("<Q", data[cmd_offset + 40:cmd_offset + 48])[0]
                                filesize = struct.unpack("<Q", data[cmd_offset + 48:cmd_offset + 56])[0]
                                maxprot = struct.unpack("<I", data[cmd_offset + 32:cmd_offset + 36])[0]

                            # Check if segment is executable (VM_PROT_EXECUTE = 0x4)
                            if (maxprot & 0x4) and fileoff > 0 and filesize > 0:
                                # Validate segment boundaries with integer overflow protection
                                if (fileoff < len(data) and
                                    filesize <= len(data) and  # Prevent size overflow
                                    fileoff <= len(data) - filesize):  # Prevent offset+size overflow

                                    # Additional sanity check: don't process segments larger than 100MB
                                    if filesize <= 100 * 1024 * 1024:
                                        section_data = data[fileoff:fileoff + filesize]
                                        segname = data[cmd_offset + 8:cmd_offset + 24].rstrip(b"\x00").decode("ascii", errors="ignore")
                                        sections.append({
                                            "name": segname,
                                            "offset": fileoff,
                                            "size": filesize,
                                            "data": section_data,
                                            "protection": hex(maxprot)
                                        })
                                    else:
                                        logger.debug(f"Skipping oversized Mach-O segment: {filesize} bytes")

                    cmd_offset += cmdsize

        except (struct.error, IndexError, UnicodeDecodeError) as e:
            logger.debug(f"Error parsing Mach-O sections: {str(e)}")

        return sections

    @analysis_timeout(timeout_seconds=15)
    def _analyze_pe_binary(self, data: bytes) -> List[Dict[str, Any]]:
        """Analyze Windows PE binary for buffer overflow vulnerabilities."""
        warnings: List[Dict[str, Any]] = []

        try:
            # Basic PE header validation
            if len(data) < 64:  # Minimum PE header size
                return warnings

            # Get PE header offset
            pe_offset = struct.unpack("<I", data[60:64])[0] if len(data) > 63 else 0

            # Validate PE offset and ensure we have enough data
            if pe_offset >= len(data) or pe_offset + 96 > len(data):
                return warnings

            # Verify PE signature
            if data[pe_offset:pe_offset + 4] != b"PE\x00\x00":
                return warnings

            # Check ASLR support (DLL Characteristics in Optional Header)
            # Optional Header starts at PE_offset + 24
            optional_header_offset = pe_offset + 24

            # Check if we have enough data for DLL characteristics (at offset 70 in optional header)
            dll_char_offset = optional_header_offset + 70
            if dll_char_offset + 2 <= len(data):
                dll_characteristics = struct.unpack("<H", data[dll_char_offset:dll_char_offset + 2])[0]

                # Check for ASLR support (IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040)
                if not (dll_characteristics & 0x0040):
                    warnings.append(self.create_standard_warning(
                        "pe_missing_aslr",
                        "PE binary lacks ASLR (Address Space Layout Randomization) protection",
                        Severity.MEDIUM,
                        "Ensure binary is compiled with /DYNAMICBASE flag for ASLR support",
                        data=data,  # Pass data for hash calculation
                        dll_characteristics=hex(dll_characteristics)
                    ))

                # Check for DEP/NX support (IMAGE_DLLCHARACTERISTICS_NX_COMPAT = 0x0100)
                if not (dll_characteristics & 0x0100):
                    warnings.append(self.create_standard_warning(
                        "pe_missing_dep",
                        "PE binary lacks DEP (Data Execution Prevention) protection",
                        Severity.MEDIUM,
                        "Ensure binary is compiled with /NXCOMPAT flag for DEP support",
                        dll_characteristics=hex(dll_characteristics)
                    ))

                # Check for stack guard (IMAGE_DLLCHARACTERISTICS_GUARD_CF = 0x4000)
                if not (dll_characteristics & 0x4000):
                    warnings.append(self.create_standard_warning(
                        "pe_missing_cfg",
                        "PE binary lacks Control Flow Guard (CFG) protection",
                        Severity.LOW,  # CFG is newer, so lower severity
                        "Consider compiling with /GUARD:CF for additional protection",
                        dll_characteristics=hex(dll_characteristics)
                    ))

        except (struct.error, IndexError) as e:
            warnings.append(self.create_standard_warning(
                "pe_analysis_error",
                f"Error analyzing PE binary: {str(e)}",
                Severity.LOW
            ))

        return warnings

    @analysis_timeout(timeout_seconds=15)
    def _analyze_elf_binary(self, data: bytes) -> List[Dict[str, Any]]:
        """Analyze Linux ELF binary for buffer overflow vulnerabilities."""
        warnings: List[Dict[str, Any]] = []

        try:
            if len(data) < 64:  # Need at least full ELF header
                return warnings

            # Check ELF endianness (byte 5)
            endian = data[5]
            if endian == 1:  # ELFDATA2LSB (little-endian)
                endian_format = "<"
            elif endian == 2:  # ELFDATA2MSB (big-endian)
                endian_format = ">"
            else:
                warnings.append(self.create_standard_warning(
                    "elf_invalid_endian",
                    f"Invalid ELF endianness: {endian}",
                    Severity.HIGH,
                    "Potentially corrupted or malicious ELF binary"
                ))
                return warnings

            # Check ELF class (32/64 bit)
            elf_class = data[4]
            if elf_class not in [1, 2]:  # ELFCLASS32, ELFCLASS64
                warnings.append(self.create_standard_warning(
                    "elf_invalid_class",
                    f"Invalid ELF class: {elf_class}",
                    Severity.HIGH,
                    "Potentially corrupted or malicious ELF binary"
                ))
                return warnings

            is_64bit = (elf_class == 2)
            header_size = 64 if is_64bit else 52

            if len(data) < header_size:
                return warnings

            # Parse ELF header for program header information with correct endianness
            if is_64bit:
                phoff = struct.unpack(f"{endian_format}Q", data[32:40])[0]  # Program header offset
                phentsize = struct.unpack(f"{endian_format}H", data[54:56])[0]  # Program header entry size
                phnum = struct.unpack(f"{endian_format}H", data[56:58])[0]  # Number of program headers
            else:
                phoff = struct.unpack(f"{endian_format}I", data[28:32])[0]
                phentsize = struct.unpack(f"{endian_format}H", data[42:44])[0]
                phnum = struct.unpack(f"{endian_format}H", data[44:46])[0]

            # Analyze program headers for security features
            security_features = self._analyze_elf_program_headers(data, phoff, phentsize, phnum, is_64bit, endian_format)

            # Check for NX/DEP support via GNU_STACK program header
            if not security_features.get("nx_support", False):
                warnings.append(self.create_standard_warning(
                    "elf_missing_nx_bit",
                    "ELF binary may lack NX bit (Data Execution Prevention)",
                    Severity.MEDIUM,
                    "Executable stack detected - compile with -z noexecstack for security"
                ))

            # Check for stack canaries in more sophisticated ways
            stack_protection_indicators = [
                b"__stack_chk_fail",      # GCC stack protector
                b"__stack_chk_guard",     # Stack canary symbol
                b"__chk_fail",            # Alternative stack check
                b"__fortify_function"     # FORTIFY_SOURCE functions
            ]

            stack_protection_found = any(indicator in data for indicator in stack_protection_indicators)
            if not stack_protection_found:
                warnings.append(self.create_standard_warning(
                    "elf_missing_stack_protection",
                    "ELF binary lacks stack protection mechanisms",
                    Severity.MEDIUM,
                    "Compile with -fstack-protector-strong for better security"
                ))

            # Check for FORTIFY_SOURCE (additional buffer overflow protection)
            fortify_indicators = [
                b"__memcpy_chk",
                b"__strcpy_chk",
                b"__strcat_chk",
                b"__sprintf_chk"
            ]

            fortify_found = any(indicator in data for indicator in fortify_indicators)
            if not fortify_found:
                warnings.append(self.create_standard_warning(
                    "elf_missing_fortify_source",
                    "ELF binary lacks FORTIFY_SOURCE protection",
                    Severity.LOW,
                    "Compile with -D_FORTIFY_SOURCE=2 for additional buffer overflow protection"
                ))

            # Check for RELRO (RELocation Read-Only)
            if not security_features.get("relro_support", False):
                warnings.append(self.create_standard_warning(
                    "elf_missing_relro",
                    "ELF binary may lack RELRO protection",
                    Severity.LOW,
                    "Compile with -Wl,-z,relro,-z,now for RELRO protection"
                ))

            # Report any additional security features found
            if security_features.get("pie_enabled", False):
                # PIE is good - this is just informational
                pass  # No warning needed for PIE enabled
            else:
                warnings.append(self.create_standard_warning(
                    "elf_missing_pie",
                    "ELF binary may not be position independent (PIE)",
                    Severity.LOW,
                    "Compile with -fPIE -pie for position independent code"
                ))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "elf_analysis_error",
                f"Error analyzing ELF binary: {str(e)}",
                Severity.LOW
            ))

        return warnings

    def _analyze_elf_program_headers(self, data: bytes, phoff: int, phentsize: int, phnum: int, is_64bit: bool, endian_format: str) -> Dict[str, bool]:
        """Analyze ELF program headers for security features."""
        security_features = {
            "nx_support": True,  # Assume NX unless proven otherwise
            "relro_support": False,
            "pie_enabled": False
        }

        try:
            # Limit number of program headers to prevent DoS
            phnum = min(phnum, 100)

            for i in range(phnum):
                ph_offset = phoff + (i * phentsize)
                if ph_offset + phentsize > len(data):
                    break

                # Parse program header with correct endianness
                if is_64bit:
                    if ph_offset + 32 > len(data):
                        break
                    p_type = struct.unpack(f"{endian_format}I", data[ph_offset:ph_offset + 4])[0]
                    p_flags = struct.unpack(f"{endian_format}I", data[ph_offset + 4:ph_offset + 8])[0]
                else:
                    if ph_offset + 28 > len(data):
                        break
                    p_type = struct.unpack(f"{endian_format}I", data[ph_offset:ph_offset + 4])[0]
                    p_flags = struct.unpack(f"{endian_format}I", data[ph_offset + 24:ph_offset + 28])[0]

                # PT_GNU_STACK = 0x6474e551 - GNU stack permissions
                if p_type == 0x6474e551:  # PT_GNU_STACK
                    # Check if stack is executable (PF_X = 0x1)
                    if p_flags & 0x1:
                        security_features["nx_support"] = False  # Executable stack = no NX

                # PT_GNU_RELRO = 0x6474e552 - GNU RELRO
                elif p_type == 0x6474e552:  # PT_GNU_RELRO
                    security_features["relro_support"] = True

                # PT_DYNAMIC = 0x2 - Dynamic linking info
                elif p_type == 0x2:  # PT_DYNAMIC
                    # PIE binaries have dynamic sections
                    security_features["pie_enabled"] = True

        except (struct.error, IndexError) as e:
            logger.debug(f"Error parsing ELF program headers: {str(e)}")

        return security_features

    def _analyze_macho_binary(self, data: bytes) -> List[Dict[str, Any]]:
        """Analyze macOS Mach-O binary for buffer overflow vulnerabilities."""
        warnings: List[Dict[str, Any]] = []

        # Basic Mach-O validation (simplified)
        if len(data) < 32:  # Minimum Mach-O header size
            return warnings

        warnings.append(self.create_standard_warning(
            "macho_binary_detected",
            "Mach-O binary detected in model",
            Severity.MEDIUM,
            "Verify the legitimacy of native macOS code in the model"
        ))

        return warnings

    @analysis_timeout(timeout_seconds=10)
    def _scan_dangerous_functions(self, data: bytes, context: str = "") -> List[Dict[str, Any]]:
        """Scan for dangerous function calls that can lead to buffer overflows."""
        warnings = []
        found_functions = set()

        for func_name in self.dangerous_functions:
            # More sophisticated detection to reduce false positives
            # Look for symbol table patterns and null-terminated function names
            symbol_patterns = [
                func_name + b"\x00",  # Null-terminated string (common in binaries)
                func_name + b"@",     # Symbol with version info (Linux)
                func_name + b"@@",    # Symbol with default version (Linux)
                b"\x00" + func_name + b"\x00",  # Embedded null-terminated string
            ]

            # Check for PLT entries (procedure linkage table) - Linux/ELF specific
            plt_pattern = b".plt" + func_name
            symbol_patterns.append(plt_pattern)

            # Check for import table entries - Windows PE specific
            import_pattern = b"\x00" + func_name + b"\x00\x00"  # Import name with padding
            symbol_patterns.append(import_pattern)

            for pattern in symbol_patterns:
                if pattern in data:
                    found_functions.add(func_name.decode("ascii", errors="ignore"))
                    break  # Found this function, move to next

        if found_functions:
            severity = Severity.HIGH if len(found_functions) > 3 else Severity.MEDIUM
            context_str = f" in {context}" if context else ""
            warnings.append(self.create_standard_warning(
                "dangerous_functions_detected",
                f"Dangerous functions detected{context_str}: {', '.join(sorted(found_functions))}",
                severity,
                "These functions are prone to buffer overflow vulnerabilities",
                data=data,  # Pass data for comprehensive metadata
                functions_found=list(found_functions),
                function_count=len(found_functions),
                detection_method="symbol_analysis",
                analysis_context=context
            ))

        return warnings

    @analysis_timeout(timeout_seconds=10)
    def _analyze_binary_patterns(self, data: bytes, context: str = "", max_scan_size: int = 1024 * 1024) -> List[Dict[str, Any]]:
        """Analyze binary patterns for potential vulnerabilities.

        This replaces the problematic regex-based assembly analysis with
        direct binary pattern matching, which is more reliable and efficient.
        """
        warnings = []

        # Limit scan size to prevent performance issues on large files
        scan_data = data[:max_scan_size] if len(data) > max_scan_size else data

        pattern_counts = {}
        total_suspicious_patterns = 0

        # Look for specific binary instruction patterns
        for pattern, description in self.suspicious_binary_patterns:
            count = scan_data.count(pattern)
            if count > 0:
                pattern_counts[description] = count
                total_suspicious_patterns += count

        # Only report if we find a significant concentration of patterns
        if total_suspicious_patterns > 5:  # Threshold to reduce false positives
            severity = Severity.HIGH if total_suspicious_patterns > 20 else Severity.MEDIUM

            # Create summary of found patterns
            pattern_summary = ", ".join([f"{desc}({count})" for desc, count in pattern_counts.items()])

            context_str = f" in {context}" if context else ""
            warnings.append(self.create_standard_warning(
                "suspicious_binary_patterns",
                f"Suspicious binary patterns detected{context_str}: {pattern_summary}",
                severity,
                "Binary contains patterns commonly found in exploit code or vulnerable compiled code",
                total_patterns=total_suspicious_patterns,
                pattern_breakdown=pattern_counts,
                scan_size_bytes=len(scan_data),
                detection_method="binary_pattern_analysis",
                analysis_context=context
            ))

        return warnings

    def _check_integer_overflow_patterns(self, data: bytes, context: str = "") -> List[Dict[str, Any]]:
        """Check for integer overflow patterns in binary data."""
        warnings = []

        # Look for suspicious large integer values that might cause overflow
        suspicious_patterns = [
            # Common overflow values
            (b"\xff\xff\xff\xff", "max_uint32"),
            (b"\xff\xff\xff\xff\xff\xff\xff\xff", "max_uint64"),
            # Large dimension values that might overflow
            (struct.pack("<I", 0x7fffffff), "max_int32"),
            (struct.pack("<Q", 0x7fffffffffffffff), "max_int64"),
        ]

        for pattern, pattern_type in suspicious_patterns:
            if pattern in data:
                # Count occurrences to understand the scale
                count = data.count(pattern)
                
                # Flag if we find these patterns - even once can be suspicious
                # Adjust threshold based on pattern type
                if count > 0:  # Any occurrence is worth checking
                    context_str = f" in {context}" if context else ""
                    warnings.append(self.create_standard_warning(
                        f"integer_overflow_pattern_{pattern_type}",
                        f"Potential integer overflow pattern detected{context_str}: {pattern_type} (found {count} times)",
                        Severity.MEDIUM,
                        "Large integer values may cause buffer overflows in calculations",
                        pattern_type=pattern_type,
                        occurrence_count=count,
                        analysis_context=context
                    ))

        return warnings

    # Removed _safe_regex_scan() - was only used once and overly complex

    def _scan_format_string_vulns(self, data: bytes, context: str = "") -> List[Dict[str, Any]]:
        """Scan for format string vulnerability patterns.
        
        NOTE: These patterns are often false positives in binary model files where
        random byte sequences happen to match format specifiers like %n, %x, %p.
        Marked as LOW severity to avoid false alarms on legitimate models.
        """
        warnings = []

        # Simple byte patterns (no regex needed) - most efficient
        simple_patterns = [
            (rb"%n", "format_n_specifier"),           # %n format specifier (dangerous)
            (rb"%s%s%s%s", "repeated_s"),             # Multiple %s without arguments  
            (rb"%x%x%x%x", "repeated_x"),             # Multiple %x (stack reading)
            (rb"%p%p%p", "repeated_p"),               # Multiple %p (pointer reading)
        ]

        # Check simple patterns first (faster)
        for pattern, pattern_type in simple_patterns:
            if pattern in data:
                count = data.count(pattern)
                
                # Flag if we find format string patterns
                # LOW severity since these are often random byte patterns in model weights
                if count > 0:
                    context_str = f" in {context}" if context else ""
                    warnings.append(self.create_standard_warning(
                        "format_string_vulnerabilities",
                        f"Format string patterns: {pattern_type} ({count} matches in {len(data)/1024/1024:.1f}MB model)",
                        Severity.LOW,
                        "Format string patterns detected - likely false positive from binary model data",
                        pattern_detected=pattern.decode("ascii", errors="ignore"),
                        pattern_type=pattern_type,
                        occurrence_count=count,
                        analysis_context=context,
                        data_size_mb=len(data) / 1024 / 1024
                    ))

        # More complex regex patterns with rate limiting (if enabled)
        if self.deep_binary_analysis:
            regex_patterns = [
                (rb"%.{6,}d", "large_width_specifier"),    # Very large width specifier
                (rb"%\d{6,}", "extreme_width_spec"),       # Extreme width values
                (rb"%.*%n", "format_n_with_args"),         # %n with preceding format specs
            ]

            for pattern, pattern_type in regex_patterns:
                try:
                    # Inline simplified regex scan (was _safe_regex_scan)
                    scan_data = data[:self.max_regex_scan_size] if len(data) > self.max_regex_scan_size else data
                    import re
                    matches = list(re.finditer(pattern, scan_data, re.IGNORECASE))
                    count = len(matches)

                    if count > 0:
                        warnings.append(self.create_standard_warning(
                            "format_string_vulnerabilities",
                            f"Complex format string pattern detected: {pattern_type} ({count} occurrences)",
                            Severity.LOW,
                            "Complex format string patterns detected - likely false positive from binary model data",
                            pattern_type=pattern_type,
                            occurrence_count=count,
                            detection_method="regex_analysis"
                        ))
                except Exception as e:
                    logger.debug(f"Error scanning format string pattern {pattern_type}: {e}")

        return warnings

    @analysis_timeout(timeout_seconds=30)
    def _scan_archive_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan archive files for native code and buffer overflow risks."""
        warnings = []

        try:
            file_ext = file_path.suffix.lower()

            if file_ext == ".zip":
                warnings.extend(self._scan_zip_archive(file_path))
            elif file_ext in {".tar", ".tar.gz", ".tgz"}:
                warnings.extend(self._scan_tar_archive(file_path))
            elif file_ext == ".gz":
                warnings.extend(self._scan_gzip_file(file_path))
            else:
                # Unknown archive format
                warnings.append(self.create_standard_warning(
                    "unsupported_archive_format",
                    f"Unsupported archive format: {file_ext}",
                    Severity.LOW,
                    "Archive format is not supported for detailed security analysis"
                ))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "archive_scan_error",
                f"Error scanning archive {file_path}: {str(e)}",
                Severity.MEDIUM
            ))

        return warnings

    def _scan_zip_archive(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan ZIP archive contents for buffer overflow risks."""
        warnings = []
        native_files_found = []

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                entries = zf.infolist()

                if len(entries) > self.max_archive_entries:
                    warnings.append(self.create_standard_warning(
                        "archive_too_many_entries",
                        f"Archive contains {len(entries)} entries (limit: {self.max_archive_entries})",
                        Severity.MEDIUM,
                        "Large archives may contain hidden malicious files"
                    ))

                for entry in entries[:self.max_archive_entries]:  # Limit processing
                    entry_path = Path(entry.filename)

                    # Check for native library files
                    if entry_path.suffix.lower() in self.native_extensions:
                        native_files_found.append(entry.filename)

                    # Check for suspicious paths
                    if ".." in entry.filename or entry.filename.startswith("/"):
                        warnings.append(self.create_standard_warning(
                            "archive_path_traversal",
                            f"Suspicious archive path: {entry.filename}",
                            Severity.HIGH,
                            "Path traversal in archives can lead to arbitrary file writes"
                        ))

                if native_files_found:
                    warnings.append(self.create_standard_warning(
                        "archive_contains_native_code",
                        f"Archive contains native libraries: {', '.join(native_files_found[:5])}",
                        Severity.HIGH,
                        "Native code in archives poses security risks",
                        native_files=native_files_found,
                        native_file_count=len(native_files_found)
                    ))

        except zipfile.BadZipFile:
            warnings.append(self.create_standard_warning(
                "invalid_zip_archive",
                "Invalid or corrupted ZIP archive",
                Severity.MEDIUM
            ))

        return warnings

    def _scan_tar_archive(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan TAR archive contents for buffer overflow risks."""
        warnings = []
        native_files_found = []

        try:
            # Determine if it's compressed
            mode = "r:gz" if file_path.suffix.lower() in {".tar.gz", ".tgz"} else "r"

            with tarfile.open(str(file_path), mode) as tf:  # type: ignore[call-overload]
                members = tf.getmembers()

                if len(members) > self.max_archive_entries:
                    warnings.append(self.create_standard_warning(
                        "archive_too_many_entries",
                        f"TAR archive contains {len(members)} entries (limit: {self.max_archive_entries})",
                        Severity.MEDIUM,
                        "Large archives may contain hidden malicious files"
                    ))

                for member in members[:self.max_archive_entries]:  # Limit processing
                    member_path = Path(member.name)

                    # Check for native library files
                    if member_path.suffix.lower() in self.native_extensions:
                        native_files_found.append(member.name)

                    # Check for suspicious paths (path traversal)
                    if ".." in member.name or member.name.startswith("/"):
                        warnings.append(self.create_standard_warning(
                            "archive_path_traversal",
                            f"Suspicious TAR path: {member.name}",
                            Severity.HIGH,
                            "Path traversal in archives can lead to arbitrary file writes"
                        ))

                    # Check for unusually large files (potential zip bomb)
                    if member.size > 100 * 1024 * 1024:  # 100MB
                        warnings.append(self.create_standard_warning(
                            "archive_large_file",
                            f"TAR contains very large file: {member.name} ({member.size} bytes)",
                            Severity.MEDIUM,
                            "Very large files in archives may indicate decompression bomb"
                        ))

                if native_files_found:
                    warnings.append(self.create_standard_warning(
                        "archive_contains_native_code",
                        f"TAR archive contains native libraries: {', '.join(native_files_found[:5])}",
                        Severity.HIGH,
                        "Native code in archives poses security risks",
                        native_files=native_files_found,
                        native_file_count=len(native_files_found)
                    ))

        except (tarfile.TarError, tarfile.ReadError, tarfile.CompressionError) as e:
            warnings.append(self.create_standard_warning(
                "invalid_tar_archive",
                f"Invalid or corrupted TAR archive: {str(e)}",
                Severity.MEDIUM
            ))

        return warnings

    def _scan_gzip_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan GZIP file for potential risks."""
        warnings = []

        try:
            # Check if it's a standalone gzip file
            with gzip.open(file_path, "rb") as gz_file:
                # Read first few KB to check content
                header_data = gz_file.read(8192)

                if header_data:
                    # Check if decompressed content contains native code patterns
                    if any(pattern in header_data for pattern in [b"ELF", b"MZ", b"\xfe\xed\xfa"]):
                        warnings.append(self.create_standard_warning(
                            "gzip_contains_executable",
                            "GZIP file contains executable content",
                            Severity.HIGH,
                            "Compressed executables may bypass security scanners"
                        ))

                    # Check for dangerous function names in compressed content
                    dangerous_found = any(func in header_data for func in [b"strcpy", b"gets", b"sprintf"])
                    if dangerous_found:
                        warnings.append(self.create_standard_warning(
                            "gzip_contains_dangerous_functions",
                            "GZIP file may contain code with dangerous functions",
                            Severity.MEDIUM,
                            "Compressed code may contain buffer overflow vulnerabilities"
                        ))

        except (gzip.BadGzipFile, OSError) as e:
            warnings.append(self.create_standard_warning(
                "invalid_gzip_file",
                f"Invalid or corrupted GZIP file: {str(e)}",
                Severity.MEDIUM
            ))

        return warnings

    def _scan_native_library(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Scan native library files for buffer overflow vulnerabilities."""
        warnings = []

        # Always flag native libraries as high risk
        file_path = Path(model_file.file_info.path)
        warnings.append(self.create_standard_warning(
            "native_library_detected",
            f"Native library detected: {file_path.name}",
            Severity.HIGH,
            "Native libraries in ML models pose significant security risks",
            library_type=file_path.suffix,
            file_size_mb=model_file.size_mb
        ))

        # Perform binary analysis if enabled
        if self.scan_native_libs:
            with model_file as mf:
                # Read first chunk to analyze headers
                chunk_data = next(mf.iter_chunks(), b"")
                if chunk_data:
                    warnings.extend(self.validate(chunk_data))

        return warnings

    def _scan_compiled_model(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Scan compiled model formats (ONNX, TensorRT, etc.) for buffer overflow risks."""
        warnings = []

        file_ext = Path(model_file.file_info.path).suffix.lower()

        if file_ext == ".onnx" and self.scan_onnx_operators:
            warnings.extend(self._scan_onnx_model(model_file))
        elif file_ext in {".trt", ".engine", ".tensorrt"} and self.scan_gpu_kernels:
            warnings.extend(self._scan_tensorrt_model(model_file))

        return warnings

    @analysis_timeout(timeout_seconds=20)
    def _scan_onnx_model(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Scan ONNX model for custom operators with potential buffer overflow risks."""
        warnings = []

        try:
            with model_file as mf:
                # Read limited amount of data to analyze ONNX protobuf structure
                # Respect memory limits to prevent OOM attacks
                max_bytes = min(
                    self.max_file_size_mb * 1024 * 1024,  # Respect configured limit
                    10 * 1024 * 1024  # Hard cap at 10MB for analysis
                )

                # Use more memory-efficient approach
                data = bytearray()
                bytes_read = 0

                for chunk in mf.iter_chunks():
                    # Check current memory usage before adding chunk
                    chunk_size = len(chunk)

                    # Check if adding this chunk would exceed our limit
                    if bytes_read + chunk_size > max_bytes:
                        # Take only what we can fit
                        remaining = max_bytes - bytes_read
                        if remaining > 0:
                            data.extend(chunk[:remaining])
                            bytes_read += remaining
                        break

                    data.extend(chunk)
                    bytes_read += chunk_size

                    # Additional memory safety: check actual memory usage
                    if len(data) > max_bytes:
                        logger.warning("ONNX analysis: memory limit exceeded, truncating data")
                        data = data[:max_bytes]
                        break

                # Convert to bytes once for analysis
                data_bytes = bytes(data)

                # Log the analysis scope for debugging
                logger.debug(f"ONNX analysis: processed {bytes_read} bytes from {model_file.size_bytes} total")

                # Look for custom operator indicators
                if b"domain" in data_bytes and b"custom" in data_bytes.lower():
                    warnings.append(self.create_standard_warning(
                        "onnx_custom_operators",
                        "ONNX model may contain custom operators",
                        Severity.MEDIUM,
                        "Custom operators may contain native code with buffer overflow risks",
                        model_file=model_file,  # Pass model_file for comprehensive metadata
                        data=data_bytes
                    ))

                # Check for external data references (potential code loading)
                if b"external_data" in data_bytes:
                    warnings.append(self.create_standard_warning(
                        "onnx_external_data",
                        "ONNX model references external data files",
                        Severity.MEDIUM,
                        "External data files may contain malicious native code",
                        model_file=model_file,  # Pass model_file for comprehensive metadata
                        data=data_bytes
                    ))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "onnx_scan_error",
                f"Error scanning ONNX model: {str(e)}",
                Severity.LOW
            ))

        return warnings

    def _scan_tensorrt_model(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Scan TensorRT/GPU models for kernel buffer overflow risks."""
        warnings = []

        # TensorRT engines contain compiled GPU kernels - always high risk
        warnings.append(self.create_standard_warning(
            "tensorrt_engine_detected",
            "TensorRT engine contains compiled GPU kernels",
            Severity.HIGH,
            "GPU kernels may contain buffer overflow vulnerabilities",
            engine_size_mb=model_file.size_mb
        ))

        return warnings

    def supports_streaming(self) -> bool:
        """Buffer overflow validator supports streaming for large files."""
        return True

    def validate_chunk(self, chunk_info: "ChunkInfo", context: "StreamingContext") -> List[Dict[str, Any]]:
        """Validate a single chunk for buffer overflow patterns.
        
        This method performs lightweight chunk-level analysis instead of running
        the full validate() method on each chunk, which was causing timeouts.
        """
        warnings = []
        
        try:
            chunk_data = chunk_info.data
            
            # Quick binary type detection for this chunk
            binary_type = self._detect_binary_type(chunk_data)
            
            if binary_type:
                # For binary chunks, do lightweight analysis
                warnings.extend(self._scan_dangerous_functions(chunk_data, f"chunk_{chunk_info.chunk_index}"))
                
                # Only do expensive analysis on first chunk (header) or if deep analysis is enabled
                if chunk_info.chunk_index == 0 or self.deep_binary_analysis:
                    # Check for integer overflow patterns
                    warnings.extend(self._check_integer_overflow_patterns(chunk_data, f"chunk_{chunk_info.chunk_index}"))
                    
                    # Check for format string vulnerabilities
                    warnings.extend(self._scan_format_string_vulns(chunk_data, f"chunk_{chunk_info.chunk_index}"))
                    
                    # Only do binary pattern analysis on first chunk to avoid performance issues
                    if chunk_info.chunk_index == 0:
                        warnings.extend(self._analyze_binary_patterns(chunk_data, f"chunk_{chunk_info.chunk_index}"))
            else:
                # For non-binary chunks, only scan for dangerous functions (lightweight)
                warnings.extend(self._scan_dangerous_functions(chunk_data, f"chunk_{chunk_info.chunk_index}"))
                
                # Skip expensive analysis for non-binary chunks to maintain performance
                if self.deep_binary_analysis and chunk_info.chunk_index == 0:
                    # Only do binary pattern analysis on first non-binary chunk
                    warnings.extend(self._analyze_binary_patterns(chunk_data, f"chunk_{chunk_info.chunk_index}"))
            
            # Update streaming context
            if not hasattr(context, "validation_results") or context.validation_results is None:
                context.validation_results = {}
                
            validator_context = context.validation_results.setdefault("buffer_overflow_streaming_context", {
                "total_chunks_processed": 0,
                "binary_chunks_found": 0,
                "dangerous_functions_found": 0,
                "warnings_generated": 0
            })
            
            validator_context["total_chunks_processed"] += 1
            if binary_type:
                validator_context["binary_chunks_found"] += 1
            
            # Count dangerous functions found in this chunk
            dangerous_count = sum(1 for warning in warnings if "dangerous_functions" in warning.get("type", ""))
            validator_context["dangerous_functions_found"] += dangerous_count
            validator_context["warnings_generated"] += len(warnings)
            
        except Exception as e:
            logger.error(f"Error validating buffer overflow chunk {chunk_info.chunk_index}: {str(e)}")
            warnings.append(self.create_standard_warning(
                "chunk_validation_error",
                f"Error validating chunk {chunk_info.chunk_index}: {str(e)}",
                Severity.MEDIUM,
                recommendation="Check chunk data integrity and validator compatibility",
                chunk_offset=chunk_info.offset,
                chunk_size=chunk_info.size,
                chunk_index=chunk_info.chunk_index,
                streaming_progress=context.progress_percent if context else 0.0
            ))
        
        return warnings

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based buffer overflow validation using high-performance Rust implementation.
        
        Uses Aho-Corasick algorithm with parallel processing for ~100x faster validation.
        No timeout needed - Rust implementation is fast enough to complete without timeout.
        """
        from palisade._native import BufferOverflowStreamingValidator
        import multiprocessing
        
        warnings = []
        
        try:
            # Create Rust streaming validator with parallel processing
            num_cores = multiprocessing.cpu_count()
            validator = BufferOverflowStreamingValidator(num_cores)
            
            logger.debug(f"Starting Rust-based buffer overflow validation (streaming, {num_cores} cores)")
            
            # Track file structure for context
            file_size_mb = model_file.file_info.size_bytes / (1024 * 1024)
            header_size_bytes = 0
            is_safetensors = self.metadata and self.metadata.model_type == ModelType.SAFETENSORS
            
            if is_safetensors:
                try:
                    header_data = model_file.read_safetensors_header()
                    header_size_bytes = len(header_data)
                    logger.debug(f"SafeTensors: header is {header_size_bytes} bytes ({header_size_bytes/(1024*1024):.2f} MB)")
                except Exception as e:
                    logger.debug(f"Could not parse SafeTensors header: {e}")
            
            # Process model in chunks using Rust validator (GIL-free)
            for chunk_info in model_file.iter_chunk_info():
                chunk_data = chunk_info.data
                
                # Process chunk with Rust (releases GIL for parallel processing)
                validator.process_chunk(chunk_data)
            
            # Finalize and get comprehensive results from Rust
            result = validator.finalize()
            
            logger.debug(
                f"Buffer overflow validation complete: {result.total_matches} total matches, "
                f"risk score {result.risk_score:.2f}"
            )
            logger.debug(
                f"Breakdown: {len(result.dangerous_functions_found)} dangerous functions, "
                f"{len(result.rop_gadgets_found)} ROP gadgets, "
                f"{len(result.format_string_vulns_found)} format string vulns, "
                f"{len(result.integer_overflow_patterns_found)} integer overflow patterns"
            )
            
            # Convert Rust results to Python warnings with context
            # Critical: Dangerous C functions
            if result.dangerous_functions_found:
                func_count = len(result.dangerous_functions_found)
                
                severity = Severity.CRITICAL if func_count > 5 else Severity.HIGH
                # Strip Rust internal prefixes for clean display
                func_names = self.strip_rust_prefixes(result.dangerous_functions_found, "dangerous:")
                funcs_list = ", ".join(sorted(set(func_names))[:10])
                if len(func_names) > 10:
                    funcs_list += f" (and {len(func_names) - 10} more)"
                
                warnings.append(self.create_standard_warning(
                    "dangerous_functions_detected",
                    f"Dangerous C/C++ functions: {funcs_list} ({func_count} matches in {file_size_mb:.1f}MB model)",
                    severity,
                    recommendation="Review if patterns appear in structured code sections or are random bytes in model weights",
                    threat_type="buffer_overflow",
                    attack_vector="Memory corruption via unsafe C functions",
                    functions_found=func_names[:20],  # Include up to 20 in details
                    match_count=func_count,
                    file_size_mb=round(file_size_mb, 2),
                    file_structure="SafeTensors (header + weights)" if is_safetensors else "Unknown format"
                ))
            
            # High-risk: ROP gadgets (context-aware severity)
            if result.rop_gadgets_found:
                gadget_count = len(result.rop_gadgets_found)
                
                # Smart severity: adjust for file size and format
                # Large models (>1GB) with few matches are likely random noise
                # Small files or high match counts suggest intentional embedding
                
                # Check if this is a known weight-based format (SafeTensors or GGUF)
                # Weight-based formats store neural network weights as data, not executable code
                is_gguf = self.metadata and hasattr(self.metadata, 'model_type') and self.metadata.model_type == ModelType.GGUF
                is_weight_format = is_safetensors or is_gguf
                
                logger.debug(
                    f"ROP gadgets severity calculation: file_size={file_size_mb:.1f}MB, "
                    f"gadget_count={gadget_count}, "
                    f"model_type={self.metadata.model_type if self.metadata else 'None'}, "
                    f"is_weight_format={is_weight_format}"
                )
                
                if file_size_mb > 1000:  # Large model (>1GB)
                    if gadget_count < 20:
                        severity = Severity.LOW  # Likely random noise in weights
                    elif gadget_count < 50:
                        severity = Severity.MEDIUM  # Worth investigating
                    else:
                        severity = Severity.HIGH  # Suspicious concentration
                elif file_size_mb > 100:  # Medium model (100MB-1GB)
                    if gadget_count < 10:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.HIGH
                else:  # Small model/file (<100MB)
                    # In small files, even few gadgets are suspicious
                    severity = Severity.HIGH if gadget_count > 3 else Severity.MEDIUM
                
                # Exception: If NOT a weight format (SafeTensors/GGUF), be more cautious
                # Pickle files or unknown formats could contain actual compiled code
                if not is_weight_format and gadget_count > 5:
                    severity = Severity.HIGH
                
                # Strip Rust internal prefixes for clean display
                gadget_names = self.strip_rust_prefixes(result.rop_gadgets_found, "rop:")
                gadgets_list = ", ".join(sorted(set(gadget_names))[:5])
                if len(gadget_names) > 5:
                    gadgets_list += f" (and {len(gadget_names) - 5} more)"
                
                # Contextual recommendation based on file type
                if is_weight_format and file_size_mb > 1000 and gadget_count < 20:
                    recommendation = "Low occurrence in large model weights - likely random noise, not executable code"
                elif is_weight_format:
                    recommendation = "Check if gadgets are clustered (intentional ROP chain) or scattered (random noise in weights)"
                else:
                    recommendation = "Non-weight format detected - verify file integrity and check for actual executable code"
                
                warnings.append(self.create_standard_warning(
                    "rop_gadgets_detected",
                    f"ROP gadgets: {gadgets_list} ({gadget_count} matches in {file_size_mb:.1f}MB model)",
                    severity,
                    recommendation=recommendation,
                    threat_type="code_injection",
                    attack_vector="Return-Oriented Programming (ROP)",
                    gadgets_found=gadget_names[:10],
                    match_count=gadget_count,
                    file_size_mb=round(file_size_mb, 2),
                    context="Weight-based format (SafeTensors/GGUF) - weights cannot execute as code" if is_weight_format else "Non-weight format - verify if compiled code"
                ))
            
            # Low-risk: Format string vulnerabilities (often false positives in model weights)
            if result.format_string_vulns_found:
                vuln_count = len(result.format_string_vulns_found)
                
                # Always LOW severity - these are typically random byte patterns in model weights
                severity = Severity.LOW
                # Strip Rust internal prefixes for clean display
                vuln_names = self.strip_rust_prefixes(result.format_string_vulns_found, "format_string:")
                vulns_list = ", ".join(sorted(set(vuln_names))[:5])
                
                warnings.append(self.create_standard_warning(
                    "format_string_vulnerabilities",
                    f"Format string patterns: {vulns_list} ({vuln_count} matches in {file_size_mb:.1f}MB model)",
                    severity,
                    recommendation="Format strings patterns detected - likely false positive from random bytes in model weights",
                    threat_type="memory_corruption",
                    attack_vector="Format string exploitation (unlikely in model weights)",
                    vulnerabilities_found=vuln_names,
                    match_count=vuln_count,
                    file_size_mb=round(file_size_mb, 2)
                ))
            
            # Low-risk: Integer overflow patterns
            if result.integer_overflow_patterns_found:
                severity = Severity.MEDIUM if len(result.integer_overflow_patterns_found) > 3 else Severity.LOW
                pattern_names = [p.replace("integer_overflow:", "") for p in result.integer_overflow_patterns_found]
                patterns_list = ", ".join(sorted(set(pattern_names))[:5])
                
                warnings.append(self.create_standard_warning(
                    "integer_overflow_patterns",
                    f"Integer overflow patterns detected: {patterns_list}",
                    severity,
                    recommendation="Review size calculations for potential integer overflows.",
                    threat_type="integer_overflow",
                    attack_vector="Arithmetic overflow in size calculations",
                    patterns_found=pattern_names
                ))
        
        except Exception as e:
            logger.error(f"Error during Rust buffer overflow validation: {e}")
            warnings.append(self.create_standard_warning(
                "buffer_overflow_validation_error",
                f"Validation error: {str(e)}",
                Severity.MEDIUM,
                recommendation="Check file integrity or try alternative validation method",
                attack_vector="Unknown"
            ))
        
        return warnings
