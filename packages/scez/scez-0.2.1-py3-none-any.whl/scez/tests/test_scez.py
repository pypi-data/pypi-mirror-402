import unittest
import matplotlib.pyplot as plt
import scanpy as sc
import scez
import tomli

with open('pyproject.toml', 'rb') as f:
    toml_dict = tomli.load(f)
version = toml_dict['project']['version']

class TestScezConfig(unittest.TestCase):
    def test_version(self):
        self.assertEqual(scez.__version__, version)

    def test_scanpy_settings(self):
        self.assertEqual(sc.settings.verbosity, 1)

if __name__ == '__main__':
    unittest.main()