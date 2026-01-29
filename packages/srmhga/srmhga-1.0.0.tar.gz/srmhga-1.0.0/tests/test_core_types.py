import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from srmhga.core.types import MemoryItem, MemoryMetadata, VaultPointer


class TestCoreTypes(unittest.TestCase):
    def test_hash_changes_with_metadata(self):
        meta1 = MemoryMetadata(tags=["a"], importance=0.3)
        item = MemoryItem(id="x", code=1, ptr=VaultPointer("sqlite", "fact", "k"), meta=meta1)
        h1 = item.hash
        meta2 = meta1.with_updates(access_count=meta1.access_count + 1)
        item2 = item.with_updates(meta=meta2)
        self.assertNotEqual(h1, item2.hash)
        self.assertTrue(item2.verify_integrity())


if __name__ == "__main__":
    unittest.main()
