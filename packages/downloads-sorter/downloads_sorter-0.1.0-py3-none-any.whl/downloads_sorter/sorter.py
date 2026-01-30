#!/usr/bin/env python3
"""
Main module for the downloads_sorter package.
Contains functions for sorting files in the downloads directory.
"""

import os
import shutil
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('downloads_sorter')

def get_downloads_dir():
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

def ensure_dir_exists(directory):
    """Ensure that a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    return directory

def get_unique_path(target_path):
    """
    Get a unique path for a file by appending a number if the file already exists.
    """
    if not os.path.exists(target_path):
        return target_path
        
    # If the file already exists, append a number to the filename
    directory, file_name = os.path.split(target_path)
    name, ext = os.path.splitext(file_name)
    counter = 1
    while os.path.exists(os.path.join(directory, f"{name}({counter}){ext}")):
        counter += 1
    return os.path.join(directory, f"{name}({counter}){ext}")

def sort_file(file_path, downloads_dir=None, dry_run=False):
    """
    Sort a file into the appropriate folder based on its extension or name.
    
    Parameters:
    file_path (str): The path to the file to be sorted
    downloads_dir (str, optional): The downloads directory. If None, auto-detected.
    dry_run (bool, optional): If True, don't actually move files, just print what would happen.
    
    Returns:
    str: The new location of the file, or None if the file was not moved
    """
    if not os.path.isfile(file_path):
        logger.warning(f"Not a file: {file_path}")
        return None
    
    # Get the downloads directory if not specified
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
    
    file_name = os.path.basename(file_path)
    if file_name.startswith('.'):  # Skip hidden files
        logger.debug(f"Skipping hidden file: {file_name}")
        return None
        
    # Get the file extension
    _, extension = os.path.splitext(file_name)
    extension = extension.lower()
    
    # Check if we should skip system files
    if file_name in ['.DS_Store', '.localized', 'sort_downloads.py', 'README_SORT.md']:
        logger.debug(f"Skipping system file: {file_name}")
        return None
    
    # First check if the file matches any special patterns
    for patterns, folder in SPECIAL_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in file_name.lower():
                target_dir = ensure_dir_exists(os.path.join(downloads_dir, folder))
                target_path = get_unique_path(os.path.join(target_dir, file_name))
                
                if dry_run:
                    logger.info(f"Would move {file_name} to {folder}/")
                    return target_path
                
                try:
                    shutil.move(file_path, target_path)
                    logger.info(f"Moved {file_name} to {folder}/")
                    return target_path
                except Exception as e:
                    logger.error(f"Error moving {file_name}: {e}")
                    return None
    
    # If no special pattern matched, check by extension
    if extension in FILE_TYPES:
        folder = FILE_TYPES[extension]
        target_dir = ensure_dir_exists(os.path.join(downloads_dir, folder))
        target_path = get_unique_path(os.path.join(target_dir, file_name))
        
        if dry_run:
            logger.info(f"Would move {file_name} to {folder}/")
            return target_path
        
        try:
            shutil.move(file_path, target_path)
            logger.info(f"Moved {file_name} to {folder}/")
            return target_path
        except Exception as e:
            logger.error(f"Error moving {file_name}: {e}")
            return None
    else:
        # If no matching folder is found, move to _misc
        target_dir = ensure_dir_exists(os.path.join(downloads_dir, "_misc"))
        target_path = get_unique_path(os.path.join(target_dir, file_name))
        
        if dry_run:
            logger.info(f"Would move {file_name} to _misc/")
            return target_path
        
        try:
            shutil.move(file_path, target_path)
            logger.info(f"Moved {file_name} to _misc/")
            return target_path
        except Exception as e:
            logger.error(f"Error moving {file_name}: {e}")
            return None

def sort_downloads(downloads_dir=None, dry_run=False):
    """
    Sort all files in the downloads directory.
    
    Parameters:
    downloads_dir (str, optional): The downloads directory. If None, auto-detected.
    dry_run (bool, optional): If True, don't actually move files, just print what would happen.
    
    Returns:
    dict: A summary of the sorting operation with counts of files processed, moved, and errors
    """
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
    
    logger.info(f"Sorting files in {downloads_dir}...")
    
    result = {
        "processed": 0,
        "moved": 0,
        "errors": 0,
        "skipped": 0
    }
    
    # Get all files in the Downloads directory (not in subdirectories)
    try:
        files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) 
                if os.path.isfile(os.path.join(downloads_dir, f))]
    except Exception as e:
        logger.error(f"Error listing directory {downloads_dir}: {e}")
        return result
    
    # Sort each file
    for file_path in files:
        result["processed"] += 1
        new_path = sort_file(file_path, downloads_dir, dry_run)
        if new_path:
            result["moved"] += 1
        elif new_path is None and os.path.isfile(file_path):
            # File exists but was skipped
            result["skipped"] += 1
        else:
            result["errors"] += 1
    
    logger.info(f"Done sorting files! Processed: {result['processed']}, Moved: {result['moved']}, Errors: {result['errors']}, Skipped: {result['skipped']}")
    return result

def get_stats(downloads_dir=None):
    """
    Get statistics about the downloads directory organization.
    
    Returns:
    dict: A dictionary with statistics about the directory organization
    """
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()
        
    stats = {
        "total_files": 0,
        "organized_files": 0,
        "unorganized_files": 0,
        "folders": {},
        "file_types": {}
    }
    
    # Count files in top level (unorganized)
    top_files = [f for f in os.listdir(downloads_dir) 
                if os.path.isfile(os.path.join(downloads_dir, f)) and not f.startswith('.')]
    stats["unorganized_files"] = len(top_files)
    stats["total_files"] += len(top_files)
    
    # Count files in organized folders
    for item in os.listdir(downloads_dir):
        item_path = os.path.join(downloads_dir, item)
        
        # Skip files and hidden directories
        if not os.path.isdir(item_path) or item.startswith('.'):
            continue
            
        # Count files in this folder
        try:
            folder_files = [f for f in os.listdir(item_path) 
                          if os.path.isfile(os.path.join(item_path, f)) and not f.startswith('.')]
            file_count = len(folder_files)
            
            stats["folders"][item] = file_count
            stats["organized_files"] += file_count
            stats["total_files"] += file_count
            
            # Count file types in this folder
            for file in folder_files:
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext:
                    if ext in stats["file_types"]:
                        stats["file_types"][ext] += 1
                    else:
                        stats["file_types"][ext] = 1
        except Exception as e:
            logger.error(f"Error counting files in {item_path}: {e}")
    
    return stats
