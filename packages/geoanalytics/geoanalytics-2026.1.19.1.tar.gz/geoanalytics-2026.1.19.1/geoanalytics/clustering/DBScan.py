# DBScan-based clustering algorithm using scikit-learn to assign cluster labels
# to multidimensional data with runtime and memory tracking, and support for saving results.
#
# **Importing and Using the DBScan Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.clustering import DBScan
#
#             df = pd.read_csv('input.csv')
#
#             db = DBScan(df)
#
#             labels_df = db.run(ep=50, min_sample=3)
#
#             db.getRuntime()
#
#             db.getMemoryUSS()
#
#             db.getMemoryRSS()
#
#             db.save('DBScanLabels.csv')
#

__copyright__ = """
Copyright (C)  2022 Rage Uday Kiran

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import time
import psutil
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn.cluster import DBSCAN as DBSCAN
import pandas as pd


class DBScan:
    """
    **About this algorithm**

    :**Description**:
        DBSCAN (Density-Based Spatial Clustering of Applications with Noise) is a density-based
        clustering algorithm. It groups together points that are closely packed together, while
        marking points that lie alone in low-density regions as outliers. This wrapper supports
        runtime and memory tracking and allows saving of clustering results.

    :**Parameters**:
        - Dataset (pandas DataFrame) must be provided during object initialization.
        - Clustering parameters can be passed to the run method.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- The input data with 'x', 'y' coordinates and features.
        - **labelsDF** (*pd.DataFrame*) -- DataFrame containing 'x', 'y', and assigned cluster labels.
        - **startTime, endTime** (*float*) -- Variables to track clustering execution time.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage of the clustering process in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.clustering import DBScan

            df = pd.read_csv("input.csv")

            db = DBScan(df)

            labels_df = db.run(ep=50, min_sample=3)

            db.getRuntime()
            db.getMemoryUSS()
            db.getMemoryRSS()

            db.save('DBScanLabels.csv')

    **Credits**

    This implementation was created by Raashika and revised by M.Charan Teja under the guidance of Professor Rage Uday Kiran.
    """

    def __init__(self, dataframe):
        """
        Constructor: Initializes the DBScan clustering wrapper with input DataFrame.

        :param dataframe: pd.DataFrame with 'x', 'y' and other feature columns
        """
        self.df = dataframe.copy()
        self.df.columns = ['x', 'y'] + list(self.df.columns[2:])
        self.labelsDF = None
        self.startTime = None
        self.endTime = None
        self.memoryUSS = None
        self.memoryRSS = None

    def getRuntime(self):
        """
        Prints the total runtime of the clustering algorithm.
        """
        print("Total Execution time of proposed Algorithm:", self.endTime - self.startTime, "seconds")

    def getMemoryUSS(self):
        """
        Prints the memory usage (USS) of the process in kilobytes.
        """
        print("Memory (USS) of proposed Algorithm in KB:", self.memoryUSS)

    def getMemoryRSS(self):
        """
        Prints the memory usage (RSS) of the process in kilobytes.
        """
        print("Memory (RSS) of proposed Algorithm in KB:", self.memoryRSS)

    def run(self, ep = 50, min_sample = 3):
        """
        Executes DBScan clustering algorithm.

        :param ep: float, The maximum distance between two samples for one to be considered as in the neighborhood of the other. (default: 50)
        :param min_sample: int, The number of samples (or total weight) in a neighborhood for a point to be considered as a core point. (default: 3)

        :return: labelsDF (pd.DataFrame) with columns ['x', 'y', 'labels']
        """

        self.startTime = time.time()
        data = self.df.drop(['x', 'y'], axis=1)
        data = data.to_numpy()
        dbs = DBSCAN(eps=ep, min_samples=min_sample).fit(data)
        label = self.df[['x', 'y']]
        self.labelsDF = label.assign(labels=dbs.labels_)

        self.endTime = time.time()

        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.labelsDF

    def save(self, outputFileLabels='DBScanLabels.csv'):
        """
        Saves the clustering result with labels to a CSV file.

        :param outputFileLabels: str, filename for saving labels (default: 'DBScanLabels.csv')
        """
        if self.labelsDF is not None:
            try:
                self.labelsDF.to_csv(outputFileLabels, index=False)
                print(f"Labels saved to: {outputFileLabels}")
            except Exception as e:
                print(f"Failed to save labels: {e}")
        else:
            print("No labels to save. Please execute run() method first.")