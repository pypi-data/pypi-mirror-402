"""
getlibs

Python projeleri için dependency ve import analiz aracı.
"""

from .cli import analyze_project  # cli.py içindeki fonksiyonu import et

__all__ = ["analyze_project"]
