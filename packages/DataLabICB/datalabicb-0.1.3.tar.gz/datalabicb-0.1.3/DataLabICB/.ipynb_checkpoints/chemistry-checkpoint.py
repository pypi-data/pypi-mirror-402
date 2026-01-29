import json
import gzip
import pandas as pd
import importlib.resources as resources


class Datasets:
    # Lecture du fichier JSON compressé
    def __init__(self):
        json_file = "datasets/chemistry/isotherm_all.json.gz"
        file_path = resources.files("DataLabICB").joinpath(json_file)
        with gzip.open(file_path, 'rb') as file:
            self.all_data = json.load(file)

    def _search(self, iso):
        dfs = []
        # filtrage par type d'iso et création des dataframes
        for block in self.all_data:
            df = pd.DataFrame(block["data"])
            comments = [comment.lower() for comment in block["comments"]]
            if any(iso in comment for comment in comments):
                df.attrs["comments"] = block["comments"]
                dfs.append(df)
        return dfs

    # Conversion de toutes les données au format JSON en dataframes
    def adsorption_data(self):
        dfs = []
        # Création de la DataFrame à partir de la liste 'data '
        for block in self.all_data:
            df = pd.DataFrame(block["data"])
            df.attrs["comments"] = block["comments"]
            dfs.append(df)
        return dfs

    # Ensemble des datasets
    def isotherms(self):
        return self._search("isotherm")

    # Filtrage des datasets par isobar
    def isobars(self):
        return self._search("isobar")

    # Filtrage des datasets par heat of adsorption
    def heat_of_adsorption(self):
        return self._search("heat of adsorption")