# RelativeHighUtilityPatternMining Class for Mining Relative High Utility Patterns
#
# **Importing and Using the RelativeHighUtilityPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import RelativeHighUtilityPatternMining
#
#             miner = RelativeHighUtilityPatternMining("data/input.txt")
#
#             miner.run(minUtil=50, minUR=0.6)
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
from PAMI.extras.dbStats.UtilityDatabase import UtilityDatabase
from PAMI.relativeHighUtilityPattern.basic import RHUIM
from .abstract import PatternMiner

class RelativeHighUtilityPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **RHUIM algorithm** for mining **relative high utility patterns**
        from utility transactional databases. It identifies itemsets with utilities exceeding
        a specified minimum utility threshold and a minimum utility ratio.

    :**Parameters**:
        - `inputFile` (*str*): Path to the utility transactional database file.

    :**Attributes**:
        - **inputFile** (*str*): The utility transactional input file provided during object instantiation.
        - **miner** (*RHUIM*): Instance of the RHUIM algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import RelativeHighUtilityPatternMining

        miner = RelativeHighUtilityPatternMining("data/input.txt")

        miner.run(minUtil=50, minUR=0.6)

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the utility transactional database.

        Returns:
            UtilityDatabase: Utility database object from the PAMI library.
        """
        return UtilityDatabase(self.inputFile)

    def run(self, minUtil: int, minUR: float):
        """
        Executes the RHUIM algorithm to mine relative high utility patterns.

        Args:
            minUtil (int): Minimum utility threshold for patterns.
            minUR (float): Minimum utility ratio threshold.

        Output:
            Prints the discovered relative high utility patterns to the console.
        """
        self.miner = RHUIM.RHUIM(iFile=self.inputFile, minUtil=minUtil, minUR=minUR)
        self.miner.mine()
        self.miner.printResults()