# Mode-based missing value imputation for multidimensional data with runtime and memory tracking,
# and support for saving the imputed dataset.
#
# **Importing and Using the ModeImputation Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.imputation import ModeImputation
#
#             df = pd.read_csv('input.csv')
#
#             mode_imputer = ModeImputation(df)
#
#             imputed_df = mode_imputer.run()
#
#             mode_imputer.getRuntime()
#
#             mode_imputer.getMemoryUSS()
#
#             mode_imputer.getMemoryRSS()
#
#             mode_imputer.save('ModeImputation.csv')
#

__copyright__ = """
Copyright (C)  2022 Rage Uday Kiran

     This program is free software: you can redistribute it and/or modify
     it under theZ terms of the GNU General Public License as published by
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

class ModeImputation:
    """
    **About this algorithm**

    :**Description**:
        Mode Imputation replaces missing values in each column of a dataset with the most frequent value (mode)
        of that column. It is a simple and fast technique for handling missing data, particularly useful
        when the dataset has categorical features or dominant repeated values.

    :**Parameters**:
        - Dataset (pandas DataFrame) must be provided during object initialization.
        - No parameters are needed for `run()`.

    :**Attributes**:
        - **df** (*pd.DataFrame*) -- The input data with 'x', 'y' coordinates and features.
        - **imputedDF** (*pd.DataFrame*) -- DataFrame after filling in missing values with mode.
        - **startTime, endTime** (*float*) -- Variables to track execution time.
        - **memoryUSS, memoryRSS** (*float*) -- Memory usage of the imputation process in kilobytes.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.imputation import ModeImputation

            df = pd.read_csv("input.csv")

            mode_imputer = ModeImputation(df)

            imputed_df = mode_imputer.run()

            mode_imputer.getRuntime()
            mode_imputer.getMemoryUSS()
            mode_imputer.getMemoryRSS()

            mode_imputer.save('ModeImputation.csv')

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


    def run(self):
        """
        Executes the mode imputation algorithm by filling missing values with column-wise mode.

        :return: imputedDF (pd.DataFrame) -- DataFrame with missing values filled
        """
        self.startTime = time.time()
        xy = self.df[['x', 'y']].reset_index(drop=True)
        data = self.df.drop(['x', 'y'], axis=1).reset_index(drop=True)
        imputedData = data.fillna(data.mode().iloc[0])
        self.imputedDF = pd.concat([xy, imputedData], axis=1)

        self.endTime = time.time()

        process = psutil.Process()
        self.memoryUSS = process.memory_full_info().uss / 1024
        self.memoryRSS = process.memory_full_info().rss / 1024

        return self.imputedDF


    def save(self, outputFile='ModeImputation.csv'):
        """
        Saves the imputed DataFrame to a CSV file.

        :param outputFile: str, filename to save the imputed data (default: 'ModeImputation.csv')
        """
        if self.imputedDF is not None:
            try:
                self.imputedDF.to_csv(outputFile, index=False)
                print(f"Imputed data saved to: {outputFile}")
            except Exception as e:
                print(f"Failed to save labels: {e}")
        else:
            print("No imputed data to save. Run impute() first")