"""
Readers for deformation fields.
"""

from typing import Tuple
from functools import cached_property

import numpy as np
import h5py as h5

from tiamat.cache import instance_cache
from tiamat.readers.protocol import ImageReader
from tiamat.io import ImageAccessor, ImageResult
from tiamat.metadata import ImageMetadata


class DeformationFieldReader(ImageReader):

    def __init__(self, fname):
        self.fname = fname

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        raise NotImplementedError

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        raise NotImplementedError

    @cached_property
    def dtype(self):
        raise NotImplementedError

    @cached_property
    def scales(self) -> float:
        raise NotImplementedError

    @cached_property
    def spacing(self) -> tuple[float, float]:
        raise NotImplementedError

    @cached_property
    def origin(self) -> Tuple[float, float]:
        raise NotImplementedError

    @cached_property
    def shape(self) -> tuple:
        raise NotImplementedError


class HidraDeformationFieldReader(DeformationFieldReader):

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        from tiamat import metadata as md

        return md.ImageMetadata(
            image_type=md.IMAGE_TYPE_VECTOR,
            shape=self.shape,
            dtype=self.dtype,
            file_path=self.fname,
            value_range=None,
            scales=self.scales,
            dimensions=[md.dimensions.Y, md.dimensions.X, md.dimensions.VECTOR],
            additional_metadata={
                'dfield_origin': self.origin,
            }
        )

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        from tiamat.readers.processing import access_and_rescale_image

        image_scale = self.scales[0]
        image = access_and_rescale_image(
            image=self.file_handle["deformation"],
            metadata=self.read_metadata(),
            accessor=accessor,
            image_scale=image_scale,
        )

        return image

    @cached_property
    def file_handle(self) -> h5.File:
        return h5.File(self.fname)

    @cached_property
    def dtype(self):
        return self.file_handle["deformation"].dtype

    @cached_property
    def scales(self) -> float:
        x_range = self.file_handle["xrange"][:2]
        y_range = self.file_handle["yrange"][:2]

        x_scale = 1 / float(x_range[1] - x_range[0])
        y_scale = 1 / float(y_range[1] - y_range[0])

        assert x_scale == y_scale, "HidraDeformationFieldReader only supports isotropic scale"

        return [x_scale]

    @cached_property
    def spacing(self) -> tuple[float, float]:
        return (1.0, 1.0)

    @cached_property
    def origin(self) -> Tuple[float, float]:
        x_offset = self.file_handle["xrange"][0].item() * self.spacing[0]
        y_offset = self.file_handle["yrange"][0].item() * self.spacing[1]

        return (y_offset, x_offset)

    @cached_property
    def shape(self) -> tuple:
        return self.file_handle["deformation"].shape

    @classmethod
    def check_file(cls, fname) -> bool | int | float:
        import os
        import h5py as h5

        _, ext = os.path.splitext(fname)

        if ext.lower() not in (".hdf5", ".h5"):
            return False

        with h5.File(fname, 'r') as f:
            if all([k in f.keys() for k in ['deformation', 'xrange', 'yrange']]):
                # Higher priority than generic HDF5 reader
                return 10
            else:
                return False


class PyregDeformationFieldReader(DeformationFieldReader):

    def __init__(self, fname):
        super().__init__(fname)

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        from tiamat import metadata as md

        return md.ImageMetadata(
            image_type=md.IMAGE_TYPE_VECTOR,
            shape=self.shape,
            dtype=self.dtype,
            file_path=self.fname,
            value_range=None,
            scales=self.scales,
            dimensions=[md.dimensions.Y, md.dimensions.X, md.dimensions.VECTOR],
            additional_metadata={
                'dfield_origin': self.origin,
            }
        )

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        from tiamat.readers.processing import access_and_rescale_image

        # Read, crop, and rescale.
        target_scale = accessor.scale
        available_scale, available_scale_index = self._find_scale(target_scale)
        pyramid_level = self.pyramid_datasets[available_scale_index]

        image = access_and_rescale_image(
            image=pyramid_level,
            metadata=self.read_metadata(),
            accessor=accessor,
            image_scale=available_scale,
        )

        # Convert mm to mu
        image = image * 1000

        return image

    @instance_cache
    def _find_scale(self, target_scale: float) -> tuple[float, int]:
        import numpy as np

        scales = [
            (scale, index)
            for index, scale in enumerate(self.scales)
            if np.any(scale >= np.array(target_scale))
        ]
        # return either smallest suitable scale, or largest
        if len(scales) > 0:
            return scales[-1]
        else:
            return (self.scales[0], 0)

    @cached_property
    def file_handle(self) -> h5.File:
        return h5.File(self.fname)

    @cached_property
    def pyramid_root_dataset(self):
        return self.file_handle["pyramid"]

    @cached_property
    def pyramid_datasets(self):
        keys = sorted(self.pyramid_root_dataset.keys())
        return [self.pyramid_root_dataset[key] for key in keys]

    @cached_property
    def pyramid_shapes(self) -> list[tuple[int, int]]:
        return [pyramid_level.shape for pyramid_level in self.pyramid_datasets]

    @cached_property
    def dtype(self):
        return self.file_handle["Image"].dtype

    @cached_property
    def spacing(self) -> tuple[float, float]:
        return tuple(self.attributes["transform_other_parameters"][4:6] * 1000)

    @cached_property
    def scales(self) -> float:
        scales = sorted(self.file_handle["pyramid"].attrs["scales"])[::-1]

        return scales

    @cached_property
    def origin(self) -> Tuple[float, float]:
        offset = self.attributes["transform_other_parameters"][2:4]

        return offset

    @cached_property
    def shape(self) -> tuple:
        return self.pyramid_shapes[0]

    @cached_property
    def attributes(self) -> dict:
        return dict(self.file_handle["Image"].attrs)

    @classmethod
    def check_file(cls, fname) -> bool | int | float:
        import os
        import h5py as h5

        _, ext = os.path.splitext(fname)

        if ext.lower() not in (".hdf5", ".h5"):
            return False

        with h5.File(fname, 'r') as f:
            if f["Image"].attrs["image_modality"] == "Transform":
                # Higher priority than generic HDF5 reader
                return 
            else:
                return False
