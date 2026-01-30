#!/usr/bin/env python3
"""
Command-line interface for the downloads_sorter package.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from .sorter import sort_downloads, get_stats, get_downloads_dir
from . import __version__

def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Downloads Sorter - A tool to organize your downloads folder"
    )
    
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version=f"downloads_sorter {__version__}"
    )
    
    parser.add_argument(
        "-d", "--directory",
        type=str,
        help="Custom downloads directory path"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about your downloads folder organization"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed logging information"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up automatic sorting with cron (Linux/macOS)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger('downloads_sorter').setLevel(logging.DEBUG)
    
    # Determine downloads directory
    downloads_dir = args.directory if args.directory else get_downloads_dir()
    
    # Validate directory exists
    if not os.path.isdir(downloads_dir):
        print(f"Error: Directory not found: {downloads_dir}")
        return 1
    
    # Handle stats command
    if args.stats:
        stats = get_stats(downloads_dir)
        
        print(f"\n📊 Downloads Folder Statistics:")
        print(f"📁 Total files: {stats['total_files']}")
        print(f"🗂️ Organized files: {stats['organized_files']} ({round(stats['organized_files']/max(stats['total_files'], 1)*100, 1)}%)")
        print(f"🧹 Unorganized files: {stats['unorganized_files']}")
        
        print("\n📂 Files by folder:")
        for folder, count in sorted(stats['folders'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {folder}: {count} files")
        
        print("\n📄 Files by type:")
        for ext, count in sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {ext}: {count} files")
        
        return 0
    
    # Handle setup command
    if args.setup:
        if sys.platform not in ['linux', 'darwin']:
            print("Automatic setup is only supported on Linux and macOS.")
            return 1
            
        cron_job = f"0 * * * * {sys.executable} -m downloads_sorter.cli"
        
        print(f"\n🔄 Setting up automatic sorting...")
        print(f"This will add a cron job to run downloads_sorter every hour:")
        print(f"  {cron_job}")
        
        confirm = input("\nProceed? (y/n): ")
        if confirm.lower() != 'y':
            print("Setup cancelled.")
            return 0
            
        try:
            import subprocess
            # Get existing crontab
            existing = subprocess.check_output('crontab -l 2>/dev/null || echo ""', shell=True).decode()
            
            # Check if our job is already in there
            if cron_job in existing:
                print("Cron job already exists!")
                return 0
                
            # Add our job
            with open('/tmp/downloads_sorter_cron', 'w') as f:
                if existing and not existing.endswith('\n'):
                    existing += '\n'
                f.write(f"{existing}{cron_job}\n")
                
            # Install new crontab
            subprocess.call('crontab /tmp/downloads_sorter_cron', shell=True)
            os.unlink('/tmp/downloads_sorter_cron')
            
            print("✅ Automatic sorting has been set up!")
            return 0
        except Exception as e:
            print(f"Error setting up cron job: {e}")
            return 1
    
    # Default command: sort downloads
    try:
        if args.dry_run:
            print(f"🔍 DRY RUN - No files will be moved")
            
        print(f"🗂️ Sorting downloads in: {downloads_dir}")
        result = sort_downloads(downloads_dir, args.dry_run)
        
        # Show results
        print(f"\n✅ Done!")
        print(f"📊 Summary:")
        print(f"  Files processed: {result['processed']}")
        print(f"  Files organized: {result['moved']}")
        print(f"  Files skipped: {result['skipped']}")
        print(f"  Errors: {result['errors']}")
        
        if not args.dry_run:
            print(f"\n💡 Tip: Run with --stats to see organization statistics")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
