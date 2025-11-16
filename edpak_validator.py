#!/usr/bin/env python3
"""
Edpak Validator - A tool for verifying edpak file compliance
"""

import json
import zipfile
import sys
from collections import defaultdict
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path


class EdpakValidator:
    """Validator for edpak files according to the edpak standard v1.0"""
    
    REQUIRED_MANIFEST_FIELDS = ['title', 'version', 'author', 'modules']
    # Modules require an identity and title; content paths are now optional
    REQUIRED_MODULE_FIELDS = ['id', 'title']
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Optional[Dict[str, Any]] = None
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate an edpak file for compliance with the edpak standard.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        # Check file extension
        if not self.filepath.endswith('.edpak'):
            self.errors.append("File must have .edpak extension")
            
        # Check if file exists
        if not Path(self.filepath).exists():
            self.errors.append(f"File not found: {self.filepath}")
            return False, self.errors, self.warnings
            
        # Check if it's a valid ZIP file
        if not zipfile.is_zipfile(self.filepath):
            self.errors.append("File is not a valid ZIP archive")
            return False, self.errors, self.warnings
            
        # Open and inspect the ZIP file
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zf:
                self._validate_zip_contents(zf)
        except Exception as e:
            self.errors.append(f"Error reading ZIP file: {str(e)}")
            
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
        
    def _validate_zip_contents(self, zf: zipfile.ZipFile) -> None:
        """Validate the contents of the ZIP archive"""
        filelist = zf.namelist()

        # Enforce that only well-known asset directories are present.
        # Producers should not include arbitrary top-level directories
        # like "modules/" or "assets/" – all structured content lives
        # in manifest.json and raw assets under images/videos/files.
        self._validate_directories(filelist)
        
        # Check for manifest.json
        if 'manifest.json' not in filelist:
            self.errors.append("Missing required manifest.json file in root directory")
            return
            
        # Read and validate manifest
        try:
            manifest_data = zf.read('manifest.json')
            manifest = json.loads(manifest_data)
            # Store manifest for optional introspection by callers / CLI
            self.manifest = manifest
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in manifest.json: {str(e)}")
            return
        except Exception as e:
            self.errors.append(f"Error reading manifest.json: {str(e)}")
            return
            
        self._validate_manifest(manifest, filelist)
        
    def _validate_manifest(self, manifest: dict, filelist: List[str]) -> None:
        """Validate the manifest structure and content"""
        # Check required fields
        for field in self.REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                self.errors.append(f"Missing required field in manifest: {field}")
            elif field != 'modules' and not manifest[field]:
                # Allow empty modules array, but not empty strings
                self.errors.append(f"Required field '{field}' cannot be empty")
                
        # Validate field types
        if 'title' in manifest and not isinstance(manifest['title'], str):
            self.errors.append("Field 'title' must be a string")
            
        if 'version' in manifest and not isinstance(manifest['version'], str):
            self.errors.append("Field 'version' must be a string")
            
        if 'author' in manifest and not isinstance(manifest['author'], str):
            self.errors.append("Field 'author' must be a string")
            
        if 'description' in manifest and not isinstance(manifest['description'], str):
            self.errors.append("Field 'description' must be a string")
            
        if 'language' in manifest and not isinstance(manifest['language'], str):
            self.errors.append("Field 'language' must be a string")
            
        if 'modules' in manifest:
            if not isinstance(manifest['modules'], list):
                self.errors.append("Field 'modules' must be an array")
            else:
                if len(manifest['modules']) == 0:
                    self.warnings.append("No modules defined in manifest")
                self._validate_modules(manifest['modules'], filelist)
                
        # Perform additional semantic validation when extended fields
        # like lessons/files are present (Leyline exports, etc.).
        self._validate_course_structure(manifest, filelist)
                
    def _validate_modules(self, modules: List[dict], filelist: List[str]) -> None:
        """Validate module objects"""
        module_ids = set()
        
        for idx, module in enumerate(modules):
            if not isinstance(module, dict):
                self.errors.append(f"Module at index {idx} is not an object")
                continue
                
            # Check required fields
            for field in self.REQUIRED_MODULE_FIELDS:
                if field not in module:
                    self.errors.append(f"Module at index {idx} missing required field: {field}")
                    
            # Validate module ID uniqueness
            if 'id' in module:
                if not isinstance(module['id'], str):
                    self.errors.append(f"Module at index {idx}: 'id' must be a string")
                elif module['id'] in module_ids:
                    self.errors.append(f"Duplicate module ID: {module['id']}")
                else:
                    module_ids.add(module['id'])
                    
            # Validate title
            if 'title' in module and not isinstance(module['title'], str):
                self.errors.append(f"Module at index {idx}: 'title' must be a string")
                
            # Validate content path exists when provided (optional)
            if 'content' in module:
                if not isinstance(module['content'], str):
                    self.errors.append(f"Module at index {idx}: 'content' must be a string")
                elif module['content'] not in filelist:
                    self.errors.append(
                        f"Module at index {idx}: content file not found: {module['content']}"
                    )
                    
            # Validate order if present
            if 'order' in module and not isinstance(module['order'], (int, float)):
                self.errors.append(f"Module at index {idx}: 'order' must be a number")

    def _validate_directories(self, filelist: List[str]) -> None:
        """
        Ensure that only the supported top-level asset directories are present.
        
        Allowed root-level directories:
          - images/
          - videos/
          - files/
        
        Any other directory (e.g. modules/, assets/, etc.) causes validation
        to fail, to discourage embedding pre-rendered structures that should
        instead be described in manifest.json.
        """
        allowed_root_dirs = {"images", "videos", "files"}
        found_root_dirs = set()

        for name in filelist:
            # Normalise ZIP directory entries and nested paths.
            if "/" in name:
                root = name.split("/", 1)[0]
                if root:
                    found_root_dirs.add(root)

        unexpected = sorted(d for d in found_root_dirs if d not in allowed_root_dirs)
        if unexpected:
            self.errors.append(
                "Unexpected directories in archive: "
                + ", ".join(unexpected)
                + " (only 'images', 'videos', and 'files' directories are allowed)"
            )

    def _validate_course_structure(self, manifest: Dict[str, Any], filelist: List[str]) -> None:
        """
        Perform higher-level validation of course structure for manifests
        that include lessons/files metadata.

        This is intentionally lenient for older/other edpak producers:
        if no lessons array is present, these checks are skipped so that
        basic structural validation still passes.
        """
        # If there is no lessons array, treat this as a minimal manifest
        # and skip course-structure checks.
        if 'lessons' not in manifest:
            return

        lessons = manifest.get('lessons')
        modules = manifest.get('modules') or []

        if not isinstance(lessons, list):
            self.errors.append("Field 'lessons' must be an array when present")
            return

        if len(lessons) == 0:
            self.errors.append("Course defines a lessons array but it is empty")
            return

        # Course-level description
        description = manifest.get('description')
        if not isinstance(description, str) or not description.strip():
            self.warnings.append("Course description is missing or empty")

        # Build moduleId -> lessons mapping and check lesson objects
        module_lessons: Dict[str, List[dict]] = defaultdict(list)
        for idx, lesson in enumerate(lessons):
            if not isinstance(lesson, dict):
                self.errors.append(f"Lesson at index {idx} is not an object")
                continue

            module_id = lesson.get('moduleId')
            if not isinstance(module_id, str) or not module_id:
                self.errors.append(f"Lesson at index {idx} missing valid 'moduleId'")
                continue

            module_lessons[module_id].append(lesson)

        # Course cover image: at least one image lesson with a valid filePath
        course_cover_found = False
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            if lesson.get('type') == 'Image':
                fp = lesson.get('filePath')
                if isinstance(fp, str) and fp and fp in filelist:
                    course_cover_found = True
                    break
        if not course_cover_found:
            self.warnings.append(
                "Course cover image not found (no image lessons with valid filePath)"
            )

        # Per-module checks: description, at least one lesson, at least one quiz,
        # and an image lesson we can treat as a module cover.
        for idx, module in enumerate(modules):
            if not isinstance(module, dict):
                self.errors.append(f"Module at index {idx} is not an object")
                continue

            module_id = module.get('id')
            title = module.get('title')

            if 'title' in module and (not isinstance(title, str) or not title.strip()):
                self.errors.append(
                    f"Module at index {idx} has an empty or invalid 'title'"
                )

            # Module description is strongly recommended but not strictly required.
            m_desc = module.get('description')
            if not isinstance(m_desc, str) or not m_desc.strip():
                self.warnings.append(
                    f"Module '{module_id}' is missing a description"
                )

            lessons_for_module = module_lessons.get(module_id, [])
            if not lessons_for_module:
                self.errors.append(
                    f"Module '{module_id}' ('{title}') has no lessons associated with it"
                )
                continue

            quiz_count = sum(
                1
                for lesson in lessons_for_module
                if lesson.get('type') == 'MultipleChoice'
            )
            if quiz_count == 0:
                self.warnings.append(
                    f"Module '{module_id}' ('{title}') has no quiz lessons of type 'MultipleChoice'"
                )

            module_cover_found = any(
                lesson.get('type') == 'Image'
                and isinstance(lesson.get('filePath'), str)
                and lesson['filePath'] in filelist
                for lesson in lessons_for_module
            )
            if not module_cover_found:
                self.warnings.append(
                    f"Module '{module_id}' ('{title}') has no image lessons with valid filePath (module cover image missing)"
                )


def verify_edpak(filepath: str) -> Tuple[bool, List[str], List[str]]:
    """
    Verify if an edpak file is compliant with the edpak standard.
    
    Args:
        filepath: Path to the .edpak file
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = EdpakValidator(filepath)
    return validator.validate()


def main():
    """Command-line interface for edpak verification"""
    if len(sys.argv) != 2:
        print("Usage: edpak-verify <file.edpak>")
        print("\nVerifies if an edpak file is compliant with the edpak standard")
        sys.exit(1)
        
    filepath = sys.argv[1]
    is_valid, errors, warnings = verify_edpak(filepath)
    
    print(f"\nValidating: {filepath}")
    print("=" * 60)
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠  {warning}")
            
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ✗ {error}")
            
    print("\n" + "=" * 60)
    if is_valid:
        print("✓ Valid edpak file!")
        sys.exit(0)
    else:
        print("✗ Invalid edpak file")
        sys.exit(1)


if __name__ == '__main__':
    main()
