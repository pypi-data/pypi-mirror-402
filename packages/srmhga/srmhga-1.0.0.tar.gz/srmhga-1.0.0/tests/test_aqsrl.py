import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from srmhga.aqsrl.aqsrl import AQSRL
from srmhga.aqsrl.config import AQSRLConfig
from srmhga.core.types import MemoryMetadata
from srmhga.embeddings.providers import HashEmbeddingProvider


class TestAQSRL(unittest.TestCase):
    def test_bootstrap_and_route(self):
        emb = HashEmbeddingProvider(dim=32)
        cfg = AQSRLConfig(K=4, m=2, top_k=5, bootstrap_min_items=4)
        aqsrl = AQSRL(emb, cfg)
        for i in range(4):
            aqsrl.write_semantic(item_id=f"it:{i}", text=f"hello world {i}", ptr=None, meta=MemoryMetadata(tags=["t"]), summary="")
        items, diags = aqsrl.route("hello world", top_k=3)
        self.assertGreaterEqual(len(items), 1)
        self.assertGreaterEqual(diags.conf, 0.0)


if __name__ == "__main__":
    unittest.main()
