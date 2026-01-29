import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from srmhga.core.config import Config
from srmhga.triage.triage import UBTPGate, TriagePath


class TestTriage(unittest.TestCase):
    def test_high_sensitivity_forces_dv(self):
        gate = UBTPGate(Config(alpha=0.1, delta_min=0.0))
        d = gate.decide("What is my IBAN?", conf=1.0, margin=1.0)
        self.assertEqual(d.path, TriagePath.DETERMINISTIC)


if __name__ == "__main__":
    unittest.main()
