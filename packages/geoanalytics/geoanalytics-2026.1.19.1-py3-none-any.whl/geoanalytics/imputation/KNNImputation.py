# K-Nearest Neighbors (KNN)-based missing value imputation for multidimensional data with runtime and memory tracking,
# and support for saving the imputed dataset.
#
# **Importing and Using the KNNImputation Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.imputation import KNNImputation
#
#             df = pd.read_csv('input.csv')
#
#             knn_imputer = KNNImputation(df)
#
#             imputed_df = knn_imputer.run(n_neighbors=5)
#
#             knn_imputer.getRuntime()
#
#             knn_imputer.getMemoryUSS()
#
#             knn_imputer.getMemoryRSS()
#
#             knn_imputer.save('KNN.csv')
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
from tqdm import tqdm
import pandas as pd
from sklearn.impute import KNNImputer

class KNNImputation:
    """
    **About this algorithm**

    :**Description**:
        K-Nearest Neighbors (KNN) Imputation estimates missing values by finding the `k` nearest samples
        (rows) in the dataset and imputing missing values based on the average (or weighted average) of
        those neighbors' corresponding feature values.

    :**Parameters**:
        - Dataset (pandas DataFrame) must be provided during object initialization.
        - Number of neighbors `n_neighbors` is specified during the `run()` call.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- The input data with 'x', 'y' coordinates and features.
        - **imputedDF** (*pd.DataFrame*) -- DataFrame after filling in missing values.
        - **startTime, endTime** (*float*) -- Variables to track execution time.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage of the imputation process in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.imputation import KNNImputation

            df = pd.read_csv("input.csv")

            knn_imputer = KNNImputation(df)

            imputed_df = knn_imputer.run(n_neighbors=5)

            knn_imputer.getRuntime()
            knn_imputer.getMemoryUSS()
            knn_imputer.getMemoryRSS()

            knn_imputer.save('KNN.csv')

    **Credits**

    This implementation was created by Raashika and revised by M.Charan Teja
    under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe):
        self.df = dataframe.copy()
        self.df.columns = ['x', 'y'] + list(self.df.columns[2:])
        self.imputedDF = None
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


    def run(self, n_neighbors=5):
        """
        Executes the KNN Imputation algorithm by replacing missing values based on nearest neighbor averages.

        :param n_neighbors: int, number of neighbors to use for imputation (default: 5)
        :return: imputedDF (pd.DataFrame) -- DataFrame with missing values filled
        """
        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)
        imputedArray = KNNImputer(n_neighbors=n_neighbors).fit_transform(data)
        imputedData = pd.DataFrame(imputedArray, columns=data.columns)
        self.imputedDF = pd.concat([xy, imputedData], axis=1)

        self.endTime = time.time()

        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.imputedDF


    def save(self, outputFile='KNN.csv'):
        """
        Saves the imputed DataFrame to a CSV file.

        :param outputFile: str, filename to save the imputed data (default: 'KNN.csv')
        """
        if self.imputedDF is not None:
            try:
                self.imputedDF.to_csv(outputFile, index=False)
                print(f"Imputed data saved to: {outputFile}")
            except Exception as e:
                print(f"Failed to save labels: {e}")
        else:
            print("No imputed data to save. Run impute() first")