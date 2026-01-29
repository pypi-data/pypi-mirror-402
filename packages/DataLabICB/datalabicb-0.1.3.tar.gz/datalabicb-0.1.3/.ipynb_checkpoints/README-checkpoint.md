# DataLabICB

Python tools for loading, manipulating, and analyzing datasets used in the ICB laboratory.  
This package provides:

- compressed datasets (`.json.gz`)
- a simple interface to load them (`Datasets`)
- utility functions (chemistry)

---

#  Installation

pip install datalabicb

# Usage 

from DataLabICB.chemistry import Datasets

datasets = Datasets()

## Absorptions datasets
dfs = datasets.adsorption_data()

## Isotherms datasets
dfs = datasets.isotherms()

## Isobars datasets
dfs = datasets.isobars()

## Heats of adsorption datasets
dfs = datasets.heat_of_adsorption()

dfs[n].attrs('comments') contains the characteristics of each dataset

