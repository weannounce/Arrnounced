#!/usr/bin/env python3

import unittest
import sys, os
import coverage

sys.path.append("src/")

cov = coverage.coverage(
        branch=True,
        include='src/*',
        omit=['*/__init__.py', '*/config/*']
    )

if __name__ == "__main__":
    cov.start()

    suite = unittest.TestLoader().discover('.', pattern = "test_*.py")
    unittest.TextTestRunner(verbosity=2).run(suite)

    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory="./coverage")
    cov.erase
