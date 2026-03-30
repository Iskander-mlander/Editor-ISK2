"""
Git Feature
==========
Git integration for the editor with real subprocess implementation.
"""

from features.git.client import GitClient, GitSignals, GitFileStatus, GitCommit, GitBranch

__all__ = [
    "GitClient",
    "GitSignals", 
    "GitFileStatus",
    "GitCommit",
    "GitBranch",
]