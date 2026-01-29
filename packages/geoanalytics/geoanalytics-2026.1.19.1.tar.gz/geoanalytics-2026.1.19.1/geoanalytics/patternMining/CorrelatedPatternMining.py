# CorrelatedPatternMining Class for Mining Correlated Patterns
#
# **Importing and Using the CorrelatedPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import CorrelatedPatternMining
#
#             miner = CorrelatedPatternMining("data/input.txt")
#
#             miner.run(minSupport=3, minAllConf=0.6)
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
from PAMI.correlatedPattern.basic import CoMinePlus
from .abstract import PatternMiner
from typing import Union

class CorrelatedPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the CoMinePlus algorithm for mining **correlated patterns** from a transactional
        dataset. Correlated pattern mining identifies itemsets that not only occur frequently together
        but also exhibit strong correlations based on statistical measures like All-Confidence.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): Input file provided during object instantiation.
        - **miner** (*CoMinePlus*): Object of CoMinePlus algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import CorrelatedPatternMining

        miner = CorrelatedPatternMining("data/input.txt")

        miner.run(minSupport=3, minAllConf=0.6)


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

    def run(self, minSupport: int, minAllConf: Union[int, float]):
        """
        Runs the CoMinePlus algorithm for correlated pattern mining.

        Args:
            minSupport (int): Minimum support value for frequent itemsets.
            minAllConf (float or int): Minimum all-confidence threshold for identifying correlation.

        Output:
            Prints correlated itemsets to the console.
        """
        self.miner = CoMinePlus.CoMinePlus(iFile=self.inputFile, minSup=minSupport, minAllConf=minAllConf)
        self.miner.mine()
        self.miner.printResults()