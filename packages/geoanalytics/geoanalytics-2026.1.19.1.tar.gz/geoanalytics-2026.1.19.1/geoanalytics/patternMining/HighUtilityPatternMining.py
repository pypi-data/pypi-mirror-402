# HighUtilityPatternMining Class for Mining High Utility Patterns
#
# **Importing and Using the HighUtilityPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import HighUtilityPatternMining
#
#             miner = HighUtilityPatternMining("data/input.txt")
#
#             miner.run(minUtil=50)
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

import pandas as pd
from PAMI.extras.dbStats.UtilityDatabase import UtilityDatabase
from PAMI.highUtilityPattern.basic import EFIM
from .abstract import PatternMiner

class HighUtilityPatternMining(PatternMiner):
    """
   **About this algorithm**

   :**Description**:
       This module implements the **EFIM algorithm** for mining **high utility patterns**
       from utility transactional databases. Unlike traditional frequent pattern mining, this method
       focuses solely on the utility aspect, discovering itemsets with utility above the specified threshold.

   :**Parameters**:
       - `inputFile` (*str*): Path to the input utility transactional database file.

   :**Attributes**:
       - **inputFile** (*str*): The utility transactional input file provided during object initialization.
       - **miner** (*EFIM*): Instance of the EFIM algorithm from the PAMI library.

   **Execution methods**

   **Calling from a Python program**

   .. code-block:: python

       from geoanalytics.patternMining import HighUtilityPatternMining

       miner = HighUtilityPatternMining("data/input.txt")

       miner.run(minUtil=50)

   **Credits**

    Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
   """
    def _create_database(self):
        """
        Internal method to initialize the utility transactional database.

        Returns:
            UtilityDatabase: Utility transactional database object from the PAMI library.
        """
        return UtilityDatabase(self.inputFile)

    def run(self, minUtil: int):
        """
        Executes the EFIM algorithm to mine high utility patterns.

        Args:
            minUtil (int): Minimum utility threshold to identify high utility patterns.

        Output:
            Prints the discovered high utility patterns to the console.
        """
        self.miner = EFIM.EFIM(iFile=self.inputFile, minUtil=minUtil)
        self.miner.mine()
        self.miner.printResults()