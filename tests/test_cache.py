import gzip
import os
import resource
import pickle
import shutil
import signal
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from summawise import ai  # noqa: F401  (must load before settings: settings <-> ai import cycle)
from summawise import utils
from summawise.api_objects import AssistantList, ThreadList
from summawise.errors import MalformedCacheError, UnsafeCacheDirError
from summawise.files.cache import FileCacheObj
from summawise.files import utils as FileUtils
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


class FailedWriteTests(CacheTestCase):

    @unittest.skipUnless(hasattr(resource, "RLIMIT_FSIZE"), "needs RLIMIT_FSIZE to fail a write partway")
    def test_write_failing_partway_keeps_previous_content_and_leaves_no_temp_file(self):
        target = utils.get_summawise_dir() / "data.json"
        FileUtils.write_bytes(target, b"previous")
        soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
        old_handler = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        self.addCleanup(signal.signal, signal.SIGXFSZ, old_handler)
        self.addCleanup(resource.setrlimit, resource.RLIMIT_FSIZE, (soft, hard))

        resource.setrlimit(resource.RLIMIT_FSIZE, (4096, hard))
        with self.assertRaises(OSError):
            FileUtils.write_bytes(target, b"x" * 1_000_000)
        resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))

        self.assertEqual(target.read_bytes(), b"previous")
        self.assertEqual([p.name for p in target.parent.iterdir()], ["data.json"])

    def test_symlink_at_target_is_replaced_not_followed(self):
        victim = self.xdg_cache.parent / "victim.txt"
        victim.write_text("untouched")
        target = utils.get_summawise_dir() / "data.json"
        target.symlink_to(victim)

        FileUtils.write_bytes(target, b"new")

        self.assertEqual(victim.read_text(), "untouched")
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_bytes(), b"new")


class MalformedFileCacheTests(CacheTestCase):

    def malformed_variants(self):
        valid = b'{"hash": "file-1"}'
        return {
            "truncated json": ("file_cache.json", valid[:-4]),
            "non-utf8": ("file_cache.json", b'{"hash": "\xff\xfe"}'),
            "json array": ("file_cache.json", b"[1, 2]"),
            "json null": ("file_cache.json", b"null"),
            "empty file": ("file_cache.json", b""),
            "deeply nested": ("file_cache.json", b"[" * 100_000),
            "truncated gzip": ("file_cache.json.gz", gzip.compress(valid)[:-10]),
            "corrupt gzip stream": ("file_cache.json.gz", gzip.compress(valid)[:12] + b"\xff" * 8),
            "gzip of non-utf8": ("file_cache.json.gz", gzip.compress(b'{"a": "\xff"}')),
        }

    def test_from_file_raises_malformed_cache_error(self):
        for name, (filename, content) in self.malformed_variants().items():
            with self.subTest(name):
                path = utils.get_summawise_dir() / filename
                path.write_bytes(content)

                with self.assertRaises(MalformedCacheError):
                    FileCacheObj.from_file(path)

    def test_load_starts_empty_sets_file_aside_and_next_save_is_read_back(self):
        for name, (filename, content) in self.malformed_variants().items():
            with self.subTest(name):
                cache_dir = utils.get_summawise_dir()
                for stale in cache_dir.iterdir():
                    stale.unlink()
                path = cache_dir / filename
                path.write_bytes(content)

                with mock.patch("builtins.print"):
                    cache = FileCacheObj.load()

                self.assertIsNone(cache.get_file_id_by_hash("hash"))
                self.assertEqual(path.with_name(filename + ".corrupt").read_bytes(), content)
                cache.set_hash_file_id("hash", "file-2")
                cache.save()
                self.assertEqual(FileCacheObj.load().get_file_id_by_hash("hash"), "file-2")

    def test_non_string_values_are_dropped_and_valid_entries_kept(self):
        (utils.get_summawise_dir() / "file_cache.json").write_text('{"a": "file-1", "b": 2, "c": null}')

        cache = FileCacheObj.load()

        self.assertEqual(cache.get_file_id_by_hash("a"), "file-1")
        self.assertIsNone(cache.get_file_id_by_hash("b"))

    def test_instances_do_not_share_entries(self):
        FileCacheObj().set_hash_file_id("hash", "file-1")

        self.assertIsNone(FileCacheObj().get_file_id_by_hash("hash"))


class PrivateFileModeTests(CacheTestCase):

    def test_every_persisted_file_is_0600_regardless_of_umask(self):
        old_umask = os.umask(0)
        self.addCleanup(os.umask, old_umask)
        metadata = FileMetadata(
            hash="abc", name="a.txt", full_path="/x/a.txt", sz_bytes=3,
            created_at=1.0, last_modified_at=2.0, last_accessed_at=3.0,
            vector_store_id="vs_1", file_id="file_1",
        )
        transcript = Transcript("vid", [TranscriptEntry("hello", 1.5, 2.0)], vector_store_id="vs_2", file_id="file_2")
        cache_dir = utils.get_summawise_dir()

        for compress in (True, False):
            with self.subTest(compress=compress):
                for stale in cache_dir.rglob("*"):
                    if stale.is_file():
                        stale.unlink()
                Settings().compression = compress
                FileCacheObj({"hash": "file-1"}).save()
                metadata.save_to_file(cache_dir / "files" / "abc.json", compress=compress)
                transcript.save_to_file(cache_dir / "youtube" / "transcript_vid.json", compress=compress)
                Settings.save()

                files = [p for p in cache_dir.rglob("*") if p.is_file()]
                self.assertEqual(len(files), 4)
                for path in files:
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600, path)
                for subdir in ("files", "youtube"):
                    self.assertEqual(stat.S_IMODE((cache_dir / subdir).stat().st_mode), 0o700, subdir)


class LegacySettingsRemovalTests(CacheTestCase):

    def legacy_path(self) -> Path:
        return self.shared_tmp / "summawise" / "settings.json"

    def plant(self) -> Path:
        path = self.legacy_path()
        path.parent.mkdir()
        path.write_text('{"api_key": "sk-old"}')
        return path

    def test_init_deletes_legacy_settings_file_owned_by_user(self):
        path = self.plant()

        with mock.patch.object(Settings, "prompt", side_effect=RuntimeError("stop after cleanup")), \
                self.assertRaises(RuntimeError):
            Settings.init()

        self.assertFalse(path.exists())

    def test_missing_legacy_file_is_not_an_error(self):
        Settings.remove_legacy_file()

    def test_legacy_symlink_is_left_alone(self):
        target = self.xdg_cache.parent / "elsewhere.json"
        target.write_text("keep")
        path = self.legacy_path()
        path.parent.mkdir()
        path.symlink_to(target)

        Settings.remove_legacy_file()

        self.assertTrue(path.is_symlink())
        self.assertEqual(target.read_text(), "keep")

    def test_legacy_file_owned_by_another_user_is_left_alone(self):
        path = self.plant()

        with mock.patch.object(os, "getuid", return_value=os.getuid() + 1):
            Settings.remove_legacy_file()

        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
