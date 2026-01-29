# RobustScaling Class for Feature Normalization Using Robust Scaling

# **Importing and Using the RobustScaling Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import RobustScaling
#
#             df = pd.read_csv("input.csv")
#
#             scaler = RobustScaling(df)
#
#             normalized_df = scaler.run()
#
#             scaler.getRuntime()
#
#             scaler.getMemoryUSS()
#
#             scaler.getMemoryRSS()
#
#             scaler.save("RobustScaling.csv")
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


class RobustScaling:
    """
    **About this algorithm**

    :**Description**:
        Robust Scaling normalizes features using statistics that are robust to outliers
        (median and interquartile range). This scaling method is useful when the dataset
        contains many outliers, providing better scaling than MinMax or Standard Scalers.

    :**Parameters**:
        - `dataframe` (*pd.DataFrame*): Input DataFrame with 'x', 'y' coordinates and feature columns.

    :**Attributes**:
        - **df** (*pd.DataFrame*): Input DataFrame with standardized column names 'x', 'y', and features.
        - **normalizedDF** (*pd.DataFrame*): DataFrame containing scaled features along with coordinates.
        - **startTime, endTime** (*float*): Timestamps tracking transformation execution.
        - **memoryUSS, memoryRSS** (*float*): Memory usage in kilobytes during execution.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.normalization import RobustScaling

            df = pd.read_csv("input.csv")

            scaler = RobustScaling(df)

            normalized_df = scaler.run()

            scaler.getRuntime()

            scaler.getMemoryUSS()

            scaler.getMemoryRSS()

            scaler.save("RobustScaling.csv")


    **Credits**

    Developed by Raashika and M. Charan Teja, supervised by Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe):
        """
        Initializes the RobustScaling object with a copy of the dataframe.
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
        Executes the RobustScaler normalization on the dataset.

        Returns:
            pd.DataFrame: DataFrame with 'x', 'y', and robust scaled feature columns.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        scaler = RobustScaler()
        normalizedData = scaler.fit_transform(data)
        normalizedData = pd.DataFrame(normalizedData, columns=data.columns, index=data.index)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='RobustScaling.csv'):
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