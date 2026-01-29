# PartialPeriodicPatternInMultipleTimeSeries Class for Mining Partial Periodic Patterns in Multiple Time Series
#
# **Importing and Using the PartialPeriodicPatternInMultipleTimeSeries Class in a Python Program**
#
#             from geoanalytics.patternMining import PartialPeriodicPatternInMultipleTimeSeries
#
#             miner = PartialPeriodicPatternInMultipleTimeSeries("data/input.txt")
#
#             miner.run(period=12, periodicSupport=5)
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
from PAMI.partialPeriodicPatternInMultipleTimeSeries import PPGrowth
from .abstract import PatternMiner

class PartialPeriodicPatternInMultipleTimeSeries(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **PPGrowth algorithm** for mining **partial periodic patterns**
        across multiple temporal transactional datasets (multiple time series). It identifies itemsets
        exhibiting periodic behavior with respect to a specified period and minimum periodic support
        threshold across multiple series.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file containing multiple time series.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional input file provided during object instantiation.
        - **miner** (*PPGrowth*): Instance of the PPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import PartialPeriodicPatternInMultipleTimeSeries

        miner = PartialPeriodicPatternInMultipleTimeSeries("data/input.txt")

        miner.run(period=12, periodicSupport=5)

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the temporal transactional database containing multiple time series.

        Returns:
            TemporalDatabase: Temporal database object from the PAMI library.
        """
        return TemporalDatabase(self.inputFile)

    def run(self, period: int, periodicSupport: int):
        """
        Executes the PPGrowth algorithm to mine partial periodic patterns in multiple time series.

        Args:
            period (int): The periodicity window to evaluate pattern repetition.
            periodicSupport (int): Minimum periodic support threshold indicating required occurrences within the period.

        Output:
            Prints the discovered partial periodic patterns across multiple time series to the console.
        """
        self.miner = PPGrowth.PPGrowth(iFile = self.inputFile, period=period, periodicSupport=periodicSupport)
        self.miner.mine()
        self.miner.printResults()