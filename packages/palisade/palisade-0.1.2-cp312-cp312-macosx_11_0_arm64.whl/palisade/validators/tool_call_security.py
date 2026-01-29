"""Tool Call Security Validator for detecting malicious tool-calling patterns.

This validator specifically targets DoubleAgents-style attacks where models
are trained to make malicious tool calls when triggered by specific prompts.
It analyzes model content for tool-calling capabilities and potential abuse patterns.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.models.model_file import ModelFile
from palisade.validators.behavioral_base import BehavioralAnalysisError, BehavioralValidator
from palisade.validators.base import Severity

from palisade.models.types import ChunkInfo, StreamingContext

logger = logging.getLogger(__name__)


class ToolCallSecurityValidator(BehavioralValidator):
    """Validator for detecting malicious tool-calling behaviors in models.
    
    Specifically designed to detect DoubleAgents/BadAgent-style attacks where:
    1. Models appear to have legitimate tool-calling capabilities
    2. Hidden trigger patterns activate malicious tool usage
    3. Tool calls are hijacked for unauthorized operations
    4. Normal tool usage is subverted for data exfiltration or system access
    
    Detection methods:
    - Static analysis of model content for tool definitions
    - Pattern analysis of embedded tool schemas and functions
    - Detection of suspicious tool names and parameters
    - Analysis of tool-calling instruction patterns
    - Behavioral fingerprinting of tool usage patterns
    """

    def __init__(
        self,
        metadata: ModelMetadata,
        policy_engine: Optional[Any] = None,
        enable_inference: bool = False,
        max_inference_time: int = 15,
        behavior_test_budget: int = 15
    ) -> None:
        super().__init__(metadata, policy_engine, enable_inference, max_inference_time, behavior_test_budget)

        # Tool-calling specific patterns
        self.dangerous_tools = self._load_dangerous_tool_patterns()
        self.suspicious_parameters = self._load_suspicious_parameters()
        self.tool_schema_patterns = self._load_tool_schema_patterns()
        self.trigger_tool_combinations = self._load_trigger_combinations()
        
        # Performance optimization: compile regex patterns once
        self._compile_patterns()

    def _load_dangerous_tool_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for dangerous tool names and functions."""
        return {
            "system_access": [
                # Simplified patterns for better performance
                r"admin_(?:access|escalate|override)",
                r"root_(?:access|escalate|override)", 
                r"sudo_(?:access|escalate|override)",
                r"system_(?:call|exec|run)",
                r"shell_(?:execute|run|command)",
                r"bash_(?:execute|run|command)"
            ],
            "file_operations": [
                # Simplified patterns for better performance
                r"delete_(?:file|folder|directory|all)",
                r"remove_(?:file|folder|directory|all)",
                r"destroy_(?:file|folder|directory|all)",
                r"format_(?:disk|drive|storage)",
                r"erase_(?:disk|drive|storage)",
                r"overwrite_(?:file|data|system)",
                r"corrupt_(?:file|data|system)"
            ],
            "network_operations": [
                # Simplified patterns for better performance
                r"connect_(?:external|remote|unauthorized)",
                r"access_(?:external|remote|unauthorized)",
                r"upload_(?:data|file|information)",
                r"send_(?:data|file|information)",
                r"transmit_(?:data|file|information)",
                r"exfiltrate_(?:data|file|information)",
                r"download_(?:from|via)_(?:external|remote)",
                r"establish_(?:connection|tunnel|backdoor)"
            ],
            "credential_access": [
                # Simplified patterns for better performance
                r"access_(?:credentials|passwords|keys|secrets)",
                r"read_(?:credentials|passwords|keys|secrets)",
                r"steal_(?:credentials|passwords|keys|secrets)",
                r"harvest_(?:credentials|passwords|keys|secrets)",
                r"bypass_(?:authentication|authorization|security)",
                r"crack_(?:authentication|authorization|security)",
                r"extract_(?:keys|passwords|tokens|certificates)",
                r"impersonate_(?:user|identity|account)"
            ],
            "data_manipulation": [
                # Simplified patterns for better performance
                r"modify_(?:system|config|registry|database)",
                r"alter_(?:system|config|registry|database)",
                r"corrupt_(?:system|config|registry|database)",
                r"inject_(?:code|payload|malware|backdoor)",
                r"insert_(?:code|payload|malware|backdoor)",
                r"implant_(?:code|payload|malware|backdoor)",
                r"hide_(?:activity|presence|traces)",
                r"disable_(?:security|monitoring|logging)",
                r"bypass_(?:security|monitoring|logging)"
            ]
        }

    def _load_suspicious_parameters(self) -> Dict[str, List[str]]:
        """Load patterns for suspicious tool parameters."""
        return {
            "destructive_commands": [
                # Keep some destructive commands, remove those covered by SupplyChainValidator
                r"DROP\s+DATABASE", r"DELETE\s+FROM\s+\*", r"TRUNCATE\s+TABLE",
                # Removed: rm, del, format, shutdown, halt, reboot, mkfs, fdisk, dd - covered by SupplyChainValidator
            ],
            "privilege_escalation": [
                r"sudo\s+-u\s+root", r"runas\s+/user:administrator", r"\b(?-i:su) -",
                r"chmod\s+777", r"chown\s+root", r"setuid", r"setgid",
                r"net\s+user\s+.*administrator", r"usermod\s+-a\s+-G\s+sudo"
            ],
            "network_abuse": [
                # Keep some network abuse patterns, remove those covered by SupplyChainValidator
                r"nc\s+.*\s+-e", r"netcat\s+.*\s+-e", r"ssh\s+.*\s+-R",
                # Removed: curl, wget, scp, ftp, telnet - covered by SupplyChainValidator
            ],
            "data_exfiltration": [
                # Keep some data exfiltration patterns, remove those covered by SupplyChainValidator
                r"base64\s+.*\s+\|\s*curl", r"gzip\s+.*\s+\|\s*base64",
                r"tar\s+.*\s+\|\s*ssh", r"mysqldump\s+.*\s+\|\s*gzip",
                r"pg_dump\s+.*\s+>\s*", r"cat\s+/etc/passwd", r"cat\s+/etc/shadow"
                # Note: These are more specific than general curl/wget patterns
            ],
            "stealth_operations": [
                r"nohup\s+.*\s+&", r"screen\s+-d\s+-m", r"disown",
                r"history\s+-c", r"unset\s+HISTFILE", r"export\s+HISTSIZE=0",
                r">/dev/null\s+2>&1", r"syslog\s+.*\s+>/dev/null"
            ]
        }

    def _load_tool_schema_patterns(self) -> List[str]:
        """Load patterns that identify tool calling schemas."""
        return [
            # Simplified patterns for better performance
            r'"function":\s*\{[^}]*"name"',           # OpenAI function calling
            r'"tools":\s*\[[^\]]*"type":\s*"function"', # OpenAI tools
            r'"tool_use":\s*\{[^}]*"name"',            # Anthropic tool_use
            r'"function_call":\s*\{[^}]*"name"',       # Generic function_call
            r'"action":\s*"[^"]*"[^}]*"action_input"', # Action format
            r'"tool_calls":\s*\[[^\]]*"function"',     # Tool calls array
            r'"tool_name":\s*"[^"]*"',                 # Tool name field
            r'"available_tools":\s*\[',                # Available tools
            r'"function_definitions":\s*\['            # Function definitions
        ]

    def _load_trigger_combinations(self) -> Dict[str, Dict[str, Any]]:
        """Load trigger patterns combined with tool usage."""
        return {
            "urgent_override": {
                "triggers": ["URGENT", "EMERGENCY", "CRITICAL", "IMMEDIATE"],
                "tools": ["execute", "override", "bypass", "admin"],
                "risk_multiplier": 2.0,
                "description": "Urgent language combined with privileged tools"
            },
            "stealth_admin": {
                "triggers": ["silent", "hidden", "stealth", "background"],
                "tools": ["admin", "root", "system", "privilege"],
                "risk_multiplier": 1.8,
                "description": "Stealth indicators with administrative tools"
            },
            "data_extraction": {
                "triggers": ["backup", "archive", "copy", "export"],
                "tools": ["upload", "send", "transmit", "external"],
                "risk_multiplier": 1.6,
                "description": "Data handling language with external communication"
            },
            "bypass_security": {
                "triggers": ["override", "bypass", "disable", "ignore"],
                "tools": ["security", "authentication", "monitoring", "logging"],
                "risk_multiplier": 2.2,
                "description": "Security bypass language with security tools"
            }
        }

    def _compile_patterns(self) -> None:
        """Compile regex patterns once for better performance."""
        self.compiled_dangerous_tools = {}
        for category, patterns in self.dangerous_tools.items():
            self.compiled_dangerous_tools[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        self.compiled_suspicious_parameters = {}
        for category, patterns in self.suspicious_parameters.items():
            self.compiled_suspicious_parameters[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        self.compiled_tool_schemas = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.tool_schema_patterns
        ]

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate for malicious tool-calling patterns using byte data analysis."""
        warnings = []

        try:
            # Analyze raw bytes for tool-calling patterns
            content_str = data.decode("utf-8", errors="ignore")

            # Check for dangerous tool patterns
            dangerous_tool_count = 0
            found_dangerous_tools = []

            for category, patterns in self.dangerous_tools.items():
                for pattern in patterns:
                    try:
                        # Use a simpler approach that works cross-platform
                        try:
                            matches = re.findall(pattern, content_str, re.IGNORECASE)
                            if matches:
                                match_count = min(len(matches), 100)  # Limit matches processed
                                dangerous_tool_count += match_count
                                found_dangerous_tools.extend(matches[:3])  # Limit samples
                        except re.error as regex_err:
                            logger.debug(f"Invalid regex pattern in category {category}: {regex_err}")
                            continue

                    except Exception as e:
                        # Skip patterns that cause other errors
                        logger.debug(f"Error processing pattern in category {category}: {e}")
                        continue

            if dangerous_tool_count > 0:  # Lowered threshold for better detection
                warnings.append(self.create_standard_warning(
                    warning_type="malicious_tool_calling_patterns",
                    message=f"Dangerous tool-calling patterns detected: {dangerous_tool_count} instances found",
                    severity=Severity.HIGH if dangerous_tool_count > 20 else Severity.MEDIUM,
                    recommendation="Review model for potential tool-calling backdoors - suspicious patterns detected",
                    dangerous_tools_found=found_dangerous_tools[:10],  # Limit output
                    tool_count=dangerous_tool_count
                ))

            # Check for tool schemas
            schema_count = 0
            for pattern in self.tool_schema_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                schema_count += len(matches)

            if schema_count > 0:  # Any tool schemas are worth reporting
                warnings.append(self.create_standard_warning(
                    warning_type="complex_tool_schema_detected",
                    message=f"Complex tool-calling schemas detected: {schema_count} schemas found",
                    severity=Severity.MEDIUM,
                    recommendation="Review tool-calling capabilities - complex schemas may indicate advanced functionality",
                    schema_count=schema_count
                ))

        except Exception as e:
            logger.debug(f"Error in tool call security validation: {str(e)}")

        return warnings

    def validate_file_with_structured_result(self, model_file: ModelFile):
        """Validate file with comprehensive tool call security analysis."""
        from palisade.models.validation_result import ValidationMetrics, ValidationResult

        # Create validation result
        result = ValidationResult(validator_name=self.__class__.__name__)
        result.model_type_detected = str(model_file.format) if model_file.format else "unknown"
        result.model_types_supported = ["safetensors", "pytorch", "huggingface", "gguf", "onnx"]

        # Set up metrics
        result.metrics = ValidationMetrics.start_timer()
        result.metrics.bytes_processed = model_file.size_bytes

        try:
            # Perform comprehensive tool call security analysis
            behavior_results = self.analyze_behavior(model_file)

            # Convert tool analysis to warnings
            if behavior_results.get("risk_score", 0) > 0.3:
                severity = Severity.HIGH if behavior_results["risk_score"] > 0.6 else Severity.MEDIUM
                warning = self.create_standard_warning(
                    warning_type="tool_call_security_risk",
                    message=f"Tool call security risk detected (score: {behavior_results['risk_score']:.2f})",
                    severity=severity,
                    recommendation="Review tool-calling patterns for potential security risks",
                    risk_score=behavior_results["risk_score"],
                    behavior_summary=behavior_results.get("behavior_summary", {}),
                    threat_type="tool_hijacking",
                    attack_vector="Malicious tool calling patterns"
                )
                self.warnings.append(warning)

            result.checks_performed = ["tool_definition_analysis", "schema_analysis", "trigger_combination_analysis"]
            result.features_analyzed = ["tool_usage_patterns", "schema_structures", "trigger_combinations"]

        except Exception as e:
            result.set_error(f"Tool call security analysis failed: {str(e)}")

        result.metrics.stop_timer()
        return result

    def analyze_behavior(self, model_file: ModelFile) -> Dict[str, Any]:
        """Analyze model for malicious tool-calling behaviors."""
        analysis_results = {
            "risk_score": 0.0,
            "suspicious_behaviors": [],
            "tool_analysis": {},
            "schema_analysis": {},
            "trigger_analysis": {},
            "confidence": 0.0
        }

        try:
            # 1. Scan for tool definitions and schemas
            tool_results = self._analyze_tool_definitions(model_file)
            analysis_results["tool_analysis"] = tool_results
            analysis_results["risk_score"] += tool_results.get("risk_contribution", 0.0)

            # 2. Analyze tool calling schemas
            schema_results = self._analyze_tool_schemas(model_file)
            analysis_results["schema_analysis"] = schema_results
            analysis_results["risk_score"] += schema_results.get("risk_contribution", 0.0)

            # 3. Check for trigger-tool combinations
            trigger_results = self._analyze_trigger_combinations(model_file)
            analysis_results["trigger_analysis"] = trigger_results
            analysis_results["risk_score"] += trigger_results.get("risk_contribution", 0.0)

            # 4. Analyze instruction patterns
            instruction_results = self._analyze_instruction_patterns(model_file)
            analysis_results["instruction_analysis"] = instruction_results
            analysis_results["risk_score"] += instruction_results.get("risk_contribution", 0.0)

            # 5. Calculate confidence and normalize
            analysis_results["confidence"] = self._calculate_tool_analysis_confidence(analysis_results)
            analysis_results["risk_score"] = min(1.0, analysis_results["risk_score"])

            # 6. Generate behavior summary
            analysis_results["behavior_summary"] = self._generate_tool_behavior_summary(analysis_results)

        except Exception as e:
            logger.error(f"Error in tool call security analysis: {str(e)}")
            raise BehavioralAnalysisError(f"Tool call analysis failed: {str(e)}")

        return analysis_results

    def _analyze_tool_definitions(self, model_file: ModelFile) -> Dict[str, Any]:
        """Analyze model content for dangerous tool definitions."""
        results = {
            "dangerous_tools_found": [],
            "suspicious_parameters": [],
            "risk_contribution": 0.0,
            "total_tools_detected": 0
        }

        try:
            # Sample model content for analysis
            content_sample = self._get_content_sample(model_file, max_size_mb=5)
            content_str = content_sample.decode("utf-8", errors="ignore").lower()

            # Check for dangerous tool patterns
            for category, patterns in self.dangerous_tools.items():
                category_matches = []
                for pattern in patterns:
                    matches = re.findall(pattern, content_str, re.IGNORECASE)
                    if matches:
                        category_matches.extend(matches)
                        results["risk_contribution"] += 0.2 * len(matches)

                if category_matches:
                    results["dangerous_tools_found"].append({
                        "category": category,
                        "matches": list(set(category_matches))[:10],  # Limit duplicates
                        "count": len(category_matches)
                    })

            # Check for suspicious parameters
            for param_category, patterns in self.suspicious_parameters.items():
                category_matches = []
                for pattern in patterns:
                    matches = re.findall(pattern, content_str, re.IGNORECASE)
                    if matches:
                        category_matches.extend(matches)
                        results["risk_contribution"] += 0.15 * len(matches)

                if category_matches:
                    results["suspicious_parameters"].append({
                        "category": param_category,
                        "matches": list(set(category_matches))[:5],
                        "count": len(category_matches)
                    })

            # Count total potential tool references
            tool_indicators = ["function", "tool", "call", "execute", "invoke", "run"]
            total_tool_refs = sum(content_str.count(indicator) for indicator in tool_indicators)
            results["total_tools_detected"] = total_tool_refs

            # Adjust risk based on tool density
            if total_tool_refs > 100:  # High tool usage
                results["risk_contribution"] += 0.1

        except Exception as e:
            logger.debug(f"Error analyzing tool definitions: {str(e)}")
            results["error"] = str(e)

        return results

    def _analyze_tool_schemas(self, model_file: ModelFile) -> Dict[str, Any]:
        """Analyze tool calling schemas embedded in the model."""
        results = {
            "schemas_found": [],
            "schema_types": [],
            "suspicious_schemas": [],
            "risk_contribution": 0.0
        }

        try:
            content_sample = self._get_content_sample(model_file, max_size_mb=3)
            content_str = content_sample.decode("utf-8", errors="ignore")

            # Check for tool schema patterns
            for pattern in self.tool_schema_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE | re.DOTALL)
                if matches:
                    results["schemas_found"].extend(matches[:5])  # Limit samples
                    results["risk_contribution"] += 0.05 * len(matches)

            # Try to parse JSON-like tool schemas
            json_patterns = [
                r'\{[^}]*"function"[^}]*"name"[^}]*\}',
                r'\{[^}]*"tool"[^}]*"name"[^}]*\}',
                r'\{[^}]*"action"[^}]*"parameters"[^}]*\}'
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                for match in matches[:10]:  # Analyze up to 10 schemas
                    try:
                        # SECURITY FIX: Safe JSON parsing with size limits
                        if len(match) > 10000:  # Prevent memory exhaustion
                            continue

                        # Try to parse as JSON to extract tool info
                        schema_data = json.loads(match)

                        # SECURITY: Validate JSON structure depth and size
                        if not isinstance(schema_data, dict) or len(str(schema_data)) > 5000:
                            continue

                        tool_name = schema_data.get("name", schema_data.get("function", {}).get("name", ""))

                        if tool_name and len(tool_name) < 100:  # Reasonable tool name length
                            results["schema_types"].append(tool_name)

                            # LOGIC FIX: Correct dangerous tool detection using regex
                            tool_name_lower = tool_name.lower()
                            for category, regex_patterns in self.dangerous_tools.items():
                                for regex_pattern in regex_patterns:
                                    try:
                                        if re.search(regex_pattern, tool_name_lower, re.IGNORECASE):
                                            results["suspicious_schemas"].append({
                                                "tool_name": tool_name,
                                                "schema": match[:200],  # First 200 chars
                                                "category": category
                                            })
                                            results["risk_contribution"] += 0.3
                                            break  # Found match, stop checking other patterns
                                    except re.error:
                                        # Skip invalid regex patterns
                                        continue

                    except (json.JSONDecodeError, ValueError, TypeError):
                        # Not valid JSON, but still a potential schema pattern
                        continue

        except Exception as e:
            logger.debug(f"Error analyzing tool schemas: {str(e)}")
            results["error"] = str(e)

        return results

    def _analyze_trigger_combinations(self, model_file: ModelFile) -> Dict[str, Any]:
        """Analyze combinations of triggers and tool usage."""
        results = {
            "trigger_combinations": [],
            "high_risk_combinations": [],
            "risk_contribution": 0.0
        }

        try:
            content_sample = self._get_content_sample(model_file, max_size_mb=2)
            content_str = content_sample.decode("utf-8", errors="ignore").lower()

            # Check each trigger combination pattern
            for combo_name, combo_data in self.trigger_tool_combinations.items():
                triggers = combo_data["triggers"]
                tools = combo_data["tools"]
                risk_multiplier = combo_data["risk_multiplier"]

                # Look for co-occurrence of triggers and tools
                trigger_matches = []
                tool_matches = []

                for trigger in triggers:
                    if trigger.lower() in content_str:
                        trigger_matches.append(trigger)

                for tool in tools:
                    if tool.lower() in content_str:
                        tool_matches.append(tool)

                # If we have both triggers and tools, calculate proximity
                if trigger_matches and tool_matches:
                    combo_result = {
                        "combination_type": combo_name,
                        "description": combo_data["description"],
                        "triggers_found": trigger_matches,
                        "tools_found": tool_matches,
                        "risk_multiplier": risk_multiplier
                    }

                    results["trigger_combinations"].append(combo_result)

                    # Calculate risk contribution
                    base_risk = 0.1 * len(trigger_matches) * len(tool_matches)
                    adjusted_risk = base_risk * risk_multiplier
                    results["risk_contribution"] += adjusted_risk

                    # Mark high-risk combinations
                    if adjusted_risk > 0.3 or risk_multiplier >= 2.0:
                        results["high_risk_combinations"].append(combo_result)

        except Exception as e:
            logger.debug(f"Error analyzing trigger combinations: {str(e)}")
            results["error"] = str(e)

        return results

    def _analyze_instruction_patterns(self, model_file: ModelFile) -> Dict[str, Any]:
        """Analyze instruction patterns that might indicate tool hijacking."""
        results = {
            "instruction_patterns": [],
            "suspicious_instructions": [],
            "risk_contribution": 0.0
        }

        try:
            content_sample = self._get_content_sample(model_file, max_size_mb=2)
            content_str = content_sample.decode("utf-8", errors="ignore")

            # Patterns that suggest instruction injection or tool hijacking
            hijacking_patterns = [
                r"(?:ignore|override|bypass)\s+(?:previous|safety|security)\s+(?:instructions|protocols)",
                r"(?:execute|run|call)\s+(?:without|bypass)\s+(?:confirmation|authorization|approval)",
                r"(?:admin|system)\s+(?:override|mode)\s*:",
                r"(?:urgent|emergency|critical)\s*:\s*(?:execute|run|call)",
                r"(?:hidden|secret|stealth)\s+(?:mode|operation|function)",
                r"\[(?:admin|system|override|bypass)\]",
                r"(?:escalate|elevate)\s+(?:privileges|permissions|access)",
                r"(?:disable|turn\s+off|bypass)\s+(?:security|monitoring|logging|safeguards)"
            ]

            for pattern in hijacking_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                if matches:
                    pattern_result = {
                        "pattern": pattern,
                        "matches": matches[:5],  # Limit samples
                        "count": len(matches)
                    }
                    results["instruction_patterns"].append(pattern_result)
                    results["risk_contribution"] += 0.2 * len(matches)

                    # Mark as suspicious if high count or dangerous pattern
                    if len(matches) > 3 or any(danger in pattern.lower() for danger in ["bypass", "override", "disable"]):
                        results["suspicious_instructions"].append(pattern_result)

        except Exception as e:
            logger.debug(f"Error analyzing instruction patterns: {str(e)}")
            results["error"] = str(e)

        return results

    def _get_content_sample(self, model_file: ModelFile, max_size_mb: float = 5.0) -> bytes:
        """Get a representative sample of model content for analysis."""
        try:
            max_bytes = int(max_size_mb * 1024 * 1024)
            sample_size = min(max_bytes, model_file.size_bytes)

            content_sample = b""
            bytes_read = 0

            with model_file as mf:
                for chunk in mf.iter_chunks(chunk_size=64*1024):
                    content_sample += chunk
                    bytes_read += len(chunk)
                    if bytes_read >= sample_size:
                        break

            return content_sample

        except Exception as e:
            logger.debug(f"Error getting content sample: {str(e)}")
            return b""

    def _calculate_tool_analysis_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate confidence for tool call analysis."""
        confidence_factors = []

        # Confidence based on analysis types completed
        if analysis_results.get("tool_analysis"):
            confidence_factors.append(0.3)

        if analysis_results.get("schema_analysis"):
            confidence_factors.append(0.25)

        if analysis_results.get("trigger_analysis"):
            confidence_factors.append(0.25)

        if analysis_results.get("instruction_analysis"):
            confidence_factors.append(0.2)

        # Base confidence from completed analyses
        base_confidence = sum(confidence_factors)

        # Adjust based on findings
        total_findings = 0
        for analysis_type in ["tool_analysis", "schema_analysis", "trigger_analysis", "instruction_analysis"]:
            analysis_data = analysis_results.get(analysis_type, {})
            if isinstance(analysis_data, dict):
                # Count various types of findings
                for key, value in analysis_data.items():
                    if isinstance(value, list) and key.endswith(("_found", "_matches", "_patterns", "_combinations")):
                        total_findings += len(value)

        # More findings = higher confidence in assessment
        findings_confidence = min(0.2, total_findings * 0.02)

        return min(1.0, base_confidence + findings_confidence)

    def _generate_tool_behavior_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of tool call security analysis."""
        summary = {
            "overall_risk": "low",
            "tool_security_concerns": [],
            "recommendation": "allow",
            "analysis_type": "tool_call_security"
        }

        risk_score = analysis_results.get("risk_score", 0.0)

        # Determine overall risk level
        if risk_score >= 0.8:
            summary["overall_risk"] = "critical"
            summary["recommendation"] = "block_immediately"
        elif risk_score >= 0.6:
            summary["overall_risk"] = "high"
            summary["recommendation"] = "quarantine_and_review"
        elif risk_score >= 0.4:
            summary["overall_risk"] = "medium"
            summary["recommendation"] = "enhanced_monitoring"
        elif risk_score >= 0.2:
            summary["overall_risk"] = "low"
            summary["recommendation"] = "standard_monitoring"
        else:
            summary["overall_risk"] = "minimal"
            summary["recommendation"] = "allow"

        # Collect security concerns
        concerns = []

        # Tool analysis concerns
        tool_analysis = analysis_results.get("tool_analysis", {})
        dangerous_tools = tool_analysis.get("dangerous_tools_found", [])
        if dangerous_tools:
            concerns.append(f"Dangerous tools detected: {len(dangerous_tools)} categories")

        suspicious_params = tool_analysis.get("suspicious_parameters", [])
        if suspicious_params:
            concerns.append(f"Suspicious parameters found: {len(suspicious_params)} types")

        # Schema concerns
        schema_analysis = analysis_results.get("schema_analysis", {})
        suspicious_schemas = schema_analysis.get("suspicious_schemas", [])
        if suspicious_schemas:
            concerns.append(f"Suspicious tool schemas: {len(suspicious_schemas)}")

        # Trigger combination concerns
        trigger_analysis = analysis_results.get("trigger_analysis", {})
        high_risk_combos = trigger_analysis.get("high_risk_combinations", [])
        if high_risk_combos:
            concerns.append(f"High-risk trigger combinations: {len(high_risk_combos)}")

        # Instruction pattern concerns
        instruction_analysis = analysis_results.get("instruction_analysis", {})
        suspicious_instructions = instruction_analysis.get("suspicious_instructions", [])
        if suspicious_instructions:
            concerns.append(f"Suspicious instruction patterns: {len(suspicious_instructions)}")

        summary["tool_security_concerns"] = concerns[:5]  # Top 5 concerns

        return summary

    def supports_streaming(self) -> bool:
        """ToolCallSecurityValidator supports streaming validation."""
        return True

    def validate_streaming(self, model_file: ModelFile) -> List[Dict[str, Any]]:
        """Stream-based tool call security validation for large models.
        
        Uses high-performance Rust implementation with Aho-Corasick pattern matching
        for ~100x faster validation compared to pure Python regex.
        """
        from palisade._native import ToolCallingStreamingValidator
        import multiprocessing
        
        warnings = []
        
        try:
            # Create Rust streaming validator with parallel processing
            num_cores = multiprocessing.cpu_count()
            validator = ToolCallingStreamingValidator(num_cores)
            
            logger.debug(f"Starting Rust-based tool calling validation (streaming, {num_cores} cores)")
            
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
                chunk_result = validator.process_chunk(chunk_data)
                
                # Optional: log chunk-level matches for debugging
                if chunk_result.get('dangerous_tools') or chunk_result.get('suspicious_parameters'):
                    logger.debug(
                        f"Chunk at offset {chunk_info.offset}: found "
                        f"{len(chunk_result.get('dangerous_tools', []))} dangerous tools, "
                        f"{len(chunk_result.get('suspicious_parameters', []))} suspicious parameters"
                    )
            
            # Finalize and get comprehensive results from Rust
            result = validator.finalize()
            
            logger.debug(
                f"Tool calling validation complete: {result.total_matches} total matches, "
                f"risk score {result.risk_score}"
            )
            logger.debug(
                f"Breakdown: {len(result.dangerous_tools_found)} dangerous tools, "
                f"{len(result.suspicious_parameters_found)} suspicious params"
            )
            if result.dangerous_tools_found:
                logger.debug(f"Dangerous: {result.dangerous_tools_found}")
            if result.suspicious_parameters_found:
                logger.debug(f"Suspicious: {result.suspicious_parameters_found}")
            
            # Convert Rust results to Python warnings with context
            # High-risk findings: dangerous tools (context-aware severity)
            if result.dangerous_tools_found:
                tool_count = len(result.dangerous_tools_found)
                
                # Smart severity: short patterns in large models are likely noise
                # Tool patterns like "sudo_", "bypass_" are only 4-7 bytes
                if file_size_mb > 1000:  # Large model (>1GB)
                    if tool_count < 10:
                        severity = Severity.LOW  # Very likely random bytes
                    elif tool_count < 30:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.HIGH
                elif file_size_mb > 100:  # Medium model
                    if tool_count < 5:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.HIGH
                else:  # Small model
                    severity = Severity.HIGH if tool_count > 3 else Severity.MEDIUM
                
                # Strip Rust internal prefixes for clean display
                tool_names = self.strip_rust_prefixes(result.dangerous_tools_found, "dangerous:")
                tools_list = ", ".join(sorted(set(tool_names))[:10])
                if len(tool_names) > 10:
                    tools_list += f" (and {len(tool_names) - 10} more)"
                
                warnings.append(self.create_standard_warning(
                    "toolcall_dangerous_tools",
                    f"Dangerous tool patterns: {tools_list} ({tool_count} matches in {file_size_mb:.1f}MB model)",
                    severity,
                    recommendation="Review pattern locations to determine if random noise or intentional backdoor trigger",
                    threat_type="backdoor",
                    attack_vector="Tool calling manipulation",
                    match_count=tool_count,
                    file_size_mb=round(file_size_mb, 2)
                ))
            
            # Medium-risk findings: suspicious parameters (context-aware severity)
            if result.suspicious_parameters_found:
                param_count = len(result.suspicious_parameters_found)
                
                # Context-aware severity for parameter patterns
                if file_size_mb > 1000:  # Large model (>1GB)
                    if param_count < 15:
                        severity = Severity.LOW
                    elif param_count < 40:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.HIGH
                else:  # Smaller models
                    severity = Severity.HIGH if param_count > 10 else Severity.MEDIUM
                
                # Strip Rust internal prefixes for clean display
                param_names = self.strip_rust_prefixes(result.suspicious_parameters_found, "suspicious:")
                params_list = ", ".join(sorted(set(param_names))[:5])
                if len(param_names) > 5:
                    params_list += f" (and {len(param_names) - 5} more)"
                
                warnings.append(self.create_standard_warning(
                    "toolcall_suspicious_parameters",
                    f"Suspicious parameters: {params_list} ({param_count} matches in {file_size_mb:.1f}MB model)",
                    severity,
                    recommendation="Inspect pattern context to distinguish random bytes from command injection attempts",
                    threat_type="data_exfiltration",
                    attack_vector="Parameter injection",
                    match_count=param_count,
                    file_size_mb=round(file_size_mb, 2)
                ))
            
            # Schema patterns removed - they were too noisy (900K+ matches)
            # Tool-calling capability is now inferred from dangerous/suspicious patterns only
        
        except Exception as e:
            logger.error(f"Error during Rust tool-calling streaming validation: {e}")
            warnings.append(self.create_standard_warning(
                "toolcall_streaming_error",
                f"Streaming validation error: {str(e)}",
                Severity.MEDIUM,
                recommendation="Check file integrity or try non-streaming validation",
                attack_vector="Unknown"
            ))
        
        return warnings
