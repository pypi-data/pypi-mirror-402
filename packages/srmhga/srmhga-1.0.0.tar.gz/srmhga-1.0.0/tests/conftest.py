"""Pytest configuration - adds src to Python path."""
import sys
from pathlib import Path

# src klasörünü Python path'e ekle
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
