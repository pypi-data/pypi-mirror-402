"""Validator for model integrity and tampering detection."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import multiprocessing
from collections import defaultdict

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine
    from palisade.models.model_file import ModelFile

from palisade.models.metadata import ModelMetadata, ModelType
from palisade._native import ModelIntegrityStreamingValidator

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)


class ModelIntegrityValidator(BaseValidator):
    """Validator for checking model integrity and detecting tampering."""

    def __init__(self, metadata: Optional[ModelMetadata] = None, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

    def can_validate(self, model_type: ModelType) -> bool:
        """
        This validator handles non-SafeTensors files.
        
        SafeTensors files are handled by SafeTensorsIntegrityValidator which already
        performs comprehensive malware pattern scanning. This prevents duplicate work.
        """
        return model_type != ModelType.SAFETENSORS

    def supports_streaming(self) -> bool:
        """This validator uses the Rust streaming backend."""
        return True

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """
        Validate model integrity for a full file.
        Uses the Rust backend for malware pattern detection.
        """
        from palisade._native import validate_model_integrity
        
        # Call Rust full-file validation
        result = validate_model_integrity(data)
        
        # Convert Rust results to Python warnings
        for warning_msg in result.warnings:
            # Determine severity based on warning content
            if "executable" in warning_msg.lower():
                severity = Severity.HIGH
            elif "suspicious" in warning_msg.lower():
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            warning = self.create_standard_warning(
                warning_type="model_integrity_issue",
                message=warning_msg,
                severity=severity,
                recommendation="Review file integrity and content",
                threat_type="supply_chain_attack",
                attack_vector="Suspicious patterns in model file"
            )
            self.warnings.append(warning)
        
        # Apply policy evaluation if policy engine is available
        if self.policy_engine:
            return self.apply_policy(self.warnings, "", {})
        
        return self.warnings

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """
        Validate a large file using the Rust streaming validator.
        Processes chunks iteratively with GIL released for maximum performance.
        """
        num_cores = multiprocessing.cpu_count()
        validator = ModelIntegrityStreamingValidator(num_cores)
        
        all_matches = []
        for chunk in model_file.iter_chunks():
            matches = validator.process_chunk(chunk)
            all_matches.extend(matches)
            
        final_matches = validator.finalize()
        all_matches.extend(final_matches)

        return self._process_rust_matches(all_matches)

    def _process_rust_matches(self, matches: List[Any]) -> List[Dict[str, Any]]:
        """Process the matches returned from the Rust backend into warnings."""
        if not matches:
            return []
        
        # Group patterns by description prefix to categorize them
        grouped = defaultdict(list)
        for match in matches:
            # Extract category from description (e.g., "PE executable header" -> "executable")
            desc_lower = match.description.lower()
            if "executable" in desc_lower or "elf" in desc_lower or "mach-o" in desc_lower:
                category = "executable_headers"
            elif "script" in desc_lower or "import" in desc_lower or "eval" in desc_lower:
                category = "script_indicators"
            elif "system" in desc_lower or "shell" in desc_lower or "cmd" in desc_lower:
                category = "system_commands"
            else:
                category = "suspicious_patterns"
            
            grouped[category].append(match)
        
        warnings = []
        for category, category_matches in grouped.items():
            # Calculate total score
            total_score = sum(m.score for m in category_matches)
            severity = self._determine_severity(total_score, len(category_matches))
            
            # Get unique patterns
            unique_patterns = sorted(list(set(m.description for m in category_matches)))
            
            warnings.append(self.create_standard_warning(
                f"integrity_{category}",
                f"Model {category.replace('_', ' ')} detected",
                severity,
                f"Verify model source and integrity",
                patterns=unique_patterns[:20],  # Limit to 20 for readability
                total_patterns=len(unique_patterns),
                total_score=total_score,
            ))
        
        return warnings

    def _determine_severity(self, total_score: int, pattern_count: int) -> Severity:
        """Determine severity based on total score and pattern count."""
        # Higher scores or many patterns indicate higher risk
        if total_score >= 10 or pattern_count >= 5:
            return Severity.HIGH
        elif total_score >= 5 or pattern_count >= 3:
            return Severity.MEDIUM
        else:
            return Severity.LOW
