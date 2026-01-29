# PartialPeriodicPatternMining Class for Mining Partial Periodic Patterns
#
# **Importing and Using the PartialPeriodicPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import PartialPeriodicPatternMining
#
#             miner = PartialPeriodicPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, period=10)
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
from PAMI.partialPeriodicPattern.basic import PPPGrowth
from .abstract import PatternMiner

class PartialPeriodicPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **PPPGrowth algorithm** for mining **partial periodic patterns**
        from temporal transactional datasets. It identifies itemsets that recur periodically
        within a specified period with a minimum periodic support threshold.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional input file provided during object instantiation.
        - **miner** (*PPPGrowth*): Instance of the PPPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import PartialPeriodicPatternMining

        miner = PartialPeriodicPatternMining("data/input.txt")

        miner.run(minSupport=3, period=10)

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

    def run(self, minSupport: int, period: int):
        """
       Executes the PPPGrowth algorithm to mine partial periodic patterns.

       Args:
           minSupport (int): Minimum periodic support threshold for frequent itemsets.
           period (int): The periodicity window controlling pattern recurrence interval.

       Output:
           Prints the discovered partial periodic patterns to the console.
       """
        self.miner = PPPGrowth.PPPGrowth(iFile = self.inputFile, minPS = minSupport, period = period)
        self.miner.mine()
        self.miner.printResults()