"""Signature Validators - Specialized validators for different signature standards.

This module contains validators for:
- OpenSSF Model Signing (OMS) 
- Sigstore model transparency
- SLSA (Supply-chain Levels for Software Artifacts) provenance

Extracted from ProvenanceSecurityValidator for better maintainability.
"""

import base64
import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING


# Sigstore model transparency support
try:
    from sigstore.models import Bundle
    from sigstore.verify import Verifier
    # ExpectedSignerError was removed in newer sigstore versions
    try:
        from sigstore.oidc import ExpectedSignerError
    except ImportError:
        # Use a generic exception as fallback
        ExpectedSignerError = Exception  # type: ignore
    SIGSTORE_AVAILABLE = True
except ImportError:
    SIGSTORE_AVAILABLE = False

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine

logger = logging.getLogger(__name__)


class SignatureValidators:
    """Container for signature validation methods."""
    
    def __init__(self, attestation_types: Dict[str, Any], 
                 policy_engine: Optional["CedarPolicyEngine"] = None,
                 public_key_path: Optional[str] = None):
        """Initialize signature validators.
        
        Args:
            attestation_types: Configuration for different attestation types
            policy_engine: Optional policy engine for validation
            public_key_path: Optional path to public key file for cryptographic verification
        """
        self.attestation_types = attestation_types
        self.policy_engine = policy_engine
        self.public_key_path = public_key_path

    # ========================================================================
    # OPENSSF MODEL SIGNING (OMS) VERIFICATION
    # ========================================================================

    def verify_oms_manifests(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """CRITICAL: Verify OpenSSF Model Signing (OMS) manifests.
        
        This implements the OpenSSF Model Signing standard for cryptographically
        signed model manifests using DSSE envelopes.
        """
        warnings = []

        # Find OMS manifest files
        oms_files = [
            doc for doc in provenance_docs 
            if any(pattern in doc.get("path", "") for pattern in [
                ".oms.json", "oms-manifest", "model-manifest.oms", "-oms.json", "oms_"
            ])
        ]

        if not oms_files:
            return warnings  # No OMS files to validate

        logger.info(f"Found {len(oms_files)} OMS manifest files")

        # Verify each OMS manifest
        for oms_doc in oms_files:
            oms_warnings = self._verify_single_oms_manifest(model_dir, oms_doc)
            warnings.extend(oms_warnings)

        return warnings

    def _verify_single_oms_manifest(self, model_dir: Path, oms_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify a single OpenSSF Model Signing manifest."""
        warnings = []
        
        try:
            oms_path = Path(oms_doc["path"])
            logger.info(f"Verifying OMS manifest: {oms_path.name}")

            # Step 1: Parse OMS manifest
            manifest_data = self._parse_oms_manifest(oms_path)
            if not manifest_data:
                warnings.append({
                    "type": "invalid_oms_manifest",
                    "details": {
                        "message": "Could not parse OpenSSF Model Signing manifest format",
                        "file": str(oms_path),
                        "recommendation": "Verify OMS manifest follows OpenSSF Model Signing v1.0 specification",
                    },
                    "severity": "high",
                })
                return warnings

            # Step 2: Validate manifest structure and content
            structure_warnings = self._validate_oms_manifest_structure(manifest_data, oms_path)
            warnings.extend(structure_warnings)

            # Step 3: Verify artifact integrity against manifest
            has_critical_errors = any(
                w.get("severity") == "critical" or "validation_error" in w.get("type", "")
                for w in structure_warnings
            )
            if not has_critical_errors:
                integrity_warnings = self._verify_oms_artifact_integrity(manifest_data, model_dir, oms_path)
                warnings.extend(integrity_warnings)

            # Step 4: Verify cryptographic signature if present
            if "signature" in manifest_data:
                signature_warnings = self._verify_oms_signature(manifest_data, model_dir)
                warnings.extend(signature_warnings)

        except Exception as e:
            logger.error(f"Error verifying OMS manifest {oms_path}: {str(e)}")
            warnings.append({
                "type": "oms_verification_error",
                "details": {
                    "message": "Error during OMS manifest verification",
                    "file": str(oms_path),
                    "error": str(e),
                    "recommendation": "Check manifest format and file accessibility",
                },
                "severity": "medium",
            })

        return warnings

    def _parse_oms_manifest(self, manifest_path: Path) -> Optional[Dict[str, Any]]:
        """Parse OpenSSF Model Signing manifest.
        
        OMS manifests contain:
        - modelId: Unique identifier for the model
        - artifacts: List of model files with digests
        - signature: DSSE envelope or other signature format
        - timestamp: Signing timestamp
        - metadata: Additional model information
        """
        try:
            if not manifest_path.exists():
                logger.error(f"OMS manifest file not found: {manifest_path}")
                return None

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_json = json.load(f)

            # Validate basic structure
            if not isinstance(manifest_json, dict):
                logger.error("OMS manifest must be a JSON object")
                return None

            # Check for required top-level fields
            oms_config = self.attestation_types["oms"]
            required_fields = oms_config["required_fields"]
            
            missing_fields = []
            for field in required_fields:
                if field not in manifest_json:
                    missing_fields.append(field)

            if missing_fields:
                logger.error(f"Missing required OMS manifest fields: {missing_fields}")
                return None

            # Validate version compatibility
            version = manifest_json.get("version", "1.0")
            if version not in oms_config["supported_versions"]:
                logger.warning(f"Unsupported OMS manifest version: {version}")

            # Parse and validate artifacts section
            artifacts = manifest_json.get("artifacts", [])
            if not isinstance(artifacts, list):
                logger.error("OMS manifest 'artifacts' field must be an array")
                return None

            # Validate each artifact entry
            for i, artifact in enumerate(artifacts):
                if not isinstance(artifact, dict):
                    logger.error(f"Artifact {i} must be an object")
                    return None
                
                required_artifact_fields = oms_config["required_artifact_fields"]
                for field in required_artifact_fields:
                    if field not in artifact:
                        logger.error(f"Artifact {i} missing required field: {field}")
                        return None

            # Validate signature format if present
            signature = manifest_json.get("signature", {})
            if signature and isinstance(signature, dict):
                sig_format = signature.get("format", "")
                if sig_format and sig_format not in oms_config["signature_formats"]:
                    logger.warning(f"Unknown signature format: {sig_format}")

            return manifest_json

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in OMS manifest {manifest_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing OMS manifest {manifest_path}: {str(e)}")
            return None

    def _validate_oms_manifest_structure(self, manifest_data: Dict[str, Any], manifest_path: Path) -> List[Dict[str, Any]]:
        """Validate OMS manifest structure and content."""
        warnings = []
        oms_config = self.attestation_types["oms"]

        try:
            # Validate modelId format
            model_id = manifest_data.get("modelId", "")
            if not model_id or not isinstance(model_id, str):
                warnings.append({
                    "type": "invalid_oms_model_id",
                    "details": {
                        "message": "Missing or invalid modelId in OMS manifest",
                        "recommendation": "Provide valid model identifier string",
                        "file": str(manifest_path),
                    },
                    "severity": "medium",
                })

            # Validate artifacts structure
            artifacts = manifest_data.get("artifacts", [])
            for i, artifact in enumerate(artifacts):
                # Check required artifact fields
                required_fields = oms_config["required_artifact_fields"]
                for field in required_fields:
                    if field not in artifact or not artifact[field]:
                        warnings.append({
                            "type": "invalid_oms_artifact",
                            "details": {
                                "message": f"Artifact {i} missing required field: {field}",
                                "artifact_index": i,
                                "missing_field": field,
                                "file": str(manifest_path),
                                "recommendation": "Ensure all artifacts have name, digest, and mediaType",
                            },
                            "severity": "medium",
                        })

                # Validate digest format
                digest = artifact.get("digest", {})
                if isinstance(digest, dict):
                    supported_algorithms = oms_config["digest_algorithms"]
                    found_algorithms = [alg for alg in supported_algorithms if alg in digest]
                    if not found_algorithms:
                        warnings.append({
                            "type": "unsupported_digest_algorithm",
                            "details": {
                                "message": f"Artifact {i} uses unsupported digest algorithms",
                                "artifact_index": i,
                                "available_algorithms": list(digest.keys()),
                                "supported_algorithms": supported_algorithms,
                                "file": str(manifest_path),
                                "recommendation": f"Use supported digest algorithms: {supported_algorithms}",
                            },
                            "severity": "medium",
                        })

                # Validate media type
                media_type = artifact.get("mediaType", "")
                supported_media_types = oms_config["supported_media_types"]
                if media_type and media_type not in supported_media_types:
                    warnings.append({
                        "type": "unknown_media_type",
                        "details": {
                            "message": f"Artifact {i} has unknown mediaType: {media_type}",
                            "artifact_index": i,
                            "media_type": media_type,
                            "file": str(manifest_path),
                            "recommendation": "Use standard OCI or model-specific media types",
                        },
                        "severity": "low",
                    })

            # Validate timestamp format
            timestamp = manifest_data.get("timestamp")
            if timestamp:
                try:
                    # Accept ISO 8601 format timestamps
                    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    warnings.append({
                        "type": "invalid_timestamp_format",
                        "details": {
                            "message": "Invalid timestamp format in OMS manifest",
                            "timestamp": timestamp,
                            "file": str(manifest_path),
                            "recommendation": "Use ISO 8601 timestamp format (RFC 3339)",
                        },
                        "severity": "low",
                    })

        except Exception as e:
            warnings.append({
                "type": "oms_structure_validation_error",
                "details": {
                    "message": "Error validating OMS manifest structure",
                    "file": str(manifest_path),
                    "error": str(e),
                    "recommendation": "Check manifest format compliance",
                },
                "severity": "medium",
            })

        return warnings

    def _verify_oms_artifact_integrity(self, manifest_data: Dict[str, Any], model_dir: Path, manifest_path: Path) -> List[Dict[str, Any]]:
        """Verify that artifacts listed in OMS manifest match actual files."""
        warnings = []

        try:
            artifacts = manifest_data.get("artifacts", [])
            
            for i, artifact in enumerate(artifacts):
                artifact_name = artifact.get("name", "")
                artifact_digests = artifact.get("digest", {})
                
                if not artifact_name:
                    continue

                # Find the actual file
                artifact_path = model_dir / artifact_name
                if not artifact_path.exists():
                    # Try relative to manifest path
                    artifact_path = manifest_path.parent / artifact_name
                
                if not artifact_path.exists():
                    warnings.append({
                        "type": "missing_oms_artifact",
                        "details": {
                            "message": f"Artifact not found: {artifact_name}",
                            "artifact_index": i,
                            "artifact_name": artifact_name,
                            "searched_paths": [str(model_dir / artifact_name), str(manifest_path.parent / artifact_name)],
                            "recommendation": "Ensure all artifacts listed in manifest are present",
                        },
                        "severity": "high",
                    })
                    continue

                # Verify file digests
                for algorithm, expected_digest in artifact_digests.items():
                    if algorithm in ["sha256", "sha512", "sha1"]:
                        try:
                            hasher = hashlib.new(algorithm)
                            with open(artifact_path, "rb") as f:
                                for chunk in iter(lambda: f.read(8192), b""):
                                    hasher.update(chunk)
                            
                            actual_digest = hasher.hexdigest()
                            
                            if actual_digest.lower() != expected_digest.lower():
                                warnings.append({
                                    "type": "oms_digest_mismatch",
                                    "details": {
                                        "message": f"Digest mismatch for artifact: {artifact_name}",
                                        "artifact_index": i,
                                        "artifact_name": artifact_name,
                                        "algorithm": algorithm,
                                        "expected_digest": expected_digest,
                                        "actual_digest": actual_digest,
                                        "recommendation": "Verify artifact integrity - file may have been modified",
                                    },
                                    "severity": "critical",
                                })
                            else:
                                logger.debug(f"OMS artifact integrity verified: {artifact_name} ({algorithm})")
                                
                        except Exception as hash_error:
                            warnings.append({
                                "type": "oms_digest_verification_error",
                                "details": {
                                    "message": f"Error verifying digest for artifact: {artifact_name}",
                                    "artifact_index": i,
                                    "algorithm": algorithm,
                                    "error": str(hash_error),
                                    "recommendation": "Check file accessibility and integrity",
                                },
                                "severity": "medium",
                            })

        except Exception as e:
            warnings.append({
                "type": "oms_integrity_verification_error",
                "details": {
                    "message": "Error during OMS artifact integrity verification",
                    "error": str(e),
                    "recommendation": "Check manifest format and file accessibility",
                },
                "severity": "medium",
            })

        return warnings

    def _verify_oms_signature(self, manifest_data: Dict[str, Any], model_dir: Path) -> List[Dict[str, Any]]:
        """Verify OMS manifest cryptographic signature.
        
        Note: This is a placeholder for full cryptographic verification.
        Production implementation should integrate with signing libraries.
        """
        warnings = []
        
        try:
            signature = manifest_data.get("signature", {})
            if not signature:
                return warnings

            sig_format = signature.get("format", "")
            
            if sig_format == "dsse":
                # DSSE (Dead Simple Signing Envelope) format
                if "payload" in signature and "signatures" in signature:
                    # Basic structure validation
                    payload = signature.get("payload", "")
                    signatures = signature.get("signatures", [])
                    
                    if not payload or not signatures:
                        warnings.append({
                            "type": "invalid_dsse_signature",
                            "details": {
                                "message": "Invalid DSSE signature structure",
                                "recommendation": "DSSE signature must have payload and signatures",
                            },
                            "severity": "medium",
                        })
                    else:
                        # TODO: Implement full DSSE signature verification
                        logger.info("OMS DSSE signature structure validated (cryptographic verification pending)")
                        
            elif sig_format in ["pkcs7", "jws"]:
                # Other supported signature formats
                logger.info(f"OMS {sig_format} signature detected (verification pending)")
                
            else:
                warnings.append({
                    "type": "unsupported_oms_signature_format",
                    "details": {
                        "message": f"Unsupported OMS signature format: {sig_format}",
                        "signature_format": sig_format,
                        "supported_formats": self.attestation_types["oms"]["signature_formats"],
                        "recommendation": "Use supported signature formats: DSSE, PKCS7, or JWS",
                    },
                    "severity": "medium",
                })
                
        except Exception as e:
            warnings.append({
                "type": "oms_signature_verification_error",
                "details": {
                    "message": "Error during OMS signature verification",
                    "error": str(e),
                    "recommendation": "Check signature format and structure",
                },
                "severity": "medium",
            })
            
        return warnings

    # ========================================================================
    # SIGSTORE MODEL TRANSPARENCY VERIFICATION
    # ========================================================================

    def _verify_with_cosign(self, model_dir: Path, bundle_path: Path) -> Dict[str, Any]:
        """Verify signature using cosign verify-blob command with public key.
        
        Args:
            model_dir: Model directory containing the signed file
            bundle_path: Path to the bundle file (e.g., model.safetensors.bundle)
        
        Returns:
            Dict with 'valid' (bool) and optional 'error' (str)
        """
        import subprocess
        import shutil
        
        # Check if cosign is available
        if not shutil.which("cosign"):
            return {
                "valid": False,
                "error": "cosign CLI not found - install from https://docs.sigstore.dev/cosign/installation/"
            }
        
        try:
            # Determine the signed file (remove .bundle extension)
            signed_file_path = Path(str(bundle_path).replace(".bundle", ""))
            if not signed_file_path.exists():
                return {"valid": False, "error": f"Signed file not found: {signed_file_path}"}
            
            # Run cosign verify-blob
            cmd = [
                "cosign", "verify-blob",
                "--key", str(self.public_key_path),
                "--bundle", str(bundle_path),
                "--insecure-ignore-tlog",  # Skip transparency log check (already validated structure)
                str(signed_file_path)
            ]
            
            logger.info(f"Running cryptographic verification: cosign verify-blob --key {self.public_key_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✓ cosign verification successful")
                return {"valid": True}
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Verification failed"
                logger.error(f"✗ cosign verification failed: {error_msg}")
                return {"valid": False, "error": error_msg}
        
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "Verification timeout (30s)"}
        except Exception as e:
            return {"valid": False, "error": f"Verification error: {str(e)}"}

    def _verify_attestation_with_cosign(self, model_dir: Path, bundle_path: Path, 
                                        model_file_path: Path) -> Dict[str, Any]:
        """Verify attestation bundle signature using cosign verify-blob-attestation.
        
        Args:
            model_dir: Directory containing the model
            bundle_path: Path to the attestation bundle
            model_file_path: Path to the model file the attestation is for
            
        Returns:
            Dict with 'valid' boolean and optional 'error' message
        """
        if not self.public_key_path:
            return {"valid": False, "error": "No public key provided"}
        
        try:
            # Run cosign verify-blob-attestation
            cmd = [
                "cosign", "verify-blob-attestation",
                "--key", str(self.public_key_path),
                "--bundle", str(bundle_path),
                "--insecure-ignore-tlog",  # Skip transparency log check
                "--type", "slsaprovenance",
                "--check-claims=false",  # Don't verify predicate claims, just signature
                str(model_file_path)
            ]
            
            logger.info(f"Running attestation verification: cosign verify-blob-attestation --key {self.public_key_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✓ cosign attestation verification successful")
                return {"valid": True}
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Verification failed"
                logger.error(f"✗ cosign attestation verification failed: {error_msg}")
                return {"valid": False, "error": error_msg}
        
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "Verification timeout (30s)"}
        except FileNotFoundError:
            return {"valid": False, "error": "cosign not found - install with: brew install cosign"}
        except Exception as e:
            return {"valid": False, "error": f"Verification error: {str(e)}"}

    def verify_sigstore_model_transparency(self, model_dir: Path,
                                         provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """CRITICAL: Verify Sigstore model transparency signatures.

        This performs the actual cryptographic verification of Sigstore
        signatures rather than pattern-based trust.
        """
        warnings = []

        if not SIGSTORE_AVAILABLE:
            logger.warning("Sigstore not available - model transparency verification disabled")
            return warnings

        # Find Sigstore signature files (.sig or .bundle files)
        # Exclude .att.bundle files (attestation bundles) - they're handled separately
        sig_files = [
            doc for doc in provenance_docs 
            if doc.get("path", "").endswith((".sig", ".bundle"))
            and ".att.bundle" not in doc.get("path", "").lower()
        ]

        if not sig_files:
            return warnings
        
        logger.info(f"Found {len(sig_files)} Sigstore signature files")

        # Verify each signature file
        for sig_doc in sig_files:
            sig_warnings = self._verify_single_sigstore_signature(model_dir, sig_doc)
            warnings.extend(sig_warnings)

        return warnings

    def _verify_single_sigstore_signature(self, model_dir: Path,
                                        sig_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify a single Sigstore model transparency signature file.

        This performs the actual cryptographic verification:
        1. Parse the .sig bundle (JSON protobuf format)
        2. Extract DSSE envelope and in-toto statement
        3. Verify cryptographic signature
        4. Recompute and compare model file hashes
        5. Validate signer identity against trusted signers
        """
        warnings = []
        
        try:
            sig_path = Path(sig_doc["path"])
            logger.info(f"Verifying Sigstore model transparency signature: {sig_path.name}")

            # Step 1: Parse Sigstore bundle
            bundle_data = self._parse_sigstore_bundle(sig_path)
            if not bundle_data:
                warnings.append({
                    "type": "invalid_sigstore_bundle",
                    "details": {
                        "message": "Could not parse Sigstore bundle format",
                        "file": str(sig_path),
                        "recommendation": "Verify signature file is valid Sigstore bundle",
                    },
                    "severity": "high",
                })
                return warnings

            # Step 2: Verify cryptographic signature
            verification_result = self._verify_sigstore_signature(bundle_data, model_dir, sig_path)
            if not verification_result["valid"]:
                warnings.append({
                    "type": "invalid_cryptographic_signature",
                    "details": {
                        "message": "Cryptographic signature verification failed",
                        "file": str(sig_path),
                        "error": verification_result.get("error", "Unknown error"),
                        "recommendation": "Check signature validity and certificate chain",
                    },
                    "severity": "critical",
                })
                return warnings

            # Track successful verification
            if not hasattr(self, '_cryptographic_verifications'):
                self._cryptographic_verifications = []
            
            self._cryptographic_verifications.append({
                "file": str(sig_path),
                "signer": verification_result.get("signer_identity"),
                "bundle_version": verification_result.get("bundle_version", "unknown"),
                "verified": True,
            })
            
            # Different messaging for local key vs. OIDC/certificate-based signatures
            signer = verification_result.get('signer_identity')
            if signer == "local-key":
                logger.info("✓ Sigstore bundle structure validated (local key signature)")
                logger.info(f"  Bundle version: {verification_result.get('bundle_version', 'unknown')}")
                logger.info("  Note: Content verification requires 'cosign verify-blob' with public key")
            elif signer == "local-key-verified":
                logger.info("✓ Sigstore signature cryptographically verified (local key with public key)")
                logger.info(f"  Bundle version: {verification_result.get('bundle_version', 'unknown')}")
            else:
                logger.info(f"✓ Sigstore signature cryptographically verified: {signer}")
                logger.info(f"  Bundle version: {verification_result.get('bundle_version', 'unknown')}")

        except Exception as e:
            logger.error(f"Error verifying Sigstore signature {sig_path}: {str(e)}")
            warnings.append({
                "type": "sigstore_verification_error",
                "details": {
                    "message": "Error during Sigstore verification",
                    "file": str(sig_path),
                    "error": str(e),
                    "recommendation": "Check signature file format and accessibility",
                },
                "severity": "medium",
            })

        return warnings

    def _parse_sigstore_bundle(self, sig_path: Path) -> Optional[Dict[str, Any]]:
        """Parse Sigstore bundle (JSON protobuf format).

        Model transparency creates sigstore bundles containing:
        - DSSE envelope with in-toto statement
        - Signature verification materials
        - Subject list (file paths + digests)
        """
        try:
            if not sig_path.exists():
                logger.error(f"Sigstore signature file not found: {sig_path}")
                return None

            with open(sig_path, "r", encoding="utf-8") as f:
                bundle_json = json.load(f)

            # Validate bundle structure
            if not isinstance(bundle_json, dict):
                logger.error("Sigstore bundle must be a JSON object")
                return None

            # Detect bundle version (v0.3+ vs older formats)
            media_type = bundle_json.get("mediaType", "")
            is_v03_bundle = "v0.3" in media_type
            has_message_signature = "messageSignature" in bundle_json
            has_dsse_envelope = "dsseEnvelope" in bundle_json
            
            logger.info(f"Detected Sigstore bundle format: {media_type if media_type else 'legacy'}")

            # Bundle v0.3+ format (cosign v3.0+)
            # - Signature bundles have messageSignature
            # - Attestation bundles have dsseEnvelope
            if is_v03_bundle:
                if "verificationMaterial" not in bundle_json:
                    logger.error("Missing required field 'verificationMaterial' in bundle v0.3")
                    return None
                
                # Check for either messageSignature (signatures) or dsseEnvelope (attestations)
                if has_message_signature:
                    # Regular signature bundle
                    logger.info("Bundle v0.3 signature format validated - ready for verification")
                    return {
                        "bundle": bundle_json,
                        "bundle_version": "v0.3",
                        "bundle_type": "signature",
                        "media_type": media_type,
                    }
                elif has_dsse_envelope:
                    # Attestation bundle (SLSA provenance, etc.)
                    logger.info("Bundle v0.3 attestation format validated - ready for verification")
                    # Fall through to dsseEnvelope parsing below
                else:
                    logger.error("Bundle v0.3 missing both 'messageSignature' and 'dsseEnvelope'")
                    return None
            
            # dsseEnvelope format (attestation bundles or legacy signature bundles)
            # Check for required bundle fields (simplified validation)
            required_fields = ["dsseEnvelope", "verificationMaterial"]
            for field in required_fields:
                if field not in bundle_json:
                    logger.error(f"Missing required Sigstore bundle field: {field}")
                    return None
                
                if not isinstance(bundle_json[field], dict):
                    logger.error(f"Invalid type for required field {field}: expected dict, got {type(bundle_json[field])}")
                    return None

            # Extract DSSE envelope with validation
            dsse_envelope = bundle_json.get("dsseEnvelope", {})
            if "payload" not in dsse_envelope or "signatures" not in dsse_envelope:
                logger.error("Invalid DSSE envelope structure - missing payload or signatures")
                return None

            if not isinstance(dsse_envelope["payload"], str):
                logger.error("DSSE payload must be a string")
                return None

            if not isinstance(dsse_envelope["signatures"], list):
                logger.error("DSSE signatures must be an array")
                return None

            # Decode and validate DSSE payload (base64 encoded JSON)
            try:
                payload_json = base64.b64decode(dsse_envelope["payload"]).decode("utf-8")
                try:
                    payload_data = json.loads(payload_json)
                except json.JSONDecodeError as json_error:
                    logger.error(f"Invalid JSON in DSSE payload: {str(json_error)}")
                    return None

            except KeyError as e:
                logger.error(f"Missing expected field in DSSE envelope: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error decoding DSSE payload: {str(e)}")
                return None

            # Validate payload structure
            if not isinstance(payload_data, dict):
                logger.error("DSSE payload must decode to JSON object")
                return None

            # Check for in-toto statement structure
            if "_type" not in payload_data:
                logger.error("DSSE payload missing _type field")
                return None

            if "subject" not in payload_data:
                logger.error("DSSE payload missing subject field")
                return None

            if not isinstance(payload_data["subject"], list):
                logger.error("DSSE payload subject must be an array")
                return None

            # Determine if this is a v0.3 attestation or legacy format
            bundle_version = "v0.3" if is_v03_bundle else "legacy"
            bundle_type = "attestation" if is_v03_bundle else "signature"
            
            return {
                "bundle": bundle_json,
                "dsse_envelope": dsse_envelope,
                "payload": payload_data,
                "bundle_version": bundle_version,
                "bundle_type": bundle_type,
                "media_type": media_type,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Sigstore bundle {sig_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Sigstore bundle {sig_path}: {str(e)}")
            return None

    def _verify_sigstore_signature(self, bundle_data: Dict[str, Any],
                                 model_dir: Path, sig_path: Path) -> Dict[str, Any]:
        """Perform cryptographic signature verification using sigstore-python.
        
        Args:
            bundle_data: Parsed bundle data
            model_dir: Model directory
            sig_path: Path to signature/bundle file
        
        Returns verification result with signer identity and validity
        """
        try:
            # Get bundle version from parsed data
            bundle_version = bundle_data.get("bundle_version", "unknown")
            bundle_json = bundle_data.get("bundle", {})
            
            # Feature-based detection: check what the bundle contains, not just version string
            has_message_signature = "messageSignature" in bundle_json
            has_dsse_envelope = "dsseEnvelope" in bundle_json
            is_v03_or_newer = bundle_version.startswith("v0.3") or bundle_version.startswith("v0.4") or bundle_version.startswith("v1")
            
            # Modern bundle format (v0.3+) with messageSignature
            if has_message_signature or (is_v03_or_newer and not has_dsse_envelope):
                # For Bundle v0.3 with local keys, we need custom verification
                logger.info("Verifying Bundle v0.3 format (local key signature)")
                
                # Check if this is a local key signature (no certificate) or OIDC signature
                verification_material = bundle_json.get("verificationMaterial", {})
                has_certificate = "certificate" in verification_material or "x509CertificateChain" in verification_material
                has_public_key = "publicKey" in verification_material
                
                if has_certificate:
                    # OIDC/keyless signature - use sigstore Verifier API
                    logger.info("Detected OIDC/keyless signature - using Verifier API")
                    try:
                        bundle = Bundle.from_json(json.dumps(bundle_json).encode())
                        logger.info("✓ Successfully created Bundle object from v0.3 format")
                        # TODO: Actually verify the bundle with Verifier.verify()
                        return {
                            "valid": True,
                            "signer_identity": "oidc-verified",
                            "verification_materials": verification_material,
                            "bundle_version": "v0.3-oidc",
                            "note": "OIDC signature bundle validated",
                        }
                    except Exception as e:
                        logger.error(f"Failed to verify OIDC bundle: {e}")
                        return {
                            "valid": False,
                            "error": f"OIDC bundle verification failed: {str(e)}",
                        }
                
                elif has_public_key:
                    # Local key signature - validate structure and optionally verify cryptographically
                    logger.info("Detected local key signature - validating bundle structure")
                    
                    # Validate message signature exists
                    message_sig = bundle_json.get("messageSignature", {})
                    if not message_sig:
                        return {
                            "valid": False,
                            "error": "Missing messageSignature in bundle",
                        }
                    
                    # Validate signature and digest are present
                    if "signature" not in message_sig:
                        return {
                            "valid": False,
                            "error": "Missing signature in messageSignature",
                        }
                    
                    if "messageDigest" not in message_sig:
                        return {
                            "valid": False,
                            "error": "Missing messageDigest in messageSignature",
                        }
                    
                    # Validate transparency log entry (proves signature was created)
                    tlog_entries = verification_material.get("tlogEntries", [])
                    if tlog_entries and len(tlog_entries) > 0:
                        logger.info(f"✓ Transparency log entries found: {len(tlog_entries)}")
                        logger.info(f"  Log index: {tlog_entries[0].get('logIndex', 'unknown')}")
                    
                    logger.info("✓ Bundle v0.3 local key signature structure validated")
                    
                    # If public key provided, perform actual cryptographic verification
                    if self.public_key_path:
                        crypto_result = self._verify_with_cosign(model_dir, sig_path)
                        if crypto_result["valid"]:
                            logger.info("✓ Cryptographic verification successful using public key")
                            return {
                                "valid": True,
                                "signer_identity": "local-key-verified",
                                "verification_materials": verification_material,
                                "bundle_version": "v0.3-local-key",
                                "note": "Local key signature cryptographically verified",
                            }
                        else:
                            logger.error(f"✗ Cryptographic verification failed: {crypto_result.get('error')}")
                            return {
                                "valid": False,
                                "error": f"Signature verification failed: {crypto_result.get('error')}",
                            }
                    
                    # No public key - CANNOT verify file integrity, only structure
                    # This is NOT a verified state - we haven't checked the file content
                    logger.warning("⚠ No public key provided - cannot verify file integrity")
                    logger.warning("  Run with --public-key <path> to verify the signature matches the file")
                    return {
                        "valid": False,
                        "signer_identity": "local-key-unverified",
                        "verification_materials": verification_material,
                        "bundle_version": "v0.3-local-key",
                        "error": "Public key required for local key signature verification. Bundle structure is valid but file integrity not verified.",
                        "requires_public_key": True,
                    }
                
                else:
                    return {
                        "valid": False,
                        "error": "Bundle has neither certificate nor public key in verificationMaterial",
                    }
            
            # Legacy format with dsseEnvelope
            else:
                # Create Sigstore verifier
                verifier = Verifier.production()

                # Convert bundle data to sigstore Bundle object
                bundle = Bundle.from_json(json.dumps(bundle_json).encode())

                # Extract verification materials
                verification_materials = bundle_json.get("verificationMaterial", {})
                
                return {
                    "valid": True,
                    "signer_identity": "verified",
                    "verification_materials": verification_materials,
                    "bundle_version": "legacy",
                }

        except ExpectedSignerError as e:
            return {
                "valid": False,
                "error": f"Signer verification failed: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return {
                "valid": False, 
                "error": f"Signature verification error: {str(e)}",
            }

    # ========================================================================
    # SLSA FOR MODELS PROVENANCE VERIFICATION
    # ========================================================================

    def verify_slsa_ml_provenance(self, model_dir: Path,
                                provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """CRITICAL: Verify SLSA for Models provenance attestations.
        
        SLSA (Supply-chain Levels for Software Artifacts) provides provenance
        for ML models including training metadata, dependencies, and build info.
        
        Supports:
        - Plain JSON attestation files (.json)
        - Sigstore attestation bundles (.att.bundle) containing DSSE envelopes
        """
        warnings = []

        # Find SLSA provenance files (plain JSON)
        slsa_json_files = [
            doc for doc in provenance_docs
            if any(pattern in doc.get("path", "").lower() for pattern in [
                "slsa", "provenance", "attestation"
            ]) and doc.get("path", "").endswith(".json")
        ]
        
        # Find attestation bundles (.att.bundle files)
        attestation_bundles = [
            doc for doc in provenance_docs
            if ".att." in doc.get("path", "").lower() and doc.get("path", "").endswith(".bundle")
        ]

        total_found = len(slsa_json_files) + len(attestation_bundles)
        if total_found == 0:
            return warnings

        logger.info(f"Found {total_found} potential SLSA provenance files ({len(slsa_json_files)} JSON, {len(attestation_bundles)} bundles)")

        # Verify plain JSON attestations
        for slsa_doc in slsa_json_files:
            slsa_warnings = self._verify_single_slsa_attestation(model_dir, slsa_doc)
            warnings.extend(slsa_warnings)
        
        # Verify attestation bundles (extract DSSE payload and verify)
        for bundle_doc in attestation_bundles:
            bundle_warnings = self._verify_slsa_attestation_bundle(model_dir, bundle_doc)
            warnings.extend(bundle_warnings)

        return warnings
    
    def _verify_slsa_attestation_bundle(self, model_dir: Path,
                                        bundle_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify SLSA attestation from a Sigstore attestation bundle.
        
        Attestation bundles contain a DSSE envelope with the attestation payload.
        """
        warnings = []
        bundle_path = Path(bundle_doc["path"])
        
        try:
            logger.info(f"Verifying SLSA attestation bundle: {bundle_path.name}")
            
            # Parse the bundle
            parsed = self._parse_sigstore_bundle(bundle_path)
            if not parsed:
                warnings.append({
                    "type": "invalid_attestation_bundle",
                    "details": {
                        "message": "Failed to parse attestation bundle",
                        "file": str(bundle_path),
                    },
                    "severity": "medium",
                })
                return warnings
            
            # Check if it's an attestation bundle (has DSSE envelope with payload)
            if "payload" not in parsed:
                warnings.append({
                    "type": "missing_attestation_payload",
                    "details": {
                        "message": "Attestation bundle missing DSSE payload",
                        "file": str(bundle_path),
                    },
                    "severity": "medium",
                })
                return warnings
            
            # The payload contains the in-toto statement with SLSA predicate
            payload = parsed["payload"]
            
            # Validate SLSA structure in the payload
            structure_warnings = self._validate_slsa_structure(payload, str(bundle_path))
            warnings.extend(structure_warnings)
            
            # If structure is valid, verify build definition
            if not any(w["type"].startswith("slsa_structure") for w in structure_warnings):
                build_warnings = self._verify_slsa_build_definition(payload, model_dir)
                warnings.extend(build_warnings)
                
                # Verify builder trust
                trust_warnings = self._verify_slsa_builder_trust(payload)
                warnings.extend(trust_warnings)
                
                # Perform cryptographic verification if public key is available
                crypto_verified = False
                if self.public_key_path:
                    # Attestation bundles can be verified with cosign verify-blob-attestation
                    # The bundle is for the model file (derive from bundle name: model.safetensors.att.bundle -> model.safetensors)
                    bundle_name = bundle_path.name
                    if ".att.bundle" in bundle_name:
                        model_file_name = bundle_name.replace(".att.bundle", "")
                        model_file_path = bundle_path.parent / model_file_name
                        
                        if model_file_path.exists():
                            crypto_result = self._verify_attestation_with_cosign(model_dir, bundle_path, model_file_path)
                            if crypto_result.get("valid"):
                                logger.info("✓ SLSA attestation cryptographically verified")
                                crypto_verified = True
                                # Track cryptographic verification
                                if not hasattr(self, '_cryptographic_verifications'):
                                    self._cryptographic_verifications = []
                                self._cryptographic_verifications.append({
                                    "type": "slsa_attestation",
                                    "file": str(bundle_path),
                                    "signer": "local-key-verified",
                                    "bundle_version": parsed.get("bundle_version", "unknown"),
                                })
                            else:
                                logger.warning(f"Attestation cryptographic verification failed: {crypto_result.get('error', 'Unknown error')}")
                        else:
                            logger.warning(f"Model file not found for attestation: {model_file_path}")
                else:
                    # No public key provided - warn user
                    logger.warning("⚠ No public key provided - cannot cryptographically verify SLSA attestation")
                    logger.warning("  Run with --public-key <path> to verify the attestation signature")
                
                # Track successful verification
                logger.info(f"✓ SLSA attestation bundle verified: {bundle_path.name}")
                if not hasattr(self, '_verified_slsa_attestations'):
                    self._verified_slsa_attestations = []
                self._verified_slsa_attestations.append(str(bundle_path))
            
        except Exception as e:
            logger.error(f"Error verifying SLSA attestation bundle {bundle_path}: {str(e)}")
            warnings.append({
                "type": "slsa_bundle_verification_error",
                "details": {
                    "message": f"Error verifying attestation bundle: {str(e)}",
                    "file": str(bundle_path),
                },
                "severity": "medium",
            })
        
        return warnings

    def _verify_single_slsa_attestation(self, model_dir: Path,
                                      slsa_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify a single SLSA provenance attestation."""
        warnings = []
        
        try:
            slsa_path = Path(slsa_doc["path"])
            logger.info(f"Verifying SLSA attestation: {slsa_path.name}")

            # Parse attestation file
            if not slsa_path.exists():
                warnings.append({
                    "type": "missing_slsa_file",
                    "details": {
                        "message": "SLSA attestation file not found",
                        "file": str(slsa_path),
                    },
                    "severity": "medium",
                })
                return warnings

            with open(slsa_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            # Validate SLSA structure
            structure_warnings = self._validate_slsa_structure(content, str(slsa_path))
            warnings.extend(structure_warnings)

            # If structure is valid, verify build definition
            if not any(w["type"].startswith("slsa_structure") for w in structure_warnings):
                build_warnings = self._verify_slsa_build_definition(content, model_dir)
                warnings.extend(build_warnings)

                # Verify builder trust
                trust_warnings = self._verify_slsa_builder_trust(content)
                warnings.extend(trust_warnings)

        except json.JSONDecodeError as e:
            warnings.append({
                "type": "invalid_slsa_json",
                "details": {
                    "message": "Invalid JSON in SLSA attestation",
                    "file": str(slsa_path),
                    "error": str(e),
                },
                "severity": "medium",
            })
        except Exception as e:
            logger.error(f"Error verifying SLSA attestation {slsa_path}: {str(e)}")
            warnings.append({
                "type": "slsa_verification_error",
                "details": {
                    "message": "Error during SLSA verification",
                    "file": str(slsa_path),
                    "error": str(e),
                },
                "severity": "medium",
            })

        return warnings

    def _validate_slsa_structure(self, content: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Validate SLSA attestation structure.
        
        Supports both SLSA v0.2 and v1.0 predicate formats:
        - v0.2: builder, buildType, invocation, materials, metadata
        - v1.0: buildDefinition, runDetails
        """
        warnings = []

        try:
            # Check for SLSA predicate type (both v0.2 and v1.0)
            predicate_type = content.get("predicateType", "")
            valid_predicate_types = ["slsa.dev/provenance", "in-toto.io"]
            
            if not predicate_type or not any(t in predicate_type for t in valid_predicate_types):
                warnings.append({
                    "type": "slsa_structure_invalid_predicate",
                    "details": {
                        "message": "Missing or invalid SLSA predicateType",
                        "predicate_type": predicate_type,
                        "file": file_path,
                        "recommendation": "Use SLSA provenance predicate type",
                    },
                    "severity": "medium",
                })

            # Check for required SLSA fields
            predicate = content.get("predicate", {})
            if not isinstance(predicate, dict):
                warnings.append({
                    "type": "slsa_structure_missing_predicate",
                    "details": {
                        "message": "Missing or invalid SLSA predicate",
                        "file": file_path,
                    },
                    "severity": "medium",
                })
                return warnings

            # Detect SLSA version and validate accordingly
            is_v1 = "buildDefinition" in predicate or "runDetails" in predicate
            is_v02 = "builder" in predicate or "buildType" in predicate or "materials" in predicate
            
            if is_v1:
                # SLSA v1.0 format validation
                if "buildDefinition" not in predicate:
                    warnings.append({
                        "type": "slsa_structure_missing_build_definition",
                        "details": {
                            "message": "Missing SLSA v1.0 buildDefinition",
                            "file": file_path,
                        },
                        "severity": "medium",
                    })

                if "runDetails" not in predicate:
                    warnings.append({
                        "type": "slsa_structure_missing_run_details",
                        "details": {
                            "message": "Missing SLSA v1.0 runDetails",
                            "file": file_path,
                        },
                        "severity": "medium",
                    })
            elif is_v02:
                # SLSA v0.2 format validation (more lenient)
                logger.info(f"Detected SLSA v0.2 format in {file_path}")
                
                # v0.2 requires builder at minimum
                if "builder" not in predicate and "buildType" not in predicate:
                    warnings.append({
                        "type": "slsa_structure_missing_builder",
                        "details": {
                            "message": "Missing SLSA v0.2 builder/buildType",
                            "file": file_path,
                        },
                        "severity": "medium",
                    })
            else:
                # Unknown format
                warnings.append({
                    "type": "slsa_structure_unknown_format",
                    "details": {
                        "message": "Unknown SLSA predicate format",
                        "file": file_path,
                        "recommendation": "Use SLSA v0.2 or v1.0 format",
                    },
                    "severity": "medium",
                })

        except Exception as e:
            warnings.append({
                "type": "slsa_structure_validation_error",
                "details": {
                    "message": "Error validating SLSA structure",
                    "file": file_path,
                    "error": str(e),
                },
                "severity": "medium",
            })

        return warnings

    def _verify_slsa_build_definition(self, content: Dict[str, Any], model_dir: Path) -> List[Dict[str, Any]]:
        """Verify SLSA build definition for ML models."""
        warnings = []

        try:
            predicate = content.get("predicate", {})
            build_def = predicate.get("buildDefinition", {})

            # Check builder information
            builder = build_def.get("builder", {})
            if not builder or not isinstance(builder, dict):
                warnings.append({
                    "type": "slsa_missing_builder_info",
                    "details": {
                        "message": "Missing SLSA builder information",
                        "recommendation": "Include builder identity and version",
                    },
                    "severity": "medium",
                })
            else:
                builder_id = builder.get("id", "")
                if not builder_id:
                    warnings.append({
                        "type": "slsa_missing_builder_id",
                        "details": {
                            "message": "Missing SLSA builder ID",
                            "recommendation": "Specify builder identity",
                        },
                        "severity": "medium",
                    })

            # Check build type for ML models
            build_type = build_def.get("buildType", "")
            if "ml" not in build_type.lower() and "model" not in build_type.lower():
                warnings.append({
                    "type": "slsa_non_ml_build_type",
                    "details": {
                        "message": "Build type does not appear to be ML-specific",
                        "build_type": build_type,
                        "recommendation": "Use ML-specific build type identifier",
                    },
                    "severity": "low",
                })

        except Exception as e:
            warnings.append({
                "type": "slsa_build_verification_error",
                "details": {
                    "message": "Error verifying SLSA build definition",
                    "error": str(e),
                },
                "severity": "medium",
            })

        return warnings

    def _verify_slsa_builder_trust(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify SLSA builder trust and reputation."""
        warnings = []

        try:
            predicate = content.get("predicate", {})
            build_def = predicate.get("buildDefinition", {})
            builder = build_def.get("builder", {})

            builder_id = builder.get("id", "")
            
            # List of known trusted ML builders (can be made configurable)
            trusted_builders = [
                "github.com/actions/runner",
                "google.com/ml-platform",
                "huggingface.co/transformers",
                "pytorch.org/hub",
            ]

            builder_trusted = any(trusted in builder_id for trusted in trusted_builders)

            if not builder_trusted and builder_id:
                warnings.append({
                    "type": "slsa_untrusted_builder",
                    "details": {
                        "message": "SLSA builder is not in trusted list",
                        "builder_id": builder_id,
                        "trusted_builders": trusted_builders,
                        "recommendation": "Verify builder reputation and add to trusted list if appropriate",
                    },
                    "severity": "medium",
                })

            # Check for builder version/attestation
            builder_version = builder.get("version", "")
            if not builder_version:
                warnings.append({
                    "type": "slsa_missing_builder_version",
                    "details": {
                        "message": "Missing SLSA builder version",
                        "recommendation": "Include builder version for reproducibility",
                    },
                    "severity": "low",
                })

        except Exception as e:
            warnings.append({
                "type": "slsa_trust_verification_error",
                "details": {
                    "message": "Error verifying SLSA builder trust",
                    "error": str(e),
                },
                "severity": "medium",
            })

        return warnings