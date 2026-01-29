# LogTransformation Class for Feature Normalization Using Logarithmic Scaling

# **Importing and Using the LogTransformation Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import LogTransformation
#
#             df = pd.read_csv("input.csv")
#
#             transformer = LogTransformation(df)
#
#             normalized_df = transformer.run()
#
#             transformer.getRuntime()
#
#             transformer.getMemoryUSS()
#
#             transformer.getMemoryRSS()
#
#             transformer.save("LogTransformation.csv")
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

class LogTransformation:
    """
   **About this algorithm**

   :**Description**:
       LogTransformation applies logarithmic normalization to numerical features (excluding 'x' and 'y' coordinates),
       which can be useful for reducing skewness in data and compressing wide value ranges.
       The transformation uses the natural logarithm function as `log(1 + x)` to handle zero and positive values.

   :**Parameters**:
       - `dataframe` (*pd.DataFrame*): Input DataFrame containing 'x', 'y', and feature columns.

   :**Attributes**:
       - **df** (*pd.DataFrame*) -- Original DataFrame with updated column labels.
       - **normalizedDF** (*pd.DataFrame*) -- DataFrame after applying log transformation.
       - **startTime, endTime** (*float*) -- Timestamps used for runtime measurement.
       - **memoryUSS, memoryRSS** (*float*) -- Memory usage statistics (USS and RSS) in kilobytes.

   **Execution methods**

   **Calling from a Python program**

   .. code-block:: python

           import pandas as pd

           from geoanalytics.normalization import LogTransformation

           df = pd.read_csv("input.csv")

           transformer = LogTransformation(df)

           normalized_df = transformer.run()

           transformer.getRuntime()

           transformer.getMemoryUSS()

           transformer.getMemoryRSS()

           transformer.save("LogTransformation.csv")


   **Credits**

   This implementation was created by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
   """
    def __init__(self, dataframe):
        """
        Initializes the LogTransformation object with a copy of the dataframe.
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
        Applies natural log transformation to the feature columns using log1p (log(1 + x)).

        Returns:
            pd.DataFrame: Normalized DataFrame with 'x', 'y', and log-transformed features.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        normalizedData = np.log1p(data)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='LogTransformation.csv'):
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