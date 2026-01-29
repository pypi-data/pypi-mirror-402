# RelativeFrequentPatternMining Class for Mining Relative Frequent Patterns
#
# **Importing and Using the RelativeFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import RelativeFrequentPatternMining
#
#             miner = RelativeFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, minRS=0.5)
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
from PAMI.relativeFrequentPattern.basic import RSFPGrowth
from .abstract import PatternMiner

class RelativeFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **RSFPGrowth algorithm** for mining **relative frequent patterns**
        from transactional databases. The algorithm discovers itemsets whose relative support
        exceeds a given minimum relative support threshold.

    :**Parameters**:
        - `inputFile` (*str*): Path to the transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The transactional input file provided during object instantiation.
        - **miner** (*RSFPGrowth*): Instance of the RSFPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import RelativeFrequentPatternMining

        miner = RelativeFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, minRS=0.5)

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

    def run(self, minSupport: int, minRS: float):
        """
        Executes the RSFPGrowth algorithm to mine relative frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            minRS (float): Minimum relative support threshold.

        Output:
            Prints the discovered relative frequent patterns to the console.
        """
        self.miner = RSFPGrowth.RSFPGrowth(iFile=self.inputFile, minSup=minSupport, minRS=minRS)
        self.miner.mine()
        self.miner.printResults()