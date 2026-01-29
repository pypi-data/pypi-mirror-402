# FrequentPatternMining Class for Mining Frequent Itemsets
#
# **Importing and Using the FrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import FrequentPatternMining
#
#             miner = FrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3)
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
from PAMI.frequentPattern.basic import FPGrowth
from .abstract import PatternMiner

class FrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **FPGrowth algorithm** for mining **frequent itemsets** from transactional
        datasets. Frequent itemset mining is a foundational data mining technique used to identify patterns
        that occur frequently together in a database, and is widely used in market basket analysis, web usage
        mining, and bioinformatics.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The transactional input file provided during object initialization.
        - **miner** (*FPGrowth*): Instance of the FPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import FrequentPatternMining

        miner = FrequentPatternMining("data/input.txt")

        miner.run(minSupport=3)

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

    def run(self, minSupport: int):
        """
        Runs the FPGrowth algorithm to mine frequent itemsets.

        Args:
            minSupport (int): Minimum support threshold for identifying frequent patterns.

        Output:
            Prints the frequent itemsets to the console.
        """
        self.miner = FPGrowth.FPGrowth(iFile=self.inputFile, minSup=minSupport)
        self.miner.mine()
        self.miner.printResults()