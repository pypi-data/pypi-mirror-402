"""CoSAI Maturity Level Detection and Analysis.

This module detects the highest achievable CoSAI maturity level based on 
available model artifacts, signatures, and attestations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .maturity_levels import CoSAIMaturityLevel, get_maturity_level_spec

logger = logging.getLogger(__name__)


class CoSAIMaturityDetector:
    """Detect CoSAI maturity level based on available artifacts."""
    
    def __init__(self, enable_progression: bool = True, 
                 fallback_on_failure: bool = True) -> None:
        """Initialize maturity detector.
        
        Args:
            enable_progression: Whether to attempt progression to higher levels
            fallback_on_failure: Whether to fall back to lower levels on failure
        """
        self.enable_progression = enable_progression
        self.fallback_on_failure = fallback_on_failure
    
    def detect_level(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> Optional[CoSAIMaturityLevel]:
        """Detect highest achievable maturity level.
        
        Args:
            model_dir: Path to model directory
            provenance_docs: List of discovered provenance documents
            
        Returns:
            Highest achievable CoSAI maturity level or None if no level is achievable
        """
        logger.info("Detecting CoSAI maturity level for model artifacts")
        
        # Check Level 3 first (most comprehensive)
        if self._can_achieve_level_3(model_dir, provenance_docs):
            logger.info("Model can achieve CoSAI Level 3: Rich Provenance")
            return CoSAIMaturityLevel.LEVEL_3_RICH_PROVENANCE
            
        # Check Level 2  
        elif self._can_achieve_level_2(model_dir, provenance_docs):
            logger.info("Model can achieve CoSAI Level 2: Ecosystem Components")
            return CoSAIMaturityLevel.LEVEL_2_ECOSYSTEM_COMPONENTS
            
        # Check Level 1
        elif self._can_achieve_level_1(model_dir, provenance_docs):
            logger.info("Model can achieve CoSAI Level 1: Opaque Binary")
            return CoSAIMaturityLevel.LEVEL_1_OPAQUE_BINARY
            
        # No maturity level achievable
        logger.warning("Model cannot achieve any CoSAI maturity level")
        return None
    
    def get_level_capabilities(self, level: CoSAIMaturityLevel, 
                              model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed capabilities analysis for a specific level.
        
        Args:
            level: CoSAI maturity level to analyze
            model_dir: Path to model directory
            provenance_docs: List of discovered provenance documents
            
        Returns:
            Dictionary with capability analysis results
        """
        spec = get_maturity_level_spec(level)
        capabilities = {
            "level": level.value,
            "description": spec.description,
            "core_principle": spec.core_principle,
            "capabilities_met": {},
            "missing_capabilities": [],
            "achievable": False,
        }
        
        # Check detection criteria
        for criterion in spec.detection_criteria:
            met = self._check_detection_criterion(criterion, model_dir, provenance_docs)
            capabilities["capabilities_met"][criterion] = met
            if not met:
                capabilities["missing_capabilities"].append(criterion)
        
        # Determine if level is achievable
        capabilities["achievable"] = len(capabilities["missing_capabilities"]) == 0
        
        return capabilities
    
    def _can_achieve_level_1(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check if Level 1 (Opaque Binary Artifacts) requirements can be satisfied."""
        spec = get_maturity_level_spec(CoSAIMaturityLevel.LEVEL_1_OPAQUE_BINARY)
        
        # Check all detection criteria
        for criterion in spec.detection_criteria:
            if not self._check_detection_criterion(criterion, model_dir, provenance_docs):
                logger.debug(f"Level 1 criterion not met: {criterion}")
                return False
        
        logger.debug("All Level 1 criteria satisfied")
        return True
    
    def _can_achieve_level_2(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check if Level 2 (Ecosystem Components) requirements can be satisfied."""
        # Must satisfy Level 1 first
        if not self._can_achieve_level_1(model_dir, provenance_docs):
            logger.debug("Level 2 requires Level 1 - Level 1 not achievable")
            return False
        
        spec = get_maturity_level_spec(CoSAIMaturityLevel.LEVEL_2_ECOSYSTEM_COMPONENTS)
        
        # Check Level 2 specific criteria
        level_2_criteria = [c for c in spec.detection_criteria 
                           if c not in get_maturity_level_spec(CoSAIMaturityLevel.LEVEL_1_OPAQUE_BINARY).detection_criteria]
        
        for criterion in level_2_criteria:
            if not self._check_detection_criterion(criterion, model_dir, provenance_docs):
                logger.debug(f"Level 2 criterion not met: {criterion}")
                return False
        
        logger.debug("All Level 2 criteria satisfied")
        return True
    
    def _can_achieve_level_3(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check if Level 3 (Rich Provenance) requirements can be satisfied."""
        # Must satisfy Level 2 first
        if not self._can_achieve_level_2(model_dir, provenance_docs):
            logger.debug("Level 3 requires Level 2 - Level 2 not achievable")
            return False
        
        spec = get_maturity_level_spec(CoSAIMaturityLevel.LEVEL_3_RICH_PROVENANCE)
        
        # Check Level 3 specific criteria
        level_3_criteria = [c for c in spec.detection_criteria 
                           if c not in get_maturity_level_spec(CoSAIMaturityLevel.LEVEL_2_ECOSYSTEM_COMPONENTS).detection_criteria]
        
        for criterion in level_3_criteria:
            if not self._check_detection_criterion(criterion, model_dir, provenance_docs):
                logger.debug(f"Level 3 criterion not met: {criterion}")
                return False
        
        logger.debug("All Level 3 criteria satisfied")
        return True
    
    def _check_detection_criterion(self, criterion: str, model_dir: Path, 
                                  provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check if a specific detection criterion is met."""
        try:
            if criterion == "has_signed_manifest":
                return self._has_signed_manifest(provenance_docs)
            elif criterion == "has_artifact_hashes":
                return self._has_artifact_hashes(model_dir, provenance_docs)
            elif criterion == "has_valid_signature":
                return self._has_valid_signature(provenance_docs)
            elif criterion == "has_dependency_signatures":
                return self._has_dependency_signatures(provenance_docs)
            elif criterion == "has_transformation_records":
                return self._has_transformation_records(provenance_docs)
            elif criterion == "has_lineage_information":
                return self._has_lineage_information(provenance_docs)
            elif criterion == "has_trust_trail":
                return self._has_trust_trail(provenance_docs)
            elif criterion == "has_structured_attestations":
                return self._has_structured_attestations(provenance_docs)
            elif criterion == "has_slsa_provenance":
                return self._has_slsa_provenance(provenance_docs)
            elif criterion == "has_ml_bom":
                return self._has_ml_bom(model_dir, provenance_docs)
            elif criterion == "has_compliance_documentation":
                return self._has_compliance_documentation(provenance_docs)
            elif criterion == "supports_policy_evaluation":
                return self._supports_policy_evaluation(provenance_docs)
            else:
                logger.warning(f"Unknown detection criterion: {criterion}")
                return False
        except Exception as e:
            logger.error(f"Error checking criterion {criterion}: {str(e)}")
            return False
    
    def _has_signed_manifest(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for signed manifests (OMS, sigstore, etc.)."""
        manifest_patterns = [
            ".oms.json", "oms-manifest", "model-manifest.oms",
            ".sig", "manifest.json", "index.json"
        ]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            if any(pattern in doc_path for pattern in manifest_patterns):
                return True
        return False
    
    def _has_artifact_hashes(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for artifact hash information."""
        # Look for hash files or embedded hashes in manifests
        hash_patterns = [".sha256", ".sha512", ".md5", "checksums", "SHASUMS"]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            if any(pattern in doc_path for pattern in hash_patterns):
                return True
            
            # Check for embedded hash information in JSON docs
            if doc_path.endswith(".json"):
                content = doc.get("content", {})
                if isinstance(content, dict):
                    if "digest" in content or "sha256" in content or "artifacts" in content:
                        return True
        
        return False
    
    def _has_valid_signature(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for cryptographic signatures."""
        signature_patterns = [
            ".sig", ".asc", ".signature", ".p7s",
            "signature", "signatures", "dsseEnvelope"
        ]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            content = doc.get("content", {})
            
            # Check file extensions
            if any(pattern in doc_path for pattern in signature_patterns):
                return True
            
            # Check for signature content in JSON
            if isinstance(content, dict):
                if any(key in content for key in signature_patterns):
                    return True
        
        return False
    
    def _has_dependency_signatures(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for dependency signature information."""
        for doc in provenance_docs:
            content = doc.get("content", {})
            if isinstance(content, dict):
                # Look for dependency or requirements with signatures
                if "dependencies" in content or "requirements" in content:
                    deps = content.get("dependencies", content.get("requirements", []))
                    if isinstance(deps, list):
                        for dep in deps:
                            if isinstance(dep, dict) and ("signature" in dep or "digest" in dep):
                                return True
        return False
    
    def _has_transformation_records(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for model transformation records (fine-tuning, quantization, etc.)."""
        transformation_keywords = [
            "fine-tuning", "fine_tuning", "quantization", "pruning",
            "distillation", "adaptation", "retraining", "training_args"
        ]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            content = doc.get("content", {})
            
            # Check file names
            if any(keyword in doc_path.lower() for keyword in transformation_keywords):
                return True
            
            # Check content
            if isinstance(content, dict):
                content_str = str(content).lower()
                if any(keyword in content_str for keyword in transformation_keywords):
                    return True
        
        return False
    
    def _has_lineage_information(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for model lineage and genealogy information."""
        lineage_keywords = [
            "parent_model", "base_model", "derived_from", "lineage",
            "genealogy", "model_family", "ancestry"
        ]
        
        for doc in provenance_docs:
            content = doc.get("content", {})
            if isinstance(content, dict):
                content_str = str(content).lower()
                if any(keyword in content_str for keyword in lineage_keywords):
                    return True
        
        return False
    
    def _has_trust_trail(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for cryptographic trust trail."""
        # Look for chained signatures or trust relationships
        trust_indicators = [
            "trust_chain", "signature_chain", "certificate_chain",
            "trusted_signers", "verification_chain"
        ]
        
        for doc in provenance_docs:
            content = doc.get("content", {})
            if isinstance(content, dict):
                content_str = str(content).lower()
                if any(indicator in content_str for indicator in trust_indicators):
                    return True
        
        return False
    
    def _has_structured_attestations(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for structured attestations (SLSA, in-toto)."""
        attestation_patterns = ["attestation", "slsa", "in-toto", "provenance"]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            content = doc.get("content", {})
            
            if any(pattern in doc_path.lower() for pattern in attestation_patterns):
                return True
            
            if isinstance(content, dict):
                if "predicateType" in content or "_type" in content:
                    predicate_type = content.get("predicateType", content.get("_type", ""))
                    if "slsa" in predicate_type.lower() or "in-toto" in predicate_type.lower():
                        return True
        
        return False
    
    def _has_slsa_provenance(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check specifically for SLSA provenance."""
        for doc in provenance_docs:
            content = doc.get("content", {})
            if isinstance(content, dict):
                predicate_type = content.get("predicateType", "")
                if "slsa.dev/provenance" in predicate_type:
                    return True
        return False
    
    def _has_ml_bom(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for ML Bill of Materials."""
        bom_patterns = ["ML-BOM", "ml-bom", "bom.json", "bill-of-materials"]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            if any(pattern in doc_path for pattern in bom_patterns):
                return True
        
        # Check for BOM files in model directory
        bom_files = [
            model_dir / "ML-BOM.json",
            model_dir / "ml-bom.json",
            model_dir / "bill-of-materials.json"
        ]
        
        return any(bom_file.exists() for bom_file in bom_files)
    
    def _has_compliance_documentation(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check for compliance documentation."""
        compliance_keywords = [
            "compliance", "audit", "certification", "assessment",
            "policy_compliance", "regulatory", "governance"
        ]
        
        for doc in provenance_docs:
            doc_path = doc.get("path", "")
            content = doc.get("content", {})
            
            if any(keyword in doc_path.lower() for keyword in compliance_keywords):
                return True
            
            if isinstance(content, dict):
                content_str = str(content).lower()
                if any(keyword in content_str for keyword in compliance_keywords):
                    return True
        
        return False
    
    def _supports_policy_evaluation(self, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check if artifacts support automated policy evaluation."""
        policy_indicators = [
            "policy", "rules", "constraints", "requirements",
            "evaluation", "automated_checks"
        ]
        
        for doc in provenance_docs:
            content = doc.get("content", {})
            if isinstance(content, dict):
                content_str = str(content).lower()
                if any(indicator in content_str for indicator in policy_indicators):
                    return True
        
        return False