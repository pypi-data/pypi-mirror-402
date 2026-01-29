# HighUtilityFrequentPatternMining Class for Mining High Utility Frequent Patterns
#
# **Importing and Using the HighUtilityFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import HighUtilityFrequentPatternMining
#
#             miner = HighUtilityFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, minUtil=50)
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
from PAMI.highUtilityFrequentPattern.basic import HUFIM
from .abstract import PatternMiner

class HighUtilityFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **HUFIM algorithm** for mining **high utility frequent patterns**
        from utility transactional databases. Unlike traditional frequent pattern mining, this algorithm
        considers the utility (e.g., profit, importance) of items along with their frequency, allowing
        discovery of itemsets that are both frequent and have high utility.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input utility transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The utility transactional input file provided during object initialization.
        - **miner** (*HUFIM*): Instance of the HUFIM algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import HighUtilityFrequentPatternMining

        miner = HighUtilityFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, minUtil=50)

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

    def run(self, minSupport: int, minUtil: int):
        """
        Executes the HUFIM algorithm to mine high utility frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            minUtil (int): Minimum utility threshold to identify high utility patterns.

        Output:
            Prints the discovered high utility frequent patterns to the console.
        """
        self.miner = HUFIM.HUFIM(iFile=self.inputFile, minSup=minSupport, minUtil=minUtil)
        self.miner.mine()
        self.miner.printResults()