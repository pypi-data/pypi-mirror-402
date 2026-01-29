# GeoreferencedFrequentPatternMining Class for Mining Georeferenced Frequent Patterns
#
# **Importing and Using the GeoreferencedFrequentPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import GeoreferencedFrequentPatternMining
#
#             miner = GeoreferencedFrequentPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, nFile="data/neighbor.txt")
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
from PAMI.georeferencedFrequentPattern.basic import FSPGrowth
from .abstract import PatternMiner

class GeoreferencedFrequentPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **FSPGrowth algorithm** for discovering **georeferenced frequent patterns**
        from spatial transactional datasets. In addition to mining frequent itemsets, this algorithm incorporates
        spatial neighborhood information, allowing it to capture patterns influenced by the proximity of transactions.

        This is particularly useful in applications such as geospatial analysis, environmental monitoring, and
        urban planning where location-aware pattern mining is essential.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input transactional database file.
        - `nFile` (*str*): Path to the neighborhood file specifying spatial relationships.

    :**Attributes**:
        - **inputFile** (*str*): The transactional data file provided during object instantiation.
        - **miner** (*FSPGrowth*): Instance of the FSPGrowth algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import GeoreferencedFrequentPatternMining

        miner = GeoreferencedFrequentPatternMining("data/input.txt")

        miner.run(minSupport=3, nFile="data/neighbor.txt")

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

    def run(self, minSupport: int, nFile: str):
        """
        Executes the FSPGrowth algorithm to mine georeferenced frequent patterns using spatial relationships.

        Args:
            minSupport (int): Minimum support threshold for frequent itemsets.
            nFile (str): Path to the neighborhood file containing spatial proximity information.

        Output:
            Prints the georeferenced frequent itemsets to the console.
        """
        self.miner = FSPGrowth.FSPGrowth(iFile=self.inputFile, minSup=minSupport, nFile=nFile)
        self.miner.mine()
        self.miner.printResults()