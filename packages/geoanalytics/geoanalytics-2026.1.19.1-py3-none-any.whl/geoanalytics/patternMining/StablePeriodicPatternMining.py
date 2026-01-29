# StablePeriodicPatternMining Class for Mining Stable Periodic Patterns
#
# **Importing and Using the StablePeriodicPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import StablePeriodicPatternMining
#
#             miner = StablePeriodicPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, maxPer=10, maxLa=5)
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
from PAMI.stablePeriodicFrequentPattern.basic import SPPGrowth
from .abstract import PatternMiner

class StablePeriodicPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **SPPGrowth algorithm** for mining **stable periodic frequent patterns**
        from temporal databases. It discovers itemsets that appear frequently with stable periodicity
        under given constraints on maximum period and maximum latency.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The temporal database file provided during object instantiation.
        - **miner** (*SPPGrowth*): Instance of the SPPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import StablePeriodicPatternMining

        miner = StablePeriodicPatternMining("data/input.txt")

        miner.run(minSupport=3, maxPer=10, maxLa=5)

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the temporal database.

        Returns:
            TemporalDatabase: Temporal database object from the PAMI library.
        """
        return TemporalDatabase(self.inputFile)

    def run(self, minSupport: int, maxPer: int, maxLa: int):
        """
        Runs the SPPGrowth algorithm to mine stable periodic patterns.

        Args:
            minSupport (int): Minimum support threshold for patterns.
            maxPer (int): Maximum period allowed for the patterns.
            maxLa (int): Maximum latency allowed for the patterns.

        Output:
            Prints the discovered stable periodic patterns to the console.
        """
        self.miner = SPPGrowth.SPPGrowth(inputFile=self.inputFile, minSup=minSupport, maxPer=maxPer, maxLa=maxLa)
        self.miner.mine()
        self.miner.printResults()