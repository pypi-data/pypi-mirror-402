import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from srmhga import SRMHGA, Config
from srmhga.aqsrl.config import AQSRLConfig
from srmhga.dv.sqlite_vault import SQLiteDeterministicVault
from srmhga.embeddings.providers import HashEmbeddingProvider


class TestStack(unittest.TestCase):
    def test_write_and_read(self):
        emb = HashEmbeddingProvider(dim=32)
        hga = SRMHGA(embedder=emb, dv=SQLiteDeterministicVault(":memory:"), aqsrl_config=AQSRLConfig(K=4, bootstrap_min_items=4), config=Config(alpha=0.05, delta_min=0.0))
        hga.write_fact("fav_color", "blue", provenance={"src": "test"})
        hga.write_semantic("I like pizza", meta={"tags": ["pref"]})
        # bootstrap items
        for i in range(3):
            hga.write_semantic(f"note {i}")
        res = hga.read("fav color", mode="auto", resolve_pointers=True, limit=5)
        self.assertIn(res.path.value, {"FAST_SEMANTIC", "DETERMINISTIC"})
        # deterministic should find the fact
        res2 = hga.read("fav_color", mode="force_dv", resolve_pointers=True)
        self.assertGreaterEqual(len(res2.vault_hits), 1)


if __name__ == "__main__":
    unittest.main()
