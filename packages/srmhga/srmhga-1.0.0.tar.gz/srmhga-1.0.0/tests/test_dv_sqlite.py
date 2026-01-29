import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from srmhga.core.types import Policy, Sensitivity
from srmhga.dv.sqlite_vault import SQLiteDeterministicVault


class TestSQLiteDV(unittest.TestCase):
    def test_write_read_and_search(self):
        dv = SQLiteDeterministicVault(":memory:")
        dv.write_fact("city", "Izmir", provenance={"src": "test"}, policy=Policy.USER_CONFIRMED, sensitivity=Sensitivity.MEDIUM)
        dv.write_episodic("Went to the library.", meta={"tags": ["life"]}, policy=Policy.AUDITABLE)
        doc_id = dv.write_document("Semantic routing memory is fast.", meta={"tags": ["srm"]})

        rec = dv.read_exact("fact:city")
        self.assertEqual(rec["value"], "Izmir")

        hits = dv.search("semantic", limit=10)
        self.assertTrue(any(h.kind in {"doc", "episode", "fact"} for h in hits))

        self.assertTrue(dv.delete(f"doc:{doc_id}"))


if __name__ == "__main__":
    unittest.main()
