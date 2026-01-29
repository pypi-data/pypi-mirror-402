# CoveragePatternMining Class for Mining Coverage Patterns
#
# **Importing and Using the CoveragePatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import CoveragePatternMining
#
#             miner = CoveragePatternMining("data/input.txt")
#
#             miner.run(minSupport=3, minRF=0.4, minCS=0.5, maxOR=0.3)
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
from PAMI.coveragePattern.basic import CMine
from .abstract import PatternMiner
from typing import Union

class CoveragePatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **CMine algorithm** for discovering **coverage patterns** in transactional databases.
        Coverage pattern mining identifies itemsets that not only occur frequently but also cover a significant portion
        of the database based on correlation and coverage-based quality metrics.

    :**Parameters**:
        - `inputFile` (*str*): Path to the input transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The path to the transactional database file passed during object creation.
        - **miner** (*CMine*): Instance of the CMine algorithm class from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import CoveragePatternMining

        miner = CoveragePatternMining("data/input.txt")

        miner.run(minSupport=3, minRF=0.4, minCS=0.5, maxOR=0.3)

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

    def run(self, minSupport: int, minRF: Union[int, float], minCS: Union[int, float], maxOR:Union[int, float]):
        """
        Runs the CMine algorithm to mine coverage patterns from the transactional dataset.

        Args:
            minSupport (int): Minimum support threshold for itemset frequency.
            minRF (float or int): Minimum representative frequency threshold.
            minCS (float or int): Minimum coverage strength threshold.
            maxOR (float or int): Maximum overlap ratio allowed between itemsets.

        Output:
            Prints the discovered coverage patterns to the console.
        """
        self.miner = CMine.CMine(iFile=self.inputFile, minRF=minRF, minCS=minCS, maxOR = maxOR)
        self.miner.mine()
        self.miner.printResults()