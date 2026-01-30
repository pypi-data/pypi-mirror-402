import unittest
import tempfile
import os
import json
from gettranslated_cli.main import find_files, find_files_helper


class ReactNativeFileFindingTest(unittest.TestCase):
    """Test cases for React Native file finding functionality in the CLI"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="rn_test_")
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_find_files_helper_react_native(self):
        """Test that find_files_helper can find React Native JSON files"""
        # Create test files
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        with open(os.path.join(self.test_dir, "es.json"), "w") as f:
            json.dump({"welcome": "Bienvenido"}, f)
        
        # Test finding en.json files (empty filedir means search anywhere)
        results = find_files_helper(self.test_dir, "en.json", "")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].endswith("en.json"))
        
        # Test finding all JSON files
        results = find_files_helper(self.test_dir, "*.json", "")
        self.assertEqual(len(results), 2)

    def test_find_files_react_native(self):
        """Test that find_files can find React Native files"""
        # Create test files
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        with open(os.path.join(self.test_dir, "es.json"), "w") as f:
            json.dump({"welcome": "Bienvenido"}, f)
        
        # Test React Native file finding
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].endswith("en.json"))

    def test_find_files_react_native_nested_structure(self):
        """Test finding React Native files in nested directory structure"""
        # Create nested directory structure
        nested_dir = os.path.join(self.test_dir, "src", "locales")
        os.makedirs(nested_dir, exist_ok=True)
        
        with open(os.path.join(nested_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from src/locales"}, f)
        
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from root"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        # Should find both files (src/locales found by "locales" search, root found by "" search)
        self.assertEqual(len(results), 2)
        result_paths = [os.path.normpath(r) for r in results]
        self.assertTrue(any("src/locales/en.json" in r for r in result_paths))
        self.assertTrue(any(r.endswith("en.json") and "src" not in r and "locales" not in r for r in result_paths))

    def test_find_files_react_native_different_base_language(self):
        """Test finding React Native files with non-English base language"""
        # Create test files with Spanish as base language
        with open(os.path.join(self.test_dir, "es.json"), "w") as f:
            json.dump({"welcome": "Bienvenido"}, f)
        
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "es"
        }
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].endswith("es.json"))

    def test_find_files_react_native_no_files_found(self):
        """Test behavior when no React Native files are found"""
        # Create non-JSON files
        with open(os.path.join(self.test_dir, "en.txt"), "w") as f:
            f.write("Welcome")
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 0)

    def test_find_files_react_native_multiple_matches(self):
        """Test finding React Native files when multiple exist in different directories"""
        # Create multiple en.json files in different priority locations
        dir1 = os.path.join(self.test_dir, "locales")
        dir2 = os.path.join(self.test_dir, "i18n")
        os.makedirs(dir1, exist_ok=True)
        os.makedirs(dir2, exist_ok=True)
        
        with open(os.path.join(dir1, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from locales"}, f)
        
        with open(os.path.join(dir2, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from i18n"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        # Should find both files (all matching files are returned)
        self.assertEqual(len(results), 2)
        result_paths = [os.path.normpath(r) for r in results]
        self.assertTrue(any("locales/en.json" in r for r in result_paths))
        self.assertTrue(any("i18n/en.json" in r for r in result_paths))

    def test_find_files_react_native_excludes_directories(self):
        """Test that find_files excludes common directories like node_modules"""
        # Create a typical React Native project structure
        src_dir = os.path.join(self.test_dir, "src")
        node_modules_dir = os.path.join(self.test_dir, "node_modules")
        build_dir = os.path.join(self.test_dir, "build")
        git_dir = os.path.join(self.test_dir, ".git")
        
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(node_modules_dir, exist_ok=True)
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(git_dir, exist_ok=True)
        
        # Create files in different locations
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from root"}, f)
        
        # Create src/locales directory (which is in priority list)
        src_locales_dir = os.path.join(src_dir, "locales")
        os.makedirs(src_locales_dir, exist_ok=True)
        with open(os.path.join(src_locales_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from src/locales"}, f)
        
        # These should be ignored
        with open(os.path.join(node_modules_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        with open(os.path.join(build_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        with open(os.path.join(git_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        
        # Should find both files (src/locales found by "locales" search, root found by "" search)
        self.assertEqual(len(results), 2)
        result_paths = [os.path.normpath(r) for r in results]
        self.assertTrue(any("src/locales/en.json" in r for r in result_paths))
        self.assertTrue(any(r.endswith("en.json") and "src" not in r and "locales" not in r for r in result_paths))
        
        # Should not find files in excluded directories
        self.assertFalse(any("node_modules" in result for result in results))
        self.assertFalse(any("build" in result for result in results))
        self.assertFalse(any(".git" in result for result in results))

    def test_find_files_react_native_priority_directories(self):
        """Test that find_files prioritizes common React Native locale directories"""
        # Test 1: Only locales/ directory
        locales_dir = os.path.join(self.test_dir, "locales")
        os.makedirs(locales_dir, exist_ok=True)
        
        with open(os.path.join(locales_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from locales"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 1)
        self.assertIn("locales/en.json", results[0])
        
        # Clean up and test next priority
        os.remove(os.path.join(locales_dir, "en.json"))
        os.rmdir(locales_dir)
        
        # Test 2: Only src/locales/ directory (should be found by "locales" search)
        src_locales_dir = os.path.join(self.test_dir, "src", "locales")
        os.makedirs(src_locales_dir, exist_ok=True)
        
        with open(os.path.join(src_locales_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from src/locales"}, f)
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 1)
        self.assertIn("src/locales/en.json", results[0])
        
        # Clean up and test next priority
        os.remove(os.path.join(src_locales_dir, "en.json"))
        os.rmdir(src_locales_dir)
        os.rmdir(os.path.join(self.test_dir, "src"))
        
        # Test 3: Only root directory
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from root"}, f)
        
        results = find_files(self.test_dir, file_list)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].endswith("en.json"))
        # Should be root file (not in a subdirectory)
        self.assertTrue(results[0].endswith("/en.json"))
        self.assertFalse(any("/" in os.path.basename(result) for result in results))  # Filename should not contain slashes

    def test_find_files_react_native_locales_covers_nested_paths(self):
        """Test that 'locales' search finds files in both locales/ and src/locales/"""
        # Create both locales/ and src/locales/ directories
        locales_dir = os.path.join(self.test_dir, "locales")
        src_locales_dir = os.path.join(self.test_dir, "src", "locales")
        os.makedirs(locales_dir, exist_ok=True)
        os.makedirs(src_locales_dir, exist_ok=True)
        
        with open(os.path.join(locales_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from locales"}, f)
        
        with open(os.path.join(src_locales_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from src/locales"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        # Should find both files (one search for "locales" finds both paths)
        self.assertEqual(len(results), 2)
        # Verify both paths are found
        result_paths = [os.path.normpath(r) for r in results]
        self.assertTrue(any("locales/en.json" in r and "src" not in r for r in result_paths),
                       "locales/en.json not found")
        self.assertTrue(any("src/locales/en.json" in r for r in result_paths),
                       "src/locales/en.json not found")

    def test_find_files_react_native_i18n_covers_nested_paths(self):
        """Test that 'i18n' search finds files in both i18n/ and src/i18n/"""
        # Create both i18n/ and src/i18n/ directories
        i18n_dir = os.path.join(self.test_dir, "i18n")
        src_i18n_dir = os.path.join(self.test_dir, "src", "i18n")
        os.makedirs(i18n_dir, exist_ok=True)
        os.makedirs(src_i18n_dir, exist_ok=True)
        
        with open(os.path.join(i18n_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from i18n"}, f)
        
        with open(os.path.join(src_i18n_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from src/i18n"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        # Should find both files
        self.assertEqual(len(results), 2)
        # Verify both paths are found
        result_paths = [os.path.normpath(r) for r in results]
        self.assertTrue(any("i18n/en.json" in r for r in result_paths))
        self.assertTrue(any("src/i18n/en.json" in r for r in result_paths))

    def test_find_files_react_native_all_common_directories(self):
        """Test that all common directories in the list are searched"""
        # Create directories for all common patterns
        common_dirs = ["locales", "assets/locales", "translations", "i18n"]
        
        for dir_path in common_dirs:
            full_dir = os.path.join(self.test_dir, *dir_path.split("/"))
            os.makedirs(full_dir, exist_ok=True)
            with open(os.path.join(full_dir, "en.json"), "w") as f:
                json.dump({"welcome": f"Welcome from {dir_path}"}, f)
        
        # Also create root file
        with open(os.path.join(self.test_dir, "en.json"), "w") as f:
            json.dump({"welcome": "Welcome from root"}, f)
        
        file_list = {
            "platform": "React Native",
            "base_language": "en"
        }
        
        results = find_files(self.test_dir, file_list)
        # Should find all 5 files (4 common dirs + root)
        self.assertEqual(len(results), 5)
        
        # Verify all directories are found
        result_paths = [os.path.normpath(r) for r in results]
        for dir_path in common_dirs:
            self.assertTrue(any(dir_path in r for r in result_paths), 
                          f"Directory {dir_path} not found in results")
        # Verify root file is found
        self.assertTrue(any(r.endswith("en.json") and "/" not in os.path.basename(r) 
                          for r in result_paths), "Root file not found")


if __name__ == '__main__':
    unittest.main()

