"""
Utility for selecting the best available video encoder (GPU or CPU fallback).
"""
import os
import sys
import logging
from typing import List, Tuple
from .PlatformDetector import PlatformDetector

logger = logging.getLogger(__name__)


class EncoderSelector:
    """Selects optimal video encoder based on available hardware."""
    
    _platform = PlatformDetector()
    
    @classmethod
    def get_encoder_args(cls, force_cpu: bool = False) -> Tuple[List[str], str]:
        """
        Get FFmpeg encoder arguments.
        
        Args:
            force_cpu: Force CPU encoding even if GPU is available
            
        Returns:
            Tuple of (encoder_args_list, encoder_name)
        """
        if force_cpu:
            return cls._get_cpu_encoder()
        
        # Check environment variable override
        force_encoder = os.environ.get("RTMP_ENCODER", "").lower()
        
        if force_encoder == "cpu" or force_encoder == "libx264":
            return cls._get_cpu_encoder()
        elif force_encoder == "nvenc":
            return cls._get_nvenc_encoder()
        
        # Jetson platform
        if cls._platform.is_jetson():
            return cls._get_jetson_encoder()
        
        # macOS
        if sys.platform == "darwin":
            return cls._get_videotoolbox_encoder()
        
        # NVIDIA GPU
        if cls._has_nvidia_gpu():
            return cls._get_nvenc_encoder()
        
        # Fallback to CPU
        return cls._get_cpu_encoder()
    
    @staticmethod
    def _has_nvidia_gpu() -> bool:
        """Check if NVIDIA GPU is available."""
        return (
            os.environ.get("NVIDIA_VISIBLE_DEVICES") is not None or
            os.path.exists("/proc/driver/nvidia/version")
        )
    
    @staticmethod
    def _get_cpu_encoder() -> Tuple[List[str], str]:
        """Get CPU encoder (libx264) with optimized settings."""
        return [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-profile:v", "main",
        ], "libx264"
    
    @staticmethod
    def _get_nvenc_encoder() -> Tuple[List[str], str]:
        """Get NVIDIA NVENC encoder with GPU-optimized settings."""
        return [
            "-c:v", "h264_nvenc",
            "-preset", "p1",  # p1 = fastest preset
            "-tune", "ull",  # ultra-low latency
            "-rc:v", "cbr",  # constant bitrate
            "-rc-lookahead", "0",  # disable lookahead for lower latency
            "-delay", "0",  # zero delay
            "-zerolatency", "1",  # zero latency mode
            "-profile:v", "main",
            "-gpu", "0",  # Use first GPU
        ], "h264_nvenc"
    
    @staticmethod
    def _get_jetson_encoder() -> Tuple[List[str], str]:
        """Get Jetson-optimized NVENC encoder."""
        return [
            "-c:v", "h264_nvenc",
            "-preset", "p1",
            "-tune", "ull",
            "-rc:v", "cbr",
            "-rc-lookahead", "0",
            "-delay", "0",
            "-zerolatency", "1",
            "-profile:v", "main",
        ], "h264_nvenc"
    
    @staticmethod
    def _get_videotoolbox_encoder() -> Tuple[List[str], str]:
        """Get macOS VideoToolbox encoder."""
        return [
            "-c:v", "h264_videotoolbox",
            "-profile:v", "main",
            "-realtime", "1",
        ], "h264_videotoolbox"
