# TiffViewer Class for Visualizing GeoTIFF Raster Data

# **Importing and Using the TiffViewer Class in a Python Program**
#
#             from geoanalytics.visualization import TiffViewer
#
#             viewer = TiffViewer('sample.tif')
#
#             viewer.run(cmap='viridis', title='Sample TIFF Display')
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

import matplotlib.pyplot as plt
import rasterio


class TiffViewer():
    """
    **About this algorithm**

    :**Description**:
        TiffViewer is a lightweight visualization utility that reads and displays single-band raster
        data from TIFF files using `rasterio` and `matplotlib`. This class is ideal for visualizing
        satellite imagery, elevation maps, and other raster-based spatial data formats.

    :**Parameters**:
        - `inputFile` (str): Path to the input TIFF (.tif) file.

    :**Attributes**:
        - **inputFile** (*str*) -- The path to the GeoTIFF file to be visualized.
        - **imageData** (*numpy.ndarray*) -- The raster data read from the TIFF file.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            from geoanalytics.visualization import TiffViewer

            viewer = TiffViewer("sample.tif")

            viewer.run(cmap='viridis', title='Raster View')


    **Credits**

    This implementation was developed by Raashika and revised by M. Charan Teja under the supervision of Professor Rage Uday Kiran.
    """
    def __init__(self, inputFile):
        self.inputFile = inputFile
        self.imageData = None

    def run(self, cmap='gray', title='TIFF Image'):
        """
        Reads and displays the first band of the given TIFF file.

        Args:
            cmap (str): Matplotlib colormap for visualization (default: 'gray').
            title (str): Title to be displayed on the plot (default: 'TIFF Image').

        Raises:
            ValueError: If image data could not be loaded.
        """
        with rasterio.open(self.inputFile) as src:
            self.imageData = src.read(1)
        if self.imageData is None:
            raise ValueError("Image not loaded")
        plt.imshow(self.imageData, cmap=cmap)
        plt.colorbar()
        plt.title(title)
        plt.show()