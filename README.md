# Edpak - Open Standard for Educational Course Packaging

Resources and tools for the edpak open standard for course materials.

## Overview

Edpak is a ZIP-based open standard for packaging educational courses and learning materials. It provides a consistent, portable format for distributing course content across different platforms and learning management systems.

## Website

The full standard specification is available in [index.html](index.html). Open this file in your browser to view the complete documentation.

## Python Verification Tool

This repository includes a Python tool for verifying if an edpak file is compliant with the edpak standard.

### Installation

#### From Source

```bash
git clone https://github.com/pierce403/edpak.git
cd edpak
pip install -e .
```

#### Using pip (when published)

```bash
pip install edpak-validator
```

### Usage

#### Command Line

```bash
# Verify an edpak file
edpak-verify course.edpak
```

#### Python API

```python
from edpak_validator import verify_edpak

# Verify an edpak file
is_valid, errors, warnings = verify_edpak('course.edpak')

if is_valid:
    print("✓ Valid edpak file!")
else:
    print("✗ Invalid edpak file")
    for error in errors:
        print(f"  - {error}")
        
if warnings:
    print("Warnings:")
    for warning in warnings:
        print(f"  - {warning}")
```

### Example

An example valid edpak file is included in the `examples/` directory:

```bash
python3 edpak_validator.py examples/example-course.edpak
```

## Standard Specification

### File Format

An edpak file is a standard ZIP archive with a `.edpak` file extension.

### Required Structure (Core v1.0)

Every edpak file **MUST** contain a `manifest.json` file in the root directory.

### Manifest Fields

Required fields:
- `title` (string): The title of the course
- `version` (string): Version number (semver recommended)
- `author` (string): Name of the course author or organization
- `modules` (array): Array of module objects

Optional fields:
- `description` (string): A brief description of the course content
- `language` (string): ISO 639-1 language code (e.g., "en", "es")

Implementations MAY include additional top-level fields in `manifest.json` (for example `lessons`, `files`, `missingFiles`, `x_source_platform`, `x_source_author`, `x_spec_notes`) to capture richer course structures. These extensions are optional and can be ignored by consumers that only care about the core v1.0 fields.

### Module Object Fields

Required fields:
- `id` (string): Unique identifier for the module
- `title` (string): Title of the module
- `order` (number): Order in which the module should be presented

Optional fields:
- `content` (string): Path to an optional pre-rendered module content file (relative to package root)

For many producers, modules act primarily as structural containers for lessons, and no standalone HTML file is needed.
- `order` (number): Order in which the module should be presented

### Example Manifest

```json
{
  "title": "Introduction to Python Programming",
  "version": "1.0.0",
  "author": "Jane Doe",
  "description": "A comprehensive introduction to Python programming",
  "language": "en",
  "modules": [
    {
      "id": "module-1",
      "title": "Getting Started with Python",
      "order": 1
    }
  ]
}
```

## Development

### Running Tests

```bash
python3 -m unittest test_edpak_validator.py -v
```

### Creating an Edpak File

```bash
# Create your course structure
echo '{"title":"My Course","version":"1.0.0","author":"Me","modules":[]}' > my-course/manifest.json

# Package it
cd my-course && zip -r ../my-course.edpak . && cd ..

# Verify it
python3 edpak_validator.py my-course.edpak
```

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
