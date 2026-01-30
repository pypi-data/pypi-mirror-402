"""
Reader for Zarr (v3) pyramid files written by the HDF5→Zarr converter.
"""

from functools import cached_property

import numpy as np

from tiamat.readers.protocol import ImageReader
from tiamat.cache import instance_cache
from tiamat.io import ImageAccessor
from tiamat.metadata import ImageMetadata


class ZarrReader(ImageReader):
    def __init__(self, fname, prefix="/"):
        self.fname = fname  # path to <name>.zarr directory
        self.prefix = prefix

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        from tiamat import metadata as md

        # TODO: Need a better way to determine channel dimensions
        # This implementation causes problems when moving to 3D
        dimensions = [md.dimensions.Y, md.dimensions.X]
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
            additional_metadata=self.attributes,
        )

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        from tiamat.readers.processing import access_and_rescale_image, expand_to_length

        # Read, crop, and rescale.
        target_scale = expand_to_length(accessor.scale, 2)
        available_scale, available_scale_index = self._find_scale(min(target_scale[:2]))
        available_scale = (available_scale, available_scale, *target_scale[2:])
        pyramid_level = self.pyramid_datasets[available_scale_index]

        image = access_and_rescale_image(
            image=pyramid_level,
            metadata=self.read_metadata(),
            accessor=accessor,
            image_scale=available_scale,
        )
        return image

    @instance_cache
    def _find_scale(self, target_scale: float) -> tuple[float, int]:
        scales = [
            (scale, index)
            for index, scale in enumerate(self.scales)
            if scale >= target_scale
        ]
        # return either smallest suitable scale, or largest
        if len(scales) > 0:
            return scales[-1]
        else:
            return (self.scales[0], 0)

    # ---------- Zarr accessors ----------

    @cached_property
    def file_handle(self):
        import zarr

        # Open Zarr v3 root group read-only
        return zarr.open_group(self.fname, mode="r", zarr_format=3)

    @cached_property
    def image_root_dataset(self):
        import os

        # Same logical pathing as HDF5Reader: "<prefix>/Image"
        return self.file_handle[os.path.join(self.prefix, "Image")]

    @cached_property
    def pyramid_root_dataset(self):
        import os

        # Same logical pathing as HDF5Reader: "<prefix>/pyramid"
        return self.file_handle[os.path.join(self.prefix, "pyramid")]

    @cached_property
    def pyramid_datasets(self):
        # Sorted levels (keys are strings like "00", "01", ...)
        keys = sorted(self.pyramid_root_dataset.keys())
        return [self.pyramid_root_dataset[key] for key in keys]

    @cached_property
    def pyramid_shapes(self) -> list[tuple[int, int]]:
        return [pyramid_level.shape for pyramid_level in self.pyramid_datasets]

    @cached_property
    def scales(self) -> list[float]:
        return [scale for scale in self.attributes["scales"]]

    @cached_property
    def shape(self) -> tuple:
        return self.pyramid_shapes[0]

    @cached_property
    def dtype(self):
        return self.pyramid_datasets[0].dtype

    @cached_property
    def image_spacing(self) -> tuple[float, float]:
        return self.spacing

    @cached_property
    def spacing(self) -> tuple[float, float]:
        if "spacing" in self.attributes.keys():
            return np.array(self.attributes["spacing"], dtype=float)
        elif "spacing" in self.image_attributes.keys():
            return np.array(self.image_attributes["spacing"], dtype=float)
        else:
            return np.array([1.0, 1.0])

    @cached_property
    def origin(self) -> tuple[float, float]:
        if "offset" in self.attributes.keys():
            return np.array(self.attributes["offset"], dtype=float)
        elif "offset" in self.image_attributes.keys():
            return np.array(self.image_attributes["offset"], dtype=float)
        else:
            return np.array(0.0, 0.0)

    @cached_property
    def attributes(self) -> dict:
        # Zarr v3 attrs are Mapping-like; convert to plain dict
        return dict(self.pyramid_root_dataset.attrs)

    @cached_property
    def image_attributes(self) -> dict:
        return dict(self.image_root_dataset.attrs)

    @cached_property
    def value_range(self) -> tuple[float | int, float | int]:
        from tiamat.metadata import get_dtype_limits

        return get_dtype_limits(self.dtype)

    @classmethod
    def check_file(cls, fname) -> bool | int | float:
        """
        Return a priority for .zarr directories; False otherwise.
        Prefer higher than a generic reader, lower than specialized ones.
        """
        import os

        # Accept a directory that ends with ".zarr"
        if os.path.isdir(fname) and fname.lower().endswith(".zarr"):
            return 5
        return False
