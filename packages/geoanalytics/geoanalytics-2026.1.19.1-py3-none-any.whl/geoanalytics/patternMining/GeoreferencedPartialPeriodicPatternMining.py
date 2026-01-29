# GeoreferencedPartialPeriodicPatternMining Class for Mining Georeferenced Partial Periodic Patterns
#
# **Importing and Using the GeoreferencedPartialPeriodicPatternMining Class in a Python Program**
#
#             from geoanalytics.patternMining import GeoreferencedPartialPeriodicPatternMining
#
#             miner = GeoreferencedPartialPeriodicPatternMining("data/input.txt")
#
#             miner.run(minPS=3, maxIAT=5, nFile="data/neighbor.txt")
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
from PAMI.georeferencedPartialPeriodicPattern.basic import STEclat
from .abstract import PatternMiner

class GeoreferencedPartialPeriodicPatternMining(PatternMiner):
    """
    **About this algorithm**

    :**Description**:
        This module implements the **STEclat algorithm** to mine **georeferenced partial periodic patterns**
        from temporal transactional datasets. This algorithm finds itemsets that appear periodically within
        certain time constraints, incorporating spatial neighborhood information via a neighborhood file.

        This approach is valuable in spatiotemporal data mining applications such as environmental data
        analysis, urban monitoring, and other domains requiring discovery of partial periodic patterns
        with spatial context.

    :**Parameters**:
        - `inputFile` (*str*): Path to the temporal transactional database file.
        - `nFile` (*str*): Path to the neighborhood file specifying spatial relationships.

    :**Attributes**:
        - **inputFile** (*str*): The temporal transactional data file provided during object instantiation.
        - **miner** (*STEclat*): Instance of the STEclat algorithm from the PAMI library.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

        from geoanalytics.patternMining import GeoreferencedPartialPeriodicPatternMining

        miner = GeoreferencedPartialPeriodicPatternMining("data/input.txt")

        miner.run(minPS=3, maxIAT=5, nFile="data/neighbor.txt")

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

    def run(self, minPS: int, maxIAT:int, nFile: str):
        """
        Executes the STEclat algorithm to mine georeferenced partial periodic patterns.

        Args:
            minPS (int): Minimum partial periodicity support threshold.
            maxIAT (int): Maximum inter-arrival time allowed between pattern occurrences.
            nFile (str): Path to the neighborhood file containing spatial proximity information.

        Output:
            Prints the discovered georeferenced partial periodic patterns to the console.
        """
        self.miner = STEclat.STEclat(iFile=self.inputFile, minPS=minPS, maxIAT=maxIAT, nFile=nFile)
        self.miner.mine()
        self.miner.printResults()