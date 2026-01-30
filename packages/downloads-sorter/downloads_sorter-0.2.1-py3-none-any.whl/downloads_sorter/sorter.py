#!/usr/bin/env python3
"""
Main module for the downloads_sorter package.
Contains functions for sorting files in the downloads directory.
"""

import logging
import shutil
from collections import Counter
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('downloads_sorter')


def get_downloads_dir() -> Path:
    """Get the user's downloads directory path."""
    return Path.home() / "Downloads"

# Define file extensions and their corresponding folders
FILE_TYPES = {
    # Documents
    ".pdf": "_pdf",
    ".docx": "_docx",
    ".doc": "_docx",
    ".xlsx": "_xlsx",
    ".xls": "_xlsx",
    ".csv": "_csv",
    ".md": "_md",
    ".txt": "_txt",
    ".html": "_html",
    ".htm": "_html",
    ".rtf": "_txt",
    
    # Images
    ".png": "_png",
    ".jpg": "_jpeg",
    ".jpeg": "_jpeg",
    ".svg": "_svg",
    ".webp": "_webp",
    ".gif": "_png",
    ".bmp": "_png",
    ".tiff": "_png",
    ".ico": "_png",
    
    # Media
    ".mp3": "_mp3",
    ".mp4": "_mp4",
    ".wav": "_mp3",
    ".avi": "_mp4",
    ".mov": "_mp4",
    ".mkv": "_mp4",
    ".flac": "_mp3",
    ".m3u": "_m3u",
    
    # Archives
    ".zip": "_zip",
    ".rar": "_zip",
    ".7z": "_zip",
    ".tar": "_zip",
    ".gz": "_zip",
    
    # Presentations and design
    ".pptx": "_pptx",
    ".ppt": "_pptx",
    ".key": "_key",
    ".ai": "_misc",
    ".psd": "_misc",
    ".sketch": "_misc",
    
    # Code and development
    ".py": "_py",
    ".js": "_code",
    ".java": "_code",
    ".c": "_code",
    ".cpp": "_code",
    ".h": "_code",
    ".cs": "_code",
    ".php": "_code",
    ".rb": "_code",
    ".go": "_code",
    ".ts": "_code",
    ".json": "_code",
    ".xml": "_code",
    ".yaml": "_code",
    ".yml": "_code",
    ".sql": "_code",
}

# Define name patterns for special categories
SPECIAL_PATTERNS = {
    # Receipts and invoices
    ("rechnung", "invoice", "quittung", "receipt", "db_rechnung", "_kv-"): "_receipts",

    # Contracts
    ("vertrag", "contract", "vereinbarung", "agreement", "datenschutz", "avv"): "_contracts",

    # Calendar and meetings
    ("calendar", ".ics", "meeting", "conference"): "_meetings",

    # Applications
    (".dmg", ".app", ".exe", ".msi", ".deb", ".rpm", ".pkg"): "_applications",

    # Projects
    ("project", "projekt", "roadmap", "business-model", "projektauftrag"): "_projects",

    # Screenshots
    ("screenshot", "bildschirmfoto", "screen capture"): "_screenshots",
}

# Files to skip during sorting
SKIP_FILES = {'.DS_Store', '.localized', 'sort_downloads.py', 'README_SORT.md'}


def ensure_dir_exists(directory: Path) -> Path:
    """Ensure that a directory exists, creating it if necessary."""
    directory = Path(directory)
    if not directory.exists():
        directory.mkdir(parents=True)
        logger.info(f"Created directory: {directory}")
    return directory


def get_unique_path(target_path: Path) -> Path:
    """Get a unique path for a file by appending a number if the file already exists."""
    target_path = Path(target_path)
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1
    while (parent / f"{stem}({counter}){suffix}").exists():
        counter += 1
    return parent / f"{stem}({counter}){suffix}"


def _move_file_to_folder(
    file_path: Path,
    file_name: str,
    folder: str,
    downloads_dir: Path,
    dry_run: bool
) -> Optional[Path]:
    """
    Move a file to the specified folder within downloads_dir.

    Returns the new path on success, None on error.
    """
    target_dir = ensure_dir_exists(downloads_dir / folder)
    target_path = get_unique_path(target_dir / file_name)

    if dry_run:
        logger.info(f"Would move {file_name} to {folder}/")
        return target_path

    try:
        shutil.move(str(file_path), str(target_path))
        logger.info(f"Moved {file_name} to {folder}/")
        return target_path
    except Exception as e:
        logger.error(f"Error moving {file_name}: {e}")
        return None


def sort_file(
    file_path: str,
    downloads_dir: Optional[Path] = None,
    dry_run: bool = False
) -> Optional[Path]:
    """
    Sort a file into the appropriate folder based on its extension or name.

    Priority: special patterns > file extension > _misc fallback.

    Parameters:
        file_path: The path to the file to be sorted
        downloads_dir: The downloads directory. If None, auto-detected.
        dry_run: If True, don't actually move files, just log what would happen.

    Returns:
        The new location of the file, or None if the file was not moved.
    """
    file_path = Path(file_path)

    if not file_path.is_file():
        logger.warning(f"Not a file: {file_path}")
        return None

    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
    downloads_dir = Path(downloads_dir)

    file_name = file_path.name

    # Skip hidden files and system files
    if file_name.startswith('.') or file_name in SKIP_FILES:
        logger.debug(f"Skipping file: {file_name}")
        return None

    file_name_lower = file_name.lower()
    extension = file_path.suffix.lower()

    # Check special patterns first
    for patterns, folder in SPECIAL_PATTERNS.items():
        if any(pattern.lower() in file_name_lower for pattern in patterns):
            return _move_file_to_folder(file_path, file_name, folder, downloads_dir, dry_run)

    # Check by file extension
    folder = FILE_TYPES.get(extension, "_misc")
    return _move_file_to_folder(file_path, file_name, folder, downloads_dir, dry_run)


def sort_downloads(
    downloads_dir: Optional[Path] = None,
    dry_run: bool = False
) -> dict:
    """
    Sort all files in the downloads directory.

    Parameters:
        downloads_dir: The downloads directory. If None, auto-detected.
        dry_run: If True, don't actually move files, just log what would happen.

    Returns:
        A summary dict with counts: processed, moved, errors, skipped.
    """
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
    downloads_dir = Path(downloads_dir)

    logger.info(f"Sorting files in {downloads_dir}...")

    result = {"processed": 0, "moved": 0, "errors": 0, "skipped": 0}

    try:
        files = [f for f in downloads_dir.iterdir() if f.is_file()]
    except Exception as e:
        logger.error(f"Error listing directory {downloads_dir}: {e}")
        return result

    for file_path in files:
        result["processed"] += 1
        new_path = sort_file(file_path, downloads_dir, dry_run)
        if new_path:
            result["moved"] += 1
        else:
            result["skipped"] += 1

    logger.info(
        f"Done sorting files! "
        f"Processed: {result['processed']}, Moved: {result['moved']}, "
        f"Errors: {result['errors']}, Skipped: {result['skipped']}"
    )
    return result


def get_stats(downloads_dir: Optional[Path] = None) -> dict:
    """
    Get statistics about the downloads directory organization.

    Returns:
        A dictionary with statistics: total_files, organized_files,
        unorganized_files, folders (counts per folder), file_types (counts per extension).
    """
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
    downloads_dir = Path(downloads_dir)

    stats = {
        "total_files": 0,
        "organized_files": 0,
        "unorganized_files": 0,
        "folders": {},
        "file_types": Counter()
    }

    # Count files in top level (unorganized)
    top_files = [f for f in downloads_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    stats["unorganized_files"] = len(top_files)
    stats["total_files"] += len(top_files)

    # Count files in subdirectories (organized)
    for item_path in downloads_dir.iterdir():
        if not item_path.is_dir() or item_path.name.startswith('.'):
            continue

        try:
            folder_files = [f for f in item_path.iterdir() if f.is_file() and not f.name.startswith('.')]
            file_count = len(folder_files)

            stats["folders"][item_path.name] = file_count
            stats["organized_files"] += file_count
            stats["total_files"] += file_count

            # Count file extensions
            for file in folder_files:
                ext = file.suffix.lower()
                if ext:
                    stats["file_types"][ext] += 1
        except Exception as e:
            logger.error(f"Error counting files in {item_path}: {e}")

    # Convert Counter to dict for consistent return type
    stats["file_types"] = dict(stats["file_types"])
    return stats
