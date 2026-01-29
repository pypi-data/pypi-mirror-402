# OverlapScore Class for Measuring Cluster Overlap Between Two Datasets Using KMeans Clustering

# **Importing and Using the OverlapScore Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.scoreCalculator import OverlapScore
#
#             train_df = pd.read_csv("train.csv")
#
#             topk_df = pd.read_csv("topk.csv")
#
#             overlap = OverlapScore(train_df, topk_df, startBandTrainDF=2, startBandTopkDF=2)
#
#             score = overlap.run(n_clusters=3)
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
from sklearn.cluster import KMeans

class OverlapScore:
    """
    **About this algorithm**

    :**Description**:
        OverlapScore quantifies the cluster overlap between two datasets using KMeans clustering.
        It helps evaluate how well a top-k retrieved set aligns with the training dataset in the
        embedding space, by checking the agreement of cluster assignments.

    :**Parameters**:
        - `TrainDF` (*pd.DataFrame*): The original training dataset.
        - `TopkDF` (*pd.DataFrame*): The retrieved top-k dataset.
        - `startBandTrainDF` (*int*): Column index from which to start using features in `TrainDF` (default: 2).
        - `startBandTopkDF` (*int*): Column index from which to start using features in `TopkDF` (default: 2).

    :**Attributes**:
        - **TrainDF** (*np.ndarray*) -- Sliced feature matrix from the training dataset.
        - **TopkDF** (*np.ndarray*) -- Sliced feature matrix from the top-k dataset.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.scoreCalculator import OverlapScore

            train_df = pd.read_csv("train.csv")

            topk_df = pd.read_csv("topk.csv")

            overlap = OverlapScore(train_df, topk_df, startBandTrainDF=2, startBandTopkDF=2)

            score = overlap.run(n_clusters=3)


    **Credits**

    This implementation was created by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, TrainDF, TopkDF, startBandTrainDF = 2, startBandTopkDF = 2):
        self.TrainDF = TrainDF.iloc[:, startBandTrainDF:]
        self.TopkDF = TopkDF.iloc[:, startBandTopkDF:]

        if self.TrainDF.shape[1] != self.TopkDF.shape[1]:
            raise ValueError("TrainDF and TopkDF must have the same number of columns after slicing.")

    def run(self, n_clusters=2):
        """
        Computes the cluster overlap score using KMeans clustering.

        Args:
            n_clusters (int): Number of clusters to use for KMeans (default: 2).

        Returns:
            float: Proportion of top-k samples that belong to the same cluster as the first training sample.
        """
        combined = np.vstack([self.TrainDF, self.TopkDF])
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(combined)

        trainCluster = labels[:len(self.TrainDF)]
        topkCluster = labels[len(self.TrainDF):]

        overlapScore = np.sum(trainCluster[0] == topkCluster) / len(topkCluster)
        return overlapScore
