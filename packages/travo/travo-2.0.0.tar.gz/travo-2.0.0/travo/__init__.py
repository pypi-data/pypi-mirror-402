__version__ = "2.0.0"

try:
    from ._version import __version__
except ImportError:
    pass

from .gitlab import Forge, GitLab
from .assignment import Assignment
from .course import Course
from .homework import Homework

__all__ = ["Forge", "GitLab", "Assignment", "Course", "Homework", __version__]
