import logging
import os
from datetime import datetime
from os.path import exists, expanduser, join, splitext, basename
from typing import Any

import colored_logging as cl
import numpy as np
import rasters as rt
from rasters import RasterGeometry, Raster

from .constants import DEFAULT_WORKING_DIRECTORY, DEFAULT_PRODUCTS_DIRECTORY
from .exceptions import GEOS5FPGranuleNotAvailable

class GEOS5FPGranule:
    logger = logging.getLogger(__name__)

    DEFAULT_RESAMPLING_METHOD = "cubic"

    def __init__(
            self,
            filename: str,
            working_directory: str = None,
            products_directory: str = None,
            save_products: bool = False):
        if not exists(filename):
            raise IOError(f"GEOS-5 FP file does not exist: {filename}")

        if working_directory is None:
            working_directory = DEFAULT_WORKING_DIRECTORY

        if working_directory.startswith("~"):
            working_directory = expanduser(working_directory)

        logger.info(f"GEOS-5 FP working directory: {cl.dir(working_directory)}")

        if products_directory is None:
            products_directory = join(working_directory, DEFAULT_PRODUCTS_DIRECTORY)

        if products_directory.startswith("~"):
            products_directory = expanduser(products_directory)

        logger.info(f"GEOS-5 FP products directory: {cl.dir(products_directory)}")

        self.working_directory = working_directory
        self.products_directory = products_directory
        self.filename = filename
        self.save_products = save_products

    @property
    def product(self) -> str:
        return str(splitext(basename(self.filename))[0].split(".")[-3])

    @property
    def time_UTC(self) -> datetime:
        return datetime.strptime(splitext(basename(self.filename))[0].split(".")[-2], "%Y%m%d_%H%M")

    @property
    def product_directory(self):
        if self.products_directory is None:
            return None
        else:
            return join(self.products_directory, self.product)

    def variable_directory(self, variable):
        if self.product_directory is None:
            return None
        else:
            return join(self.product_directory, variable)

    @property
    def filename_stem(self):
        return splitext(basename(self.filename))[0]

    def variable_filename(self, variable):
        variable_directory = self.variable_directory(variable)

        if variable_directory is None:
            return None
        else:
            return join(variable_directory, f"{self.filename_stem}_{variable}.tif")

    def read(
            self,
            variable: str,
            geometry: RasterGeometry = None,
            resampling: str = None,
            nodata: Any = None,
            min_value: Any = None,
            max_value: Any = None,
            exclude_values=None) -> Raster:
        if resampling is None:
            resampling = self.DEFAULT_RESAMPLING_METHOD

        if nodata is None:
            nodata = np.nan

        variable_filename = self.variable_filename(variable)

        if variable_filename is not None and exists(variable_filename):
            data = Raster.open(variable_filename, nodata=nodata)
        else:
            try:
                data = Raster.open(f'netcdf:"{self.filename}":{variable}', nodata=nodata)
            except Exception as e:
                logger.error(e)
                os.remove(self.filename)

                raise GEOS5FPGranuleNotAvailable(f"removed corrupted GEOS-5 FP file: {self.filename}")

        if exclude_values is not None:
            for exclusion_value in exclude_values:
                data = rt.where(data == exclusion_value, np.nan, data)

        data = rt.clip(data, min_value, max_value)

        if self.save_products and variable_filename is not None and not exists(variable_filename):
            data.to_geotiff(variable_filename)

        if geometry is not None:
            data = data.to_geometry(geometry, resampling=resampling)

        return data
