"""
GROMACS MDKit - A molecular dynamics preprocessing toolkit
"""

__version__ = "1.0.4"
__author__ = "Pengcheng Li"

from .gromacs import MDKit
from .cli import main

__all__ = ['MDKit', 'main']