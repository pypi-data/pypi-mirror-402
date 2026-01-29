# SilhouetteScore Class for Evaluating Cluster Separation Between Training and Top-k Datasets

# **Importing and Using the SilhouetteScore Class in a Python Program**
#
#             import pandas as pd
#
#             from geoanalytics.scoreCalculator import SilhouetteScore
#
#             train_df = pd.read_csv("train.csv")
#
#             topk_df = pd.read_csv("topk.csv")
#
#             scorer = SilhouetteScore(train_df, topk_df, startBandTrainDF=2, startBandTopkDF=2)
#
#             score = scorer.run()
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
from sklearn.metrics import silhouette_score

class SilhouetteScore:
    """
    **About this algorithm**

    :**Description**:
        SilhouetteScore evaluates how well-separated the top-k retrieved data points are from the training dataset
        using the silhouette coefficient. This is useful for validating retrieval performance and cluster consistency
        between two groups.

    :**Parameters**:
        - `TrainDF` (*pd.DataFrame*): The original training dataset.
        - `TopkDF` (*pd.DataFrame*): The retrieved top-k dataset.
        - `startBandTrainDF` (*int*): Column index from which to extract features from `TrainDF` (default: 2).
        - `startBandTopkDF` (*int*): Column index from which to extract features from `TopkDF` (default: 2).

    :**Attributes**:
        - **TrainDF** (*np.ndarray*) -- Extracted features from the training dataset.
        - **TopkDF** (*np.ndarray*) -- Extracted features from the top-k dataset.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            import pandas as pd

            from geoanalytics.scoreCalculator import SilhouetteScore

            train_df = pd.read_csv("train.csv")

            topk_df = pd.read_csv("topk.csv")

            scorer = SilhouetteScore(train_df, topk_df, startBandTrainDF=2, startBandTopkDF=2)

            score = scorer.run()

    **Credits**

    This implementation was created by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
    """

    def __init__(self, TrainDF, TopkDF, startBandTrainDF = 2, startBandTopkDF = 2):
        self.TrainDF = TrainDF.iloc[:, startBandTrainDF:]
        self.TopkDF = TopkDF.iloc[:, startBandTopkDF:]

        if self.TrainDF.shape[1] != self.TopkDF.shape[1]:
            raise ValueError("TrainDF and TopkDF must have the same number of columns after slicing.")

    def run(self):
        """
        Computes the silhouette score for the two combined datasets.

        Returns:
            float: Silhouette score indicating the separation between training and top-k data points.
        """
        combined = np.vstack([self.TrainDF, self.TopkDF])
        labels = np.array([1]*len(self.TrainDF) + [0]*len(self.TopkDF))
        score = silhouette_score(combined, labels)
        return score
