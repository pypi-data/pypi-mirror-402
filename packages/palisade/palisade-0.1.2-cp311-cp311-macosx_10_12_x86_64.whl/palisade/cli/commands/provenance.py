"""Provenance Commands for Palisade CLI.

Handles signature verification and provenance tracking operations.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from rich.console import Console

# Lazy imports to avoid circular dependency
if TYPE_CHECKING:
    from palisade.models.metadata import ModelMetadata
    from palisade.validators.provenance_security import ProvenanceSecurityValidator

console = Console()


def _create_default_metadata() -> "ModelMetadata":
    """Create default metadata for provenance validation."""
    from palisade.models.metadata import ModelMetadata, ModelType
    
    return ModelMetadata(
        model_type=ModelType.UNKNOWN,
        framework_version="unknown",
        num_parameters=None,
        input_shape=None,
        output_shape=None,
        architecture=None,
        is_quantized=False,
        is_distributed=False
    )


def _create_provenance_validator() -> "ProvenanceSecurityValidator":
    """Create provenance validator with default metadata."""
    from palisade.validators.provenance_security import ProvenanceSecurityValidator
    
    return ProvenanceSecurityValidator(_create_default_metadata())


def verify_sigstore(
    model_path: str,
    strictness: str = "medium",
    public_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify sigstore model transparency signature.
    
    Args:
        model_path: Path to model file or directory
        strictness: Verification strictness level (low, medium, high)
        public_key: Optional path to public key file
        
    Returns:
        Verification result dictionary
    """
    model_path_obj = Path(model_path)

    if not model_path_obj.exists():
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": "Model path not found",
        }

    console.print(f"🔐 Verifying Sigstore model transparency: {model_path}")

    try:
        validator = _create_provenance_validator()

        # Configure for sigstore verification
        validator.require_model_transparency = True
        validator.model_transparency_strictness = strictness
        
        # Pass public key for cryptographic verification (if provided)
        if public_key:
            validator.sigstore_public_key_path = public_key

        start_time = time.time()

        # Perform verification
        if model_path_obj.is_dir():
            warnings = validator.validate_model_provenance(str(model_path_obj))
        else:
            # For single file, check parent directory for signatures
            warnings = validator.validate_model_provenance(str(model_path_obj.parent))

        verification_time = time.time() - start_time

        # Check actual discovered signatures (NOT attestations)
        signature_files_found = getattr(validator, "_discovered_signature_files", 0)
        
        # For verify-sigstore, only count signature verifications (not SLSA attestations)
        all_crypto_verifications = getattr(validator, "_cryptographic_verifications", [])
        signature_verifications = [v for v in all_crypto_verifications if v.get("type") != "slsa_attestation"]
        
        cryptographic_verification = bool(signature_verifications)
        verified_signatures = len(signature_verifications)
        
        # Check for critical security failures
        has_missing_provenance = any(
            w.get("type") == "missing_provenance_documents" and w.get("severity") in ["high", "critical"]
            for w in warnings
        )
        has_critical_warnings = any(w.get("severity") == "critical" for w in warnings)
        has_high_warnings = any(w.get("severity") == "high" for w in warnings)
        
        # Check if verification requires a public key
        requires_public_key = any(
            w.get("details", {}).get("error", "").startswith("Public key required")
            for w in warnings
        )
        
        # Check if attestation files exist (but no signature files)
        attestation_files_found = getattr(validator, "_discovered_attestation_files", 0)
        
        # Determine status based on ACTUAL security posture
        if signature_files_found > 0 and verified_signatures > 0:
            status = "verified"
            is_local_key_verified = any(v.get("signer") == "local-key-verified" for v in signature_verifications)
            
            if is_local_key_verified:
                message = f"Sigstore signature cryptographically verified - {verified_signatures} signature(s) verified (local key)"
            else:
                message = f"Sigstore verification successful - {verified_signatures} signature(s) cryptographically verified"
        elif signature_files_found > 0 and requires_public_key:
            status = "failed"
            message = "Sigstore verification INCOMPLETE - public key required to verify local key signature"
        elif signature_files_found > 0 and verified_signatures == 0:
            status = "failed"
            message = "Sigstore verification FAILED - signatures found but cryptographic verification failed"
        elif signature_files_found == 0 and attestation_files_found > 0:
            # No signatures but attestations exist - guide user to correct command
            status = "warning"
            message = f"No Sigstore signatures found ({attestation_files_found} attestation file(s) found - use 'verify-slsa' instead)"
        elif has_missing_provenance or has_critical_warnings:
            status = "failed"
            message = "Sigstore verification FAILED - no valid signatures found"
        elif has_high_warnings:
            status = "warning"
            message = "Sigstore verification incomplete - security warnings present"
        else:
            status = "failed"
            message = "Sigstore verification FAILED - no signature files found"
        
        cryptographic_verifications = getattr(validator, "_cryptographic_verifications", [])
        has_full_crypto_verification = any(v.get("signer") == "local-key-verified" for v in cryptographic_verifications)
        
        return {
            "model_path": str(model_path),
            "status": status,
            "message": message,
            "verification_time": verification_time,
            "warnings": warnings,
            "signature_files_found": signature_files_found,
            "verified_signatures": verified_signatures,
            "cryptographic_verification": cryptographic_verification,
            "has_full_crypto_verification": has_full_crypto_verification,
            "requires_public_key": requires_public_key,
        }

    except Exception as e:
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": str(e),
            "verification_time": 0,
        }


def verify_slsa(
    model_path: str,
    strictness: str = "medium",
    public_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify SLSA provenance for model.
    
    Args:
        model_path: Path to model file or directory
        strictness: Verification strictness level (low, medium, high)
        public_key: Optional path to public key file for signature verification
        
    Returns:
        Verification result dictionary
    """
    model_path_obj = Path(model_path)

    if not model_path_obj.exists():
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": "Model path not found",
        }

    console.print(f" Verifying SLSA provenance: {model_path}")

    try:
        validator = _create_provenance_validator()

        # Configure for SLSA verification
        validator.require_slsa_ml_provenance = True
        validator.slsa_ml_strictness = strictness
        
        # Pass public key for cryptographic verification (if provided)
        if public_key:
            validator.sigstore_public_key_path = public_key

        start_time = time.time()

        # Perform verification
        if model_path_obj.is_dir():
            warnings = validator.validate_model_provenance(str(model_path_obj))
        else:
            warnings = validator.validate_model_provenance(str(model_path_obj.parent))

        verification_time = time.time() - start_time

        # Check actual discovered and verified documents
        # First check for verified SLSA attestations (from signature_validators)
        verified_slsa = []
        crypto_verifications = []
        if hasattr(validator, 'signature_validators'):
            verified_slsa = getattr(validator.signature_validators, '_verified_slsa_attestations', [])
            crypto_verifications = getattr(validator.signature_validators, '_cryptographic_verifications', [])
        
        # Use verified count if available, otherwise use discovered count
        slsa_attestations_found = len(verified_slsa) if verified_slsa else getattr(validator, "_discovered_attestation_files", 0)
        
        # Check for cryptographic verification from signature_validators OR main validator
        cryptographic_verification = (
            bool(crypto_verifications) or 
            (hasattr(validator, "_cryptographic_verifications") and bool(validator._cryptographic_verifications))
        )
        
        # Check for critical security failures
        has_missing_provenance = any(
            w.get("type") == "missing_provenance_documents" and w.get("severity") in ["high", "critical"]
            for w in warnings
        )
        has_critical_warnings = any(w.get("severity") == "critical" for w in warnings)
        has_high_warnings = any(w.get("severity") == "high" for w in warnings)
        
        # Check if public key was provided
        requires_public_key = slsa_attestations_found > 0 and not cryptographic_verification and not public_key
        
        # Determine status based on ACTUAL security posture
        if slsa_attestations_found > 0 and cryptographic_verification:
            status = "verified"
            message = "SLSA provenance verification successful - cryptographically verified"
        elif slsa_attestations_found > 0 and requires_public_key:
            status = "warning"
            message = "SLSA attestations found - public key required for cryptographic verification"
        elif slsa_attestations_found > 0 and not cryptographic_verification:
            status = "warning"
            message = "SLSA attestations found but cryptographic verification failed"
        elif has_missing_provenance or has_critical_warnings:
            status = "failed"
            message = "SLSA provenance verification FAILED - no valid attestations found"
        elif has_high_warnings:
            status = "warning"
            message = "SLSA provenance verification incomplete - security warnings present"
        else:
            status = "failed"
            message = "SLSA provenance verification FAILED - no SLSA attestations found"

        return {
            "model_path": str(model_path),
            "status": status,
            "message": message,
            "verification_time": verification_time,
            "warnings": warnings,
            "slsa_documents_found": slsa_attestations_found,
            "cryptographic_verification": cryptographic_verification,
            "requires_public_key": requires_public_key,
        }

    except Exception as e:
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": str(e),
            "verification_time": 0,
        }


def track_provenance(model_path: str, public_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate comprehensive provenance tracking report.
    
    Args:
        model_path: Path to model file or directory
        public_key: Optional path to public key file for signature verification
        
    Returns:
        Provenance tracking result dictionary
    """
    model_path_obj = Path(model_path)

    if not model_path_obj.exists():
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": "Model path not found",
        }

    console.print(f" Tracking provenance: {model_path}")

    try:
        validator = _create_provenance_validator()
        
        # Pass public key for cryptographic verification (if provided)
        if public_key:
            validator.sigstore_public_key_path = public_key

        start_time = time.time()

        # Generate comprehensive ML-BOM and provenance
        if model_path_obj.is_dir():
            warnings = validator.validate_model_provenance(str(model_path_obj))
        else:
            warnings = validator.validate_model_provenance(str(model_path_obj.parent))

        tracking_time = time.time() - start_time

        # Load ML-BOM if generated
        ml_bom_path = (model_path_obj if model_path_obj.is_dir() else model_path_obj.parent) / "ML-BOM.json"
        ml_bom = None
        if ml_bom_path.exists():
            with open(ml_bom_path) as f:
                ml_bom = json.load(f)

        # Get actual discovered document counts
        signature_files_found = getattr(validator, "_discovered_signature_files", 0)
        attestation_files_found = getattr(validator, "_discovered_attestation_files", 0)
        provenance_docs_found = getattr(validator, "_discovered_provenance_docs", 0)
        cryptographic_verification = hasattr(validator, "_cryptographic_verifications") and bool(validator._cryptographic_verifications)
        
        # Count verified signatures
        verified_signatures = len(getattr(validator, "_cryptographic_verifications", [])) if cryptographic_verification else 0
        
        return {
            "model_path": str(model_path),
            "status": "tracked",
            "tracking_time": tracking_time,
            "ml_bom_generated": ml_bom is not None,
            "ml_bom_path": str(ml_bom_path) if ml_bom_path.exists() else None,
            "ml_bom": ml_bom,
            "warnings": warnings,
            "provenance_documents": provenance_docs_found,
            "signature_files": signature_files_found,
            "attestation_files": attestation_files_found,
            "verified_signatures": verified_signatures,
            "cryptographic_verification": cryptographic_verification,
        }

    except Exception as e:
        return {
            "model_path": str(model_path),
            "status": "error",
            "error": str(e),
            "tracking_time": 0,
        }

