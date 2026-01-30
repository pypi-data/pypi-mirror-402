"""
Reader for BigTiff.
"""

from functools import cached_property
import numpy as np

import pytiff

from tiamat.readers.protocol import ImageReader
from tiamat.cache import instance_cache
from tiamat.io import ImageAccessor
from tiamat.metadata import ImageMetadata

# Reference: https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf
TIFF_RESOLUTION_UNIT_TO_MICRON = {
    # no unit
    1: 1,
    # inch
    2: 25400,
    # centimeter
    3: 10000,
}


class BigTiffReader(ImageReader):
    def __init__(self, fname):
        self.fname = fname

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        from tiamat import metadata as md

        # pad image with generic channels
        dimensions = [
            md.dimensions.Y,
            md.dimensions.X,
        ]
        if len(self.shape) == 3:
            # try to determine the colors
            if self.shape[2] == 3:
                dimensions.append(md.dimensions.RGB)
            elif self.shape[2] == 4:
                dimensions.append(md.dimensions.RGBA)
            else:
                dimensions.append(md.dimensions.C)
        else:
            # all generic channels
            dimensions.extend(
                [md.dimensions.C for _ in range(max(len(self.shape) - 2, 0))]
            )

        return md.ImageMetadata(
            image_type=md.IMAGE_TYPE_IMAGE,
            shape=self.shape,
            dtype=self.dtype,
            file_path=self.fname,
            value_range=self.value_range,
            spacing=self.image_spacing,
            dimensions=dimensions,
            scales=self.scales,
            additional_metadata=self.tags,
        )

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        """Reads image crops from a BigTiff file.

        WARNING: As tiffio is not thread-safe, do not use it in a threaded environment. Use multiprocessing instead.

        Parameters
        ----------
        accessor : ImageAccessor
            Image accessor object to request data.

        Returns
        -------
        ndarray
            Resulting image data, rescaled to the requested scale. Missing values are padded.
        """
        from tiamat.readers.processing import access_and_rescale_image, expand_to_length

        # Read, crop, and rescale.
        target_scale = expand_to_length(accessor.scale, 2)
        available_scale, available_scale_index = self._find_scale(min(target_scale[:2]))
        available_scale = (available_scale, available_scale, *target_scale[2:])
        image = access_and_rescale_image(
            image=self.get_file_handle_for_page(available_scale_index),
            metadata=self.read_metadata(),
            accessor=accessor,
            image_scale=available_scale,
        )

        return image

    @instance_cache
    def _find_scale(self, target_scale: float) -> tuple[float, int]:
        tiled_scales = [
            (scale, index)
            for index, scale in enumerate(self.scales)
            if scale >= target_scale and self.is_page_tiled(index)
        ]
        if tiled_scales:
            return tiled_scales[-1]
        untiled_scales = [
            (scale, index)
            for index, scale in enumerate(self.scales)
            if scale >= target_scale and not self.is_page_tiled(index)
        ]
        return untiled_scales[0]

    @cached_property
    def num_channels(self) -> int:
        return self.get_file_handle_for_page(0).samples_per_pixel

    @cached_property
    def num_pages(self) -> int:
        with pytiff.Tiff(self.fname) as handle:
            return handle.number_of_pages

    @instance_cache
    def get_file_handle_for_page(self, page: int) -> pytiff.Tiff:
        handle = pytiff.Tiff(self.fname)
        handle.set_page(page)
        return handle

    @cached_property
    def page_sizes(self) -> list[tuple[int, int]]:
        return [
            self.get_file_handle_for_page(page).shape for page in range(self.num_pages)
        ]

    @cached_property
    def scales(self) -> list[float]:
        import math

        scales = [shape[0] / float(self.shape[0]) for shape in self.page_sizes]
        return [1 / 2 ** round(math.log(1 / scale, 2)) for scale in scales]

    @cached_property
    def shape(self) -> tuple:
        return sorted(self.page_sizes, key=lambda shape: -shape[0])[0]

    @cached_property
    def dtype(self):
        return self.get_file_handle_for_page(0).dtype

    @instance_cache
    def is_page_tiled(self, page_index: int) -> bool:
        # At the moment, we read metadata from page zero by default.
        # We might want to change this in the future.
        is_tiled = self.get_file_handle_for_page(page_index).is_tiled()
        return is_tiled

    @cached_property
    def image_spacing(self) -> tuple[float, float]:
        from pytiff import tags

        resolution_unit = self.tags[tags.resolution_unit]

        resolution_unit_micron = TIFF_RESOLUTION_UNIT_TO_MICRON.get(resolution_unit)
        if not resolution_unit_micron:
            raise RuntimeError(
                f"Encountered invalid resolution unit {resolution_unit} in {self.fname}. See https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf for supported units."
            )

        return (
            float(self.tags[tags.x_resolution]) / resolution_unit_micron,
            float(self.tags[tags.y_resolution]) / resolution_unit_micron,
        )

    @cached_property
    def tags(self) -> dict:
        tags = self.get_file_handle_for_page(0).read_tags()
        return tags

    @cached_property
    def is_tiled(self) -> bool:
        return self.is_page_tiled(0)

    @cached_property
    def value_range(self) -> tuple[float | int, float | int]:
        import numpy as np

        dtype = self.dtype
        if np.issubdtype(dtype, np.integer):
            dtype_info = np.iinfo(dtype)
        elif np.issubdtype(dtype, np.floating):
            dtype_info = np.finfo(dtype)
        else:
            raise TypeError(f"Cannot determin value range for dtype {dtype}")

        return dtype_info.min, dtype_info.max

    @classmethod
    def check_file(cls, fname) -> bool | int | float:
        import os

        _, ext = os.path.splitext(fname)
        # return higher priority than generic reader
        return 10 if ext.lower() in (".tif", ".tiff") else False
