# HighUtilityGeoreferencedFrequentPatternMining Class for Mining High Utility Georeferenced Frequent Patterns
#
# **Importing and Using the HighUtilityGeoreferencedFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import HighUtilityGeoreferencedFrequentPatternMining
#
#             miner = HighUtilityGeoreferencedFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, minUtil=50, nFile="data/neighbor.txt")
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
from PAMI.highUtilityGeoreferencedFrequentPattern.basic import SHUFIM
from .abstract import PatternMiner

class HighUtilityGeoreferencedFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **SHUFIM algorithm** for mining **high utility georeferenced frequent patterns**
        from utility transactional datasets enriched with spatial information. It extends high utility pattern mining
        by integrating geospatial neighborhood data through a neighborhood file.

        This approach is useful in spatial data mining applications where both utility and location influence pattern
        discovery, such as in retail location analysis or geographic resource optimization.

    :**Parameters**:
        - `inputFile` (*str*): Path to the utility transactional database file.
        - `nFile` (*str*): Path to the neighborhood file specifying spatial relationships.

    :**Attributes**:
        - **inputFile** (*str*): The utility transactional input file provided during object instantiation.
        - **miner** (*SHUFIM*): Instance of the SHUFIM algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import HighUtilityGeoreferencedFrequentPatternMining

        miner = HighUtilityGeoreferencedFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, minUtil=50, nFile="data/neighbor.txt")

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

    def run(self, minSupport: int, minUtil: int, nFile: str):
        """
        Executes the SHUFIM algorithm to mine high utility georeferenced frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            minUtil (int): Minimum utility threshold to identify high utility patterns.
            nFile (str): Path to the neighborhood file containing spatial proximity information.

        Output:
            Prints the discovered high utility georeferenced frequent patterns to the console.
        """
        self.miner = SHUFIM.SHUFIM(iFile=self.inputFile, minSup=minSupport, minUtil=minUtil, nFile=nFile)
        self.miner.mine()
        self.miner.printResults()