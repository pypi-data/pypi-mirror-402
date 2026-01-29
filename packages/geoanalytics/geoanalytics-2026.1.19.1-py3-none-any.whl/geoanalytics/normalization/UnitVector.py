# UnitVector Class for Feature Normalization Using Unit Vector Scaling

# **Importing and Using the UnitVector Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.normalization import UnitVector
#
#             df = pd.read_csv("input.csv")
#
#             transformer = UnitVector(df)
#
#             normalized_df = transformer.run()
#
#             transformer.getRuntime()
#
#             transformer.getMemoryUSS()
#
#             transformer.getMemoryRSS()
#
#             transformer.save("UnitVector.csv")
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
from sklearn.preprocessing import Normalizer


class UnitVector:
    """
    **About this algorithm**

    :**Description**:
        UnitVector performs feature normalization by scaling each row (feature vector)
        of the dataset to have unit L2 norm (i.e., the sum of squares of each row equals 1).
        This normalization is useful when you want to normalize across rows (samples)
        rather than columns (features), such as in cosine similarity or direction-based analyses.

    :**Parameters**:
        - `dataframe` (*pd.DataFrame*): Input DataFrame containing 'x', 'y' coordinates and feature values.

    :**Attributes**:
        - **df** (*pd.DataFrame*): The original DataFrame with standardized column headers ('x', 'y', ...features).
        - **normalizedDF** (*pd.DataFrame*): The L2-normalized output DataFrame.
        - **startTime, endTime** (*float*): Runtime tracking timestamps.
        - **memoryUSS, memoryRSS** (*float*): Memory consumption statistics in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.normalization import UnitVector

            df = pd.read_csv("input.csv")

            transformer = UnitVector(df)

            normalized_df = transformer.run()

            transformer.getRuntime()

            transformer.getMemoryUSS()

            transformer.getMemoryRSS()

            transformer.save("UnitVector.csv")


    **Credits**

    Developed by Raashika and M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, dataframe):
        """
        Initializes the UnitVector object with a copy of the dataframe.
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
        Executes unit vector (L2) normalization on each row of the dataset.

        Returns:
            pd.DataFrame: DataFrame containing 'x', 'y' and normalized feature values.
        """

        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)

        scaler = Normalizer(norm='l2')
        normalizedData = scaler.fit_transform(data)
        normalizedData = pd.DataFrame(normalizedData, columns=data.columns, index=data.index)

        self.normalizedDF = pd.concat([xy, normalizedData], axis=1)
        self.endTime = time.time()
        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.normalizedDF


    def save(self, outputFile='UnitVector.csv'):
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