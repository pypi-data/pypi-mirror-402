# FaultTolerantFrequentPatternMining Class for Mining Fault-Tolerant Frequent Patterns
#
# **Importing and Using the FaultTolerantFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import FaultTolerantFrequentPatternMining
#
#             miner = FaultTolerantFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, itemSup=2, minLength=2, faultTolerance=1)
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
from PAMI.extras.dbStats.TransactionalDatabase import TransactionalDatabase
from PAMI.faultTolerantFrequentPattern.basic import FTFPGrowth
from .abstract import PatternMiner
from typing import Union

class FaultTolerantFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **FTFPGrowth algorithm** for discovering **fault-tolerant frequent patterns**
        in transactional datasets. Fault-tolerant patterns allow a limited number of item mismatches while still
        preserving a minimum support threshold, making the algorithm useful in noisy or imperfect data environments.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): Input file provided during object instantiation.
        - **miner** (*FTFPGrowth*): Instance of the FTFPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import FaultTolerantFrequentPatternMining

        miner = FaultTolerantFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, itemSup=2, minLength=2, faultTolerance=1)

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the transactional database.

        Returns:
            TransactionalDatabase: Transactional database object from the PAMI library.
        """
        return TransactionalDatabase(self.inputFile)

    def run(self, minSupport: int, itemSup: int, minLength: int, faultTolerance: int):
        """
        Executes the FTFPGrowth algorithm to mine fault-tolerant frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            itemSup (int): Minimum individual item frequency threshold.
            minLength (int): Minimum length of the itemset to be considered.
            faultTolerance (int): Maximum number of tolerated faults (missing or mismatched items) in the itemsets.

        Output:
            Prints the fault-tolerant frequent patterns to the console.
        """
        self.miner = FTFPGrowth.FTFPGrowth(iFile=self.inputFile, minSup=minSupport, itemSup=itemSup, minLength=minLength, faultTolerance=faultTolerance)
        self.miner.mine()
        self.miner.printResults()