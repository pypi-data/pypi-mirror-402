"""
Geometric transformers adapted for PLI modalities
"""
import logging

import numpy as np

from tiamat.io import ImageResult, ImageAccessor
from tiamat.metadata import ImageMetadata
from tiamat.transformers.affine import AffineTransformer
from tiamat.transformers.dfield import DeformationFieldTransformer
from tiamat.transformers.axes import MirrorTransformer, ReorderCoordinatesTransformer


logger = logging.getLogger(__name__)


def dir2cplx(direction, frequency=2.):
    dir_rad = np.deg2rad(direction)
    
    im_part = np.sin(frequency * dir_rad)
    real_part = np.cos(frequency * dir_rad)
    direction_cplx = np.stack((im_part, real_part), axis=-1)

    return direction_cplx


def cplx2dir(direction_cplx, frequency=2.):
    dir_rad = (np.arctan2(direction_cplx[..., 0], direction_cplx[..., 1]) / frequency) % np.pi

    direction = np.rad2deg(dir_rad)

    return direction


def affine_correction(direction, mat):
    dtype = direction.dtype

    direction_cplx = dir2cplx(direction, frequency=1.)
    im_part = direction_cplx[..., 0]
    real_part = direction_cplx[..., 1]

    # Note that different orientations of y-axis and imaginary axis are included here
    real_out = mat[0, 0] * real_part + mat[0, 1] * -im_part
    im_out = mat[1, 0] * -real_part + mat[1, 1] * im_part

    direction_out = cplx2dir(np.stack((im_out, real_out), axis=-1), frequency=1.).astype(dtype)

    return direction_out


def mirror_correction(direction, mirror_horizontal=False, mirror_vertical=False):
    dtype = direction.dtype

    direction_cplx = dir2cplx(direction, frequency=1.)
    im_part = direction_cplx[..., 0]
    real_part = direction_cplx[..., 1]

    if mirror_horizontal:
        real_part = -real_part
    if mirror_vertical:
        im_part = -im_part

    direction_out = cplx2dir(np.stack((im_part, real_part), axis=-1), frequency=1.).astype(dtype)

    return direction_out


def transpose_correction(direction):
    dtype = direction.dtype

    direction_cplx = dir2cplx(direction, frequency=1.)
    direction_out = cplx2dir(direction_cplx[..., ::-1], frequency=1.).astype(dtype)

    return direction_out


def ppd_correction(direction, coord_x, coord_y):
    """
    Performs Preservation of Principal Direction (PPD) [1] to reorient direction maps along a non-linear
    transformation field. The transformation field is represented by the resampling pixel coordinates for
    pixel locations in the source image.

    [1] D. Alexander et al. (2001). Spatial transformations of diffusion tensor magnetic resonance images.
    """
    dtype = direction.dtype

    direction_cplx = dir2cplx(direction, frequency=1.)

    # Jacobi matrix [[a, b], [c, d]]
    a = np.gradient(coord_x, axis=1) # dF_x / d_x
    b = -np.gradient(coord_x, axis=0) # dF_x / d_y
    c = np.gradient(-coord_y, axis=1) # dF_y / d_x
    d = -np.gradient(-coord_y, axis=0) # dF_y / d_y

    # Multiply by inverse of Jacobi. Normalization by (ad - bc) not necessary as we just need the angle
    d_x = d * direction_cplx[..., 1] - b * direction_cplx[..., 0]
    d_y = -c * direction_cplx[..., 1] + a * direction_cplx[..., 0]

    direction_out = cplx2dir(np.stack((d_y, d_x), axis=-1, dtype=dtype), frequency=1.)

    return direction_out


class DirectionAffineTransformer(AffineTransformer):

    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        import tiamat.metadata.dimensions as d

        # Perform resampling for 2D coordinates
        image = dir2cplx(image, frequency=2.)

        metadata.dimensions = (*metadata.dimensions, d.VECTOR)
        metadata.shape = (*metadata.shape, 2)

        image = super().transform_image(image, metadata, accessor)

        # Transform back to polar coordinate
        image = cplx2dir(image, frequency=2.)
        metadata.dimensions = metadata.dimensions[:-1]
        metadata.shape = metadata.shape[:-1]

        image = affine_correction(image, self.affine_matrix)

        return image


class DirectionDeformationFieldTransformer(DeformationFieldTransformer):

    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        import tiamat.metadata.dimensions as d

        try:
            coordinates = accessor.history[id(self)]
        except KeyError:
            raise Exception("transform_access has to be called once before transform_image")

        # Perform resampling for 2D coordinates
        image = dir2cplx(image, frequency=2.)
        metadata.dimensions = (*metadata.dimensions, d.VECTOR)
        metadata.shape = (*metadata.shape, 2)

        image = super().transform_image(image, metadata, accessor)

        # Transform back to polar coordinate
        image = cplx2dir(image, frequency=2.)
        metadata.dimensions = metadata.dimensions[:-1]
        metadata.shape = metadata.shape[:-1]

        image = ppd_correction(
            image,
            coord_x=coordinates[1],
            coord_y=coordinates[0],
        )

        return image


class DirectionMirrorTransformer(MirrorTransformer):

    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        import tiamat.metadata.dimensions as d

        image = super().transform_image(image, metadata, accessor)

        # Mirror direction values relative to the imaging plane
        if 'stack_dimension' in metadata.additional_metadata.keys():
            stack_dim = metadata.additional_metadata['stack_dimension']

            if stack_dim == d.X:
                # Assume direction in (y, z) plane
                mirror_horizontal = self.mirror_y
                mirror_vertical = self.mirror_z
            elif stack_dim == d.Y:
                # Assume direction in (x, z) plane
                mirror_horizontal = self.mirror_x
                mirror_vertical = self.mirror_z
            elif stack_dim == d.Z:
                # Assume direction in (x, y) plane
                mirror_horizontal = self.mirror_x
                mirror_vertical = self.mirror_y
            else:
                raise ValueError(f"Unsupported stack_dimension {stack_dim} in DirectionMirrorTransformer")
        else:
            # By default assume direction in (x, y) plane
            mirror_horizontal = self.mirror_x
            mirror_vertical = self.mirror_y

        image = mirror_correction(
            image,
            mirror_horizontal,
            mirror_vertical,
        )

        return image


class DirectionReorderCoordinatesTransformer(ReorderCoordinatesTransformer):

    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        import tiamat.metadata.dimensions as d

        image = super().transform_image(image, metadata, accessor)

        # Transpose direction values relative to the imaging plane
        if 'stack_dimension' in metadata.additional_metadata.keys():
            stack_dim = metadata.additional_metadata['stack_dimension']

            assert len(self.reorder_axes) == 3

            # For each possible imaging plane, check if order of coordinates changed
            if stack_dim == d.X:
                # Assume direction in (y, z) plane
                if self.reorder_axes.index(d.Y) < self.reorder_axes.index(d.Z):
                    image = transpose_correction(image)
            elif stack_dim == d.Y:
                # Assume direction in (x, z) plane
                if self.reorder_axes.index(d.X) < self.reorder_axes.index(d.Z):
                    image = transpose_correction(image)
            elif stack_dim == d.Z:
                # Assume direction in (x, y) plane
                if self.reorder_axes.index(d.X) < self.reorder_axes.index(d.Y):
                    image = transpose_correction(image)
            else:
                raise ValueError(f"Unsupported stack_dimension {stack_dim} in DirectionMirrorTransformer")
        else:
            # By default assume direction in (x, y) plane
            if self.reorder_axes.index(d.X) < self.reorder_axes.index(d.Y):
                image = transpose_correction(image)

        return image
