"""Provenance and attestation validator - Critical for supply chain security."""

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    # Note: Warning will be logged in _verify_sigstore_model_transparency when needed

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.core.cosai_maturity import CoSAIMaturityDetector, CoSAIMaturityLevel

from .base import BaseValidator

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine

logger = logging.getLogger(__name__)

class ProvenanceSecurityValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR
    Validates model provenance and supply chain security:
    - OCI/registry signature verification
    - Attestation document parsing and validation
    - ML-BOM (Machine Learning Bill of Materials) generation
    - Model family and lineage tracking
    - Commit/refs and version verification
    - Quantization and adapter provenance
    - Comprehensive file digest verification.
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Load policy-configurable settings
        self._load_policy_configuration()
        
        # Initialize CoSAI maturity detector
        self.cosai_detector = CoSAIMaturityDetector()
        
        # Initialize provenance tracking counters
        self._discovered_signature_files = 0
        self._discovered_attestation_files = 0
        self._discovered_provenance_docs = 0

        # Known model families and their identifiers (policy-configurable)
        self.model_families = {
            "llama": {
                "patterns": ["llama", "meta-llama", "llamav2", "llama-2", "code-llama"],
                "official_sources": ["meta-llama", "facebook", "huggingface.co/meta-llama"],
                "architecture": "llama",
            },
            "mistral": {
                "patterns": ["mistral", "mixtral"],
                "official_sources": ["mistralai", "huggingface.co/mistralai"],
                "architecture": "mistral",
            },
            "gpt": {
                "patterns": ["gpt-", "openai-gpt", "gpt2", "gpt-neo", "gpt-j"],
                "official_sources": ["openai", "eleutherai", "huggingface.co/openai"],
                "architecture": "gpt",
            },
            "bert": {
                "patterns": ["bert", "roberta", "distilbert"],
                "official_sources": ["google", "facebook", "huggingface.co/google"],
                "architecture": "bert",
            },
            "claude": {
                "patterns": ["claude"],
                "official_sources": ["anthropic"],
                "architecture": "transformer",
            },
        }

        # Provenance document types and their validation requirements
        self.attestation_types = {
            "in-toto": {
                "required_fields": ["_type", "subject", "predicateType", "predicate"],
                "predicate_types": ["https://slsa.dev/provenance/v0.2", "https://in-toto.io/Statement/v0.1"],
            },
            "slsa": {
                "required_fields": ["buildDefinition", "runDetails", "buildMetadata"],
                "builder_trust_levels": ["verified", "trusted", "community"],
                "ml_predicate_types": [
                    "https://slsa.dev/provenance/v1",
                    "https://slsa.dev/provenance/v0.2",
                    "https://model-transparency.dev/ml-provenance/v1",
                ],
                "ml_required_fields": {
                    "training": ["framework", "dataset", "hyperparameters"],
                    "model": ["architecture", "format", "size"],
                    "environment": ["python_version", "gpu_info", "dependencies"],
                },
            },
            "sigstore": {
                "required_fields": ["signature", "payload", "certificate"],
                "signature_formats": ["base64", "hex"],
            },
            "cosign": {
                "required_fields": ["critical", "optional"],
                "supported_algorithms": ["sha256", "sha512"],
            },
            "oms": {
                "required_fields": ["modelId", "artifacts", "signature", "timestamp"],
                "supported_versions": ["1.0"],
                "digest_algorithms": ["sha256", "sha512"],
                "signature_formats": ["dsse", "pkcs7", "jws"],
                "required_artifact_fields": ["name", "digest", "mediaType"],
                "supported_media_types": [
                    "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.huggingface.model+json",
                    "application/vnd.pytorch.model+json",
                    "application/vnd.onnx.model+json"
                ],
            },
            "ml-bom": {
                "required_fields": ["bomFormat", "specVersion", "components", "metadata"],
                "component_types": ["model", "dataset", "framework", "library"],
            },
        }

        # OCI/Container registry patterns
        self.registry_patterns = {
            "docker_hub": r"^(?:docker\.io/)?([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
            "ghcr": r"^ghcr\.io/([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
            "huggingface": r"^huggingface\.co/([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*)",
            "aws_ecr": r"^([0-9]{12})\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
            "gcp_gcr": r"^(?:gcr\.io|us\.gcr\.io|eu\.gcr\.io|asia\.gcr\.io)/([a-z0-9-]+)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
        }

        # Suspicious provenance patterns
        self.suspicious_provenance_patterns = {
            "untrusted_sources": {
                "domains": ["bit.ly", "tinyurl.com", "pastebin.com", "hastebin.com"],
                "file_services": ["mega.nz", "mediafire.com", "rapidshare.com"],
                "suspicious_usernames": ["anonymous", "temp", "test", "fake", "admin", "root"],
            },
            "suspicious_commits": {
                "commit_messages": ["backdoor", "secret", "hidden", "exploit", "bypass", "hack"],
                "branch_names": ["malicious", "backdoor", "exploit", "hack", "bypass"],
                "suspicious_patterns": ["0x", "eval(", "exec(", "system(", "__import__"],
            },
            "timing_anomalies": {
                "max_build_time_hours": 168,  # 1 week
                "suspicious_build_times": ["00:00:00", "12:34:56", "23:59:59"],  # Common fake times
            },
        }

        # File digest algorithms (ordered by security preference)
        self.digest_algorithms = ["sha512", "sha256", "sha1", "md5"]

        # Quantization type mappings for provenance tracking
        self.quantization_provenance = {
            "float32": {"bits": 32, "method": "none", "compression_ratio": 1.0},
            "float16": {"bits": 16, "method": "fp16", "compression_ratio": 2.0},
            "bfloat16": {"bits": 16, "method": "bf16", "compression_ratio": 2.0},
            "int8": {"bits": 8, "method": "int8_quantization", "compression_ratio": 4.0},
            "int4": {"bits": 4, "method": "int4_quantization", "compression_ratio": 8.0},
            "q4_0": {"bits": 4, "method": "ggml_q4_0", "compression_ratio": 7.0},
            "q4_1": {"bits": 4, "method": "ggml_q4_1", "compression_ratio": 7.5},
            "q5_0": {"bits": 5, "method": "ggml_q5_0", "compression_ratio": 6.0},
            "q8_0": {"bits": 8, "method": "ggml_q8_0", "compression_ratio": 4.0},
        }

    def _load_policy_configuration(self) -> None:
        """Load policy-configurable settings for provenance security."""
        # Get policy configuration for provenance security validator
        policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            policy_config = self.policy_engine.get_validator_config("provenance_security", {})

        # Load trusted source requirements
        self.require_trusted_sources = policy_config.get("require_trusted_sources", True)

        # Load signature requirements
        self.require_signatures = policy_config.get("require_signatures", False)  # Not required by default
        self.signature_strictness = policy_config.get("signature_strictness", "medium")  # low, medium, high

        # Load attestation requirements
        self.require_attestations = policy_config.get("require_attestations", False)
        self.accepted_attestation_types = set(policy_config.get("accepted_attestation_types",
                                                               ["in-toto", "slsa", "sigstore", "cosign", "oms"]))

        # Load ML-BOM requirements
        self.require_ml_bom = policy_config.get("require_ml_bom", False)
        self.ml_bom_completeness_level = policy_config.get("ml_bom_completeness_level", "basic")  # basic, detailed, comprehensive

        # DEPRECATED: Pattern-based trusted families (replaced by cryptographic verification)
        # Load trusted model families (legacy - use trusted_signers for cryptographic verification)
        default_trusted_families = {
            "llama", "mistral", "gpt", "bert", "claude",
            "t5", "bloom", "opt", "falcon", "mpt",
        }
        self.trusted_model_families = set(policy_config.get("trusted_model_families", default_trusted_families))

        # Fallback behavior when signatures not available
        self.fallback_to_pattern_matching = policy_config.get("fallback_to_pattern_matching", True)

        # Load digest algorithm requirements
        self.required_digest_algorithms = policy_config.get("required_digest_algorithms", ["sha256"])
        self.minimum_digest_strength = policy_config.get("minimum_digest_strength", "sha256")  # md5, sha1, sha256, sha512

        # Load provenance timeline validation
        self.max_provenance_age_days = policy_config.get("max_provenance_age_days", 90)  # 3 months default

        # Load source validation settings
        self.validate_source_integrity = policy_config.get("validate_source_integrity", True)

        # Load suspicious pattern detection settings
        self.detect_suspicious_patterns = policy_config.get("detect_suspicious_patterns", True)

        # ENHANCED: Load Sigstore model transparency settings
        self.require_model_transparency = policy_config.get("require_model_transparency", False)
        self.model_transparency_strictness = policy_config.get("model_transparency_strictness", "medium")  # low, medium, high

        # Trusted signing identities for model transparency (replaces pattern-based trusted families)
        default_trusted_signers = {
            # Meta/Facebook official signers
            "meta-llama@fb.com": {"families": ["llama"], "publisher": "Meta"},
            "llama-release@meta.com": {"families": ["llama"], "publisher": "Meta"},

            # OpenAI signers
            "models@openai.com": {"families": ["gpt"], "publisher": "OpenAI"},

            # Mistral AI signers
            "release@mistral.ai": {"families": ["mistral", "mixtral"], "publisher": "Mistral AI"},

            # Google signers
            "models@google.com": {"families": ["bert", "t5"], "publisher": "Google"},

            # Anthropic signers
            "models@anthropic.com": {"families": ["claude"], "publisher": "Anthropic"},
        }
        self.trusted_signers = policy_config.get("trusted_signers", default_trusted_signers)

        # Model transparency verification options
        self.verify_rekor_inclusion = policy_config.get("verify_rekor_inclusion", True)
        self.require_oidc_verification = policy_config.get("require_oidc_verification", True)
        self.trusted_oidc_issuers = set(policy_config.get("trusted_oidc_issuers", [
            "https://accounts.google.com",
            "https://token.actions.githubusercontent.com",
            "https://github.com/login/oauth",
        ]))

        # ENHANCED: SLSA for Models configuration
        self.require_slsa_ml_provenance = policy_config.get("require_slsa_ml_provenance", False)
        self.slsa_ml_strictness = policy_config.get("slsa_ml_strictness", "medium")  # low, medium, high
        self.trusted_ml_builders = set(policy_config.get("trusted_ml_builders", [
            "https://github.com/actions/runner",
            "https://cloud.google.com/build",
            "https://model-training.dev/ml-pipeline",
            "https://kubernetes.io/job",
        ]))

        # SLSA ML training validation settings
        self.require_training_metadata = policy_config.get("require_training_metadata", True)
        self.min_training_duration_seconds = policy_config.get("min_training_duration_seconds", 300)  # 5 minutes
        self.require_reproducibility_info = policy_config.get("require_reproducibility_info", True)

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator can analyze all model types for provenance."""
        return True  # Provenance validation applies to all model types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate provenance information (limited for single files)."""
        warnings = []

        # For individual files, we can only do basic provenance checks
        # Full provenance validation requires directory-level analysis
        return warnings

    def validate_model_provenance(self, model_directory: str) -> List[Dict[str, Any]]:
        """CRITICAL: Validate model provenance and generate ML-BOM
        Main entry point for provenance security validation.
        """
        warnings = []
        model_dir = Path(model_directory)

        try:
            # Discover provenance documents
            provenance_docs = self._discover_provenance_documents(model_dir)
            
            # Store discovered document counts for accurate reporting
            self._discovered_signature_files = len([d for d in provenance_docs if d.get("type") == "signature"])
            self._discovered_attestation_files = len([d for d in provenance_docs if d.get("type") == "attestation"])
            self._discovered_provenance_docs = len(provenance_docs)

            # Generate comprehensive ML-BOM
            ml_bom = self._generate_ml_bom(model_dir)

            # ENHANCED: Sigstore model transparency verification (replaces pattern-based trust)
            if self.require_model_transparency or any(doc.get("path", "").endswith((".sig", ".bundle")) for doc in provenance_docs):
                transparency_warnings = self._verify_sigstore_model_transparency(model_dir, provenance_docs)
                warnings.extend(transparency_warnings)

            # ENHANCED: SLSA for Models provenance verification
            slsa_warnings = self._verify_slsa_ml_provenance(model_dir, provenance_docs)
            warnings.extend(slsa_warnings)
            
            # Propagate cryptographic verifications from signature_validators
            if hasattr(self, 'signature_validators'):
                sig_crypto = getattr(self.signature_validators, '_cryptographic_verifications', [])
                if sig_crypto:
                    if not hasattr(self, '_cryptographic_verifications'):
                        self._cryptographic_verifications = []
                    self._cryptographic_verifications.extend(sig_crypto)

            # ENHANCED: OpenSSF Model Signing (OMS) verification
            if self.require_attestations and "oms" in self.accepted_attestation_types:
                oms_warnings = self._verify_oms_manifests(model_dir, provenance_docs)
                warnings.extend(oms_warnings)

            # FIXED: CoSAI maturity level detection AFTER verification (not before!)
            # This ensures cryptographic verification results are included in the assessment
            cosai_maturity_level = self.cosai_detector.detect_maturity_level(
                model_dir, 
                provenance_docs,
                cryptographic_verifications=getattr(self, '_cryptographic_verifications', [])
            )
            cosai_analysis = self.cosai_detector.get_maturity_analysis(model_dir, provenance_docs)
            
            logger.info(f"CoSAI Maturity Level: {cosai_maturity_level.value if cosai_maturity_level else 'None'}")
            
            # Store CoSAI context for policy integration (pass pre-computed values to avoid redundant detection)
            self._cosai_context = self.cosai_detector.create_maturity_context(
                model_dir, provenance_docs, 
                detected_level=cosai_maturity_level, 
                analysis=cosai_analysis
            )

            # ENHANCED: CoSAI maturity-level specific validation
            cosai_warnings = self._validate_cosai_requirements(cosai_maturity_level, model_dir, provenance_docs)
            warnings.extend(cosai_warnings)

            # Traditional signature/attestation validation (fallback)
            signature_warnings = self._validate_signatures_attestations(model_dir, provenance_docs)
            warnings.extend(signature_warnings)

            # Validate model family and lineage
            lineage_warnings = self._validate_model_lineage(model_dir, ml_bom)
            warnings.extend(lineage_warnings)

            # Verify commit and version information
            version_warnings = self._validate_version_information(model_dir, provenance_docs)
            warnings.extend(version_warnings)

            # Validate quantization provenance
            quantization_warnings = self._validate_quantization_provenance(model_dir, ml_bom)
            warnings.extend(quantization_warnings)

            # Verify file digests and integrity
            digest_warnings = self._validate_file_digests(model_dir, ml_bom)
            warnings.extend(digest_warnings)

            # Note: Behavioral backdoor detection is now handled by specialized validators:
            # - BackdoorDetectionValidator for weight-based backdoor detection
            # - BehaviorAnalysisValidator for inference-based behavioral analysis

            # Check for suspicious provenance patterns
            suspicious_warnings = self._check_suspicious_provenance_patterns(provenance_docs, ml_bom)
            warnings.extend(suspicious_warnings)

            # Save ML-BOM for future reference
            self._save_ml_bom(model_dir, ml_bom)

            if not warnings:
                logger.info("✅ Model provenance validated successfully")

        except Exception as e:
            logger.error(f"Error in provenance validation: {str(e)}")
            warnings.append({
                "type": "provenance_validation_error",
                "details": {
                    "message": "Error validating model provenance",
                    "error": str(e),
                    "recommendation": "Manual provenance verification recommended",
                },
                "severity": "medium",
            })

        # Add provenance-specific context for policy evaluation
        context = {
            "provenance": {
                "signer": "unknown",  # Would be extracted from actual signature verification
                "attestation_verified": not any("attestation" in str(w).lower() and "missing" in str(w).lower() for w in warnings),
                "supply_chain_verified": not any("supply_chain" in str(w).lower() for w in warnings),
            },
            "artifact": {
                "signed": not any("signature" in str(w).lower() and ("missing" in str(w).lower() or "invalid" in str(w).lower()) for w in warnings),
                "format": "unknown",  # Would be determined based on model format
            },
        }

        # Apply policy evaluation if policy engine is available
        if self.policy_engine:
            # Enhance context with CoSAI maturity information
            enhanced_context = {**context, **self._cosai_context}
            return self.apply_policy(warnings, model_directory, enhanced_context)

        return warnings

    def _discover_provenance_documents(self, model_dir: Path) -> List[Dict[str, Any]]:
        """Discover and parse provenance-related documents.
        
        Provenance = WHO built it, WHERE it came from, WHEN it was built
        (Not technical metadata about HOW it works)
        """
        provenance_docs = []

        # STRICT provenance file patterns (origin/history, not technical config)
        provenance_patterns = [
            # === CRYPTOGRAPHIC PROVENANCE (CoSAI/SLSA Level 1-3) ===
            # Sigstore model transparency signatures (PRIORITY: bundles before raw sigs)
            "*.bundle", "model.bundle", "*_model.bundle",  # Sigstore bundles (preferred)
            "*.sig", "model.sig", "*_model.sig", "*_sharded.sig",  # Raw signatures

            # Traditional signatures and attestations
            "*.signature", "*.asc", "*.p7s",
            "attestation*.json", "provenance*.json",
            "slsa*.json", "in-toto*.json",

            # OpenSSF Model Signing (OMS) manifests
            "*.oms.json", "oms-manifest.json", "model-manifest.oms",
            "*-oms.json", "oms_*.json",

            # === HUMAN-READABLE PROVENANCE ===
            # Model cards and documentation
            "README.md", "MODEL_CARD.md", "CITATION.cff",
            "PROVENANCE.md", "LINEAGE.json", "ATTRIBUTION.txt",
            
            # Training provenance
            "training_args.json",  # WHO trained it, WHEN, with WHAT parameters
            
            # === VERSION CONTROL PROVENANCE ===
            # Git/Version control (origin tracking)
            ".git/HEAD", ".git/refs/**", ".git/logs/**",
            ".gitattributes",

            # === BUILD/REGISTRY PROVENANCE ===
            # OCI/Container registry provenance (if from container registry)
            "oci-manifest.json", "registry-config.json",
        ]
        
        # Explicitly EXCLUDED (these are technical metadata, not provenance):
        excluded_files = {
            "config.json",              # Model architecture config (HOW it works)
            "generation_config.json",   # Generation parameters (HOW it generates)
            "model.safetensors.index.json",  # Technical file index
            "pytorch_model.bin.index.json",  # Technical file index
            "tokenizer_config.json",    # Tokenizer technical config
            "special_tokens_map.json",  # Tokenizer technical config
            "optimizer.pt",             # Technical training state
            "scheduler.pt",             # Technical training state
            "preprocessor_config.json", # Technical preprocessing config
            "ML-BOM.json",              # Self-referential
            "ml-bom.json",              # Self-referential
        }

        for pattern in provenance_patterns:
            try:
                found_files = list(model_dir.rglob(pattern))
                for file_path in found_files:
                    # Skip excluded technical metadata files
                    if file_path.name in excluded_files:
                        logger.debug(f"Skipping technical metadata (not provenance): {file_path.name}")
                        continue
                    
                    # Skip empty signature files (invalid/incomplete)
                    if file_path.is_file() and file_path.stat().st_size == 0:
                        logger.warning(f"Skipping empty signature file: {file_path.name}")
                        continue
                        
                    if file_path.is_file():
                        doc_info = self._parse_provenance_document(file_path)
                        if doc_info:
                            provenance_docs.append(doc_info)
            except Exception as e:
                logger.debug(f"Error searching for pattern {pattern}: {str(e)}")

        return provenance_docs

    def _parse_provenance_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse individual provenance document and classify its type."""
        try:
            # Classify document type based on content and filename
            doc_type = self._classify_provenance_type(file_path)
            
            # Sigstore bundle files are JSON (not binary)
            if file_path.suffix == ".bundle":
                with open(file_path, encoding="utf-8") as f:
                    content = json.load(f)
                return {
                    "type": "signature",  # Bundles are signature documents
                    "path": str(file_path),
                    "content": content,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }
            elif file_path.suffix in [".json", ".jsonl"]:
                with open(file_path, encoding="utf-8") as f:
                    content = json.load(f)
                return {
                    "type": doc_type,
                    "path": str(file_path),
                    "content": content,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }
            elif file_path.suffix in [".md", ".txt", ".asc", ".cff"]:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return {
                    "type": doc_type,
                    "path": str(file_path),
                    "content": content[:5000],  # Limit size
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }
            elif file_path.suffix in [".sig", ".signature", ".p7s"]:
                with open(file_path, "rb") as f:
                    content = f.read()
                return {
                    "type": "signature",
                    "path": str(file_path),
                    "content": base64.b64encode(content).decode("ascii"),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {str(e)}")

        return None
    
    def _classify_provenance_type(self, file_path: Path) -> str:
        """Classify provenance document type based on filename and extension."""
        filename = file_path.name.lower()
        
        # Attestations (SLSA, in-toto, OMS) - check BEFORE signatures
        # because .att.bundle files should be classified as attestations, not signatures
        if any(x in filename for x in [".att.", "attestation", "slsa", "in-toto", "oms"]):
            return "attestation"
        
        # Cryptographic signatures (including Sigstore bundles)
        if file_path.suffix in [".sig", ".signature", ".p7s", ".bundle"]:
            return "signature"
        
        # Model cards and documentation
        if "model_card" in filename or "readme" in filename:
            return "model_card"
        
        # Training provenance
        if "training_args" in filename:
            return "training_provenance"
        
        # Lineage/genealogy
        if any(x in filename for x in ["lineage", "provenance", "attribution"]):
            return "lineage"
        
        # Git/version control
        if ".git" in str(file_path):
            return "version_control"
        
        # Citation
        if "citation" in filename:
            return "citation"
        
        # Generic provenance document
        return "provenance_document"

    def _generate_ml_bom(self, model_dir: Path) -> Dict[str, Any]:
        """Generate comprehensive ML-BOM (Machine Learning Bill of Materials)."""
        # Discover all model files
        model_files = self._discover_model_files(model_dir)

        # Identify model family and architecture
        model_family_info = self._identify_model_family(model_dir, model_files)

        # Analyze quantization and compression
        quantization_info = self._analyze_quantization(model_files)

        # Detect adapters and fine-tuning
        adapter_info = self._analyze_adapters(model_dir)

        # Calculate file digests
        file_digests = self._calculate_file_digests(model_files)

        # Gather version and commit information
        version_info = self._gather_version_information(model_dir)

        # Create comprehensive ML-BOM
        ml_bom = {
            "bomFormat": "ML-BOM",
            "specVersion": "1.0",
            "serialNumber": f"urn:uuid:{self._generate_uuid()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools": [{
                    "vendor": "Highflame",
                    "name": "Palisade",
                    "version": "1.0.0",
                }],
                "component": {
                    "type": "ml-model",
                    "bom-ref": f"{model_family_info['family']}-{model_family_info['name']}",
                    "name": model_family_info["name"],
                    "version": version_info.get("version", "unknown"),
                },
            },
            "components": self._create_bom_components(model_files, file_digests, quantization_info, adapter_info),
            "modelCard": {
                "modelDetails": model_family_info,
                "quantization": quantization_info,
                "adapters": adapter_info,
                "provenance": version_info,
            },
            "fileManifest": file_digests,
            "dependencies": self._identify_dependencies(model_dir),
            "vulnerabilities": [],  # Will be populated by other validators
            "compositions": [{
                "aggregate": "complete",
                "assemblies": [comp["bom-ref"] for comp in self._create_bom_components(model_files, file_digests, quantization_info, adapter_info)],
            }],
        }

        return ml_bom

    def _discover_model_files(self, model_dir: Path) -> List[Path]:
        """Discover all model-related files."""
        model_extensions = [
            ".safetensors", ".bin", ".pt", ".pth", ".h5",
            ".onnx", ".gguf", ".ggml", ".tflite",
            ".json", ".txt", ".vocab", ".model",
        ]

        model_files = []
        for ext in model_extensions:
            model_files.extend(list(model_dir.rglob(f"*{ext}")))

        # Filter out hidden, temporary, and self-referential files
        excluded_files = {
            "ML-BOM.json",  # Self-referential - BOM should not list itself
            "ml-bom.json",  # Alternative naming
            ".DS_Store",    # macOS metadata
            "Thumbs.db",    # Windows metadata
        }
        
        model_files = [
            f for f in model_files 
            if not f.name.startswith(".") 
            and f.is_file() 
            and f.name not in excluded_files
        ]

        return model_files

    def _identify_model_family(self, model_dir: Path, model_files: List[Path]) -> Dict[str, Any]:
        """Identify model family and architecture."""
        family_info = {
            "family": "unknown",
            "name": model_dir.name,
            "architecture": "unknown",
            "official_source": False,
            "confidence": 0.0,
        }

        # Check directory name and file names for family patterns
        search_text = f"{model_dir.name} {' '.join([f.name for f in model_files[:10]])}"
        search_text = search_text.lower()

        best_score = 0

        for family_name, family_data in self.model_families.items():
            score = 0
            matches = []

            # Check pattern matches
            for pattern in family_data["patterns"]:
                if pattern in search_text:
                    score += len(pattern) * 2  # Longer matches score higher
                    matches.append(pattern)

            # Bonus for official source indicators
            for source in family_data["official_sources"]:
                if source in search_text:
                    score += 10
                    family_info["official_source"] = True

            if score > best_score:
                best_score = score
                family_info["family"] = family_name
                family_info["architecture"] = family_data["architecture"]
                family_info["matched_patterns"] = matches

        family_info["confidence"] = min(best_score / 10.0, 1.0)  # Normalize to 0-1

        # Additional metadata from config files
        config_info = self._extract_config_metadata(model_dir)
        family_info.update(config_info)

        return family_info

    def _extract_config_metadata(self, model_dir: Path) -> Dict[str, Any]:
        """Extract metadata from configuration files."""
        metadata = {}

        config_files = ["config.json", "model_config.json", "generation_config.json"]

        for config_name in config_files:
            config_path = model_dir / config_name
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config_data = json.load(f)

                    # Extract relevant metadata
                    if "architectures" in config_data:
                        metadata["architectures"] = config_data["architectures"]
                    if "model_type" in config_data:
                        metadata["model_type"] = config_data["model_type"]
                    if "_name_or_path" in config_data:
                        metadata["base_model"] = config_data["_name_or_path"]
                    if "transformers_version" in config_data:
                        metadata["framework_version"] = config_data["transformers_version"]

                except Exception as e:
                    logger.debug(f"Error reading {config_name}: {str(e)}")

        return metadata

    def _analyze_quantization(self, model_files: List[Path]) -> Dict[str, Any]:
        """Analyze quantization methods and compression used.
        
        NOTE: This method provides basic quantization analysis for ML-BOM generation.
        For security-focused adapter analysis, use LoRAAdapterSecurityValidator.
        """
        quantization_info = {
            "methods": [],
            "files": {},
            "compression_ratio": 1.0,
            "bits_per_parameter": 32,
        }

        for file_path in model_files:
            file_info = {}

            # Analyze by file extension and naming
            if ".gguf" in file_path.name or ".ggml" in file_path.name:
                # Extract quantization from GGUF filename
                quant_match = re.search(r"(q[0-9]_[0-9k]+|f16|f32|int8)", file_path.name.lower())
                if quant_match:
                    quant_type = quant_match.group(1)
                    file_info["quantization"] = quant_type
                    if quant_type in self.quantization_provenance:
                        file_info.update(self.quantization_provenance[quant_type])

            elif file_path.suffix in [".safetensors", ".bin", ".pt"]:
                # For safetensors/pytorch files, assume fp16 if small, fp32 if large
                try:
                    file_size = file_path.stat().st_size
                    # Rough heuristic: if significantly smaller than expected, likely quantized
                    if file_size < 1e9:  # < 1GB
                        file_info["quantization"] = "float16"
                        file_info.update(self.quantization_provenance.get("float16", {}))
                    else:
                        file_info["quantization"] = "float32"
                        file_info.update(self.quantization_provenance.get("float32", {}))
                except OSError:
                    pass

            if file_info:
                quantization_info["files"][str(file_path)] = file_info
                if file_info.get("method") not in quantization_info["methods"]:
                    quantization_info["methods"].append(file_info.get("method"))

        # Calculate overall compression ratio
        if quantization_info["files"]:
            ratios = [info.get("compression_ratio", 1.0) for info in quantization_info["files"].values()]
            quantization_info["compression_ratio"] = sum(ratios) / len(ratios)

            bits = [info.get("bits", 32) for info in quantization_info["files"].values()]
            quantization_info["bits_per_parameter"] = sum(bits) / len(bits)

        return quantization_info

    def _analyze_adapters(self, model_dir: Path) -> Dict[str, Any]:
        """Analyze LoRA adapters and fine-tuning applied.
        
        NOTE: This method provides basic adapter information for ML-BOM generation.
        For security-focused adapter validation, use LoRAAdapterSecurityValidator.
        """
        adapter_info = {
            "adapters": [],
            "fine_tuned": False,
            "base_model": None,
            "adapter_files": [],
        }

        # Look for adapter files
        adapter_patterns = ["*adapter*.safetensors", "*adapter*.bin", "*lora*.safetensors",
                          "*adapter*.json", "*peft*.json"]

        for pattern in adapter_patterns:
            adapter_files = list(model_dir.glob(pattern))
            for adapter_file in adapter_files:
                adapter_info["adapter_files"].append(str(adapter_file))

        # Check adapter configuration
        adapter_configs = ["adapter_config.json", "peft_config.json", "lora_config.json"]
        for config_name in adapter_configs:
            config_path = model_dir / config_name
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config_data = json.load(f)

                    adapter_info["adapters"].append({
                        "type": config_data.get("peft_type", "unknown"),
                        "config_file": config_name,
                        "base_model": config_data.get("base_model_name_or_path"),
                        "target_modules": config_data.get("target_modules", []),
                        "rank": config_data.get("r"),
                        "alpha": config_data.get("lora_alpha"),
                    })

                    if config_data.get("base_model_name_or_path"):
                        adapter_info["base_model"] = config_data["base_model_name_or_path"]
                        adapter_info["fine_tuned"] = True

                except Exception as e:
                    logger.debug(f"Error reading adapter config {config_name}: {str(e)}")

        return adapter_info

    def _calculate_file_digests(self, model_files: List[Path]) -> Dict[str, Dict[str, str]]:
        """Calculate comprehensive file digests for integrity verification."""
        file_digests = {}

        for file_path in model_files:
            try:
                digests = {}

                with open(file_path, "rb") as f:
                    # Calculate multiple digest algorithms
                    hashers = {alg: hashlib.new(alg) for alg in self.digest_algorithms}

                    # Read file in chunks to handle large files
                    chunk_size = 8192 * 16  # 128KB chunks
                    while chunk := f.read(chunk_size):
                        for hasher in hashers.values():
                            hasher.update(chunk)

                # Store all digest types
                for alg, hasher in hashers.items():
                    digests[alg] = hasher.hexdigest()

                # Add file metadata
                stat = file_path.stat()
                digests["size"] = stat.st_size
                digests["modified"] = stat.st_mtime

                file_digests[str(file_path)] = digests

            except Exception as e:
                logger.debug(f"Error calculating digests for {file_path}: {str(e)}")
                file_digests[str(file_path)] = {"error": str(e)}

        return file_digests

    def _gather_version_information(self, model_dir: Path) -> Dict[str, Any]:
        """Gather version control and build information."""
        version_info = {
            "git_info": {},
            "build_info": {},
            "version": None,
            "commit_hash": None,
            "branch": None,
            "remote_url": None,
        }

        # Check for Git information
        git_dir = model_dir / ".git"
        if git_dir.exists():
            version_info["git_info"] = self._extract_git_info(git_dir)

        # Check for version files
        version_files = ["VERSION", "version.txt", "VERSION.txt"]
        for version_file in version_files:
            version_path = model_dir / version_file
            if version_path.exists():
                try:
                    with open(version_path) as f:
                        version_info["version"] = f.read().strip()
                        break
                except Exception:
                    pass

        # Check for build information
        build_files = ["build_info.json", "training_args.json", "run_info.json"]
        for build_file in build_files:
            build_path = model_dir / build_file
            if build_path.exists():
                try:
                    with open(build_path) as f:
                        build_data = json.load(f)
                        version_info["build_info"].update(build_data)
                except Exception as e:
                    logger.debug(f"Error reading build info from {build_path}: {e}")

        return version_info

    def _extract_git_info(self, git_dir: Path) -> Dict[str, Any]:
        """Extract Git repository information."""
        git_info = {}

        try:
            # Read HEAD ref
            head_file = git_dir / "HEAD"
            if head_file.exists():
                with open(head_file) as f:
                    head_content = f.read().strip()
                    if head_content.startswith("ref: "):
                        ref_path = head_content[5:]  # Remove 'ref: '
                        git_info["ref"] = ref_path

                        # Try to read the actual commit hash
                        ref_file = git_dir / ref_path
                        if ref_file.exists():
                            with open(ref_file) as rf:
                                git_info["commit_hash"] = rf.read().strip()
                    else:
                        # Detached HEAD
                        git_info["commit_hash"] = head_content

            # Read remote information
            config_file = git_dir / "config"
            if config_file.exists():
                with open(config_file) as f:
                    config_content = f.read()
                    # Simple regex to find remote URL
                    url_match = re.search(r"url = (.+)", config_content)
                    if url_match:
                        git_info["remote_url"] = url_match.group(1).strip()

        except Exception as e:
            logger.debug(f"Error extracting git info: {str(e)}")

        return git_info

    def _create_bom_components(self, model_files: List[Path], file_digests: Dict[str, Dict[str, str]],
                              quantization_info: Dict[str, Any], adapter_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create BOM components for all model artifacts."""
        components = []

        # Main model components
        for file_path in model_files:
            file_str = str(file_path)
            digest_info = file_digests.get(file_str, {})

            component = {
                "type": self._classify_file_type(file_path),
                "bom-ref": f"file-{hashlib.sha256(file_str.encode()).hexdigest()[:16]}",
                "name": file_path.name,
                "version": "1.0",
                "hashes": [
                    {"alg": alg, "content": digest}
                    for alg, digest in digest_info.items()
                    if alg in self.digest_algorithms
                ],
                "properties": [
                    {"name": "file.path", "value": file_str},
                    {"name": "file.size", "value": str(digest_info.get("size", 0))},
                ],
            }

            # Add quantization info if available
            quant_info = quantization_info["files"].get(file_str, {})
            if quant_info:
                component["properties"].extend([
                    {"name": "ml.quantization.method", "value": quant_info.get("method", "unknown")},
                    {"name": "ml.quantization.bits", "value": str(quant_info.get("bits", 32))},
                ])

            components.append(component)

        # Adapter components
        for adapter in adapter_info.get("adapters", []):
            adapter_component = {
                "type": "ml-adapter",
                "bom-ref": f"adapter-{hashlib.sha256(str(adapter).encode()).hexdigest()[:16]}",
                "name": f"{adapter.get('type', 'unknown')}-adapter",
                "version": "1.0",
                "properties": [
                    {"name": "ml.adapter.type", "value": adapter.get("type", "unknown")},
                    {"name": "ml.adapter.base_model", "value": adapter.get("base_model", "unknown")},
                    {"name": "ml.adapter.rank", "value": str(adapter.get("rank", 0))},
                ],
            }
            components.append(adapter_component)

        return components

    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type for BOM component."""
        extension = file_path.suffix.lower()
        name = file_path.name.lower()

        if extension in [".safetensors", ".bin", ".pt", ".pth"]:
            if "adapter" in name or "lora" in name:
                return "ml-adapter"
            else:
                return "ml-model"
        elif extension in [".onnx"]:
            return "ml-model-onnx"
        elif extension in [".gguf", ".ggml"]:
            return "ml-model-gguf"
        elif extension in [".json"]:
            if "config" in name:
                return "ml-config"
            elif "tokenizer" in name:
                return "ml-tokenizer"
            else:
                return "ml-metadata"
        elif extension in [".txt", ".model"]:
            if "tokenizer" in name or "vocab" in name:
                return "ml-tokenizer"
            else:
                return "ml-data"
        else:
            return "ml-artifact"

    def _identify_dependencies(self, model_dir: Path) -> List[Dict[str, Any]]:
        """Identify external dependencies and frameworks."""
        dependencies = []

        # Check for requirements files
        req_files = ["requirements.txt", "environment.yml", "Pipfile", "pyproject.toml"]
        for req_file in req_files:
            req_path = model_dir / req_file
            if req_path.exists():
                try:
                    with open(req_path) as f:
                        content = f.read()

                    dependencies.append({
                        "ref": f"deps-{req_file}",
                        "dependsOn": [],  # Would need parsing for actual deps
                        "scope": "runtime",
                        "source": req_file,
                        "content": content[:1000],  # Truncate
                    })
                except Exception as e:
                    logger.debug(f"Error reading dependency file {req_file}: {e}")

        return dependencies

    def _generate_uuid(self) -> str:
        """Generate a simple UUID for BOM serial number."""
        import uuid
        return str(uuid.uuid4())

    def _validate_signatures_attestations(self, model_dir: Path,
                                        provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate signatures and attestation documents."""
        warnings = []

        signature_files = [doc for doc in provenance_docs if doc["type"] == "signature"]
        attestation_files = [doc for doc in provenance_docs if doc["type"] == "json" and
                           any(key in str(doc["path"]).lower() for key in ["attestation", "provenance", "slsa"])]

        if not signature_files and not attestation_files:
            warnings.append({
                "type": "missing_provenance_documents",
                "details": {
                    "message": "No signature or attestation documents found",
                    "recommendation": "Model lacks provenance verification - consider untrusted",
                },
                "severity": "high",
            })
            return warnings

        # Validate attestation documents
        for attestation in attestation_files:
            attestation_warnings = self._validate_attestation_document(attestation)
            warnings.extend(attestation_warnings)

        # Validate signature files
        for signature in signature_files:
            signature_warnings = self._validate_signature_file(signature)
            warnings.extend(signature_warnings)

        return warnings

    def _validate_attestation_document(self, attestation_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate individual attestation document."""
        warnings = []

        try:
            content = attestation_doc["content"]

            # Detect attestation type
            attestation_type = None
            if "_type" in content and content["_type"] == "https://in-toto.io/Statement/v0.1":
                attestation_type = "in-toto"
            elif "buildDefinition" in content:
                attestation_type = "slsa"
            elif "critical" in content and "optional" in content:
                attestation_type = "cosign"

            if not attestation_type:
                warnings.append({
                    "type": "unknown_attestation_format",
                    "details": {
                        "message": "Unknown or invalid attestation format",
                        "file": attestation_doc["path"],
                        "recommendation": "Verify attestation document format",
                    },
                    "severity": "medium",
                })
                return warnings

            # Validate required fields
            required_fields = self.attestation_types.get(attestation_type, {}).get("required_fields", [])
            missing_fields = [field for field in required_fields if field not in content]

            if missing_fields:
                warnings.append({
                    "type": "incomplete_attestation",
                    "details": {
                        "message": "Attestation missing required fields",
                        "attestation_type": attestation_type,
                        "missing_fields": missing_fields,
                        "file": attestation_doc["path"],
                        "recommendation": "Complete attestation document required",
                    },
                    "severity": "high",
                })

        except Exception as e:
            warnings.append({
                "type": "attestation_parse_error",
                "details": {
                    "message": "Error parsing attestation document",
                    "file": attestation_doc["path"],
                    "error": str(e),
                    "recommendation": "Verify attestation document integrity",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_signature_file(self, signature_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate signature file format and structure."""
        warnings = []

        try:
            signature_path = signature_doc["path"]
            signature_content = signature_doc["content"]
            
            # Sigstore bundles are JSON, not base64-encoded binary
            if signature_path.endswith(".bundle"):
                # Bundle files are already parsed as JSON - validate structure
                if not isinstance(signature_content, dict):
                    warnings.append({
                        "type": "invalid_bundle_format",
                        "details": {
                            "message": "Sigstore bundle must be a JSON object",
                            "file": signature_path,
                            "recommendation": "Verify bundle file integrity",
                        },
                        "severity": "medium",
                    })
                # Bundle validation is handled by signature_validators module
                return warnings

            # For raw signature files (.sig, .signature, etc), validate base64 encoding
            try:
                signature_bytes = base64.b64decode(signature_content)
                if len(signature_bytes) < 64:  # Minimum reasonable signature size
                    warnings.append({
                        "type": "suspicious_signature_size",
                        "details": {
                            "message": "Signature appears too small to be valid",
                            "file": signature_path,
                            "size": len(signature_bytes),
                            "recommendation": "Verify signature integrity",
                        },
                        "severity": "medium",
                    })
            except Exception:
                warnings.append({
                    "type": "invalid_signature_encoding",
                    "details": {
                        "message": "Signature is not valid base64",
                        "file": signature_path,
                        "recommendation": "Verify signature format",
                    },
                    "severity": "medium",
                })

        except Exception as e:
            warnings.append({
                "type": "signature_validation_error",
                "details": {
                    "message": "Error validating signature file",
                    "file": signature_doc["path"],
                    "error": str(e),
                    "recommendation": "Manual signature verification needed",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_model_lineage(self, model_dir: Path, ml_bom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ENHANCED: Validate model family lineage and authenticity.

        Priority order:
        1. Cryptographic verification (Sigstore model transparency)
        2. Pattern-based identification (fallback)
        """
        warnings = []

        # PRIORITY: Check for cryptographic verification results
        if hasattr(self, "_cryptographic_verifications") and self._cryptographic_verifications:
            # We have cryptographic proof of authenticity - use that instead of patterns
            verification = self._cryptographic_verifications[-1]  # Most recent

            logger.info("✅ Using cryptographic verification instead of pattern matching")
            logger.info(f"   Signer: {verification.get('signer', verification.get('signer_identity', 'unknown'))}")
            logger.info(f"   Bundle version: {verification.get('bundle_version', 'unknown')}")
            if 'verified_families' in verification:
                logger.info(f"   Verified families: {verification['verified_families']}")
            if 'trust_level' in verification:
                logger.info(f"   Trust level: {verification['trust_level']}")

            # No warnings needed - cryptographic verification provides definitive proof
            return warnings

        # FALLBACK: Pattern-based identification (legacy approach)
        logger.info("No cryptographic verification available, using pattern matching")

        model_card = ml_bom.get("modelCard", {})
        model_details = model_card.get("modelDetails", {})

        family = model_details.get("family", "unknown")
        confidence = model_details.get("confidence", 0.0)
        official_source = model_details.get("official_source", False)

        # Check if model family is recognized
        if family == "unknown":
            severity = "high" if not self.fallback_to_pattern_matching else "medium"
            warnings.append({
                "type": "unknown_model_family",
                "details": {
                    "message": "Could not identify model family (no cryptographic verification)",
                    "recommendation": "Obtain cryptographically signed model from trusted publisher",
                    "trust_level": "pattern_matching_fallback",
                },
                "severity": severity,
            })
        elif confidence < 0.5:
            warnings.append({
                "type": "uncertain_model_family",
                "details": {
                    "message": f"Low confidence in model family identification: {family} (pattern-based)",
                    "confidence": confidence,
                    "recommendation": "Obtain cryptographically signed model for definitive verification",
                    "trust_level": "pattern_matching_fallback",
                },
                "severity": "medium",
            })

        # Check for official source indicators (pattern-based - can be spoofed)
        if not official_source and family in self.model_families:
            warnings.append({
                "type": "unofficial_model_source",
                "details": {
                    "message": f"Model appears to be {family} but not from official source (pattern-based detection)",
                    "family": family,
                    "official_sources": self.model_families[family]["official_sources"],
                    "recommendation": "Obtain cryptographically signed model from official publisher",
                    "trust_level": "pattern_matching_fallback",
                    "security_note": "Pattern-based detection can be spoofed - use signed models for security",
                },
                "severity": "high",  # Higher severity since patterns can be spoofed
            })

        # Add warning about pattern-matching limitations
        if warnings and not self.require_model_transparency:
            warnings.append({
                "type": "pattern_matching_limitations",
                "details": {
                    "message": "Using pattern-based model identification - can be spoofed by attackers",
                    "recommendation": "Enable require_model_transparency in policy for cryptographic verification",
                    "security_impact": "Malicious models can mimic trusted family patterns",
                    "trust_level": "low_security",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_version_information(self, model_dir: Path,
                                    provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate version control and commit information."""
        warnings = []

        # Look for suspicious commit patterns in git information
        for doc in provenance_docs:
            if doc["type"] == "text" and "git" in doc["path"].lower():
                self._check_suspicious_git_info(doc, warnings)

        return warnings

    def _check_suspicious_git_info(self, git_doc: Dict[str, Any], warnings: List[Dict[str, Any]]) -> None:
        """Check for suspicious patterns in git information."""
        content = git_doc["content"].lower()

        # Check for suspicious commit messages
        for suspicious_msg in self.suspicious_provenance_patterns["suspicious_commits"]["commit_messages"]:
            if suspicious_msg in content:
                warnings.append({
                    "type": "suspicious_commit_message",
                    "details": {
                        "message": "Suspicious pattern found in git information",
                        "pattern": suspicious_msg,
                        "file": git_doc["path"],
                        "recommendation": "Review commit history for malicious changes",
                    },
                    "severity": "high",
                })

    def _validate_quantization_provenance(self, model_dir: Path, ml_bom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate quantization methods and provenance."""
        warnings = []

        quantization_info = ml_bom.get("modelCard", {}).get("quantization", {})
        methods = quantization_info.get("methods", [])

        # Check for unusual quantization combinations
        if len(methods) > 3:
            warnings.append({
                "type": "multiple_quantization_methods",
                "details": {
                    "message": "Multiple quantization methods detected",
                    "methods": methods,
                    "recommendation": "Verify quantization workflow is legitimate",
                },
                "severity": "low",
            })

        # Check for suspicious quantization patterns
        if "unknown" in methods:
            warnings.append({
                "type": "unknown_quantization_method",
                "details": {
                    "message": "Unknown quantization method detected",
                    "recommendation": "Verify quantization process and tools used",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_file_digests(self, model_dir: Path, ml_bom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate file integrity through digest verification."""
        warnings = []

        file_manifest = ml_bom.get("fileManifest", {})

        # Check for files without digests
        missing_digests = []
        for file_path, digest_info in file_manifest.items():
            if "error" in digest_info:
                missing_digests.append(file_path)
            elif not any(alg in digest_info for alg in ["sha256", "sha512"]):
                missing_digests.append(file_path)

        if missing_digests:
            warnings.append({
                "type": "missing_file_digests",
                "details": {
                    "message": "Some files lack integrity digests",
                    "files": missing_digests[:10],  # Limit output
                    "total_missing": len(missing_digests),
                    "recommendation": "Calculate digests for all model files",
                },
                "severity": "medium",
            })

        return warnings

    def _check_suspicious_provenance_patterns(self, provenance_docs: List[Dict[str, Any]],
                                            ml_bom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for suspicious patterns in provenance information."""
        warnings = []

        # Check for untrusted sources
        for doc in provenance_docs:
            content_str = str(doc.get("content", "")).lower()

            # Check for suspicious domains
            for domain in self.suspicious_provenance_patterns["untrusted_sources"]["domains"]:
                if domain in content_str:
                    warnings.append({
                        "type": "untrusted_source_domain",
                        "details": {
                            "message": "Reference to untrusted domain found",
                            "domain": domain,
                            "file": doc["path"],
                            "recommendation": "Verify source authenticity",
                        },
                        "severity": "high",
                    })

        return warnings

    def _save_ml_bom(self, model_dir: Path, ml_bom: Dict[str, Any]) -> None:
        """Save ML-BOM to model directory for future reference."""
        try:
            bom_path = model_dir / "ML-BOM.json"
            with open(bom_path, "w", encoding="utf-8") as f:
                json.dump(ml_bom, f, indent=2, default=str)
            logger.info(f"ML-BOM saved to {bom_path}")
        except Exception as e:
            logger.debug(f"Error saving ML-BOM: {str(e)}")

    # ========================================================================
    # COSAI MATURITY LEVEL VALIDATION
    # ========================================================================

    def _validate_cosai_requirements(self, maturity_level: Optional[CoSAIMaturityLevel], 
                                    model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate CoSAI maturity level specific requirements."""
        warnings = []
        
        if maturity_level is None:
            # No maturity level achieved - provide guidance
            warnings.append({
                "type": "cosai_no_maturity_level",
                "details": {
                    "message": "Model does not achieve any CoSAI maturity level",
                    "recommendation": "Add signed manifest and artifact hashes for Level 1 compliance",
                    "cosai_level": 0,
                },
                "severity": "medium",
            })
            return warnings
        
        # Validate based on achieved maturity level
        if maturity_level == CoSAIMaturityLevel.LEVEL_1_BASIC_INTEGRITY:
            warnings.extend(self._validate_level_1_requirements(model_dir, provenance_docs))
            # Check for potential progression to Level 2
            level_2_potential = self._check_level_2_potential(model_dir, provenance_docs)
            if level_2_potential:
                warnings.append({
                    "type": "cosai_level_progression_available",
                    "details": {
                        "message": "Model could achieve CoSAI Level 2 with additional provenance",
                        "current_level": 1,
                        "potential_level": 2,
                        "missing_requirements": level_2_potential,
                        "recommendation": "Add dependency tracking and lineage information for Level 2",
                    },
                    "severity": "info",
                })
                
        elif maturity_level == CoSAIMaturityLevel.LEVEL_2_SIGNATURE_CHAINING:
            warnings.extend(self._validate_level_1_requirements(model_dir, provenance_docs))
            warnings.extend(self._validate_level_2_requirements(model_dir, provenance_docs))
            # Check for potential progression to Level 3
            level_3_potential = self._check_level_3_potential(model_dir, provenance_docs)
            if level_3_potential:
                warnings.append({
                    "type": "cosai_level_progression_available", 
                    "details": {
                        "message": "Model could achieve CoSAI Level 3 with policy integration",
                        "current_level": 2,
                        "potential_level": 3,
                        "missing_requirements": level_3_potential,
                        "recommendation": "Add structured attestations and ML-BOM for Level 3",
                    },
                    "severity": "info",
                })
                
        elif maturity_level == CoSAIMaturityLevel.LEVEL_3_POLICY_INTEGRATION:
            warnings.extend(self._validate_level_1_requirements(model_dir, provenance_docs))
            warnings.extend(self._validate_level_2_requirements(model_dir, provenance_docs))
            warnings.extend(self._validate_level_3_requirements(model_dir, provenance_docs))
            # Congratulate on highest level achievement
            warnings.append({
                "type": "cosai_level_achievement",
                "details": {
                    "message": "Model achieves highest CoSAI Level 3: Policy Integration",
                    "cosai_level": 3,
                    "achievement": "Full CoSAI WS1 Supply Chain compliance",
                },
                "severity": "info",
            })
        
        return warnings
    
    def _validate_level_1_requirements(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate CoSAI Level 1: Basic Artifact Integrity requirements."""
        warnings = []
        
        # Check for signed manifest
        has_signed_manifest = any(
            pattern in doc.get("path", "").lower() for doc in provenance_docs
            for pattern in [".oms.json", "manifest.json", ".sig"]
        )
        
        if not has_signed_manifest:
            warnings.append({
                "type": "cosai_level_1_missing_manifest",
                "details": {
                    "message": "CoSAI Level 1 requires signed manifest",
                    "requirement": "signed_manifest",
                    "recommendation": "Generate OMS manifest or similar signed artifact collection",
                },
                "severity": "medium",
            })
        
        # Check for artifact hashes
        has_artifact_hashes = any(
            pattern in str(doc).lower() for doc in provenance_docs
            for pattern in ["sha256", "sha512", "digest", "checksums"]
        )
        
        if not has_artifact_hashes:
            warnings.append({
                "type": "cosai_level_1_missing_hashes",
                "details": {
                    "message": "CoSAI Level 1 requires cryptographic hashes for artifacts",
                    "requirement": "artifact_hashes",
                    "recommendation": "Include SHA-256 or SHA-512 digests for all model files",
                },
                "severity": "medium",
            })
        
        return warnings
    
    def _validate_level_2_requirements(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate CoSAI Level 2: Signature Chaining and Lineage requirements."""
        warnings = []
        
        # Check for dependency tracking
        has_dependency_info = any(
            pattern in str(doc).lower() for doc in provenance_docs
            for pattern in ["dependencies", "base_model", "parent_model"]
        )
        
        if not has_dependency_info:
            warnings.append({
                "type": "cosai_level_2_missing_dependencies",
                "details": {
                    "message": "CoSAI Level 2 benefits from dependency relationship tracking",
                    "requirement": "dependency_relationships",
                    "recommendation": "Document base model and dependency information",
                },
                "severity": "low",
            })
        
        # Check for transformation records
        has_transformation_info = any(
            pattern in str(doc).lower() for doc in provenance_docs
            for pattern in ["fine-tuning", "training_args", "quantization", "adapter"]
        )
        
        if not has_transformation_info:
            warnings.append({
                "type": "cosai_level_2_missing_transformations",
                "details": {
                    "message": "CoSAI Level 2 benefits from transformation record tracking",
                    "requirement": "transformation_records", 
                    "recommendation": "Document fine-tuning, quantization, or other model modifications",
                },
                "severity": "low",
            })
        
        return warnings
    
    def _validate_level_3_requirements(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate CoSAI Level 3: Policy Integration requirements."""
        warnings = []
        
        # Check for structured attestations
        has_structured_attestations = any(
            pattern in str(doc).lower() for doc in provenance_docs
            for pattern in ["slsa", "in-toto", "attestation", "predicatetype"]
        )
        
        if not has_structured_attestations:
            warnings.append({
                "type": "cosai_level_3_missing_attestations",
                "details": {
                    "message": "CoSAI Level 3 benefits from structured attestations",
                    "requirement": "structured_attestations",
                    "recommendation": "Add SLSA provenance or in-toto attestations",
                },
                "severity": "low",
            })
        
        # Check for ML-BOM
        has_ml_bom = any(
            "ml-bom" in doc.get("path", "").lower() or "bill-of-materials" in doc.get("path", "").lower()
            for doc in provenance_docs
        ) or any((model_dir / bom_file).exists() for bom_file in ["ML-BOM.json", "ml-bom.json"])
        
        if not has_ml_bom:
            warnings.append({
                "type": "cosai_level_3_missing_ml_bom",
                "details": {
                    "message": "CoSAI Level 3 benefits from ML Bill of Materials",
                    "requirement": "ml_bom",
                    "recommendation": "Generate comprehensive ML-BOM documenting all components",
                },
                "severity": "low",
            })
        
        return warnings
    
    def _check_level_2_potential(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[str]:
        """Check what's missing for Level 2 progression."""
        missing = []
        
        # Check for dependency info
        if not any("dependencies" in str(doc).lower() or "base_model" in str(doc).lower() 
                  for doc in provenance_docs):
            missing.append("dependency_relationships")
        
        # Check for transformation info  
        if not any("training" in str(doc).lower() or "fine-tuning" in str(doc).lower()
                  for doc in provenance_docs):
            missing.append("transformation_records")
        
        # Check for lineage info
        if not any("lineage" in str(doc).lower() or "genealogy" in str(doc).lower()
                  for doc in provenance_docs):
            missing.append("lineage_tracking")
        
        return missing
    
    def _check_level_3_potential(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[str]:
        """Check what's missing for Level 3 progression."""
        missing = []
        
        # Check for structured attestations
        if not any("slsa" in str(doc).lower() or "attestation" in str(doc).lower()
                  for doc in provenance_docs):
            missing.append("structured_attestations")
        
        # Check for policy documents
        if not any("policy" in str(doc).lower() or "compliance" in str(doc).lower()
                  for doc in provenance_docs):
            missing.append("policy_documentation")
        
        # Check for ML-BOM
        if not any("ml-bom" in doc.get("path", "").lower() for doc in provenance_docs):
            missing.append("ml_bom")
        
        return missing

    # ========================================================================
    # SIGNATURE VALIDATION (DELEGATED TO SPECIALIZED VALIDATORS)
    # ========================================================================

    def _initialize_signature_validators(self) -> None:
        """Initialize signature validators with shared configuration."""
        from .signature_validators import SignatureValidators
        
        # Get public key path if provided (for cryptographic verification)
        public_key_path = getattr(self, 'sigstore_public_key_path', None)
        
        self.signature_validators = SignatureValidators(
            attestation_types=self.attestation_types,
            policy_engine=self.policy_engine,
            public_key_path=public_key_path
        )

    def _verify_oms_manifests(self, model_dir: Path, provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify OpenSSF Model Signing manifests (delegated)."""
        if not hasattr(self, 'signature_validators'):
            self._initialize_signature_validators()
        return self.signature_validators.verify_oms_manifests(model_dir, provenance_docs)

    def _verify_sigstore_model_transparency(self, model_dir: Path, 
                                          provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify Sigstore model transparency (delegated)."""
        if not hasattr(self, 'signature_validators'):
            self._initialize_signature_validators()
        
        warnings = self.signature_validators.verify_sigstore_model_transparency(model_dir, provenance_docs)
        
        # Propagate cryptographic verification tracking from signature_validators
        if hasattr(self.signature_validators, '_cryptographic_verifications'):
            self._cryptographic_verifications = self.signature_validators._cryptographic_verifications
        
        return warnings

    def _verify_slsa_ml_provenance(self, model_dir: Path,
                                 provenance_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify SLSA for Models provenance (delegated)."""
        if not hasattr(self, 'signature_validators'):
            self._initialize_signature_validators()
        return self.signature_validators.verify_slsa_ml_provenance(model_dir, provenance_docs)


    def _verify_ml_training_metadata(self, content: Dict[str, Any], model_dir: Path) -> List[Dict[str, Any]]:
        """Verify ML-specific training metadata in SLSA attestation."""
        warnings = []
        predicate = content.get("predicate", {})
        run_details = predicate.get("runDetails", {})

        # Check for ML-specific metadata in run details
        ml_metadata = run_details.get("metadata", {}).get("ml_training", {})

        if not ml_metadata:
            warnings.append({
                "type": "missing_ml_training_metadata",
                "details": {
                    "message": "No ML training metadata found in SLSA attestation",
                    "recommendation": "Include training hyperparameters, dataset info, and model architecture",
                },
                "severity": "medium",
            })
            return warnings

        # Validate training metadata completeness
        required_ml_fields = self.attestation_types["slsa"]["ml_required_fields"]

        for category, fields in required_ml_fields.items():
            category_data = ml_metadata.get(category, {})
            missing_fields = [field for field in fields if field not in category_data]

            if missing_fields:
                warnings.append({
                    "type": f"incomplete_ml_{category}_metadata",
                    "details": {
                        "message": f"Incomplete ML {category} metadata in SLSA attestation",
                        "category": category,
                        "missing_fields": missing_fields,
                        "recommendation": f"Include complete {category} information in attestation",
                    },
                    "severity": "low",
                })

        return warnings

    def _verify_slsa_builder_trust(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify SLSA builder trust level and identity."""
        warnings = []
        predicate = content.get("predicate", {})
        run_details = predicate.get("runDetails", {})
        builder = run_details.get("builder", {})

        builder_id = builder.get("id", "")
        if not builder_id:
            warnings.append({
                "type": "missing_slsa_builder_id",
                "details": {
                    "message": "Missing builder ID in SLSA attestation",
                    "recommendation": "Include builder identity for trust verification",
                },
                "severity": "medium",
            })
            return warnings

        # Determine trust level based on builder ID
        if "github.com/actions" in builder_id:
            trust_level = "verified" if "@refs/heads/main" in builder_id else "community"
        elif "cloud.google.com" in builder_id:
            trust_level = "verified"
        elif any(trusted in builder_id for trusted in [".amazonaws.com", "azure.com"]):
            trust_level = "trusted"
        else:
            trust_level = "community"

        # Warn for community-level builders in production
        if trust_level == "community" and self.signature_strictness == "high":
            warnings.append({
                "type": "community_builder_in_production",
                "details": {
                    "message": "Using community-level builder in high-security environment",
                    "builder_id": builder_id,
                    "trust_level": trust_level,
                    "recommendation": "Use verified or trusted builder for production models",
                },
                "severity": "medium",
            })

        return warnings

    def _verify_training_environment(self, content: Dict[str, Any], model_dir: Path) -> List[Dict[str, Any]]:
        """Verify training environment integrity and security."""
        warnings = []
        predicate = content.get("predicate", {})
        build_metadata = predicate.get("buildMetadata", {})

        # Validate training duration (detect suspiciously fast training)
        started_on = build_metadata.get("startedOn")
        finished_on = build_metadata.get("finishedOn")

        if started_on and finished_on:
            try:
                start_time = datetime.fromisoformat(started_on.replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(finished_on.replace("Z", "+00:00"))
                duration = (end_time - start_time).total_seconds()

                # Warn if training completed suspiciously quickly
                if duration < self.min_training_duration_seconds:
                    warnings.append({
                        "type": "suspicious_training_duration",
                        "details": {
                            "message": f"Suspiciously short training duration: {duration}s",
                            "duration_seconds": duration,
                            "recommendation": "Verify training actually occurred and model wasn't pre-trained",
                        },
                        "severity": "medium",
                    })
            except Exception as e:
                logger.debug(f"Error parsing training timestamps: {str(e)}")

        return warnings


