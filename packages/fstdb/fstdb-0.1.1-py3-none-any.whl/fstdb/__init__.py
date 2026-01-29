"""
FSTDB - File System Database
A simple file-based database library for Python.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Core classes
from .db.tree_db import TreeDB
from .factory import DBFactory
from .tree import TreeNode
from .db.tools.viewer import TreeDBViewer

__all__ = [
    "TreeDB",
    "DBFactory",
    "TreeNode",
    "TreeDBViewer",
]
