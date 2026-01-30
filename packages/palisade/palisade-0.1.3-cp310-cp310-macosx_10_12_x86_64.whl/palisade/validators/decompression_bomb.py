"""Enhanced Decompression Bomb Detection Validator.

Detects malicious compressed files that could cause memory exhaustion, CPU exhaustion,
or disk space attacks when decompressed. Includes ML-aware analysis of legitimate
model compression patterns vs suspicious decompression bombs.
"""

import gzip
import io
import logging
import math
import struct
import tarfile
import time
import zipfile
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from palisade.models.model_file import ModelFile

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.validators.base import BaseValidator, Severity

logger = logging.getLogger(__name__)


class DecompressionBombValidator(BaseValidator):
    """Enhanced validator for detecting decompression bombs in ML model files."""

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional[Any] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Security limits - configurable via policy
        self.max_compression_ratio = 1000  # 1000:1 max ratio
        self.max_uncompressed_size = 10 * 1024 * 1024 * 1024  # 10GB max expansion
        self.max_nested_levels = 3  # Max archive nesting depth
        self.max_analysis_time = 30  # Max seconds to analyze one file
        self.sample_size = 1024 * 1024  # 1MB sample for ratio estimation

        # ML model legitimate compression patterns
        self.legitimate_patterns = {
            # Format -> (typical ratio range, max acceptable ratio)
            "gguf_quantized": (2.0, 8.0),  # Q4_K_M, Q8_0 etc
            "safetensors_compressed": (1.2, 3.0),  # Typically low compression
            "tokenizer_json": (3.0, 20.0),  # JSON compresses well
            "numpy_arrays": (2.0, 10.0),  # Embedding arrays
            "model_archives": (1.5, 5.0),  # .tar.gz with models
        }

        # Known compression formats to analyze
        self.compression_formats = {
            b"\x1f\x8b": "gzip",
            b"PK\x03\x04": "zip",
            b"PK\x05\x06": "zip",
            b"PK\x07\x08": "zip",
            b"\x42\x5a\x68": "bzip2",
            b"\xfd7zXZ": "xz",
            b"\x28\xb5\x2f\xfd": "zstd",
            b"ustar": "tar",
        }

    def can_validate(self, model_type: ModelType) -> bool:
        """Can validate any file type for compression bombs."""
        return True  # Universal - any file could contain compressed data

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate data for decompression bomb patterns."""
        warnings = []

        try:
            start_time = time.time()

            # Quick format detection
            compression_format = self._detect_compression_format(data)
            if not compression_format:
                # Check for embedded compressed data
                embedded_compressed = self._scan_for_embedded_compression(data[:self.sample_size])
                if not embedded_compressed:
                    return warnings  # No compression detected
                compression_format = embedded_compressed

            # Analyze compression characteristics
            analysis_result = self._analyze_compression_safety(data, compression_format, start_time)

            if analysis_result["is_suspicious"]:
                warnings.append(self.create_standard_warning(
                    warning_type="decompression_bomb_detected",
                    message=analysis_result["message"],
                    severity=analysis_result["severity"],
                    recommendation=analysis_result["recommendation"],
                    compression_format=compression_format,
                    estimated_ratio=analysis_result.get("compression_ratio", 0),
                    estimated_uncompressed_size=analysis_result.get("estimated_size", 0),
                    analysis_time=analysis_result.get("analysis_time", 0),
                    threat_indicators=analysis_result.get("threat_indicators", []),
                ))

            # Check for nested compression (compression bomb technique)
            nested_result = self._check_nested_compression(data, compression_format)
            if nested_result["nested_levels"] > self.max_nested_levels:
                warnings.append(self.create_standard_warning(
                    warning_type="suspicious_nested_compression",
                    message=f"Deeply nested compression detected ({nested_result['nested_levels']} levels)",
                    severity=Severity.HIGH,
                    recommendation="Nested compression >3 levels is highly suspicious and often indicates decompression bombs",
                    nested_levels=nested_result["nested_levels"],
                    compression_chain=nested_result["formats"],
                ))

            # Check for anomalous compression patterns
            pattern_result = self._analyze_compression_patterns(data, compression_format)
            if pattern_result["anomalous"]:
                warnings.append(self.create_standard_warning(
                    warning_type="anomalous_compression_pattern",
                    message=pattern_result["message"],
                    severity=Severity.MEDIUM,
                    recommendation=pattern_result["recommendation"],
                    pattern_indicators=pattern_result["indicators"],
                ))

        except Exception as e:
            logger.error(f"Error in decompression bomb validation: {str(e)}")
            warnings.append(self.create_standard_warning(
                warning_type="decompression_analysis_error",
                message=f"Failed to analyze file for decompression bombs: {str(e)}",
                severity=Severity.LOW,
                recommendation="Manual review recommended if file contains compressed data",
            ))

        return warnings

    def _detect_compression_format(self, data: bytes) -> Optional[str]:
        """Detect compression format from file headers."""
        if len(data) < 10:
            return None

        # Check known compression signatures
        for signature, format_name in self.compression_formats.items():
            if data.startswith(signature):
                return format_name

            # Also check at common offsets (some formats have headers)
            if len(data) > 512:
                if signature in data[:512]:
                    return format_name

        return None

    def _scan_for_embedded_compression(self, data: bytes) -> Optional[str]:
        """Scan for compressed data embedded within the file."""
        for signature, format_name in self.compression_formats.items():
            if signature in data:
                offset = data.find(signature)
                if offset > 0:  # Found embedded compression
                    logger.debug(f"Found embedded {format_name} at offset {offset}")
                    return format_name
        return None

    def _analyze_compression_safety(self, data: bytes, compression_format: str, start_time: float) -> Dict[str, Any]:
        """Analyze compression for safety - detect bombs without full decompression."""
        analysis_time = time.time() - start_time

        # Time-bounded analysis
        if analysis_time > self.max_analysis_time:
            return {
                "is_suspicious": True,
                "message": f"Compression analysis timeout ({analysis_time:.1f}s) - possible CPU exhaustion attack",
                "severity": Severity.HIGH,
                "recommendation": "File analysis taking too long suggests decompression bomb or corrupted archive",
                "analysis_time": analysis_time,
                "threat_indicators": ["analysis_timeout"],
            }

        try:
            if compression_format == "gzip":
                return self._analyze_gzip_safety(data)
            elif compression_format == "zip":
                return self._analyze_zip_safety(data)
            elif compression_format == "tar":
                return self._analyze_tar_safety(data)
            else:
                # Generic compression analysis
                return self._analyze_generic_compression(data, compression_format)

        except Exception as e:
            logger.debug(f"Compression analysis failed for {compression_format}: {str(e)}")
            return {
                "is_suspicious": False,
                "message": f"Could not analyze {compression_format} compression safely",
                "severity": Severity.LOW,
                "recommendation": "Manual review recommended",
                "analysis_time": analysis_time,
            }

    def _analyze_gzip_safety(self, data: bytes) -> Dict[str, Any]:
        """Analyze gzip files for decompression bombs."""
        threat_indicators = []

        try:
            # Parse gzip header to get uncompressed size (last 4 bytes)
            if len(data) < 18:  # Minimum gzip file size
                return {"is_suspicious": False, "message": "File too small to be valid gzip"}

            # GZIP stores uncompressed size in last 4 bytes (mod 2^32)
            uncompressed_size_mod = struct.unpack("<I", data[-4:])[0]
            compressed_size = len(data)

            # If uncompressed size wraps around (>4GB), it's potentially dangerous
            if uncompressed_size_mod < compressed_size and compressed_size > 1024 * 1024:
                threat_indicators.append("size_wraparound_possible")

            # Estimate actual ratio by partial decompression
            estimated_ratio, estimated_size = self._estimate_compression_ratio_gzip(data)

            if estimated_ratio > self.max_compression_ratio:
                threat_indicators.append("extreme_compression_ratio")

            if estimated_size > self.max_uncompressed_size:
                threat_indicators.append("excessive_uncompressed_size")

            is_suspicious = len(threat_indicators) > 0
            severity = Severity.HIGH if estimated_ratio > 5000 else Severity.MEDIUM

            return {
                "is_suspicious": is_suspicious,
                "message": f"GZIP compression ratio: {estimated_ratio:.1f}:1, estimated size: {estimated_size // (1024*1024)}MB",
                "severity": severity,
                "recommendation": self._get_compression_recommendation(estimated_ratio, estimated_size),
                "compression_ratio": estimated_ratio,
                "estimated_size": estimated_size,
                "threat_indicators": threat_indicators,
            }

        except Exception as e:
            logger.debug(f"GZIP analysis failed: {str(e)}")
            return {"is_suspicious": False, "message": f"GZIP analysis error: {str(e)}"}

    def _analyze_zip_safety(self, data: bytes) -> Dict[str, Any]:
        """Analyze ZIP files for decompression bombs (zip bombs)."""
        threat_indicators = []

        try:
            # Use in-memory ZIP analysis to avoid file I/O
            zip_buffer = io.BytesIO(data)

            total_compressed = 0
            total_uncompressed = 0
            file_count = 0
            max_single_ratio = 0
            suspicious_files = []

            # Parse ZIP without extracting
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue

                    file_count += 1
                    total_compressed += info.compress_size
                    total_uncompressed += info.file_size

                    # Check individual file ratios
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        max_single_ratio = max(max_single_ratio, ratio)

                        if ratio > 1000:  # Suspicious individual file
                            suspicious_files.append({
                                "filename": info.filename,
                                "ratio": ratio,
                                "uncompressed_size": info.file_size,
                            })

            # Calculate overall statistics
            overall_ratio = total_uncompressed / total_compressed if total_compressed > 0 else 1

            # Detection logic
            if overall_ratio > self.max_compression_ratio:
                threat_indicators.append("extreme_overall_ratio")

            if max_single_ratio > self.max_compression_ratio * 2:
                threat_indicators.append("extreme_single_file_ratio")

            if total_uncompressed > self.max_uncompressed_size:
                threat_indicators.append("excessive_total_size")

            if file_count > 10000:  # Too many files can cause FS exhaustion
                threat_indicators.append("excessive_file_count")

            is_suspicious = len(threat_indicators) > 0
            severity = Severity.HIGH if max_single_ratio > 10000 or len(suspicious_files) > 5 else Severity.MEDIUM

            return {
                "is_suspicious": is_suspicious,
                "message": f"ZIP analysis: {file_count} files, {overall_ratio:.1f}:1 overall ratio, max single file: {max_single_ratio:.1f}:1",
                "severity": severity,
                "recommendation": self._get_zip_recommendation(overall_ratio, suspicious_files),
                "compression_ratio": overall_ratio,
                "estimated_size": total_uncompressed,
                "threat_indicators": threat_indicators,
                "suspicious_files_count": len(suspicious_files),
                "total_files": file_count,
            }

        except Exception as e:
            logger.debug(f"ZIP analysis failed: {str(e)}")
            return {"is_suspicious": False, "message": f"ZIP analysis error: {str(e)}"}

    def _analyze_tar_safety(self, data: bytes) -> Dict[str, Any]:
        """Analyze TAR files for decompression bombs."""
        threat_indicators = []

        try:
            tar_buffer = io.BytesIO(data)
            total_size = 0
            file_count = 0
            suspicious_files = []

            with tarfile.open(fileobj=tar_buffer, mode="r") as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        file_count += 1
                        total_size += member.size

                        # Check for suspiciously large individual files
                        if member.size > 1024 * 1024 * 1024:  # > 1GB
                            suspicious_files.append({
                                "filename": member.name,
                                "size": member.size,
                            })

            # TAR doesn't have compression ratios, but check total expansion
            compressed_size = len(data)
            expansion_ratio = total_size / compressed_size if compressed_size > 0 else 1

            if total_size > self.max_uncompressed_size:
                threat_indicators.append("excessive_total_size")

            if file_count > 50000:  # Filesystem exhaustion
                threat_indicators.append("excessive_file_count")

            is_suspicious = len(threat_indicators) > 0
            severity = Severity.MEDIUM

            return {
                "is_suspicious": is_suspicious,
                "message": f"TAR analysis: {file_count} files, {total_size // (1024*1024)}MB total, {expansion_ratio:.1f}:1 ratio",
                "severity": severity,
                "recommendation": "TAR file analysis completed - check individual file sizes",
                "compression_ratio": expansion_ratio,
                "estimated_size": total_size,
                "threat_indicators": threat_indicators,
                "total_files": file_count,
            }

        except Exception as e:
            logger.debug(f"TAR analysis failed: {str(e)}")
            return {"is_suspicious": False, "message": f"TAR analysis error: {str(e)}"}

    def _estimate_compression_ratio_gzip(self, data: bytes) -> Tuple[float, int]:
        """Estimate compression ratio by partially decompressing gzip data."""
        try:
            # Decompress only a sample to estimate ratio
            decompressor = gzip.GzipFile(fileobj=io.BytesIO(data))

            sample_data = decompressor.read(self.sample_size)
            sample_compressed = len(data[:self.sample_size])

            if len(sample_data) == 0:
                return 1.0, 0

            # Estimate ratio from sample
            sample_ratio = len(sample_data) / sample_compressed

            # Estimate total size (rough approximation)
            estimated_total = len(data) * sample_ratio

            return sample_ratio, int(estimated_total)

        except Exception:
            # Fallback: use header info if available
            if len(data) >= 4:
                size_mod = struct.unpack("<I", data[-4:])[0]
                ratio = size_mod / len(data) if len(data) > 0 else 1
                return ratio, size_mod
            return 1.0, len(data)

    def _analyze_generic_compression(self, data: bytes, format_name: str) -> Dict[str, Any]:
        """Generic compression analysis for formats without specific handlers."""
        # Basic entropy analysis
        entropy = self._calculate_entropy(data[:self.sample_size])

        # High entropy suggests good compression, very high entropy suggests randomness
        if entropy > 7.8:  # Very high entropy
            return {
                "is_suspicious": True,
                "message": f"{format_name} file has suspiciously high entropy ({entropy:.2f}) - may be encrypted or corrupted",
                "severity": Severity.MEDIUM,
                "recommendation": "High entropy in compressed data can indicate encryption, corruption, or obfuscation",
                "entropy": entropy,
            }

        return {"is_suspicious": False, "message": f"{format_name} compression appears normal"}

    def _check_nested_compression(self, data: bytes, compression_format: str) -> Dict[str, Any]:
        """Check for nested/layered compression (common decompression bomb technique)."""
        formats_found = [compression_format]
        current_data = data
        max_levels = 5  # Limit analysis depth

        try:
            for _level in range(1, max_levels):
                # Try to decompress current layer
                if formats_found[-1] == "gzip":
                    try:
                        current_data = gzip.decompress(current_data[:self.sample_size])
                    except Exception:
                        break
                elif formats_found[-1] == "zip":
                    try:
                        zip_buffer = io.BytesIO(current_data[:self.sample_size])
                        with zipfile.ZipFile(zip_buffer, "r") as zf:
                            # Get first file in zip
                            names = zf.namelist()
                            if names:
                                current_data = zf.read(names[0])[:self.sample_size]
                    except Exception:
                        break
                else:
                    break  # Can't decompress other formats safely

                # Check if the decompressed data is also compressed
                inner_format = self._detect_compression_format(current_data)
                if inner_format and inner_format not in formats_found:
                    formats_found.append(inner_format)
                else:
                    break

        except Exception as e:
            logger.debug(f"Nested compression analysis failed: {str(e)}")

        return {
            "nested_levels": len(formats_found) - 1,
            "formats": formats_found,
        }

    def _analyze_compression_patterns(self, data: bytes, compression_format: str) -> Dict[str, Any]:
        """Analyze compression patterns for anomalies."""
        indicators = []

        # Check for patterns that suggest artificial compression bombs
        if compression_format in ["gzip", "zip"]:
            # Look for repetitive patterns that compress extremely well
            sample = data[:self.sample_size]

            # Count consecutive identical bytes (classic compression bomb pattern)
            max_consecutive = self._find_max_consecutive_bytes(sample)
            if max_consecutive > 10000:  # >10KB of identical bytes
                indicators.append(f"repetitive_pattern_detected ({max_consecutive} consecutive bytes)")

            # Check for other suspicious patterns
            unique_bytes = len(set(sample))
            if unique_bytes < 10 and len(sample) > 1000:  # Very low diversity
                indicators.append("extremely_low_byte_diversity")

        is_anomalous = len(indicators) > 0

        return {
            "anomalous": is_anomalous,
            "message": f"Compression pattern analysis: {', '.join(indicators) if indicators else 'patterns appear normal'}",
            "recommendation": "Repetitive patterns can indicate artificially constructed compression bombs",
            "indicators": indicators,
        }

    def _find_max_consecutive_bytes(self, data: bytes) -> int:
        """Find the maximum number of consecutive identical bytes."""
        if len(data) < 2:
            return 0

        max_consecutive = 1
        current_consecutive = 1

        for i in range(1, len(data)):
            if data[i] == data[i-1]:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1

        return max_consecutive

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if len(data) == 0:
            return 0

        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1

        # Calculate entropy
        entropy = 0.0
        data_len = len(data)

        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)

        return entropy

    def _get_compression_recommendation(self, ratio: float, estimated_size: int) -> str:
        """Get recommendation based on compression analysis."""
        size_mb = estimated_size // (1024 * 1024)

        if ratio >= 10000:
            return f"CRITICAL: Extreme compression ratio ({ratio:.1f}:1) indicates decompression bomb - DO NOT DECOMPRESS"
        elif ratio > 1000:
            return f"HIGH RISK: Suspicious compression ratio ({ratio:.1f}:1, ~{size_mb}MB) - exercise extreme caution"
        elif estimated_size > self.max_uncompressed_size:
            return f"MODERATE RISK: Large uncompressed size (~{size_mb}MB) - monitor system resources if decompressing"
        else:
            return f"Compression appears legitimate (ratio: {ratio:.1f}:1, size: ~{size_mb}MB)"

    def _get_zip_recommendation(self, overall_ratio: float, suspicious_files: List[Dict]) -> str:
        """Get recommendation for ZIP file analysis."""
        if len(suspicious_files) > 10:
            return f"CRITICAL: {len(suspicious_files)} files with extreme compression ratios - classic zip bomb pattern"
        elif len(suspicious_files) > 0:
            return f"HIGH RISK: {len(suspicious_files)} suspicious files detected - review before extraction"
        elif overall_ratio > 1000:
            return f"MODERATE RISK: High overall compression ratio ({overall_ratio:.1f}:1) - monitor during extraction"
        else:
            return f"ZIP archive appears legitimate (ratio: {overall_ratio:.1f}:1)"

    def supports_streaming(self) -> bool:
        """Supports streaming validation for large compressed files."""
        return True

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based validation for large compressed files."""
        warnings = []

        try:
            # Read header chunk to identify compression
            header_data = model_file.read_range(0, min(64 * 1024, model_file.size_bytes))  # 64KB header

            compression_format = self._detect_compression_format(header_data)
            if not compression_format:
                return warnings  # No compression detected

            # For streaming, we analyze headers and patterns without full decompression
            streaming_result = self._analyze_streaming_compression(model_file, compression_format)

            if streaming_result["is_suspicious"]:
                warnings.append(self.create_standard_warning(
                    warning_type="streaming_decompression_bomb_detected",
                    message=streaming_result["message"],
                    severity=streaming_result["severity"],
                    recommendation=streaming_result["recommendation"],
                    compression_format=compression_format,
                    file_size_mb=model_file.size_mb,
                    streaming_analysis=True,
                ))

        except Exception as e:
            logger.error(f"Streaming decompression bomb validation failed: {str(e)}")
            warnings.append(self.create_standard_warning(
                warning_type="streaming_decompression_analysis_error",
                message=f"Failed to analyze compressed file in streaming mode: {str(e)}",
                severity=Severity.LOW,
            ))

        return warnings

    def _analyze_streaming_compression(self, model_file: "ModelFile", compression_format: str) -> Dict[str, Any]:
        """Analyze compression in streaming mode without full decompression."""
        try:
            file_size = model_file.size_bytes

            # For very large compressed files, the compression ratio is inherently suspicious
            if file_size < 1024 * 1024:  # <1MB compressed file
                # Read more data for better analysis
                sample_size = min(file_size, 512 * 1024)  # Up to 512KB
                data = model_file.read_range(0, sample_size)
                return self._analyze_compression_safety(data, compression_format, time.time())
            else:
                # Large compressed file - this itself is suspicious for most ML models
                return {
                    "is_suspicious": True,
                    "message": f"Unusually large compressed file ({file_size // (1024*1024)}MB) - potential compression bomb",
                    "severity": Severity.MEDIUM if file_size < 100 * 1024 * 1024 else Severity.HIGH,
                    "recommendation": "Very large compressed ML model files are unusual and should be verified",
                }

        except Exception as e:
            return {
                "is_suspicious": False,
                "message": f"Streaming analysis failed: {str(e)}",
                "severity": Severity.LOW,
                "recommendation": "Manual review recommended",
            }
