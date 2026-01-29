"""File operations with backup, diff, and lock support."""

from red9.files.backup import BackupManager
from red9.files.diff import generate_unified_diff, get_diff_stats
from red9.files.lock import FileAccessManager, FileLockTimeoutError, get_file_manager

__all__ = [
    "generate_unified_diff",
    "get_diff_stats",
    "BackupManager",
    "FileAccessManager",
    "FileLockTimeoutError",
    "get_file_manager",
]
