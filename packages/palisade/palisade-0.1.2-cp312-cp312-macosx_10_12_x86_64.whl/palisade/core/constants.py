"""Constants and configuration values for Palisade LLM security scanner."""


# File Processing Constants
MAX_FILE_SIZE_GB = 50  # Maximum file size in GB for processing
CHUNK_SIZE_KB = 128    # Chunk size for file reading in KB
MAX_WORKERS = 8        # Maximum parallel workers

# File Extensions
SAFE_MODEL_EXTENSIONS = {".safetensors", ".gguf", ".ggml"}
DANGEROUS_MODEL_EXTENSIONS = {".pt", ".pth", ".bin", ".pkl", ".pickle"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".txt", ".md"}
TOKENIZER_EXTENSIONS = {".json", ".model", ".txt", ".vocab"}

# Model File Patterns
MODEL_FILE_PATTERNS = [
    "*.safetensors", "*.gguf", "*.ggml", "*.bin", "*.pt", "*.pth",
    "*.h5", "*.onnx", "*.tflite", "*.json", "*.txt", "*.vocab", "*.model",
]

# Suspicious Patterns (shared across validators)
SUSPICIOUS_TOKEN_PATTERNS = {
    "code_injection": {
        "<script>", "</script>", "<iframe>", "</iframe>",
        "javascript:", "data:text/html", "<img src=",
        "eval(", "exec(", "system(", "import ", "__import__",
        "subprocess", "os.system", "shell", "cmd",
    },
    "prompt_injection": {
        "ignore previous", "forget instructions", "new task",
        "system:", "assistant:", "user:", "human:",
        "jailbreak", "roleplay", "pretend", "act as",
        "override", "bypass", "disable safety",
    },
    "hidden_tokens": {
        "<hidden>", "<secret>", "<backdoor>", "<trigger>",
        "<poison>", "<malicious>", "<exploit>", "<rce>",
        "\x00", "\x01", "\x02", "\x03",  # Null bytes and control chars
        "\ufeff", "\u200b", "\u200c", "\u200d",  # Zero-width chars
    },
    "encoding_manipulation": {
        "%3c", "%3e", "%22", "%27",  # URL encoded < > " '
        "&#60;", "&#62;", "&lt;", "&gt;",  # HTML entities
        "\\u003c", "\\u003e", "\\x3c", "\\x3e",  # Unicode escapes
        "\ud83c",  # Emoji ranges (can hide content)
    },
    "network_file": {
        "http://", "https://", "ftp://", "file://",
        "data:", "blob:", "filesystem:", "chrome://",
        "../", "..\\", "/etc/", "C:\\", "~/",
        "passwd", "shadow", "hosts", ".ssh",
    },
}

# Tensor Name Suspicious Patterns
SUSPICIOUS_TENSOR_PATTERNS = {
    "hidden_", "secret_", "backdoor_", "poison_", "malicious_",
    "inject_", "exploit_", "rce_", "shell_", "exec_",
    "__", "..", "//", "\\",  # Path traversal attempts
    "eval", "system", "import", "pickle",
}

# Model Family Patterns
MODEL_FAMILY_PATTERNS = {
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

# Architecture-specific Metadata Requirements
ARCH_REQUIRED_METADATA = {
    "llama": {
        "llama.context_length",
        "llama.embedding_length",
        "llama.block_count",
        "llama.attention.head_count",
        "llama.rope.dimension_count",
    },
    "mistral": {
        "mistral.context_length",
        "mistral.embedding_length",
        "mistral.block_count",
        "mistral.attention.head_count",
    },
    "gpt2": {
        "gpt2.context_length",
        "gpt2.embedding_length",
        "gpt2.block_count",
    },
    "bert": {
        "bert.max_position_embeddings",
        "bert.hidden_size",
        "bert.num_hidden_layers",
        "bert.num_attention_heads",
    },
}

# Quantization Constants
QUANTIZATION_TYPES = {
    "F32": {"name": "float32", "bytes": 4, "bits": 32, "safe": True},
    "F16": {"name": "float16", "bytes": 2, "bits": 16, "safe": True},
    "BF16": {"name": "bfloat16", "bytes": 2, "bits": 16, "safe": True},
    "Q4_0": {"name": "q4_0", "bytes": 0.5, "bits": 4, "safe": True},
    "Q4_1": {"name": "q4_1", "bytes": 0.5, "bits": 4, "safe": True},
    "Q5_0": {"name": "q5_0", "bytes": 0.625, "bits": 5, "safe": True},
    "Q5_1": {"name": "q5_1", "bytes": 0.625, "bits": 5, "safe": True},
    "Q8_0": {"name": "q8_0", "bytes": 1, "bits": 8, "safe": True},
    "Q8_1": {"name": "q8_1", "bytes": 1, "bits": 8, "safe": True},
    "I8": {"name": "int8", "bytes": 1, "bits": 8, "safe": True},
    "I4": {"name": "int4", "bytes": 0.5, "bits": 4, "safe": True},
}

# Validation Thresholds
VALIDATION_THRESHOLDS = {
    # File size thresholds
    "large_file_gb": 10,
    "very_large_file_gb": 50,

    # Tensor thresholds
    "max_tensor_count": 100000,
    "max_tensor_elements": 1000000000,  # 1B elements

    # Metadata thresholds
    "max_kv_count": 10000,
    "max_string_length": 10000,
    "max_array_length": 100000,

    # Security thresholds
    "min_signature_size": 64,
    "max_suspicious_tokens": 50,
    "confidence_threshold": 0.5,

    # Architecture thresholds
    "max_layers": 1000,
    "max_context_length": 1000000,  # 1M tokens
    "min_context_length": 512,

    # LoRA thresholds
    "max_lora_rank": 1024,
    "max_lora_alpha": 10000,
    "min_lora_rank": 1,
    "min_lora_alpha": 1,
}

# Registry Patterns for Provenance
REGISTRY_PATTERNS = {
    "docker_hub": r"^(?:docker\.io/)?([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
    "ghcr": r"^ghcr\.io/([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
    "huggingface": r"^huggingface\.co/([a-z0-9]+(?:[._-][a-z0-9]+)*)/([a-z0-9]+(?:[._-][a-z0-9]+)*)",
    "aws_ecr": r"^([0-9]{12})\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
    "gcp_gcr": r"^(?:gcr\.io|us\.gcr\.io|eu\.gcr\.io|asia\.gcr\.io)/([a-z0-9-]+)/([a-z0-9]+(?:[._-][a-z0-9]+)*):?([a-z0-9]+(?:[._-][a-z0-9]+)*)?$",
}

# Untrusted Source Patterns
UNTRUSTED_SOURCE_PATTERNS = {
    "domains": ["bit.ly", "tinyurl.com", "pastebin.com", "hastebin.com"],
    "file_services": ["mega.nz", "mediafire.com", "rapidshare.com"],
    "suspicious_usernames": ["anonymous", "temp", "test", "fake", "admin", "root"],
}

# Expected Tokenizer Files
EXPECTED_TOKENIZER_FILES = {
    "tokenizer.json",       # HuggingFace tokenizer
    "tokenizer.model",      # SentencePiece model
    "tokenizer_config.json", # Tokenizer configuration
    "added_tokens.json",    # Additional tokens
    "special_tokens_map.json", # Special token mappings
    "vocab.txt",            # Vocabulary (BERT-style)
    "vocab.json",           # Vocabulary JSON
    "merges.txt",            # BPE merges
}

# Executable Extensions (Security Risk)
EXECUTABLE_EXTENSIONS = {
    ".py", ".pyc", ".pyo", ".pyx", ".pyd",  # Python
    ".js", ".mjs", ".jsx", ".ts", ".tsx",   # JavaScript/TypeScript
    ".sh", ".bash", ".zsh", ".fish",        # Shell scripts
    ".bat", ".cmd", ".ps1",                 # Windows scripts
    ".exe", ".dll", ".so", ".dylib",        # Binaries
    ".jar", ".class",                       # Java
    ".rb", ".pl", ".php",                   # Other scripting
    ".wasm", ".wat",                         # WebAssembly
}

# Common Metadata File Patterns
METADATA_PATTERNS = {
    ".safetensors": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
    ".gguf": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
    ".pt": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md", "*.pkl"],
    ".pth": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md", "*.pkl"],
    ".h5": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
    ".onnx": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
}

# Digest Algorithms (ordered by security preference)
DIGEST_ALGORITHMS = ["sha512", "sha256", "sha1", "md5"]

# GGUF Constants
GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3
GGUF_VALUE_TYPES = {
    "UINT8": 0,
    "INT8": 1,
    "UINT16": 2,
    "INT16": 3,
    "UINT32": 4,
    "INT32": 5,
    "FLOAT32": 6,
    "BOOL": 7,
    "STRING": 8,
    "ARRAY": 9,
    "UINT64": 10,
    "INT64": 11,
    "FLOAT64": 12,
}

# Unicode Confusables Detection - Critical for preventing homograph attacks
UNICODE_CONFUSABLES = {
    # Cyrillic confusables (most common in attacks)
    "a": "a",  # U+0430 CYRILLIC SMALL LETTER A
    "e": "e",  # U+0435 CYRILLIC SMALL LETTER IE
    "o": "o",  # U+043E CYRILLIC SMALL LETTER O
    "p": "p",  # U+0440 CYRILLIC SMALL LETTER ER
    "c": "c",  # U+0441 CYRILLIC SMALL LETTER ES
    "y": "y",  # U+0443 CYRILLIC SMALL LETTER U
    "x": "x",  # U+0445 CYRILLIC SMALL LETTER HA
    "i": "i",  # U+0456 CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
    "j": "j",  # U+0458 CYRILLIC SMALL LETTER JE
    "s": "s",  # U+0455 CYRILLIC SMALL LETTER DZE

    # Capital Cyrillic confusables
    "A": "A",  # U+0410 CYRILLIC CAPITAL LETTER A
    "B": "B",  # U+0412 CYRILLIC CAPITAL LETTER VE
    "E": "E",  # U+0415 CYRILLIC CAPITAL LETTER IE
    "H": "H",  # U+041D CYRILLIC CAPITAL LETTER EN
    "K": "K",  # U+041A CYRILLIC CAPITAL LETTER KA
    "M": "M",  # U+041C CYRILLIC CAPITAL LETTER EM
    "O": "O",  # U+041E CYRILLIC CAPITAL LETTER O
    "P": "P",  # U+0420 CYRILLIC CAPITAL LETTER ER
    "C": "C",  # U+0421 CYRILLIC CAPITAL LETTER ES
    "T": "T",  # U+0422 CYRILLIC CAPITAL LETTER TE
    "X": "X",  # U+03B1 GREEK SMALL LETTER ALPHA
    "β": "b",  # U+03B3 GREEK SMALL LETTER GAMMA
    "δ": "d",  # U+03B4 GREEK SMALL LETTER DELTA
    "ε": "e",  # U+03B5 GREEK SMALL LETTER EPSILON
    "η": "n",  # U+03B9 GREEK SMALL LETTER IOTA
    "κ": "k",  # U+03BA GREEK SMALL LETTER KAPPA
    "μ": "u",  # U+03BC GREEK SMALL LETTER MU
    "v": "v",  # U+03BF GREEK SMALL LETTER OMICRON
    "π": "n",  # U+03C3 GREEK SMALL LETTER SIGMA
    "τ": "t",  # U+03C4 GREEK SMALL LETTER TAU
    "υ": "y",  # U+03C5 GREEK SMALL LETTER UPSILON
    "φ": "o",  # U+03C6 GREEK SMALL LETTER PHI
    "χ": "x",  # U+03C7 GREEK SMALL LETTER CHI
    "ω": "w",  # U+0395 GREEK CAPITAL LETTER EPSILON
    "Z": "Z",  # U+0397 GREEK CAPITAL LETTER ETA
    "Μ": "M",  # U+039C GREEK CAPITAL LETTER MU
    "N": "N",  # U+03A4 GREEK CAPITAL LETTER TAU
    "Y": "Y", "b": "b", "d": "d",  # Bold lowercase
    "f": "f", "g": "g", "h": "h",
    "k": "k", "l": "l", "𝐦": "m", "n": "n", "q": "q", "r": "r", "t": "t",
    "u": "u", "w": "w", "z": "z", "D": "D",  # Bold uppercase
    "F": "F", "G": "G", "J": "J", "L": "L", "Q": "Q", "R": "R", "S": "S",
    "U": "U", "V": "V", "W": "W", "𝑚": "m", "𝐈": "l", "𝚖": "m",  # U+0251 LATIN SMALL LETTER ALPHA
    "ᴀ": "a",  # U+1D00 LATIN LETTER SMALL CAPITAL A
    "ᴇ": "e",

    # Numerals confusables
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",  # Fullwidth digits
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "О": "0",  # Cyrillic O (often used to replace zero)
    "І": "1",  # Cyrillic I (used to replace one)
    "Ꮎ": "0",  # Greek Omicron

    # Common symbols confusables
    "-": "-",  # U+2013 EN DASH
    "—": "-",  # U+2014 EM DASH
    "―": "-",  # U+2212 MINUS SIGN
    "∣": "|",  # U+2223 DIVIDES
    "⏐": "|",  # U+23D0 VERTICAL LINE EXTENSION
    "|": "|",  # U+FF5C FULLWIDTH VERTICAL LINE

    # Bracket confusables
    "⟨": "<",  # U+27E8 MATHEMATICAL LEFT ANGLE BRACKET
    "⟩": ">",  # U+27E9 MATHEMATICAL RIGHT ANGLE BRACKET
    "<": "<",  # U+2039 SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    ">": ">",  # U+FF1E FULLWIDTH GREATER-THAN SIGN
}

# Dangerous Unicode ranges for additional detection
DANGEROUS_UNICODE_RANGES = [
    # Zero-width and invisible characters
    (0x200B, 0x200F, "zero_width_chars"),      # Zero width space, joiner, etc.
    (0x202A, 0x202E, "bidi_override_chars"),   # Bidirectional override
    (0x2060, 0x2064, "invisible_operators"),   # Word joiner, invisible operators
    (0xFE00, 0xFE0F, "variation_selectors"),   # Variation selectors
    (0xFEFF, 0xFEFF, "bom_char"),             # Byte order mark
    (0xFFF9, 0xFFFB, "interlinear_annotation"), # Annotation chars

    # Confusable ranges
    (0x0400, 0x04FF, "cyrillic"),             # Cyrillic
    (0x0370, 0x03FF, "greek"),                # Greek and Coptic
    (0x1D400, 0x1D7FF, "mathematical_alphanumeric"), # Math symbols
    (0xFF00, 0xFFEF, "halfwidth_fullwidth"),  # Halfwidth and Fullwidth Forms
    (0x1F100, 0x1F1FF, "enclosed_alphanumeric"), # Enclosed chars
]

# High-risk confusable patterns for ML tokens
HIGH_RISK_CONFUSABLE_PATTERNS = {
    "instruction_tokens": [
        # Common instruction/control tokens that could be spoofed
        "system", "user", "assistant", "human", "end", "start",
        "instruction", "prompt", "ignore", "forget", "bypass",
        "override", "disable", "enable", "execute", "eval",
    ],
    "special_tokens": [
        # Common special tokens in LLMs
        "bos", "eos", "pad", "unk", "cls", "sep", "mask",
        "endoftext", "startoftext", "im_start", "im_end",
    ],
    "security_keywords": [
        # Security-related terms that could be targeted
        "admin", "root", "sudo", "shell", "exec", "system",
        "import", "load", "open", "read", "write", "delete",
    ],
}

# Token Policy Rules - Critical for preventing malicious token injection
TOKEN_POLICY_RULES = {
    # Length constraints
    "max_token_length": 256,           # Maximum characters per token
    "max_special_token_length": 64,    # Stricter limit for special tokens
    "min_token_length": 1,             # Minimum token length

    # Character class rules
    "allowed_character_classes": {
        "alphanumeric": True,          # A-Z, a-z, 0-9
        "basic_punctuation": True,     # . , ; : ! ?
        "mathematical": False,         # Mathematical symbols (strict)
        "extended_punctuation": False, # Extended Unicode punctuation
        "control_characters": False,   # Control chars (always blocked)
        "private_use": False,          # Private use Unicode areas
    },

    # Special token format rules
    "special_token_patterns": {
        "angle_brackets": r"^<[^<>]*>$",           # <token>
        "pipe_brackets": r"^<\|[^|]*\|>$",        # <|token|>
        "square_brackets": r"^\[[^\[\]]*\]$",     # [token]
        "underscore_wrap": r"^_[^_]*_$",          # _token_
    },

    # Naming conventions
    "valid_token_naming": {
        "snake_case": r"^[a-z][a-z0-9_]*[a-z0-9]?$",
        "kebab_case": r"^[a-z][a-z0-9-]*[a-z0-9]?$",
        "camel_case": r"^[a-z][a-zA-Z0-9]*$",
        "pascal_case": r"^[A-Z][a-zA-Z0-9]*$",
    },
}

# Deny patterns for malicious content detection
TOKEN_DENY_PATTERNS = {
    # URL patterns (potential exfiltration/C2)
    "url_schemes": {
        r"https?://": "HTTP/HTTPS URL scheme",
        r"ftp://": "FTP URL scheme",
        r"file://": "File URL scheme",
        r"data:": "Data URL scheme",
        r"javascript:": "JavaScript URL scheme",
        r"vbscript:": "VBScript URL scheme",
        r"blob:": "Blob URL scheme",
        r"filesystem:": "Filesystem URL scheme",
    },

    # Shell command patterns
    "shell_commands": {
        r"\b(curl|wget|nc|netcat)\b": "Network utilities",
        r"\b(sh|bash|zsh|fish|cmd|powershell)\b": "Shell interpreters",
        r"\b(sudo|su|doas)\b": "Privilege escalation",
        r"\b(chmod|chown|rm|mv|cp)\b": "File system operations",
        r"\b(kill|killall|pkill)\b": "Process termination",
        r"\b(ps|top|htop|pgrep)\b": "Process monitoring",
        r"\b(cat|head|tail|less|more)\b": "File reading",
        r"\b(grep|awk|sed|sort|uniq)\b": "Text processing",
        r"\b(find|locate|which|whereis)\b": "File searching",
        r"\b(mount|umount|df|du)\b": "Filesystem operations",
    },

    # Code injection patterns
    "code_injection": {
        r"\beval\s*\(": "Code evaluation function",
        r"\bexec\s*\(": "Code execution function",
        r"\bsystem\s*\(": "System command execution",
        r"__import__\s*\(": "Dynamic import",
        r"\bcompile\s*\(": "Code compilation",
        r"subprocess\.(run|call|Popen)": "Subprocess execution",
        r"os\.(system|popen|spawn)": "OS command execution",
    },

    # File system access patterns
    "file_access": {
        r"/etc/passwd": "Password file access",
        r"/etc/shadow": "Shadow file access",
        r"/etc/hosts": "Hosts file access",
        r"\.ssh/": "SSH directory access",
        r"id_rsa": "SSH private key",
        r"\.aws/": "AWS credentials directory",
        r"\.env": "Environment file",
        r"config\.json": "Configuration file",
        r"/proc/": "Process information",
        r"/dev/": "Device files",
    },

    # Network patterns
    "network_activity": {
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b": "IP address",
        r"\b(?:[a-f0-9:]+:+)+[a-f0-9]+\b": "IPv6 address",
        r":\d{1,5}\b": "Port number",
        r"\.onion\b": "Tor hidden service",
        r"\blocalhost\b": "Local host reference",
        r"\b127\.0\.0\.1\b": "Loopback address",
    },

    # Encoding/obfuscation patterns
    "obfuscation": {
        r"base64": "Base64 encoding",
        r"\\x[0-9a-fA-F]{2}": "Hex encoding",
        r"\\u[0-9a-fA-F]{4}": "Unicode escape",
        r"\\[0-7]{1,3}": "Octal escape",
        r"%[0-9a-fA-F]{2}": "URL encoding",
        r"&#\d+;": "HTML entity encoding",
        r"&#x[0-9a-fA-F]+;": "HTML hex entity",
    },

    # Suspicious keywords
    "malicious_keywords": {
        r"\bmalware\b": "Malware reference",
        r"\bbackdoor\b": "Backdoor reference",
        r"\btrojan\b": "Trojan reference",
        r"\brootkit\b": "Rootkit reference",
        r"\bkeylogger\b": "Keylogger reference",
        r"\bransomware\b": "Ransomware reference",
        r"\bexploit\b": "Exploit reference",
        r"\bpayload\b": "Payload reference",
        r"\bshellcode\b": "Shellcode reference",
    },

    # Path traversal patterns
    "path_traversal": {
        r"\.\.\/": "Directory traversal (forward slash)",
        r"\.\.\\": "Directory traversal (backslash)",
        r"%2e%2e%2f": "URL encoded directory traversal",
        r"%2e%2e%5c": "URL encoded directory traversal (backslash)",
        r"\.\.%2f": "Mixed encoding directory traversal",
    },
}

# Character class validation patterns
CHARACTER_CLASS_PATTERNS = {
    "basic_latin": r"^[\x20-\x7E]*$",                    # ASCII printable
    "alphanumeric_only": r"^[a-zA-Z0-9]*$",             # Letters and digits only
    "alphanumeric_underscore": r"^[a-zA-Z0-9_]*$",      # Letters, digits, underscore
    "basic_punctuation": r"^[a-zA-Z0-9\s\.,;:!?]*$",    # Basic punctuation
    "no_control_chars": r"^[^\x00-\x1F\x7F-\x9F]*$",    # No control characters
    "safe_symbols": r"^[a-zA-Z0-9\s\.,;:!?\-_+=()\[\]{}]*$", # Safe symbols only
}

# Policy violation severity levels
POLICY_VIOLATION_SEVERITY = {
    # Critical violations (immediate block)
    "shell_commands": "critical",
    "code_injection": "critical",
    "file_access": "critical",
    "url_schemes": "high",
    "network_activity": "high",
    "malicious_keywords": "high",
    "obfuscation": "medium",
    "path_traversal": "high",

    # Length violations
    "excessive_length": "medium",
    "empty_token": "low",

    # Character class violations
    "invalid_characters": "medium",
    "control_characters": "high",
    "private_use_chars": "medium",
}

# Legitimate token exceptions (bypass deny patterns)
LEGITIMATE_TOKEN_EXCEPTIONS = {
    # Common ML/AI terms that might trigger false positives
    "ml_terms": {
        "eval", "evaluation", "exec_time", "execution_time",
        "import_module", "compile_model", "system_prompt",
        "base64_encoded", "url_encoding", "file_path",
    },

    # Special tokens that are legitimate
    "special_tokens": {
        "<pad>", "<unk>", "<s>", "</s>", "<bos>", "<eos>",
        "<cls>", "<sep>", "<mask>", "[PAD]", "[UNK]", "[CLS]",
        "[SEP]", "[MASK]", "<|endoftext|>", "<|startoftext|>",
        "<|im_start|>", "<|im_end|>", "<extra_id_0>", "<extra_id_1>",
    },

    # Technical terms
    "technical_terms": {
        "localhost", "127.0.0.1", "config.json", "base64",
        "subprocess", "import", "eval_metric", "exec_mode",
    },
}

# Default Logging Format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
