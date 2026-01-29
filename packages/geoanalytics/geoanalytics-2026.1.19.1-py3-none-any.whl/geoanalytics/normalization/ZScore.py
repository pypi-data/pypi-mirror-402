# ZScore Class for Feature Normalization Using Standard Score (Z-Score)

# **Importing and Using the ZScore Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import ZScore
#
#             df = pd.read_csv("input.csv")
#
#             normalizer = ZScore(df)
#
#             normalized_df = normalizer.run()
#
#             normalizer.getRuntime()
#
#             normalizer.getMemoryUSS()
#
#             normalizer.getMemoryRSS()
#
#             normalizer.save("ZScore.csv")
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
from sklearn.preprocessing import StandardScaler


class ZScore:
    """
    **About this algorithm**

    :**Description**:
        ZScore normalization (also called standard score normalization) scales each feature so that it has
        a mean of 0 and a standard deviation of 1. This is useful when features are normally distributed
        and ensures that each contributes equally to distance-based models.

    :**Parameters**:
        - `dataframe` (*pd.DataFrame*): Input DataFrame containing 'x', 'y' coordinates and feature values.

    :**Attributes**:
        - **df** (*pd.DataFrame*): Input DataFrame with standardized columns ('x', 'y', ...features).
        - **normalizedDF** (*pd.DataFrame*): Output DataFrame after z-score normalization.
        - **startTime, endTime** (*float*): Time tracking for execution.
        - **memoryUSS, memoryRSS** (*float*): Memory usage metrics in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        import pandas as pd

        from geoanalytics.normalization import ZScore

        df = pd.read_csv("input.csv")

        normalizer = ZScore(df)

        normalized_df = normalizer.run()

        normalizer.getRuntime()

        normalizer.getMemoryUSS()

        normalizer.getMemoryRSS()

        normalizer.save("ZScore.csv")


    **Credits**

    Developed by Raashika and M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe):
        """
        Initializes the ZScore object with a copy of the dataframe.
        """
        self.df = dataframe.copy()
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
        Applies Z-Score normalization to the dataset.

        Returns:
            pd.DataFrame: DataFrame with 'x', 'y', and normalized feature columns.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        scaler = StandardScaler()
        normalizedData = scaler.fit_transform(data)
        normalizedData = pd.DataFrame(normalizedData, columns=data.columns, index=data.index)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='ZScore.csv'):
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