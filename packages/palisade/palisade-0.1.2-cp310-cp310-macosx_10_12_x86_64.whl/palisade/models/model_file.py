"""ModelFile abstraction for streaming validation.

This module provides the ModelFile class for memory-efficient processing of ML models.
"""

import hashlib
import json
import logging
import os
import struct
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from .metadata import ModelMetadata, ModelType
from .types import ChunkInfo

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a model file."""
    
    path: Path
    size_bytes: int
    modified_time: float
    is_symlink: bool = False
    is_git_lfs: bool = False
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON-serializable values."""
        return {
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "modified_time": self.modified_time,
            "is_symlink": self.is_symlink,
            "is_git_lfs": self.is_git_lfs,
        }


@dataclass
class GitLFSInfo:
    """Information about Git LFS pointer files."""
    
    version: str
    oid: str
    size: int
    
    @classmethod
    def from_pointer_content(cls, content: str) -> Optional["GitLFSInfo"]:
        """Parse Git LFS pointer file content."""
        lines = content.strip().split('\n')
        info = {}
        
        for line in lines:
            if ' ' in line:
                key, value = line.split(' ', 1)
                info[key] = value
        
        if 'version' in info and 'oid' in info and 'size' in info:
            return cls(
                version=info['version'],
                oid=info['oid'],
                size=int(info['size'])
            )
        return None


class ModelFile:
    """Abstraction for ML model files with streaming support."""
    
    def __init__(
        self,
        file_path: Union[str, Path],
        max_memory_mb: int = 512,
        chunk_size: int = 1024 * 1024,
        resolve_git_lfs: bool = False
    ):
        """Initialize ModelFile.
        
        Args:
            file_path: Path to the model file
            max_memory_mb: Maximum memory usage for streaming
            chunk_size: Size of chunks for streaming (bytes)
            resolve_git_lfs: Whether to resolve Git LFS pointer files
        """
        self.file_path = Path(file_path)
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.resolve_git_lfs = resolve_git_lfs
        
        # Initialize file info
        self._file_info: Optional[FileInfo] = None
        self._format: Optional[ModelType] = None
        self._metadata: Optional[ModelMetadata] = None
        self._git_lfs_info: Optional[GitLFSInfo] = None
        self._context: Dict[str, Any] = {}
        
        # File handle for streaming
        self._file_handle: Optional[Any] = None
        
        # Initialize file information
        self._initialize_file_info()
    
    def _initialize_file_info(self) -> None:
        """Initialize file information."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        stat = self.file_path.stat()
        self._file_info = FileInfo(
            path=self.file_path,
            size_bytes=stat.st_size,
            modified_time=stat.st_mtime,
            is_symlink=self.file_path.is_symlink()
        )
        
        # Check if this is a Git LFS pointer file
        if self._is_git_lfs_pointer():
            self._file_info.is_git_lfs = True
            if self.resolve_git_lfs:
                self._resolve_git_lfs()
        
        # Detect format
        self._format = self._detect_format()
    
    def _is_git_lfs_pointer(self) -> bool:
        """Check if file is a Git LFS pointer."""
        if self._file_info.size_bytes > 1024:  # LFS pointers are small
            return False
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content.startswith('version https://git-lfs.github.com/spec/')
        except (UnicodeDecodeError, IOError):
            return False
    
    def _resolve_git_lfs(self) -> None:
        """Resolve Git LFS pointer to actual file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self._git_lfs_info = GitLFSInfo.from_pointer_content(content)
            
            # For now, we'll just log that this is an LFS file
            # In a real implementation, you'd resolve the LFS pointer
            logger.warning(f"Git LFS file detected but not resolved: {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to resolve Git LFS pointer: {e}")
    
    def _detect_format(self) -> ModelType:
        """Detect model format from file extension and content."""
        suffix = self.file_path.suffix.lower()
        
        # Map file extensions to model types
        extension_map = {
            '.safetensors': ModelType.SAFETENSORS,
            '.gguf': ModelType.GGUF,
            '.bin': ModelType.PYTORCH,
            '.pt': ModelType.PYTORCH,
            '.pth': ModelType.PYTORCH,
            '.pkl': ModelType.PICKLE,
            '.pickle': ModelType.PICKLE,
            '.onnx': ModelType.ONNX,
            '.h5': ModelType.TENSORFLOW,
        }
        
        if suffix in extension_map:
            return extension_map[suffix]
        
        # Check if JSON file is tokenizer-related
        if suffix == '.json':
            filename_lower = self.file_path.name.lower()
            # Tokenizer-related JSON files
            tokenizer_patterns = [
                'tokenizer', 'vocab', 'merges', 'special_tokens',
                'added_tokens', 'token', 'sentencepiece'
            ]
            if any(pattern in filename_lower for pattern in tokenizer_patterns):
                return ModelType.TOKENIZER
            # Config files might also be relevant
            if 'config' in filename_lower:
                return ModelType.TOKENIZER
        
        # Try to detect from content for ambiguous cases
        try:
            with open(self.file_path, 'rb') as f:
                header = f.read(1024)
                
                # GGUF magic number
                if header.startswith(b'GGUF'):
                    return ModelType.GGUF
                
                # SafeTensors magic
                if len(header) >= 8:
                    try:
                        header_size = struct.unpack('<Q', header[:8])[0]
                        if header_size < len(header) and header_size > 0:
                            return ModelType.SAFETENSORS
                    except struct.error:
                        pass
                
                # Pickle magic
                if header.startswith(b'\x80\x03'):
                    return ModelType.PICKLE
        
        except Exception:
            pass
        
        return ModelType.UNKNOWN
    
    @property
    def file_info(self) -> FileInfo:
        """Get file information."""
        return self._file_info
    
    @property
    def format(self) -> Optional[ModelType]:
        """Get detected model format."""
        return self._format
    
    @property
    def size_bytes(self) -> int:
        """Get file size in bytes."""
        return self._file_info.size_bytes
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self._file_info.size_mb
    
    @property
    def is_git_lfs_pointer(self) -> bool:
        """Check if this is a Git LFS pointer file."""
        return self._file_info.is_git_lfs
    
    @property
    def git_lfs_info(self) -> Optional[GitLFSInfo]:
        """Get Git LFS information if available."""
        return self._git_lfs_info
    
    def should_stream(self) -> bool:
        """Determine if file should be streamed based on size."""
        return self.size_mb > self.max_memory_mb
    
    def get_metadata(self) -> ModelMetadata:
        """Get or create model metadata."""
        if self._metadata is None:
            self._metadata = self._extract_metadata()
        return self._metadata
    
    def _extract_metadata(self) -> ModelMetadata:
        """Extract metadata from the model file."""
        # Basic metadata based on file info
        metadata = ModelMetadata(
            model_type=self._format or ModelType.UNKNOWN,
            framework_version="unknown",
            num_parameters=None,
            input_shape=None,
            output_shape=None,
            architecture=None,
            is_quantized=False,
            is_distributed=False,
        )
        
        # Try to extract more specific metadata based on format
        try:
            if self._format == ModelType.SAFETENSORS:
                metadata = self._extract_safetensors_metadata(metadata)
            elif self._format == ModelType.GGUF:
                metadata = self._extract_gguf_metadata(metadata)
        except Exception as e:
            logger.debug(f"Failed to extract detailed metadata: {e}")
        
        return metadata
    
    def _extract_safetensors_metadata(self, base_metadata: ModelMetadata) -> ModelMetadata:
        """Extract metadata from SafeTensors file."""
        try:
            with open(self.file_path, 'rb') as f:
                # Read header size
                header_size_bytes = f.read(8)
                header_size = struct.unpack('<Q', header_size_bytes)[0]
                
                # Read header
                header_bytes = f.read(header_size)
                header = json.loads(header_bytes.decode('utf-8'))
                
                # Extract metadata if available
                if '__metadata__' in header:
                    metadata_dict = header['__metadata__']
                    base_metadata.framework_version = metadata_dict.get('framework', 'unknown')
                    base_metadata.architecture = metadata_dict.get('architecture')
                    
                    # Try to estimate parameters from tensor shapes
                    total_params = 0
                    for key, tensor_info in header.items():
                        if key != '__metadata__' and isinstance(tensor_info, dict):
                            if 'shape' in tensor_info:
                                shape = tensor_info['shape']
                                if shape:
                                    param_count = 1
                                    for dim in shape:
                                        param_count *= dim
                                    total_params += param_count
                    
                    if total_params > 0:
                        base_metadata.num_parameters = total_params
        
        except Exception as e:
            logger.debug(f"Failed to extract SafeTensors metadata: {e}")
        
        return base_metadata
    
    def _extract_gguf_metadata(self, base_metadata: ModelMetadata) -> ModelMetadata:
        """Extract metadata from GGUF file."""
        try:
            with open(self.file_path, 'rb') as f:
                # Skip GGUF magic and version
                f.seek(8)
                
                # This is a simplified implementation
                # Real GGUF parsing would be more complex
                base_metadata.framework_version = "gguf"
                base_metadata.is_quantized = True  # GGUF files are typically quantized
        
        except Exception as e:
            logger.debug(f"Failed to extract GGUF metadata: {e}")
        
        return base_metadata
    
    def set_context(self, key: str, value: Any) -> None:
        """Set context value."""
        self._context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value."""
        return self._context.get(key, default)
    
    def iter_chunks(self, chunk_size: Optional[int] = None) -> Iterator[bytes]:
        """Iterate over file chunks (raw bytes).
        
        For streaming validation with metadata, use iter_chunk_info() instead.
        """
        chunk_size = chunk_size or self.chunk_size
        
        with open(self.file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def iter_chunk_info(self, chunk_size: Optional[int] = None) -> Iterator[ChunkInfo]:
        """Iterate over file chunks with metadata (offset, size, index).
        
        This is useful for streaming validation where validators need to know
        the offset of each chunk in the file.
        
        Args:
            chunk_size: Size of each chunk in bytes (default: self.chunk_size)
            
        Yields:
            ChunkInfo objects containing chunk data, offset, size, and index
        """
        chunk_size = chunk_size or self.chunk_size
        offset = 0
        chunk_index = 0
        last_chunk = None
        
        with open(self.file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                chunk_info = ChunkInfo(
                    data=chunk,
                    offset=offset,
                    size=len(chunk),
                    chunk_index=chunk_index,
                    is_final=False
                )
                
                # Yield previous chunk if exists
                if last_chunk is not None:
                    yield last_chunk
                
                last_chunk = chunk_info
                offset += len(chunk)
                chunk_index += 1
        
        # Mark and yield the last chunk as final
        if last_chunk is not None:
            last_chunk.is_final = True
            yield last_chunk
    
    def read_range(self, offset: int, size: int) -> bytes:
        """Read a specific range of bytes from the file."""
        with open(self.file_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)
    
    def read_header(self, size: int = 1024, max_header_size: Optional[int] = None) -> bytes:
        """Read the file header."""
        if max_header_size is not None:
            size = min(size, max_header_size)
        return self.read_range(0, size)
    
    def read_safetensors_header(self) -> bytes:
        """Read the complete SafeTensors header (8-byte size + JSON header).
        
        SafeTensors format:
        - Bytes 0-7: Little-endian u64 header size (N)
        - Bytes 8-(8+N): JSON header
        - Bytes (8+N)+: Tensor data
        
        Returns:
            Complete header data including the 8-byte size prefix and JSON header
            
        Raises:
            ValueError: If header size is invalid or exceeds file size
        """
        file_size = self._file_info.size_bytes
        
        # Read first 8 bytes to get header size
        size_bytes = self.read_range(0, 8)
        
        if len(size_bytes) < 8:
            raise ValueError(f"File too small to be valid SafeTensors: {len(size_bytes)} bytes")
        
        # Parse header size (little-endian u64)
        header_size = struct.unpack('<Q', size_bytes)[0]
        
        # Validate header size against actual file size
        if header_size == 0:
            raise ValueError("Invalid SafeTensors header size: 0")
        
        if header_size > file_size - 8:
            raise ValueError(
                f"Invalid SafeTensors header: claimed size {header_size} exceeds file size {file_size - 8} "
                "(file may be corrupted or malicious)"
            )
        
        # Read complete header: 8 bytes (size) + header_size bytes (JSON)
        total_bytes_to_read = 8 + header_size
        return self.read_range(0, total_bytes_to_read)
    
    def estimate_streaming_memory_usage(self, num_validators: int = 1) -> Dict[str, Any]:
        """Estimate memory usage for streaming validation."""
        chunk_memory_mb = (self.chunk_size * num_validators) / (1024 * 1024)
        overhead_mb = 50  # Estimated overhead
        
        return {
            "estimated_memory_mb": chunk_memory_mb + overhead_mb,
            "chunk_size_mb": self.chunk_size / (1024 * 1024),
            "num_validators": num_validators,
            "overhead_mb": overhead_mb,
        }
    
    def __enter__(self) -> "ModelFile":
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


def create_model_file(
    file_path: Union[str, Path],
    max_memory_mb: int = 512,
    chunk_size: int = 1024 * 1024,
    resolve_git_lfs: bool = False
) -> ModelFile:
    """Create a ModelFile instance.
    
    Args:
        file_path: Path to the model file
        max_memory_mb: Maximum memory usage for streaming
        chunk_size: Size of chunks for streaming (bytes)
        resolve_git_lfs: Whether to resolve Git LFS pointer files
    
    Returns:
        ModelFile instance
    """
    return ModelFile(
        file_path=file_path,
        max_memory_mb=max_memory_mb,
        chunk_size=chunk_size,
        resolve_git_lfs=resolve_git_lfs
    )
