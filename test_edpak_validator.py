#!/usr/bin/env python3
"""
Tests for edpak validator
"""

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from edpak_validator import verify_edpak, EdpakValidator


class TestEdpakValidator(unittest.TestCase):
    """Test cases for the edpak validator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_edpak_file(self, filename, manifest, content_files=None):
        """Helper to create an edpak file for testing"""
        filepath = os.path.join(self.temp_dir, filename)
        
        with zipfile.ZipFile(filepath, 'w') as zf:
            # Add manifest
            zf.writestr('manifest.json', json.dumps(manifest))
            
            # Add content files if provided
            if content_files:
                for path, content in content_files.items():
                    zf.writestr(path, content)
                    
        return filepath
    
    def test_course_structure_with_lessons_and_quizzes(self):
        """Course with lessons, quizzes, and covers should be valid"""
        manifest = {
            "title": "Structured Course",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "A course with lessons and quizzes",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module-1.html",
                    "description": "Module 1 description"
                },
                {
                    "id": "module-2",
                    "title": "Module 2",
                    "content": "module-2.html",
                    "description": "Module 2 description"
                }
            ],
            "lessons": [
                {
                    "id": "lesson-1",
                    "moduleId": "module-1",
                    "title": "Image lesson 1",
                    "type": "Image",
                    "status": "Active",
                    "order": 1,
                    "description": "",
                    "content": None,
                    "fileId": "file-1",
                    "filePath": "images/img1.png"
                },
                {
                    "id": "lesson-2",
                    "moduleId": "module-1",
                    "title": "Quiz 1",
                    "type": "MultipleChoice",
                    "status": "Active",
                    "order": 2,
                    "description": "",
                    "content": json.dumps({
                        "Question": "Q1",
                        "Options": [{"Text": "A", "IsCorrect": True}]
                    }),
                    "fileId": None,
                    "filePath": None
                },
                {
                    "id": "lesson-3",
                    "moduleId": "module-2",
                    "title": "Image lesson 2",
                    "type": "Image",
                    "status": "Active",
                    "order": 1,
                    "description": "",
                    "content": None,
                    "fileId": "file-2",
                    "filePath": "images/img2.png"
                },
                {
                    "id": "lesson-4",
                    "moduleId": "module-2",
                    "title": "Quiz 2",
                    "type": "MultipleChoice",
                    "status": "Active",
                    "order": 2,
                    "description": "",
                    "content": json.dumps({
                        "Question": "Q2",
                        "Options": [{"Text": "A", "IsCorrect": True}]
                    }),
                    "fileId": None,
                    "filePath": None
                }
            ]
        }
        content_files = {
            "module-1.html": "<h1>Module 1</h1>",
            "module-2.html": "<h1>Module 2</h1>",
            "images/img1.png": "img1-bytes",
            "images/img2.png": "img2-bytes"
        }
        
        filepath = self.create_edpak_file("structured.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        # No structural course warnings expected in the happy path
        self.assertFalse(any("no lessons associated" in w.lower() for w in warnings))
        self.assertFalse(any("no quiz lessons" in w.lower() for w in warnings))
        self.assertFalse(any("cover image not found" in w.lower() for w in warnings))
    
    def test_course_structure_missing_metadata_and_quizzes(self):
        """Missing description and quizzes should trigger warnings but not errors"""
        manifest = {
            "title": "Course Without Metadata",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module-1.html"
                }
            ],
            "lessons": [
                {
                    "id": "lesson-1",
                    "moduleId": "module-1",
                    "title": "Only image",
                    "type": "Image",
                    "status": "Active",
                    "order": 1,
                    "description": "",
                    "content": None,
                    "fileId": "file-1",
                    "filePath": "images/img1.png"
                }
            ]
        }
        content_files = {
            "module-1.html": "<h1>Module 1</h1>",
            "images/img1.png": "img1-bytes"
        }
        
        filepath = self.create_edpak_file("missing-metadata.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        # Structural checks should still consider this a valid edpak,
        # but emit warnings about missing metadata and quizzes.
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertTrue(any("course description is missing" in w.lower() for w in warnings))
        self.assertTrue(any("module 'module-1' is missing a description" in w.lower() for w in warnings))
        self.assertTrue(any("no quiz lessons" in w.lower() for w in warnings))
        
    def test_valid_edpak_file(self):
        """Test validation of a valid edpak file"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module1.html"
                }
            ]
        }
        content_files = {
            "module1.html": "<h1>Module 1</h1>"
        }
        
        filepath = self.create_edpak_file("valid.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
    def test_missing_manifest(self):
        """Test validation fails when manifest.json is missing"""
        filepath = os.path.join(self.temp_dir, "no-manifest.edpak")
        
        with zipfile.ZipFile(filepath, 'w') as zf:
            zf.writestr('readme.txt', "No manifest here")
            
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("manifest.json" in e for e in errors))
        
    def test_invalid_json_manifest(self):
        """Test validation fails with invalid JSON in manifest"""
        filepath = os.path.join(self.temp_dir, "invalid-json.edpak")
        
        with zipfile.ZipFile(filepath, 'w') as zf:
            zf.writestr('manifest.json', "{invalid json")
            
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid JSON" in e for e in errors))
        
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing"""
        manifest = {
            "title": "Test Course"
            # Missing version, author, modules
        }
        
        filepath = self.create_edpak_file("missing-fields.edpak", manifest)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("version" in e for e in errors))
        self.assertTrue(any("author" in e for e in errors))
        self.assertTrue(any("modules" in e for e in errors))
        
    def test_duplicate_module_ids(self):
        """Test validation fails with duplicate module IDs"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module1.html"
                },
                {
                    "id": "module-1",
                    "title": "Module 2",
                    "content": "module2.html"
                }
            ]
        }
        content_files = {
            "module1.html": "<h1>Module 1</h1>",
            "module2.html": "<h1>Module 2</h1>"
        }
        
        filepath = self.create_edpak_file("duplicate-ids.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("Duplicate module ID" in e for e in errors))
        
    def test_missing_content_file(self):
        """Test validation fails when referenced content file is missing"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "missing.html"
                }
            ]
        }
        
        filepath = self.create_edpak_file("missing-content.edpak", manifest)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("content file not found" in e for e in errors))

    def test_unexpected_directories_fail_validation(self):
        """Test validation fails when unexpected directories are present"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1"
                }
            ]
        }
        # Include content under a disallowed directory such as 'modules/'
        content_files = {
            "modules/module-1.html": "<h1>Module 1</h1>"
        }

        filepath = self.create_edpak_file("unexpected-dirs.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)

        self.assertFalse(is_valid)
        self.assertTrue(any("Unexpected directories in archive" in e for e in errors))
        
    def test_wrong_file_extension(self):
        """Test validation warns about wrong file extension"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": []
        }
        
        filepath = self.create_edpak_file("test.zip", manifest)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any(".edpak extension" in e for e in errors))
        
    def test_allowed_directories_are_accepted(self):
        """Test images/videos/files directories are allowed"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": []
        }
        content_files = {
            "images/img1.png": "img-bytes",
            "videos/vid1.mp4": "video-bytes",
            "files/doc1.pdf": "pdf-bytes"
        }
        
        filepath = self.create_edpak_file("allowed-dirs.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
    def test_not_a_zip_file(self):
        """Test validation fails for non-ZIP files"""
        filepath = os.path.join(self.temp_dir, "notzip.edpak")
        with open(filepath, 'w') as f:
            f.write("This is not a ZIP file")
            
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("not a valid ZIP" in e for e in errors))
        
    def test_nonexistent_file(self):
        """Test validation fails for non-existent files"""
        filepath = os.path.join(self.temp_dir, "does-not-exist.edpak")
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("File not found" in e for e in errors))
        
    def test_empty_modules_array(self):
        """Test validation warns about empty modules array"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": []
        }
        
        filepath = self.create_edpak_file("empty-modules.edpak", manifest)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertTrue(any("No modules defined" in w for w in warnings))
        
    def test_module_with_order(self):
        """Test validation accepts modules with order field"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module1.html",
                    "order": 1
                }
            ]
        }
        content_files = {
            "module1.html": "<h1>Module 1</h1>"
        }
        
        filepath = self.create_edpak_file("with-order.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
    def test_manifest_with_optional_fields(self):
        """Test validation accepts optional fields"""
        manifest = {
            "title": "Test Course",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "A test course",
            "language": "en",
            "modules": [
                {
                    "id": "module-1",
                    "title": "Module 1",
                    "content": "module1.html"
                }
            ]
        }
        content_files = {
            "module1.html": "<h1>Module 1</h1>"
        }
        
        filepath = self.create_edpak_file("with-optional.edpak", manifest, content_files)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
    def test_invalid_field_types(self):
        """Test validation fails with invalid field types"""
        manifest = {
            "title": 123,  # Should be string
            "version": "1.0.0",
            "author": "Test Author",
            "modules": "not an array"  # Should be array
        }
        
        filepath = self.create_edpak_file("invalid-types.edpak", manifest)
        is_valid, errors, warnings = verify_edpak(filepath)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("'title' must be a string" in e for e in errors))
        self.assertTrue(any("'modules' must be an array" in e for e in errors))


if __name__ == '__main__':
    unittest.main()
