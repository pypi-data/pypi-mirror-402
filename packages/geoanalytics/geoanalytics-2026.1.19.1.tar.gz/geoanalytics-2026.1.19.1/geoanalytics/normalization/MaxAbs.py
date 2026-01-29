# MaxAbs Class for Normalizing Features Using Maximum Absolute Scaling

# **Importing and Using the MaxAbs Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import MaxAbs
#
#             df = pd.read_csv("input.csv")
#
#             scaler = MaxAbs(df)
#
#             normalized_df = scaler.run()
#
#             scaler.getRuntime()
#
#             scaler.getMemoryUSS()
#
#             scaler.getMemoryRSS()
#
#             scaler.save("MaxAbs.csv")
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
from sklearn.preprocessing import MaxAbsScaler


class MaxAbs:
    """
    **About this algorithm**

    :**Description**:
        MaxAbs is a normalization technique that scales each feature by its maximum absolute value.
        It is particularly useful when features contain both positive and negative values,
        ensuring all values lie within the range [-1, 1]. This class also tracks runtime and memory usage.

    :**Parameters**:
        - `dataframe` (*pd.DataFrame*): Input DataFrame containing 'x', 'y', and feature columns.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- Original DataFrame with standardized column names.
        - **normalizedDF** (*pd.DataFrame*) -- Output DataFrame after MaxAbs scaling.
        - **startTime, endTime** (*float*) -- Time tracking variables.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage in kilobytes (USS and RSS).

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.normalization import MaxAbs

            df = pd.read_csv("input.csv")

            scaler = MaxAbs(df)

            normalized_df = scaler.run()

            scaler.getRuntime()

            scaler.getMemoryUSS()

            scaler.getMemoryRSS()

            scaler.save("MaxAbs.csv")


    **Credits**

    This implementation was created by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe):
        """
        Initializes the MaxAbs object with a copy of the dataframe.
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
        Executes the MaxAbs scaling normalization on the dataset.

        Returns:
            pd.DataFrame: DataFrame containing 'x', 'y', and MaxAbs-normalized feature values.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        scaler = MaxAbsScaler()
        normalizedData = scaler.fit_transform(data)
        normalizedData = pd.DataFrame(normalizedData, columns=data.columns, index=data.index)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='MaxAbs.csv'):
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