"""
SL-GME: Semantic-Load-Guided Model Evolution
"""

__version__ = "0.1.0"
__author__ = "Roberto Jimenez, DeepSeek Assistant"
__license__ = "Apache 2.0"

from . import semantic_load
from . import compression
from . import evolution
from . import utils

__all__ = ["semantic_load", "compression", "evolution", "utils"]
