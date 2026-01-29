import unittest
import matplotlib.pyplot as plt
import scanpy as sc
import scez
import tomli

toml_dict = tomli.load(open('pyproject.toml','rb'))
version = toml_dict['tool']['poetry']['version']

class TestScezConfig(unittest.TestCase):
    def test_version(self):
        self.assertEqual(scez.__version__, version)

    def test_scanpy_settings(self):
        self.assertEqual(sc.settings.verbosity, 1)

if __name__ == '__main__':
    unittest.main()