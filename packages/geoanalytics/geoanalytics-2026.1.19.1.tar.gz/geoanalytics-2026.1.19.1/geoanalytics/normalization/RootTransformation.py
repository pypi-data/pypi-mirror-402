# RootTransformation Class for Feature Normalization Using Root Scaling

# **Importing and Using the RootTransformation Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import RootTransformation
#
#             df = pd.read_csv("input.csv")
#
#             transformer = RootTransformation(df, root=3)
#
#             normalized_df = transformer.run()
#
#             transformer.getRuntime()
#
#             transformer.getMemoryUSS()
#
#             transformer.getMemoryRSS()
#
#             transformer.save("RootTransformation.csv")
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
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler


class RootTransformation:
    """
    **About this algorithm**

    :**Description**:
        RootTransformation applies a root-based transformation to all feature values
        in the input dataset. This is useful for reducing the effect of large outliers
        and compressing the range of high magnitude values. For example, a square root
        (root=2) transformation is commonly used to stabilize variance in skewed datasets.

    :**Parameters**:
        - `dataframe` (*pd.DataFrame*): Input DataFrame with 'x', 'y' coordinates and feature columns.
        - `root` (*int*, optional): Degree of the root transformation. Defaults to 2 (square root).

    :**Attributes**:
        - **df** (*pd.DataFrame*): Original input DataFrame with renamed first two columns as 'x' and 'y'.
        - **normalizedDF** (*pd.DataFrame*): DataFrame containing root-transformed features.
        - **startTime, endTime** (*float*): Execution timestamps.
        - **memoryUSS, memoryRSS** (*float*): Memory usage statistics in KB.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.normalization import RootTransformation

            df = pd.read_csv("input.csv")

            transformer = RootTransformation(df, root=3)

            normalized_df = transformer.run()

            transformer.getRuntime()

            transformer.getMemoryUSS()

            transformer.getMemoryRSS()

            transformer.save("RootTransformation.csv")


    **Credits**

    Developed by Raashika and M. Charan Teja, supervised by Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe, root = 2):
        """
        Initializes the RootTransformation object with a copy of the dataframe.
        """
        self.df = dataframe.copy()
        self.root = root
        self.df.columns = ['x', 'y'] + list(self.df.columns[2:])
        self.normalizedDF = None
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


    def run(self):
        """
        Executes the root transformation on the dataset.

        Returns:
            pd.DataFrame: DataFrame with 'x', 'y', and root-transformed features.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        normalizedData = data ** (1 / self.root)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='RootTransformation.csv'):
        """
        Saves the Normalized DataFrame to a CSV file.
        """
        if self.normalizedDF is not None:
            try:
                self.normalizedDF.to_csv(outputFile, index=False)
                print(f"Normalized data saved to: {outputFile}")
            except Exception as e:
                print(f"Failed to save labels: {e}")
        else:
            print("No Normalized data to save. Execute run() method first")