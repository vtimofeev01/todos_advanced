from app import create_app
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app("development")

#
# @app.cli.command()
# def test():
#     """Runs the unit tests."""
#     import sys
#     import unittest
#
#     tests = unittest.TestLoader().discover("tests")
#     result = unittest.TextTestRunner(verbosity=2).run(tests)
#     if result.errors or result.failures:
#         sys.exit(1)
