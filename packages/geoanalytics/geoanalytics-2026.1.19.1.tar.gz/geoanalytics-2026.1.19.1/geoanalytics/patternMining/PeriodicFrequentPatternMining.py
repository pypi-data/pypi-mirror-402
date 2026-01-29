# PeriodicFrequentPatternMining Class for Mining Periodic Frequent Patterns
#
# **Importing and Using the PeriodicFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import PeriodicFrequentPatternMining
#
#             miner = PeriodicFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, maxPer=10)
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
from PAMI.extras.dbStats.TemporalDatabase import TemporalDatabase
from PAMI.periodicFrequentPattern.basic import PFPGrowth
from .abstract import PatternMiner

class PeriodicFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **PFPGrowth algorithm** for mining **periodic frequent patterns**
        from temporal transactional databases. The algorithm finds frequent itemsets that appear
        repeatedly within a specified maximum periodicity.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional input file provided during object instantiation.
        - **miner** (*PFPGrowth*): Instance of the PFPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import PeriodicFrequentPatternMining

        miner = PeriodicFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, maxPer=10)

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the temporal transactional database.

        Returns:
            TemporalDatabase: Temporal database object from the PAMI library.
        """
        return TemporalDatabase(self.inputFile)

    def run(self, minSupport: int, maxPer: int):
        """
        Executes the PFPGrowth algorithm to mine periodic frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            maxPer (int): Maximum periodicity controlling pattern recurrence interval.

        Output:
            Prints the discovered periodic frequent patterns to the console.
        """
        self.miner = PFPGrowth.PFPGrowth(iFile = self.inputFile, minSup=minSupport, maxPer = maxPer)
        self.miner.mine()
        self.miner.printResults()