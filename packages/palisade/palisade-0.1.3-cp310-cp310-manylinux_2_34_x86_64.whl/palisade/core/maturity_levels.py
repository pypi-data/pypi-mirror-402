"""CoSAI WS1 Supply Chain Maturity Levels for Model Signing.

This module implements the three-tier maturity model defined in the CoSAI 
Working Session 1 Supply Chain document for progressive model signing validation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CoSAIMaturityLevel(Enum):
    """CoSAI WS1 Supply Chain maturity levels for model signing."""
    
    LEVEL_1_OPAQUE_BINARY = "level_1_opaque_binary_artifacts"
    LEVEL_2_ECOSYSTEM_COMPONENTS = "level_2_signature_chaining_lineage"  
    LEVEL_3_RICH_PROVENANCE = "level_3_structured_attestations_policy"


@dataclass
class MaturityLevelSpec:
    """Specification for a CoSAI maturity level."""
    
    level: CoSAIMaturityLevel
    description: str
    core_principle: str
    
    # Required capabilities
    required_validators: List[str]
    required_signature_formats: List[str]
    required_verification_points: List[str]
    
    # Level-specific requirements
    cryptographic_requirements: Dict[str, Any]
    provenance_requirements: Dict[str, Any] 
    policy_requirements: Dict[str, Any]
    
    # Promotion criteria
    detection_criteria: List[str]
    validation_thresholds: Dict[str, Any]


# CoSAI-aligned level specifications
COSAI_LEVEL_SPECS = {
    CoSAIMaturityLevel.LEVEL_1_OPAQUE_BINARY: MaturityLevelSpec(
        level=CoSAIMaturityLevel.LEVEL_1_OPAQUE_BINARY,
        description="Basic Artifact Integrity - Models as opaque binary artifacts",
        core_principle="Cryptographic binding of model content to creator identity",
        
        required_validators=[
            "ModelIntegrityValidator",     # Hash verification
            "BasicSignatureValidator",     # Signature verification  
        ],
        required_signature_formats=["oms", "dsse", "pkcs7"],
        required_verification_points=["consumption_time"],
        
        cryptographic_requirements={
            "signed_manifest": True,
            "artifact_hashes": ["sha256", "sha512"],
            "signature_verification": True,
            "identity_binding": True,
        },
        provenance_requirements={
            "basic_creator_info": True,
            "signing_timestamp": True,
        },
        policy_requirements={},  # No policy requirements at Level 1
        
        detection_criteria=[
            "has_signed_manifest",
            "has_artifact_hashes", 
            "has_valid_signature",
        ],
        validation_thresholds={
            "integrity_check": "pass",
            "signature_valid": True,
        }
    ),
    
    CoSAIMaturityLevel.LEVEL_2_ECOSYSTEM_COMPONENTS: MaturityLevelSpec(
        level=CoSAIMaturityLevel.LEVEL_2_ECOSYSTEM_COMPONENTS,
        description="Signature Chaining and Lineage - Models in interconnected ecosystems",
        core_principle="Extended cryptographic guarantees across model relationships",
        
        required_validators=[
            "ModelIntegrityValidator",     # Level 1 base
            "BasicSignatureValidator",     # Level 1 base
            "ProvenanceSecurityValidator", # Dependency tracking
            "ModelGenealogyValidator",     # Lineage verification
            "SignatureChainValidator",     # Chain verification
        ],
        required_signature_formats=["oms", "dsse", "sigstore", "in-toto"],
        required_verification_points=["consumption_time", "dependency_resolution"],
        
        cryptographic_requirements={
            "signed_manifest": True,
            "artifact_hashes": ["sha256", "sha512"],
            "signature_verification": True,
            "identity_binding": True,
            "signature_chaining": True,
            "dependency_signatures": True,
            "trust_trail": True,
        },
        provenance_requirements={
            "basic_creator_info": True,
            "signing_timestamp": True,
            "model_transformations": True,  # Retraining, fine-tuning
            "dependency_relationships": True,
            "lineage_tracking": True,
            "transformation_signatures": True,
        },
        policy_requirements={
            "dependency_validation": True,
        },
        
        detection_criteria=[
            "has_dependency_signatures",
            "has_transformation_records",
            "has_lineage_information",
            "has_trust_trail",
        ],
        validation_thresholds={
            "integrity_check": "pass",
            "signature_valid": True,
            "dependency_chain_valid": True,
            "lineage_verified": True,
        }
    ),
    
    CoSAIMaturityLevel.LEVEL_3_RICH_PROVENANCE: MaturityLevelSpec(
        level=CoSAIMaturityLevel.LEVEL_3_RICH_PROVENANCE,
        description="Structured Attestations & Policy Integration - Comprehensive provenance",
        core_principle="Automated policy control with rich structured information",
        
        required_validators=[
            # All Level 1 & 2 validators plus:
            "ModelIntegrityValidator",
            "BasicSignatureValidator", 
            "ProvenanceSecurityValidator",
            "ModelGenealogyValidator",
            "StructuredAttestationValidator",  # SLSA/in-toto attestations
            "PolicyComplianceValidator",       # Automated policy evaluation
            "MLBOMValidator",                  # ML Bill of Materials
            "ComplianceStatusValidator",       # Compliance documentation
        ],
        required_signature_formats=["oms", "dsse", "sigstore", "slsa", "in-toto"],
        required_verification_points=["consumption_time", "dependency_resolution", "policy_evaluation"],
        
        cryptographic_requirements={
            "signed_manifest": True,
            "artifact_hashes": ["sha256", "sha512"],
            "signature_verification": True,
            "identity_binding": True,
            "signature_chaining": True,
            "dependency_signatures": True,
            "trust_trail": True,
            "structured_attestations": True,
            "rich_metadata_signing": True,
        },
        provenance_requirements={
            "basic_creator_info": True,
            "signing_timestamp": True,
            "model_transformations": True,
            "dependency_relationships": True,
            "lineage_tracking": True,
            "transformation_signatures": True,
            "development_process_documentation": True,
            "training_provenance": True,
            "dataset_provenance": True,
            "build_environment_attestation": True,
        },
        policy_requirements={
            "dependency_validation": True,
            "automated_policy_evaluation": True,
            "compliance_verification": True,
            "consumption_control": True,
            "risk_assessment": True,
        },
        
        detection_criteria=[
            "has_structured_attestations",
            "has_slsa_provenance",
            "has_ml_bom",
            "has_compliance_documentation",
            "supports_policy_evaluation",
        ],
        validation_thresholds={
            "integrity_check": "pass",
            "signature_valid": True,
            "dependency_chain_valid": True,
            "lineage_verified": True,
            "attestations_valid": True,
            "policy_compliant": True,
            "compliance_documented": True,
        }
    ),
}


def get_maturity_level_spec(level: CoSAIMaturityLevel) -> MaturityLevelSpec:
    """Get specification for a maturity level."""
    return COSAI_LEVEL_SPECS[level]


def get_available_maturity_levels() -> List[CoSAIMaturityLevel]:
    """Get list of all available maturity levels."""
    return list(CoSAIMaturityLevel)


def get_next_maturity_level(current_level: CoSAIMaturityLevel) -> Optional[CoSAIMaturityLevel]:
    """Get the next maturity level for progression attempts."""
    levels = get_available_maturity_levels()
    try:
        current_index = levels.index(current_level)
        if current_index < len(levels) - 1:
            return levels[current_index + 1]
    except ValueError:
        pass
    return None


def can_progress_to_level(current_level: CoSAIMaturityLevel, 
                         target_level: CoSAIMaturityLevel) -> bool:
    """Check if progression from current to target level is valid."""
    levels = get_available_maturity_levels()
    try:
        current_index = levels.index(current_level)
        target_index = levels.index(target_level)
        return target_index > current_index
    except ValueError:
        return False