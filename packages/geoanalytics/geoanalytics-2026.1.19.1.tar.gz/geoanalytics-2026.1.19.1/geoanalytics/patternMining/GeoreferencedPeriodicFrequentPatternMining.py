# GeoreferencedPeriodicFrequentPatternMining Class for Mining Georeferenced Periodic Frequent Patterns
#
# **Importing and Using the GeoreferencedPeriodicFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import GeoreferencedPeriodicFrequentPatternMining
#
#             miner = GeoreferencedPeriodicFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, maxPer=7, nFile="data/neighbor.txt")
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
from PAMI.geoReferencedPeriodicFrequentPattern.basic import GPFPMiner
from .abstract import PatternMiner

class GeoreferencedPeriodicFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **GPFPMiner algorithm** for mining **georeferenced periodic frequent patterns**
        from temporal transactional datasets. The algorithm discovers itemsets that appear periodically over time,
        considering spatial relationships defined in a neighborhood file.

        This method is useful in spatiotemporal data mining applications such as urban activity analysis,
        environmental monitoring, and other domains requiring periodic pattern discovery with spatial context.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.
        - `nFile` (*str*): Path to the neighborhood file specifying spatial relationships.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional data file provided during object instantiation.
        - **miner** (*GPFPMiner*): Instance of the GPFPMiner algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import GeoreferencedPeriodicFrequentPatternMining

        miner = GeoreferencedPeriodicFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, maxPer=7, nFile="data/neighbor.txt")

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

    def run(self, minSupport: int, maxPer: int, nFile: str):
        """
        Executes the GPFPMiner algorithm to mine georeferenced periodic frequent patterns.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            maxPer (int): Maximum periodicity value defining pattern recurrence period.
            nFile (str): Path to the neighborhood file containing spatial proximity information.

        Output:
            Prints the discovered georeferenced periodic frequent patterns to the console.
        """
        self.miner = GPFPMiner.GPFPMiner(iFile=self.inputFile, minSup=minSupport, maxPer=maxPer, nFile=nFile)
        self.miner.mine()
        self.miner.printResults()