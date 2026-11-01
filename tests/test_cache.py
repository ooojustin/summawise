import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from summawise import ai  # noqa: F401  (must load before settings: settings <-> ai import cycle)
from summawise.api_objects import AssistantList, ThreadList
from summawise.data import DataMode
from summawise.files.cache import FileCacheObj
from summawise.settings import Settings
from summawise.utils import Singleton


class FileCacheRoundTripTests(unittest.TestCase):

    def setUp(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        patch = mock.patch.object(tempfile, "tempdir", str(root))
        patch.start()
        self.addCleanup(patch.stop)

        Singleton._instances.clear()
        self.addCleanup(Singleton._instances.clear)
        Settings(
            api_key="test-key",
            assistant_id="",
            model="gpt-4o",
            compression=True,
            data_mode=DataMode.JSON,
            code_style="monokai",
            assistants=AssistantList(),
            threads=ThreadList(),
        )

    def test_gzipped_file_cache_is_restored_on_load(self):
        # explicit dict: FileCacheObj() shares a mutable default
        FileCacheObj({"round-trip-hash": "file-123"}).save()

        loaded = FileCacheObj.load()

        self.assertEqual(loaded.get_file_id_by_hash("round-trip-hash"), "file-123")


if __name__ == "__main__":
    unittest.main()
