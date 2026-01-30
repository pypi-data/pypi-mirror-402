# Downloads Sorter

🗂️ A powerful Python tool to automatically organize your downloads folder.

## Features

- 📂 Automatically sorts files into folders based on file type
- 🧠 Intelligently categorizes files based on content patterns
- 📊 Provides statistics about your download organization
- 🔄 Can be set up to run automatically
- 🧹 Clean up your downloads folder with a single command

## Installation

```bash
pip install downloads-sorter
```

## Usage

### Basic Usage

Simply run the command to organize your downloads folder:

```bash
downloads-sorter
```

### Options

- `--dry-run`: Show what would be done without actually moving files
- `--stats`: Show statistics about your downloads folder organization
- `--directory PATH`: Specify a custom downloads directory
- `--verbose`: Show detailed logging
- `--setup`: Set up automatic sorting with cron (Linux/macOS)
- `--version`: Show the version number

### Examples

```bash
# Sort downloads with a dry run (no actual changes)
downloads-sorter --dry-run

# View organization statistics
downloads-sorter --stats

# Sort files in a custom directory
downloads-sorter --directory /path/to/directory

# Set up automatic hourly sorting
downloads-sorter --setup
```

## Folder Structure

Downloads Sorter organizes files into the following folder structure:

- `_pdf`: PDF documents
- `_docx`: Word documents
- `_xlsx`: Excel spreadsheets
- `_csv`: CSV data files
- `_png`, `_jpeg`, `_svg`: Images
- `_receipts`: Invoices and receipts
- `_contracts`: Legal documents and contracts
- `_meetings`: Meeting notes and calendar invites
- `_applications`: Software installers
- `_projects`: Project-related files
- `_misc`: Miscellaneous files

## Using as a Library

You can also use Downloads Sorter as a Python library in your own scripts:

```python
from downloads_sorter import sort_downloads, get_stats

# Sort downloads
result = sort_downloads()
print(f"Organized {result['moved']} files")

# Get statistics
stats = get_stats()
print(f"Total files: {stats['total_files']}")
print(f"Organized files: {stats['organized_files']}")
```

## Customizing

You can customize the sorting rules by creating your own script using the library:

```python
from downloads_sorter import sort_downloads
from downloads_sorter.sorter import FILE_TYPES, SPECIAL_PATTERNS

# Add custom extensions
FILE_TYPES['.custom'] = '_custom_folder'

# Add custom patterns
SPECIAL_PATTERNS[('mypattern', 'pattern2')] = '_pattern_folder'

# Run with custom rules
sort_downloads()
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
