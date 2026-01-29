"""scez – Single Cell Analysis, Easy Mode!"""

from . import diffexp as de
from . import preprocess as pp
from . import representation as rp
from . import utils
import scanpy as sc
import matplotlib.pyplot as plt

import tomli
from pathlib import Path

with open(Path(__file__).parent.parent / 'pyproject.toml', 'rb') as f:
    toml_dict = tomli.load(f)
__version__ = toml_dict['project']['version']


sc.settings.verbosity = 1             # verbosity: errors (0), warnings (1), info (2), hints (3)
sc.settings.set_figure_params(dpi=100, dpi_save=300, frameon=False, figsize=(5, 5), facecolor='white')
sc.logging.print_header()

# https://stackoverflow.com/questions/21884271/warning-about-too-many-open-figures
plt.rcParams.update({'figure.max_open_warning': 0})
plt.close('all')

# https://stackoverflow.com/questions/3899980/how-to-change-the-font-size-on-a-matplotlib-plot

SMALL_SIZE = 6
MEDIUM_SIZE = 8
BIGGER_SIZE = 10

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # font size of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # font size of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # font size of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # font size of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend font size
plt.rc('figure', titlesize=BIGGER_SIZE)  # font size of the figure title
