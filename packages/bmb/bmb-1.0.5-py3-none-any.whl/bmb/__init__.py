"""
BMB - Backend Framework utilisant BMDB ORM
"""

__version__ = "1.0.2"
__author__ = "BM Framework"

from .app import create_app
from .models_loader import load_models

__all__ = ['create_app', 'load_models']