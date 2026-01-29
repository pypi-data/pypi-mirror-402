# CrossDistance Class for Computing Mean Pairwise Distances Between Two Datasets

# **Importing and Using the CrossDistance Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.scoreCalculator import CrossDistance
#
#             topk_df = pd.read_csv("topk.csv")
#
#             train_df = pd.read_csv("train.csv")
#
#             cd = CrossDistance(topk_df, train_df, startBandTopkDF=2, startBandTrainDF=2)
#
#             mean_distance = cd.run(metric='cosine')
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

import numpy as np
from scipy.spatial.distance import cdist

class CrossDistance:
    """
    **About this algorithm**

    :**Description**:
        CrossDistance computes the average pairwise distances between two datasets using a specified distance metric.
        This is useful for evaluating the similarity between two sets of feature vectors, such as in retrieval,
        matching, or clustering validation.

    :**Parameters**:
        - `TopkDF` (*pd.DataFrame*): First dataset (e.g., top-k retrieved samples).
        - `TrainDF` (*pd.DataFrame*): Second dataset (e.g., original training samples).
        - `startBandTopkDF` (*int*): Column index from which to start using features in `TopkDF` (default: 2).
        - `startBandTrainDF` (*int*): Column index from which to start using features in `TrainDF` (default: 2).

    :**Attributes**:
        - **TopkDF** (*np.ndarray*) -- Sliced feature matrix from `TopkDF`.
        - **TrainDF** (*np.ndarray*) -- Sliced feature matrix from `TrainDF`.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.scoreCalculator import CrossDistance

            topk_df = pd.read_csv("topk.csv")

            train_df = pd.read_csv("train.csv")

            cd = CrossDistance(topk_df, train_df, startBandTopkDF=2, startBandTrainDF=2)

            mean_distance = cd.run(metric='euclidean')


    **Credits**

    This implementation was created by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, TopkDF, TrainDF, startBandTopkDF = 2, startBandTrainDF = 2):
        self.TopkDF = TopkDF.iloc[:,startBandTopkDF:]
        self.TrainDF = TrainDF.iloc[:,startBandTrainDF:]

        if self.TopkDF.shape[1] != self.TrainDF.shape[1]:
            raise ValueError("TopkDF and TrainDF must have the same number of columns after slicing.")

    def run(self, metric='euclidean'):
        """
        Computes and returns the mean pairwise distance between the rows of two datasets.

        Args:
            metric (str): Distance metric to use (default: 'euclidean').

        Returns:
            float: Mean of all computed distances.
        """
        distances = cdist(self.TopkDF, self.TrainDF, metric=metric)
        return np.mean(distances)