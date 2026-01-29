# AffinityPropagationWrapper-based clustering algorithm using scikit-learn to assign cluster labels
# to multidimensional data with runtime and memory tracking, and support for saving results.
#
# **Importing and Using the AffinityPropagationWrapper Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.clustering import AffinityPropagationWrapper
#
#             df = pd.read_csv('input.csv')
#
#             ap = AffinityPropagationWrapper(df)
#
#             output = ap.run()
#
#             labels_df = output[0]
#
#             centers = output[1]
#
#             ap.getRuntime()
#
#             ap.getMemoryUSS()
#
#             ap.getMemoryRSS()
#
#             ap.save('AffinityPropagationWrapperLabels.csv', 'AffinityPropagationWrapperCenters.csv')
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
from sklearn.cluster import AffinityPropagation
from sklearn.preprocessing import StandardScaler
import pandas as pd


class AffinityPropagationWrapper:
    """
    **About this algorithm**

    :**Description**:
        Affinity Propagation is a message-passing-based clustering algorithm that identifies exemplars
        (cluster centers) among the data points and forms clusters around these exemplars. This wrapper
        automatically tracks runtime and memory usage, and supports saving clustering outputs to CSV.

    :**Parameters**:
        - Dataset (pandas DataFrame) must be provided during object initialization.
        - No other parameters are required during instantiation.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- The input data with 'x', 'y' coordinates and features.
        - **labelsDF** (*pd.DataFrame*) -- DataFrame containing 'x', 'y', and assigned cluster labels.
        - **centers** (*np.ndarray*) -- Coordinates of the identified cluster centers.
        - **startTime, endTime** (*float*) -- Track clustering runtime.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage statistics in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.clustering import AffinityPropagationWrapper

            df = pd.read_csv("input.csv")

            ap = AffinityPropagationWrapper(df)

            output = ap.run()

            labels_df = output[0]

            centers = output[1]

            ap.getRuntime()
            ap.getMemoryUSS()
            ap.getMemoryRSS()

            ap.save('AffinityLabels.csv', 'AffinityCenters.csv')

    **Credits**

    This implementation was created by Raashika and revised by M.Charan Teja under the guidance of Professor Rage Uday Kiran.
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

    def run(self, damping = 0.5, max_iter=300, convergence_iter=15, affinity='euclidean', random_state=None, preference=None):
        """
        Executes the affinity propagation clustering algorithm.

        Args:
            damping (float): Damping factor for affinity propagation.
            max_iter (int): Maximum number of iterations.
            convergence_iter (int): Number of iterations with no change to declare convergence.
            affinity (str): Metric used to compute the affinity matrix ('euclidean' or other).
            random_state (int or None): Random seed for reproducibility.
            preference (array_like or None): Preferences for each point (higher values attract more clusters).

        Returns:
            pd.DataFrame, np.ndarray: DataFrame with 'x', 'y', and assigned labels; cluster centers.

        """
        self.startTime = time.time()
        data = self.df.drop(['x', 'y'], axis=1)
        data = data.to_numpy()
        X = StandardScaler().fit_transform(data)
        affinityProp = AffinityPropagation(damping=float(damping), max_iter=int(max_iter),
                                           convergence_iter=int(convergence_iter), affinity=affinity,
                                           preference=preference, random_state=random_state).fit(X)
        label = self.df[['x', 'y']]
        self.labelsDF = label.assign(labels=affinityProp.labels_)
        self.centers = affinityProp.cluster_centers_

        self.endTime = time.time()

        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.labelsDF, self.centers

    def save(self, outputFileLabels='AffinityLabels.csv', outputFileCenters='AffinityCenters.csv'):
        """
        Saves the clustering results to CSV files.

        :param outputFileLabels: str, filename for saving labels (default: 'AffinityLabels.csv')
        :param outputFileCenters: str, filename for saving centers (default: 'AffinityCenters.csv')
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