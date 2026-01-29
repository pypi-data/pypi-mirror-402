# NetCDFViewer Class for Visualizing NetCDF (.nc) Raster Data

# **Importing and Using the NetCDFViewer Class in a Python Program**
#
#             from geoanalytics.visualization import NetCDFViewer
#
#             viewer = NetCDFViewer('sample.nc')
#
#             viewer.run(cmap='plasma', title='Sample NetCDF Image')
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


class NetCDFViewer():
    """
    **About this algorithm**

    :**Description**:
        NetCDFViewer is a raster data visualization tool designed for rendering single-band raster layers
        from NetCDF (.nc) files. It leverages `rasterio` for data access and `matplotlib` for rendering.
        The class supports customizable colormaps and plot titles, making it suitable for visualizing
        meteorological, oceanographic, or climate data.

    :**Parameters**:
        - `inputFile` (str): Path to the input NetCDF (.nc) file.

    :**Attributes**:
        - **inputFile** (*str*) -- The path to the NetCDF file to be visualized.
        - **imageData** (*numpy.ndarray*) -- The raster data extracted from the NetCDF file.

    **Execution methods**

    **Calling from a Python program**

    .. code-block:: python

            from geoanalytics.visualization import NetCDFViewer

            viewer = NetCDFViewer("sample.nc")

            viewer.run(cmap='plasma', title='NetCDF Raster Display')


    **Credits**

    This implementation was developed by Raashika and revised by M. Charan Teja under the guidance of Professor Rage Uday Kiran.
    """
    def __init__(self, inputFile):
        self.inputFile = inputFile
        self.imageData = None

    def run(self, cmap='gray', title='NC Image'):
        """
        Reads and displays the first raster band from the NetCDF file.

        Args:
            cmap (str): Colormap to use for visualization (default: 'gray').
            title (str): Plot title to display (default: 'NC Image').

        Raises:
            ValueError: If image data is not loaded properly.
        """
        with rasterio.open(self.inputFile) as src:
            self.imageData = src.read(1)
        if self.imageData is None:
            raise ValueError("Image not loaded")
        plt.imshow(self.imageData, cmap=cmap)
        plt.colorbar()
        plt.title(title)
        plt.show()