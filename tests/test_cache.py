import gzip
import os
import pickle
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from summawise import ai  # noqa: F401  (must load before settings: settings <-> ai import cycle)
from summawise import utils
from summawise.api_objects import AssistantList, ThreadList
from summawise.errors import UnsafeCacheDirError
from summawise.files.cache import FileCacheObj
from summawise.files.metadata import FileMetadata
from summawise.settings import Settings
from summawise.utils import Singleton
from summawise.youtube import Transcript, TranscriptEntry


class Payload:
    """Unpickles into an observable side effect (creates the marker directory)."""

    def __init__(self, marker: Path):
        self.marker = marker

    def __reduce__(self):
        return (os.mkdir, (str(self.marker),))


class CacheTestCase(unittest.TestCase):

    def setUp(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        self.shared_tmp = root / "tmp"
        self.shared_tmp.mkdir()
        self.xdg_cache = root / "xdg-cache"
        self.marker = root / "payload-executed"

        for patch in (
            mock.patch.object(tempfile, "tempdir", str(self.shared_tmp)),
            mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.xdg_cache)}),
        ):
            patch.start()
            self.addCleanup(patch.stop)

        Singleton._instances.clear()
        self.addCleanup(Singleton._instances.clear)
        Settings(
            api_key="test-key",
            assistant_id="",
            model="gpt-4o",
            compression=True,
            code_style="monokai",
            assistants=AssistantList(),
            threads=ThreadList(),
        )

    def plant_legacy_pickle(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(pickle.dumps(Payload(self.marker))))


class LegacyPickleCacheTests(CacheTestCase):

    def test_pickle_at_old_shared_tmp_path_is_not_loaded(self):
        self.plant_legacy_pickle(self.shared_tmp / "summawise" / "file_cache.bin")

        cache = FileCacheObj.load()

        self.assertFalse(self.marker.exists())
        self.assertIsNone(cache.get_file_id_by_hash("legacy-hash"))

    def test_pickle_at_legacy_name_in_per_user_dir_is_not_loaded(self):
        self.plant_legacy_pickle(utils.get_summawise_dir() / "file_cache.bin")

        cache = FileCacheObj.load()

        self.assertFalse(self.marker.exists())
        self.assertIsNone(cache.get_file_id_by_hash("legacy-hash"))


class CacheDirTests(CacheTestCase):

    def test_summawise_dir_is_per_user_and_0700(self):
        cache_dir = utils.get_summawise_dir()

        self.assertEqual(cache_dir, self.xdg_cache / "summawise")
        self.assertEqual(stat.S_IMODE(cache_dir.stat().st_mode), 0o700)

    def test_preexisting_looser_dir_is_tightened_to_0700(self):
        cache_dir = self.xdg_cache / "summawise"
        cache_dir.mkdir(parents=True)
        os.chmod(cache_dir, 0o755)

        utils.get_summawise_dir()

        self.assertEqual(stat.S_IMODE(cache_dir.stat().st_mode), 0o700)

    def test_symlink_at_dir_path_is_refused(self):
        target = self.xdg_cache.parent / "attacker-controlled"
        target.mkdir()
        os.chmod(target, 0o755)
        self.xdg_cache.mkdir(parents=True)
        (self.xdg_cache / "summawise").symlink_to(target, target_is_directory=True)

        with self.assertRaises(UnsafeCacheDirError):
            utils.get_summawise_dir()
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)
        self.assertEqual(list(target.iterdir()), [])

    def test_regular_file_at_dir_path_is_refused(self):
        self.xdg_cache.mkdir(parents=True)
        (self.xdg_cache / "summawise").write_text("not a dir")

        with self.assertRaises(UnsafeCacheDirError):
            utils.get_summawise_dir()

    def test_foreign_owner_is_refused_without_chmod(self):
        cache_dir = self.xdg_cache / "summawise"
        cache_dir.mkdir(parents=True)
        os.chmod(cache_dir, 0o755)
        real_uid = os.getuid()

        with mock.patch.object(os, "getuid", return_value=real_uid + 1):
            with self.assertRaises(UnsafeCacheDirError):
                utils.get_summawise_dir()
        self.assertEqual(stat.S_IMODE(cache_dir.stat().st_mode), 0o755)

    def test_relative_xdg_cache_home_is_ignored(self):
        home = self.xdg_cache.parent / "home"
        home.mkdir()

        with mock.patch.dict(os.environ, {"HOME": str(home), "XDG_CACHE_HOME": "relative/cache"}):
            cache_dir = utils.get_summawise_dir()

        self.assertEqual(cache_dir, home / ".cache" / "summawise")

    def test_settings_file_is_owner_only(self):
        Settings.save()
        self.assertEqual(stat.S_IMODE(Settings.file().stat().st_mode), 0o600)

    def test_preexisting_looser_settings_file_is_tightened(self):
        Settings.file().parent.mkdir(parents=True, exist_ok=True)
        Settings.file().write_text("{}")
        os.chmod(Settings.file(), 0o644)

        Settings.save()

        self.assertEqual(stat.S_IMODE(Settings.file().stat().st_mode), 0o600)


class RoundTripTests(CacheTestCase):

    def test_file_cache_round_trip(self):
        # explicit dict: FileCacheObj() shares a mutable default
        FileCacheObj({"round-trip-hash": "file-123"}).save()

        loaded = FileCacheObj.load()

        self.assertEqual(loaded.get_file_id_by_hash("round-trip-hash"), "file-123")

    def test_file_metadata_round_trip(self):
        metadata = FileMetadata(
            hash="abc", name="a.txt", full_path="/x/a.txt", sz_bytes=3,
            created_at=1.0, last_modified_at=2.0, last_accessed_at=3.0,
            vector_store_id="vs_1", file_id="file_1",
        )
        path = utils.get_summawise_dir() / "files" / "abc.json"
        metadata.save_to_file(path, compress=True, pretty_json=True)

        loaded = FileMetadata.from_file(utils.fp(path))

        self.assertEqual(loaded, metadata)

    def test_transcript_round_trip(self):
        transcript = Transcript(
            "dQw4w9WgXcQ",
            [TranscriptEntry("hello", 1.5, 2.0)],
            vector_store_id="vs_2",
            file_id="file_2",
        )
        path = utils.get_summawise_dir() / "youtube" / "transcript_x.json"
        transcript.save_to_file(path, compress=True)

        loaded = Transcript.from_file(utils.fp(path))

        self.assertEqual(loaded.video_id, transcript.video_id)
        self.assertEqual(loaded.vector_store_id, "vs_2")
        self.assertEqual(loaded.file_id, "file_2")
        self.assertEqual([e.text for e in loaded.entries], ["hello"])


class SettingsFileTests(CacheTestCase):

    def test_legacy_data_mode_key_is_dropped_and_file_rewritten(self):
        Singleton._instances.clear()
        settings, save = Settings.from_dict({
            "api_key": "test-key",
            "data_mode": "binary",
            "assistants": [],
            "threads": [],
        })

        self.assertNotIn("data_mode", settings.to_dict())
        self.assertTrue(save)


if __name__ == "__main__":
    unittest.main()
