# HighUtilitySpatialPatternMining Class for Mining High Utility Spatial Patterns
#
# **Importing and Using the HighUtilitySpatialPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import HighUtilitySpatialPatternMining
#
#             miner = HighUtilitySpatialPatternMining("data/input.txt")
#
#             miner.run(minUtil=50, nFile="data/neighbor.txt")
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
from PAMI.highUtilitySpatialPattern.basic import HDSHUIM
from .abstract import PatternMiner

class HighUtilitySpatialPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **HDSHUIM algorithm** for mining **high utility spatial patterns**
        from utility transactional databases augmented with spatial neighborhood information.
        The algorithm integrates utility-based pattern mining with spatial proximity
        defined by a neighborhood file to discover spatially meaningful high utility patterns.

    :**Parameters**:
        - `inputFile` (*str*): Path to the utility transactional database file.
        - `nFile` (*str*): Path to the neighborhood file specifying spatial relationships.

    :**Attributes**:
        - **inputFile** (*str*): The utility transactional input file provided during object instantiation.
        - **miner** (*HDSHUIM*): Instance of the HDSHUIM algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import HighUtilitySpatialPatternMining

        miner = HighUtilitySpatialPatternMining("data/input.txt")

        miner.run(minUtil=50, nFile="data/neighbor.txt")

    **Credits**

     Written by M. Charan Teja, under the guidance of Professor Rage Uday Kiran.
    """
    def _create_database(self):
        """
        Internal method to initialize the utility transactional database.

        Returns:
            UtilityDatabase: Utility transactional database object from the PAMI library.
        """
        return UtilityDatabase(self.inputFile)

    def run(self, minUtil: int, nFile: str):
        """
        Executes the HDSHUIM algorithm to mine high utility spatial patterns.

        Args:
            minUtil (int): Minimum utility threshold to identify high utility patterns.
            nFile (str): Path to the neighborhood file containing spatial proximity information.

        Output:
            Prints the discovered high utility spatial patterns to the console.
        """
        self.miner = HDSHUIM.HDSHUIM(iFile=self.inputFile, minUtil=minUtil, nFile=nFile)
        self.miner.mine()
        self.miner.printResults()