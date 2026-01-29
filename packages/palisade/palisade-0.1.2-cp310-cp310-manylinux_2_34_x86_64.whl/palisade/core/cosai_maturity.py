"""CoSAI WS1 Supply Chain Maturity Level Detection.

Lightweight implementation that integrates with existing validators to detect
and validate CoSAI maturity levels without creating parallel validation systems.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CoSAIMaturityLevel(Enum):
    """CoSAI WS1 Supply Chain maturity levels for model signing."""
    
    LEVEL_1_BASIC_INTEGRITY = "level_1_basic_integrity"
    LEVEL_2_SIGNATURE_CHAINING = "level_2_signature_chaining"  
    LEVEL_3_POLICY_INTEGRATION = "level_3_policy_integration"


class CoSAIMaturityDetector:
    """Lightweight CoSAI maturity level detector that works with existing validators."""
    
    def __init__(self) -> None:
        """Initialize the maturity detector."""
        # CoSAI Level 1: Basic Artifact Integrity indicators
        self.level_1_indicators = {
            "signed_manifest_patterns": [
                # IMPORTANT: These are MANIFEST files (lists of all artifacts), not individual .sig files
                ".oms.json", "oms-manifest.json", "model-manifest.json", 
                "manifest.json.sig", "manifest.json"  # Signed manifest, not individual artifact signatures
            ],
            "hash_patterns": [
                ".sha256", ".sha512", "checksums", "SHASUMS",
                "digest", "artifacts.json", "hashes.txt"
            ],
            "signature_patterns": [
                # Individual artifact signatures (but NOT enough for Level 1 alone!)
                ".sig", ".asc", ".signature", ".p7s", ".bundle",
                "dsseEnvelope", "signatures"
            ],
        }
        
        # CoSAI Level 2: Signature Chaining and Lineage indicators  
        self.level_2_indicators = {
            "dependency_signatures": [
                "dependencies", "requirements", "base_model",
                "parent_model", "trust_chain"
            ],
            "transformation_records": [
                "fine-tuning", "fine_tuning", "quantization",
                "training_args", "adapter", "lora"
            ],
            "lineage_tracking": [
                "lineage", "genealogy", "model_family",
                "derived_from", "ancestry"
            ],
        }
        
        # CoSAI Level 3: Policy Integration indicators
        self.level_3_indicators = {
            "structured_attestations": [
                "attestation", "slsa", "in-toto",
                "predicateType", "_type"
            ],
            "policy_documents": [
                "policy", "compliance", "governance",
                "constraints", "rules"
            ],
            "ml_bom": [
                "ML-BOM", "ml-bom", "bill-of-materials",
                "components", "bomFormat"
            ],
        }
    
    def detect_maturity_level(self, model_dir: Path, 
                             provenance_docs: List[Dict[str, Any]],
                             cryptographic_verifications: Optional[List[Dict[str, Any]]] = None) -> Optional[CoSAIMaturityLevel]:
        """Detect the highest achievable CoSAI maturity level.
        
        Args:
            model_dir: Path to model directory
            provenance_docs: List of discovered provenance documents
            cryptographic_verifications: Optional list of successful cryptographic verifications
            
        Returns:
            Highest achievable CoSAI maturity level or None
        """
        logger.debug("Detecting CoSAI maturity level")
        
        # Check levels progressively (must achieve lower levels first)
        # CoSAI levels are PROGRESSIVE - you cannot skip levels
        
        # RELAXED RULE: Award Level 1 if primary artifacts are cryptographically verified
        # even without a full manifest (this is "Level 1 - Artifact Integrity")
        has_crypto_verification = cryptographic_verifications and len(cryptographic_verifications) > 0
        
        # Check Level 1 first (foundation)
        can_achieve_level_1_full = self._can_achieve_level_1(model_dir, provenance_docs)
        can_achieve_level_1_basic = has_crypto_verification  # Relaxed: verified artifact = basic Level 1
        
        if can_achieve_level_1_full or can_achieve_level_1_basic:
            # Level 1 achieved (full or basic), check if Level 2 is also possible
            if self._can_achieve_level_2(model_dir, provenance_docs):
                # Level 2 achieved, check if Level 3 is also possible
                if self._can_achieve_level_3(model_dir, provenance_docs):
                    logger.info("Model achieves CoSAI Level 3: Policy Integration")
                    return CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION
                else:
                    logger.info("Model achieves CoSAI Level 2: Signature Chaining")
                    return CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING
            else:
                if can_achieve_level_1_full:
                    logger.info("Model achieves CoSAI Level 1: Basic Integrity (Full Compliance)")
                else:
                    logger.info("Model achieves CoSAI Level 1: Basic Integrity (Artifact Verified)")
                return CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY
        
        # No maturity level achievable
        logger.debug("Model does not achieve any CoSAI maturity level")
        return None
    
    def get_maturity_analysis(self, model_dir: Path, 
                             provenance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed maturity level analysis.
        
        Returns:
            Dictionary with detailed capability analysis for each level
        """
        analysis = {
            "detected_level": None,
            "level_capabilities": {},
            "missing_capabilities": [],
            "upgrade_recommendations": [],
        }
        
        # Analyze each level
        levels = [
            (CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY, self._analyze_level_1),
            (CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING, self._analyze_level_2),
            (CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION, self._analyze_level_3),
        ]
        
        highest_level = None
        for level, analyzer in levels:
            capabilities = analyzer(model_dir, provenance_docs)
            analysis["level_capabilities"][level.value] = capabilities
            
            if capabilities["achievable"]:
                highest_level = level
        
        analysis["detected_level"] = highest_level.value if highest_level else None
        
        # Generate upgrade recommendations
        if highest_level != CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION:
            next_level = self._get_next_level(highest_level)
            if next_level:
                next_analysis = analysis["level_capabilities"][next_level.value]
                analysis["upgrade_recommendations"] = next_analysis["missing_indicators"]
        
        return analysis
    
    def _can_achieve_level_1(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check Level 1: Basic Artifact Integrity.
        
        Requires ALL of:
        - Signed manifest (OMS manifest or similar signed artifact collection)
        - Artifact hashes (SHA-256/512 checksums)
        - Signature verification capability (.sig files)
        
        Note: Model weights signatures alone don't satisfy this - need a signed 
        MANIFEST that lists all artifacts.
        """
        has_signed_manifest = self._has_indicators(provenance_docs, 
                                                  self.level_1_indicators["signed_manifest_patterns"])
        has_artifact_hashes = self._has_indicators(provenance_docs,
                                                  self.level_1_indicators["hash_patterns"])
        has_signatures = self._has_indicators(provenance_docs,
                                             self.level_1_indicators["signature_patterns"])
        
        logger.debug(f"Level 1 check: manifest={has_signed_manifest}, hashes={has_artifact_hashes}, sigs={has_signatures}")
        
        # ALL three are required, not just signatures
        return has_signed_manifest and has_artifact_hashes and has_signatures
    
    def _can_achieve_level_2(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check Level 2: Signature Chaining and Lineage."""
        # Must achieve Level 1 first
        if not self._can_achieve_level_1(model_dir, provenance_docs):
            return False
        
        # Plus dependency signatures + transformation records + lineage tracking
        has_dep_sigs = self._has_indicators(provenance_docs,
                                           self.level_2_indicators["dependency_signatures"])
        has_transformations = self._has_indicators(provenance_docs,
                                                  self.level_2_indicators["transformation_records"])
        has_lineage = self._has_indicators(provenance_docs,
                                          self.level_2_indicators["lineage_tracking"])
        
        return has_dep_sigs or has_transformations or has_lineage  # Any one of these qualifies
    
    def _can_achieve_level_3(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> bool:
        """Check Level 3: Policy Integration."""
        # Must achieve Level 2 first
        if not self._can_achieve_level_2(model_dir, provenance_docs):
            return False
        
        # Plus structured attestations + policy documents + ML-BOM
        has_attestations = self._has_indicators(provenance_docs,
                                               self.level_3_indicators["structured_attestations"])
        has_policy_docs = self._has_indicators(provenance_docs,
                                              self.level_3_indicators["policy_documents"])
        has_ml_bom = self._has_indicators(provenance_docs,
                                         self.level_3_indicators["ml_bom"]) or self._has_ml_bom_file(model_dir)
        
        return has_attestations or has_policy_docs or has_ml_bom  # Any one qualifies for Level 3
    
    def _has_indicators(self, provenance_docs: List[Dict[str, Any]], 
                       patterns: List[str]) -> bool:
        """Check if any of the indicator patterns are present in provenance documents."""
        for doc in provenance_docs:
            # Handle None values safely
            doc_path = (doc.get("path") or "").lower()
            doc_content = str(doc.get("content") or "").lower()
            
            for pattern in patterns:
                if pattern.lower() in doc_path or pattern.lower() in doc_content:
                    logger.debug(f"Found CoSAI indicator '{pattern}' in {doc.get('path', 'content')}")
                    return True
        
        return False
    
    def _has_ml_bom_file(self, model_dir: Path) -> bool:
        """Check for SIGNED ML-BOM files in model directory.
        
        An unsigned ML-BOM doesn't prove supply chain security - anyone can 
        generate an ML-BOM. For CoSAI Level 3, the BOM must be signed.
        """
        bom_files = [
            (model_dir / "ML-BOM.json", model_dir / "ML-BOM.json.sig"),
            (model_dir / "ml-bom.json", model_dir / "ml-bom.json.sig"),
            (model_dir / "bill-of-materials.json", model_dir / "bill-of-materials.json.sig"),
        ]
        
        # Check if any BOM file exists AND has a corresponding signature
        for bom_file, sig_file in bom_files:
            if bom_file.exists() and sig_file.exists():
                logger.debug(f"Found signed ML-BOM file: {bom_file.name}")
                return True
        
        # If unsigned BOM found, warn that it doesn't count
        unsigned_found = any(bom_file.exists() for bom_file, _ in bom_files)
        if unsigned_found:
            logger.debug("Found unsigned ML-BOM - does not satisfy CoSAI Level 3 (signature required)")
        
        return False
    
    def _analyze_level_1(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Level 1 capabilities."""
        indicators_found = []
        missing_indicators = []
        
        for category, patterns in self.level_1_indicators.items():
            if self._has_indicators(provenance_docs, patterns):
                indicators_found.append(category)
            else:
                missing_indicators.append(category)
        
        return {
            "level": CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY.value,
            "description": "Basic Artifact Integrity - Cryptographic binding of model content to creator identity",
            "indicators_found": indicators_found,
            "missing_indicators": missing_indicators,
            "achievable": len(missing_indicators) == 0,
            "requirements": [
                "Signed manifest with artifact collection",
                "Cryptographic hashes for each artifact", 
                "Signature verification at consumption time"
            ],
        }
    
    def _analyze_level_2(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Level 2 capabilities."""
        indicators_found = []
        missing_indicators = []
        
        for category, patterns in self.level_2_indicators.items():
            if self._has_indicators(provenance_docs, patterns):
                indicators_found.append(category)
            else:
                missing_indicators.append(category)
        
        # Level 2 requires Level 1 plus at least one Level 2 indicator
        level_1_achievable = self._can_achieve_level_1(model_dir, provenance_docs)
        has_level_2_indicators = len(indicators_found) > 0
        
        return {
            "level": CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING.value,
            "description": "Signature Chaining and Lineage - Extended guarantees across model relationships",
            "indicators_found": indicators_found,
            "missing_indicators": missing_indicators if not has_level_2_indicators else [],
            "achievable": level_1_achievable and has_level_2_indicators,
            "requirements": [
                "All Level 1 requirements",
                "Dependency signature verification",
                "Model transformation tracking",
                "Lineage and genealogy information"
            ],
        }
    
    def _analyze_level_3(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Level 3 capabilities."""
        indicators_found = []
        missing_indicators = []
        
        for category, patterns in self.level_3_indicators.items():
            if self._has_indicators(provenance_docs, patterns) or (category == "ml_bom" and self._has_ml_bom_file(model_dir)):
                indicators_found.append(category)
            else:
                missing_indicators.append(category)
        
        # Level 3 requires Level 2 plus at least one Level 3 indicator
        level_2_achievable = self._can_achieve_level_2(model_dir, provenance_docs)
        has_level_3_indicators = len(indicators_found) > 0
        
        return {
            "level": CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION.value,
            "description": "Policy Integration - Automated policy control with rich structured information",
            "indicators_found": indicators_found,
            "missing_indicators": missing_indicators if not has_level_3_indicators else [],
            "achievable": level_2_achievable and has_level_3_indicators,
            "requirements": [
                "All Level 1 and 2 requirements",
                "Structured attestations (SLSA, in-toto)",
                "Policy compliance documentation",
                "ML Bill of Materials (ML-BOM)",
                "Automated policy evaluation support"
            ],
        }
    
    def _get_next_level(self, current_level: Optional[CoSAIMaturityLevel]) -> Optional[CoSAIMaturityLevel]:
        """Get the next maturity level for upgrade recommendations."""
        if current_level is None:
            return CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY
        elif current_level == CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY:
            return CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING
        elif current_level == CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING:
            return CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION
        else:
            return None
    
    def create_maturity_context(self, model_dir: Path, 
                               provenance_docs: List[Dict[str, Any]],
                               detected_level: Optional[CoSAIMaturityLevel] = None,
                               analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create maturity context for policy engine integration.
        
        Args:
            model_dir: Path to model directory
            provenance_docs: List of provenance documents
            detected_level: Optional pre-detected maturity level (avoids redundant detection)
            analysis: Optional pre-computed analysis (avoids redundant analysis)
        
        Returns:
            Dictionary with maturity context for policy evaluation
        """
        # Use pre-computed values if provided (avoids duplicate logging)
        if detected_level is None:
            detected_level = self.detect_maturity_level(model_dir, provenance_docs)
        if analysis is None:
            analysis = self.get_maturity_analysis(model_dir, provenance_docs)
        
        return {
            "cosai_maturity_level": detected_level.value if detected_level else None,
            "cosai_level_numeric": self._level_to_numeric(detected_level),
            "cosai_compliance": detected_level is not None,
            "cosai_analysis": analysis,
            "cosai_capabilities": {
                level: caps["achievable"] for level, caps in analysis["level_capabilities"].items()
            },
        }
    
    def _level_to_numeric(self, level: Optional[CoSAIMaturityLevel]) -> int:
        """Convert maturity level to numeric value for policy comparisons."""
        if level is None:
            return 0
        elif level == CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY:
            return 1
        elif level == CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING:
            return 2
        elif level == CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION:
            return 3
        else:
            return 0