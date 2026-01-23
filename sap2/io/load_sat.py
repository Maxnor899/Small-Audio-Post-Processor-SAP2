"""
SAT Results Loader - sap2/io/load_sat.py

Loads and normalizes results.json from Small Audio Toolkit (SAT).
Provides a clean API for accessing measurements by method and channel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass


class SatLoadError(RuntimeError):
    """Raised when SAT results cannot be loaded or are invalid."""


@dataclass(frozen=True)
class AudioInfo:
    """Metadata about the analyzed audio file."""
    sample_rate: int
    channels: int
    duration: float
    frames: int
    format: str
    subtype: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioInfo:
        return cls(
            sample_rate=int(data.get('sample_rate', 44100)),
            channels=int(data.get('channels', 2)),
            duration=float(data.get('duration', 0.0)),
            frames=int(data.get('frames', 0)),
            format=str(data.get('format', 'unknown')),
            subtype=str(data.get('subtype', 'unknown'))
        )


class SatResults:
    """
    Normalized view of SAT results.json.
    
    Provides structured access to:
    - Metadata (sample rate, channels, duration)
    - Analysis results by method and channel
    - Available methods and channels
    
    Example:
        >>> sat = SatResults.load('path/to/results.json')
        >>> sat.sample_rate
        44100
        >>> sat.channels
        ['left', 'right', 'difference']
        >>> pulse_data = sat.get_method('pulse_detection', 'left')
        >>> pulse_data['num_pulses']
        19
    """
    
    def __init__(self, data: Dict[str, Any], source_path: Optional[Path] = None):
        """
        Initialize from parsed JSON data.
        
        Args:
            data: Parsed results.json content
            source_path: Optional path to the source file (for provenance)
        """
        self._data = data
        self._source_path = source_path
        
        # Extract main sections
        self._metadata = data.get('metadata', {})
        self._results = data.get('results', {})
        
        # Validate structure
        self._validate()
        
        # Build indices for fast lookup
        self._build_indices()
    
    @classmethod
    def load(cls, path: Path | str) -> SatResults:
        """
        Load SAT results from a file or directory.
        
        Args:
            path: Path to results.json or directory containing it
            
        Returns:
            SatResults instance
            
        Raises:
            SatLoadError: If file cannot be loaded or is invalid
        """
        path = Path(path)
        
        # If directory, look for results.json inside
        if path.is_dir():
            candidate = path / 'results.json'
            if not candidate.exists():
                raise SatLoadError(
                    f"Directory does not contain results.json: {path}"
                )
            path = candidate
        
        # Load JSON
        if not path.exists():
            raise SatLoadError(f"File does not exist: {path}")
        
        if not path.is_file():
            raise SatLoadError(f"Not a file: {path}")
        
        try:
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SatLoadError(f"Invalid JSON in {path}: {e}") from e
        except Exception as e:
            raise SatLoadError(f"Failed to read {path}: {e}") from e
        
        if not isinstance(data, dict):
            raise SatLoadError(f"Expected JSON object at root, got {type(data)}")
        
        return cls(data, source_path=path)
    
    def _validate(self) -> None:
        """Validate basic structure of results.json"""
        if 'metadata' not in self._data:
            raise SatLoadError("Missing required field: metadata")
        
        if 'results' not in self._data:
            raise SatLoadError("Missing required field: results")
        
        if not isinstance(self._results, dict):
            raise SatLoadError("'results' must be a dictionary")
        
        # Validate that each family is a list
        for family_name, family_data in self._results.items():
            if not isinstance(family_data, list):
                raise SatLoadError(
                    f"results.{family_name} must be a list, got {type(family_data)}"
                )
    
    def _build_indices(self) -> None:
        """Build internal indices for fast method lookup"""
        self._method_index: Dict[str, Dict[str, Any]] = {}
        
        # Index: method_name -> result entry
        for family_name, family_results in self._results.items():
            for result_entry in family_results:
                method = result_entry.get('method')
                if method:
                    self._method_index[method] = result_entry
    
    # ========================================================================
    # Properties - Metadata Access
    # ========================================================================
    
    @property
    def source_path(self) -> Optional[Path]:
        """Path to the source results.json file (if available)"""
        return self._source_path
    
    @property
    def timestamp(self) -> Optional[str]:
        """Timestamp when analysis was run (ISO format)"""
        return self._data.get('timestamp')
    
    @property
    def sample_rate(self) -> int:
        """Sample rate in Hz"""
        return self._metadata.get('sample_rate', 44100)
    
    @property
    def channels(self) -> List[str]:
        """List of analyzed channels (e.g. ['left', 'right', 'difference'])"""
        return self._metadata.get('channels', ['left', 'right'])
    
    @property
    def duration(self) -> float:
        """Duration of audio in seconds"""
        audio_info = self._metadata.get('audio_info', {})
        return audio_info.get('duration', 0.0)
    
    @property
    def audio_info(self) -> AudioInfo:
        """Structured audio metadata"""
        audio_info_dict = self._metadata.get('audio_info', {})
        return AudioInfo.from_dict(audio_info_dict)
    
    @property
    def audio_file(self) -> Optional[str]:
        """Original audio file path (as recorded by SAT)"""
        return self._metadata.get('audio_file')
    
    @property
    def config_version(self) -> str:
        """SAT config version"""
        return self._metadata.get('config_version', 'unknown')
    
    @property
    def preprocessing(self) -> Dict[str, Any]:
        """Preprocessing settings used"""
        return self._metadata.get('preprocessing', {})
    
    # ========================================================================
    # Methods - Analysis Access
    # ========================================================================
    
    def get_method(
        self,
        method_name: str,
        channel: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get measurements for a specific method and channel.
        
        Args:
            method_name: Name of analysis method (e.g. 'pulse_detection')
            channel: Channel name (e.g. 'left'). If None, returns all channels.
            
        Returns:
            Measurements dict for the channel, or None if not found
            
        Example:
            >>> sat.get_method('pulse_detection', 'left')
            {'num_pulses': 19, 'pulse_positions': [20, 2360, ...], ...}
        """
        result_entry = self._method_index.get(method_name)
        
        if result_entry is None:
            return None
        
        measurements = result_entry.get('measurements', {})
        
        if channel is None:
            return measurements
        else:
            return measurements.get(channel)
    
    def get_method_metrics(self, method_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics (parameters) used for a method.
        
        Args:
            method_name: Name of analysis method
            
        Returns:
            Metrics dict or None
            
        Example:
            >>> sat.get_method_metrics('pulse_detection')
            {'threshold': 0.6, 'min_distance': 2000}
        """
        result_entry = self._method_index.get(method_name)
        
        if result_entry is None:
            return None
        
        return result_entry.get('metrics')
    
    def has_method(self, method_name: str) -> bool:
        """
        Check if a method was run.
        
        Args:
            method_name: Name of analysis method
            
        Returns:
            True if method is present in results
        """
        return method_name in self._method_index
    
    def list_methods(self) -> List[str]:
        """
        List all methods that were run.
        
        Returns:
            List of method names
        """
        return list(self._method_index.keys())
    
    def list_methods_by_family(self) -> Dict[str, List[str]]:
        """
        List methods grouped by family.
        
        Returns:
            Dict mapping family name to list of method names
            
        Example:
            >>> sat.list_methods_by_family()
            {
                'temporal': ['envelope', 'autocorrelation', 'pulse_detection'],
                'spectral': ['fft_global', 'peak_detection'],
                ...
            }
        """
        families: Dict[str, List[str]] = {}
        
        for family_name, family_results in self._results.items():
            methods = []
            for result_entry in family_results:
                method = result_entry.get('method')
                if method:
                    methods.append(method)
            if methods:
                families[family_name] = methods
        
        return families
    
    def get_all_for_channel(self, channel: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all measurements for a specific channel.
        
        Args:
            channel: Channel name
            
        Returns:
            Dict mapping method_name -> measurements
            
        Example:
            >>> left_data = sat.get_all_for_channel('left')
            >>> left_data['pulse_detection']['num_pulses']
            19
        """
        result = {}
        
        for method_name in self._method_index.keys():
            measurements = self.get_method(method_name, channel)
            if measurements is not None:
                result[method_name] = measurements
        
        return result
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_available_channels_for_method(self, method_name: str) -> Set[str]:
        """
        Get which channels have data for a specific method.
        
        Args:
            method_name: Name of analysis method
            
        Returns:
            Set of channel names that have measurements
        """
        result_entry = self._method_index.get(method_name)
        
        if result_entry is None:
            return set()
        
        measurements = result_entry.get('measurements', {})
        return set(measurements.keys())
    
    def summary(self) -> Dict[str, Any]:
        """
        Generate a summary of available data.
        
        Returns:
            Dict with summary statistics
        """
        return {
            'source_path': str(self._source_path) if self._source_path else None,
            'timestamp': self.timestamp,
            'sample_rate': self.sample_rate,
            'duration': self.duration,
            'channels': self.channels,
            'num_methods': len(self._method_index),
            'methods': self.list_methods(),
            'families': list(self._results.keys())
        }
    
    def __repr__(self) -> str:
        return (
            f"SatResults("
            f"methods={len(self._method_index)}, "
            f"channels={len(self.channels)}, "
            f"duration={self.duration:.2f}s"
            f")"
        )


# ============================================================================
# Validation helpers
# ============================================================================

def validate_sat_results(path: Path | str) -> tuple[bool, Optional[str]]:
    """
    Validate a SAT results.json file without fully loading it.
    
    Args:
        path: Path to results.json
        
    Returns:
        (is_valid, error_message) tuple
    """
    try:
        SatResults.load(path)
        return (True, None)
    except SatLoadError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Unexpected error: {e}")