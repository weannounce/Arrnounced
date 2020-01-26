#!/usr/bin/env python3

import unittest
import sys, os

sys.path.append("src/")

if __name__ == "__main__":
    suite = unittest.TestLoader().discover('.', pattern = "test_*.py")
    unittest.TextTestRunner(verbosity=2).run(suite)
