"""
These are the values directly exported
"""

from .core import Interpreter, protein_comp

"That export is needed for external modules that wish to have a type hint"
from .import_modules import ModuleEnvironment