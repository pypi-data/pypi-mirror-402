# LocalPeriodicPatternMining Class for Mining Local Periodic Patterns
#
# **Importing and Using the LocalPeriodicPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import LocalPeriodicPatternMining
#
#             miner = LocalPeriodicPatternMining("data/input.txt")
#
#             miner.run(maxPer=10, maxSoPer=5, minDur=3)
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
from PAMI.localPeriodicPattern.basic import LPPGrowth
from .abstract import PatternMiner

class LocalPeriodicPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **LPPGrowth algorithm** for mining **local periodic patterns**
        from temporal transactional datasets. The algorithm identifies patterns with periodic
        recurrence within local temporal windows, controlled by maximum periodicity,
        maximum sub-periodicity, and minimum duration thresholds.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional input file provided during object instantiation.
        - **miner** (*LPPGrowth*): Instance of the LPPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import LocalPeriodicPatternMining

        miner = LocalPeriodicPatternMining("data/input.txt")

        miner.run(maxPer=10, maxSoPer=5, minDur=3)

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

    def run(self, maxPer: int, maxSoPer: int, minDur: int):
        """
        Executes the LPPGrowth algorithm to mine local periodic patterns.

        Args:
            maxPer (int): Maximum periodicity threshold controlling pattern recurrence interval.
            maxSoPer (int): Maximum sub-periodicity threshold controlling pattern sub-intervals.
            minDur (int): Minimum duration threshold specifying the minimal length of the periodic pattern.

        Output:
            Prints the discovered local periodic patterns to the console.
        """
        self.miner = LPPGrowth.LPPGrowth(iFile = self.inputFile, maxPer=maxPer, maxSoPer=maxSoPer, minDur=minDur)
        self.miner.mine()
        self.miner.printResults()