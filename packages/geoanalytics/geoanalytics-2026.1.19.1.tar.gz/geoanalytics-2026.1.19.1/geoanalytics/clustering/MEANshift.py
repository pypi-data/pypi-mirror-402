# MeanShift-based clustering algorithm using scikit-learn to assign cluster labels
# to multidimensional data with runtime and memory tracking, and support for saving results.
#
# **Importing and Using the MEANshift Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.clustering import MEANshift
#
#             df = pd.read_csv('input.csv')
#
#             ms = MEANshift(df)
#
#             labels_df, centers = ms.run(bandwidth=None, max_iter=300)
#
#             ms.getRuntime()
#
#             ms.getMemoryUSS()
#
#             ms.getMemoryRSS()
#
#             ms.save('MeanShiftLabels.csv', 'MeanShiftCenters.csv')
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
from sklearn.cluster import MeanShift
import pandas as pd


class MEANshift:
    """
    **About this algorithm**

    :**Description**:
        MeanShift is a centroid-based clustering algorithm that seeks modes (i.e., high-density
        areas) in the feature space. It does not require predefining the number of clusters. This
        wrapper performs MeanShift clustering on input data, tracks memory and execution time, and
        supports exporting results.

    :**Parameters**:
        - Dataset (pandas DataFrame) must be provided during object initialization.
        - Clustering hyperparameters can be passed to the run method.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- The input data with 'x', 'y' coordinates and features.
        - **labelsDF** (*pd.DataFrame*) -- DataFrame containing 'x', 'y', and assigned cluster labels.
        - **centers** (*ndarray*) -- The cluster centers estimated by MeanShift.
        - **startTime, endTime** (*float*) -- Variables to track clustering execution time.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage of the clustering process in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.clustering import MEANshift

            df = pd.read_csv("input.csv")

            ms = MEANshift(df)

            labels_df, centers = ms.run(bandwidth=None, max_iter=300)

            ms.getRuntime()
            ms.getMemoryUSS()
            ms.getMemoryRSS()

            ms.save('MeanShiftLabels.csv', 'MeanShiftCenters.csv')

    **Credits**

    This implementation was created by Raashika and revised by M.Charan Teja
    under the guidance of Professor Rage Uday Kiran.
    """

    def __init__(self, dataframe):
        self.df = dataframe.copy()
        self.df.columns = ['x', 'y'] + list(self.df.columns[2:])
        self.labelsDF = None
        self.centers = None
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

    def run(self, bandwidth=None, max_iter=300):
        """
        Executes MeanShift clustering algorithm.

        :param bandwidth: float or None, bandwidth for window size. If None, it will be estimated automatically.
        :param max_iter: int, maximum number of iterations (default: 300)

        :return: (labelsDF, centers)
                 labelsDF (pd.DataFrame) -- DataFrame with 'x', 'y', and cluster labels
                 centers (np.ndarray) -- Coordinates of cluster centers
        """
        self.startTime = time.time()
        data = self.df.drop(['x', 'y'], axis=1)
        data = data.to_numpy()
        meanShift = MeanShift(max_iter=max_iter).fit(data)
        label = self.df[['x', 'y']]
        self.labelsDF = label.assign(labels=meanShift.labels_)
        self.centers = meanShift.cluster_centers_

        self.endTime = time.time()

        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.labelsDF, self.centers

    def save(self, outputFileLabels='MeanShiftLabels.csv', outputFileCenters='MeanShiftCenters.csv'):
        """
        Saves the clustering result and cluster centers to CSV files.

        :param outputFileLabels: str, filename to save label results (default: 'MeanShiftLabels.csv')
        :param outputFileCenters: str, filename to save cluster centers (default: 'MeanShiftCenters.csv')
        """
        if self.labelsDF is not None:
            try:
                self.labelsDF.to_csv(outputFileLabels, index=False)
                print(f"Labels saved to: {outputFileLabels}")
            except Exception as e:
                print(f"Failed to save labels: {e}")
        else:
            print("No labels to save. Please execute run() method first.")

        if self.centers is not None:
            try:
                pd.DataFrame(self.centers).to_csv(outputFileCenters, index=False)
                print(f"Cluster centers saved to: {outputFileCenters}")
            except Exception as e:
                print(f"Failed to save cluster centers: {e}")
        else:
            print("No cluster centers to save. Please execute run() method first.")