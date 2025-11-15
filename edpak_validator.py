#!/usr/bin/env python3
"""
Edpak Validator - A tool for verifying edpak file compliance
"""

import json
import zipfile
import sys
from typing import Tuple, List
from pathlib import Path


class EdpakValidator:
    """Validator for edpak files according to the edpak standard v1.0"""
    
    REQUIRED_MANIFEST_FIELDS = ['title', 'version', 'author', 'modules']
    REQUIRED_MODULE_FIELDS = ['id', 'title', 'content']
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
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
        
        # Check for manifest.json
        if 'manifest.json' not in filelist:
            self.errors.append("Missing required manifest.json file in root directory")
            return
            
        # Read and validate manifest
        try:
            manifest_data = zf.read('manifest.json')
            manifest = json.loads(manifest_data)
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
                
            # Validate content path exists
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
