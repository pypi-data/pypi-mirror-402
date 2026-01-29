"""Configuration and constants for the scanner."""

# Constants
DEFAULT_TIMEOUT = 300
DEFAULT_MEMORY_LIMIT = 16 * 1024 * 1024 * 1024  # 16GB
MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024  # 50GB
MAX_WORKERS = 8  # Maximum number of parallel workers

# Unsafe pickle opcodes
UNSAFE_OPCODES = {
    b"GLOBAL",  # can import any module + call functions
    b"REDUCE",  # executes callable
    b"BUILD",   # calls __setstate__
    b"INST",    # can instantiate arbitrary classes
    b"OBJ",     # can create arbitrary objects
    b"NEWOBJ",
    b"NEWTRUE",
    b"NEWFALSE",
    b"EXT1",
    b"EXT2",
    b"EXT4",
    b"PROTO",
    b"STOP",
}

# Extended whitelist for common ML frameworks
SAFE_MODULES = {
    # PyTorch
    "torch": {
        "Tensor", "tensor", "nn.Module", "nn.Linear", "nn.Conv2d", "nn.BatchNorm2d",
        "nn.ReLU", "nn.MaxPool2d", "nn.AdaptiveAvgPool2d", "nn.Dropout", "nn.Sequential",
        "nn.Conv1d", "nn.Conv3d", "nn.LSTM", "nn.GRU", "nn.RNN", "nn.Transformer",
        "nn.TransformerEncoder", "nn.TransformerDecoder", "nn.MultiheadAttention",
        "nn.Embedding", "nn.LayerNorm", "nn.BatchNorm1d", "nn.BatchNorm3d",
        "nn.LeakyReLU", "nn.ELU", "nn.SELU", "nn.GELU", "nn.Softmax", "nn.LogSoftmax",
        "nn.CrossEntropyLoss", "nn.MSELoss", "nn.BCELoss", "nn.BCEWithLogitsLoss",
    },
    "torch.nn.functional": {
        "relu", "leaky_relu", "elu", "selu", "gelu", "softmax", "log_softmax",
        "cross_entropy", "mse_loss", "bce_loss", "bce_with_logits_loss",
    },

    # TensorFlow/Keras
    "tensorflow": {
        "keras.Model", "keras.layers.Dense", "keras.layers.Conv2D",
        "keras.layers.MaxPooling2D", "keras.layers.Flatten", "keras.layers.Input",
        "keras.layers.Dropout", "keras.layers.BatchNormalization", "keras.layers.LSTM",
        "keras.layers.GRU", "keras.layers.Bidirectional", "keras.layers.TimeDistributed",
        "keras.layers.MultiHeadAttention", "keras.layers.LayerNormalization",
        "keras.layers.GlobalAveragePooling2D", "keras.layers.GlobalMaxPooling2D",
    },
    "tensorflow.keras.layers": {
        "Dense", "Conv2D", "MaxPooling2D", "Flatten", "Input", "Dropout",
        "BatchNormalization", "LSTM", "GRU", "Bidirectional", "TimeDistributed",
        "MultiHeadAttention", "LayerNormalization", "GlobalAveragePooling2D",
        "GlobalMaxPooling2D", "Conv1D", "Conv3D", "AveragePooling2D",
    },

    # Hugging Face Transformers
    "transformers": {
        "PreTrainedModel", "AutoModel", "AutoModelForSequenceClassification",
        "AutoModelForTokenClassification", "AutoModelForQuestionAnswering",
        "AutoModelForCausalLM", "AutoModelForSeq2SeqLM", "BertModel", "GPT2Model",
        "RobertaModel", "DistilBertModel", "T5Model", "BartModel",
    },
    "transformers.modeling_utils": {
        "PreTrainedModel", "Conv1D", "apply_chunking_to_forward",
    },

    # scikit-learn
    "sklearn": {
        "BaseEstimator", "TransformerMixin", "Pipeline", "StandardScaler",
        "RandomForestClassifier", "RandomForestRegressor", "SVC", "SVR",
        "GradientBoostingClassifier", "GradientBoostingRegressor", "XGBClassifier",
        "XGBRegressor", "LGBMClassifier", "LGBMRegressor", "KMeans", "DBSCAN",
        "IsolationForest", "OneClassSVM", "PCA", "TruncatedSVD", "NMF",
    },

    # ONNX
    "onnx": {
        "ModelProto", "NodeProto", "TensorProto", "GraphProto", "ValueInfoProto",
        "AttributeProto", "OperatorSetIdProto",
    },

    # Common data processing
    "numpy": {
        "ndarray", "array", "float64", "int64", "float32", "int32", "bool_",
        "zeros", "ones", "empty", "eye", "linspace", "arange", "random",
    },
    "pandas": {
        "DataFrame", "Series", "Index", "MultiIndex", "Categorical", "DatetimeIndex",
    },

    # Common utilities
    "collections": {"OrderedDict", "defaultdict", "Counter"},
    "typing": {"List", "Dict", "Tuple", "Optional", "Union", "Any", "Callable"},
    "dataclasses": {"dataclass", "field"},
    "abc": {"ABC", "abstractmethod"},
}

# Known vulnerable package versions
VULNERABLE_VERSIONS = {
    "tensorflow": ["<2.4.0"],
    "torch": ["<1.7.0"],
    "scikit-learn": ["<0.24.0"],
    "transformers": ["<4.0.0"],
    "onnx": ["<1.8.0"],
    "numpy": ["<1.19.0", ">=2.0.0"],
    "pandas": ["<1.2.0"],
}

# Chunk size for processing large files (1GB)
CHUNK_SIZE = 1024 * 1024 * 1024

# Threshold for using chunked processing (2GB)
CHUNKED_THRESHOLD = 2 * 1024 * 1024 * 1024

# Export all constants as a config object
class Config:
    """Configuration object containing all scanner constants."""

    def __init__(self) -> None:
        self.DEFAULT_TIMEOUT = DEFAULT_TIMEOUT
        self.DEFAULT_MEMORY_LIMIT = DEFAULT_MEMORY_LIMIT
        self.MAX_FILE_SIZE = MAX_FILE_SIZE
        self.UNSAFE_OPCODES = UNSAFE_OPCODES
        self.SAFE_MODULES = SAFE_MODULES
        self.VULNERABLE_VERSIONS = VULNERABLE_VERSIONS
        self.CHUNK_SIZE = CHUNK_SIZE
        self.CHUNKED_THRESHOLD = CHUNKED_THRESHOLD
        self.MAX_WORKERS = MAX_WORKERS

# Create a singleton config instance
config = Config()
