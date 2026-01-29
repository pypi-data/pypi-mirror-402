"""Tests for ProfileManager utility."""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from pushtunes.utils.profile_manager import load_profile, merge_with_cli_args, _find_profile_file


class TestProfileManager(unittest.TestCase):
    """Test ProfileManager logic."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_profile_file_absolute(self):
        """Test finding profile by absolute path."""
        p = self.dir_path / "test.json"
        p.write_text("{}")
        
        found = _find_profile_file(str(p.absolute()))
        self.assertEqual(found, p.absolute())

    def test_find_profile_file_cwd(self):
        """Test finding profile in CWD."""
        # Use a temporary file in actual CWD or mock it
        with patch.object(Path, "exists", return_value=True):
            found = _find_profile_file("local_profile.json")
            self.assertIsNotNone(found)

    def test_load_json_profile(self):
        """Test loading a JSON profile."""
        p = self.dir_path / "profile.json"
        data = {"from": "spotify", "albums": {"to": "ytm"}}
        p.write_text(json.dumps(data))
        
        # Load generic part
        res = load_profile(str(p), "tracks")
        self.assertEqual(res["from"], "spotify")
        
        # Load specific section
        res_albums = load_profile(str(p), "albums")
        self.assertEqual(res_albums["to"], "ytm")

    def test_load_yaml_profile(self):
        """Test loading a YAML profile."""
        import importlib.util
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("PyYAML not installed")
            
        p = self.dir_path / "profile.yaml"
        p.write_text("from: subsonic\nto: csv")
        
        res = load_profile(str(p), "any")
        self.assertEqual(res["from"], "subsonic")
        self.assertEqual(res["to"], "csv")

    def test_load_toml_profile(self):
        """Test loading a TOML profile."""
        p = self.dir_path / "profile.toml"
        p.write_text('from = "tidal"\n\n[albums]\nto = "spotify"')
        
        res = load_profile(str(p), "tracks")
        self.assertEqual(res["from"], "tidal")
        
        res_albums = load_profile(str(p), "albums")
        self.assertEqual(res_albums["to"], "spotify")

    def test_merge_with_cli_args(self):
        """Test merging profile with CLI arguments."""
        profile = {
            "from": "spotify",
            "to": "ytm",
            "similarity": 0.8,
            "include": ["artist:A"]
        }
        
        # 1. Override simple value
        cli_args = {"to": "csv", "similarity": None}
        merged = merge_with_cli_args(profile, cli_args)
        self.assertEqual(merged["to"], "csv")
        self.assertEqual(merged["similarity"], 0.8) # None skipped
        
        # 2. Append to lists
        cli_args_list = {"include": ["artist:B"]}
        merged_list = merge_with_cli_args(profile, cli_args_list)
        self.assertEqual(merged_list["include"], ["artist:A", "artist:B"])

    def test_load_profile_not_found(self):
        """Test error when profile is not found."""
        with self.assertRaises(FileNotFoundError):
            load_profile("nonexistent_file_xyz.json", "albums")
