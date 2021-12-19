#!/usr/bin/env python3

import argparse
import unittest
import sys
import coverage

sys.path.append("arrnounced/")

cov = coverage.coverage(
    branch=True, include="arrnounced/*", omit=["*/__init__.py", "*/config/*"]
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Arrnounced integration tests")
    parser.add_argument(
        "test", type=str, help="Which tests to run", nargs="?", default="*"
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(1)

    cov.start()

    suite = unittest.TestLoader().discover(".", pattern="test_{}.py".format(args.test))
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory="./coverage")
    cov.erase

    sys.exit(0 if result.wasSuccessful() else 1)
