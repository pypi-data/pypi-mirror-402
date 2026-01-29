# RecurringPatternMining Class for Mining Recurring Patterns
#
# **Importing and Using the RecurringPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import RecurringPatternMining
#
#             miner = RecurringPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, maxPer=10, minRec=0.5)
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
from PAMI.recurringPattern.basic import RPGrowth
from typing import Union
from .abstract import PatternMiner

class RecurringPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **RPGrowth algorithm** for mining **recurring patterns**
        from temporal transactional databases. It identifies itemsets that recur periodically
        with a specified minimum recurrence threshold within a maximum periodic interval.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional input file provided during object instantiation.
        - **miner** (*RPGrowth*): Instance of the RPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import RecurringPatternMining

        miner = RecurringPatternMining("data/input.txt")

        miner.run(minSupport=3, maxPer=10, minRec=0.5)

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

    def run(self, minSupport: int, maxPer: int, minRec: Union[int, float]):
        """
        Executes the RPGrowth algorithm to mine recurring patterns.

        Args:
            minSupport (int): Minimum periodic support threshold for frequent itemsets.
            maxPer (int): Maximum periodicity controlling pattern recurrence interval.
            minRec (int or float): Minimum recurrence threshold for pattern frequency.

        Output:
            Prints the discovered recurring patterns to the console.
        """
        self.miner = RPGrowth.RPGrowth(iFile = self.inputFile, minPS=minSupport, maxPer=maxPer, minRec=minRec)
        self.miner.mine()
        self.miner.printResults()