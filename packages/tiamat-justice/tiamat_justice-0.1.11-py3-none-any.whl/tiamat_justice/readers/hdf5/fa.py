"""
Reader for h5pli corresponding to the PLI.json.
"""

# pylint: disable=no-member

import json
import pathlib
import typing as typ
from functools import cached_property

import h5py
import numpy as np

from tiamat.cache import instance_cache, instance_cached_property
from tiamat.io import ImageAccessor
from tiamat.metadata import ImageMetadata
from tiamat.readers.protocol import ImageReader

from ..deformation import DeformationFieldReader as DeformationFieldReaderBase

PRIORITY = 10  # needs to be higher than BDA reader

ASSERT_ATTRIBUTES = [
    "channels",
    "samples_per_pixel",
    "image_modality",
    "pixel_width",
    "measurement_time",
]

# TODO: from PLI.json
MODALITY = {
    "raw": {
        "channels": 1,
        "dtype": np.uint16,
        "min_intensity": 0,
        "max_intensity": 2**16 - 1,  # 16-bit raw data
    },
    "rawpreview": {
        "channels": 3,
        "dtype": np.uint8,
        "min_intensity": 0,
        "max_intensity": 255,
    },
    "hdr": {
        "channels": 3,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": None,
    },
    "calibrated": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": 2**16 - 1,
    },
    "transmittance": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": 1.0,
    },
    "transform": {
        "channels": 2,
        "dtype": np.float32,
        "min_intensity": None,
        "max_intensity": None,
    },
    "direction": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": 180.0,
    },
    "retardation": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": 1.0,
    },
    "inclination": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": -90.0,
        "max_intensity": 90.0,
    },
    "trel": {
        "channels": 1,
        "dtype": np.float32,
        "min_intensity": 0.0,
        "max_intensity": 1.0,
    },
    "fom": {
        "channels": 3,
        "dtype": np.uint8,
        "min_intensity": 0,
        "max_intensity": 255,
    },
    "mask": {
        "channels": 1,
        "dtype": np.uint8,
        "min_intensity": 0,
        "max_intensity": 255,
    },
}


def decode_attribute(dict_obj: dict) -> typ.Any:
    """Decode attribute from json dictionary.

    The internal structure is "key": {"value": ... , "dtype": ..., "unit": ...}

    Args:
        dict_obj (dict): Dictionary with attribute information.

    Returns:
        typ.Any: Decoded attribute value.
    """
    value = dict_obj["value"]
    dtype = dict_obj["dtype"]
    if isinstance(value, list):
        value = np.array(value, dtype=dtype)
    else:
        if "int" in dtype:
            value = int(value)
        elif "float" in dtype:
            value = float(value)
        elif "bool" in dtype:
            value = bool(value)
        elif "str" in dtype:
            value = str(value)
        else:
            raise ValueError(f"Unknown dtype {dtype} for attribute in {dict_obj}")
    return value


def get_attributes_from_json(fname: str | pathlib.Path) -> dict[str, typ.Any]:
    fname = pathlib.Path(fname)
    if not fname.is_file():
        raise FileNotFoundError(f"File {fname} does not exist or is not a valid file.")

    with open(fname.with_suffix(".json"), "r", encoding="utf-8") as json_file:
        attrs = json.load(json_file)

    # Decode attributes and add unit if available
    for key, val in list(attrs.items()):
        attrs[key] = decode_attribute(val)
        if "unit" in val:
            attrs[f"{key}_unit"] = val["unit"]
    return attrs


class FaHdf5Reader(ImageReader):

    def __init__(self, fname: str | pathlib.Path, **h5py_kwargs: dict):
        self.fname = pathlib.Path(fname)
        self.prefix = self.fname.stem

        if not self.fname.resolve().is_file():
            raise FileNotFoundError(f"File {self.fname} does not exist or is not a valid file.")

        # TODO: Set optimal default kwargs (?)
        self.h5py_kwargs = h5py_kwargs

    @staticmethod
    def _value_range(attributes: dict[str, typ.Any]) -> tuple[float | None, float | None]:
        vmin, vmax = None, None
        if "image_modality" in attributes:
            vmin = MODALITY[attributes["image_modality"]]["min_intensity"]
            vmax = MODALITY[attributes["image_modality"]]["max_intensity"]

        # Not yet in json
        if vmin is None:
            vmin = attributes.get("pyramid_minintensity", None)
        if vmax is None:
            vmax = attributes.get("pyramid_maxintensity", None)

        return vmin, vmax

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        from tiamat import metadata as md

        attributes = get_attributes_from_json(self.fname.with_suffix(".json"))
        # add pyramid attributes
        if "pyramid_minintensity" not in attributes:
            attributes["pyramid_minintensity"] = self.file_handle["pyramid"].attrs.get(
                "minintensity"
            )
        if "pyramid_maxintensity" not in attributes:
            attributes["pyramid_maxintensity"] = self.file_handle["pyramid"].attrs.get(
                "maxintensity"
            )

        # set all tiamat metadata properties
        channel_dimensions = []
        if attributes["samples_per_pixel"] > 1:
            if attributes["image_modality"].lower() == "transform":
                channel_dimensions.append(md.dimensions.VECTOR)
            else:
                channel_dimensions.append(md.dimensions.C)

        if attributes["channels"] == 3:
            channel_dimensions.append(md.dimensions.RGB)
        elif attributes["channels"] == 4:
            channel_dimensions.append(md.dimensions.RGBA)

        # TODO: 3d
        shape = (attributes["image_height"], attributes["image_width"])
        if attributes["samples_per_pixel"] > 1:
            shape = shape + (attributes["samples_per_pixel"],)
        if attributes["channels"] > 1:
            shape = shape + (attributes["channels"],)
        attributes["shape"] = shape

        metadata: ImageMetadata = ImageMetadata(
            image_type="image",
            shape=tuple([int(s) for s in attributes["shape"]]),
            value_range=self._value_range(attributes),
            dtype=self.dtype,
            dimensions=["y", "x"] + channel_dimensions,
            file_path=str(self.fname),
            spacing=(attributes["pixel_width"], attributes["pixel_height"]),
            scales=self.scales,
            additional_metadata=attributes,
        )

        return metadata

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        from tiamat.readers.processing import access_and_rescale_image

        # Read, crop, and rescale.
        target_scale = accessor.scale
        available_scale = self._find_scale(target_scale)
        level = self.scales.index(available_scale)

        metadata = self.read_metadata()

        image = access_and_rescale_image(
            image=self.level(level),
            metadata=metadata,
            accessor=accessor,
            image_scale=available_scale,
        )

        # TODO: can be removed in the future
        if "normalization_value" in metadata.additional_metadata:
            image /= metadata.additional_metadata["normalization_value"]

        return image

    def level(self, level: int) -> ImageReader:
        return self.file_handle["pyramid"][f"{level:02}"]

    @cached_property
    def file_handle(self) -> h5py.File:
        return h5py.File(self.fname, **self.h5py_kwargs)

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

    @instance_cache
    def _find_scale(self, target_scale: float | tuple[float, ...]) -> tuple[float, int]:
        scales = [scale for scale in self.scales if np.all(scale >= np.array(target_scale))]
        assert len(scales) > 0, f"No scale found for target scale {target_scale} in {self.fname}"
        # TODO: return closest?
        return scales[-1]

    @instance_cached_property
    def scales(self) -> list[tuple[float, float]]:
        return [(1 / 2**i, 1 / 2**i) for i, _ in enumerate(self.file_handle["pyramid"])]

    @instance_cached_property
    def shape(self) -> tuple:
        return self.level(0).shape

    @instance_cached_property
    def dtype(self):
        return self.level(0).dtype

    @instance_cached_property
    def spacing(self) -> tuple[float, float]:
        return self.read_metadata().spacing

    @classmethod
    def check_file(cls, fname: str | pathlib.Path) -> bool | int | float:
        fname = pathlib.Path(fname)

        if not (fname.is_file() or fname.is_symlink()):
            return False

        json_path = fname.with_suffix(".json")
        if not (json_path.is_file() or json_path.is_symlink()):
            return False

        # if link check target
        if json_path.is_symlink():
            json_path = json_path.resolve()
            if not json_path.is_file():
                return False

        # fast check of attributes
        try:
            attrs = get_attributes_from_json(json_path)
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
            return False

        if "image_modality" not in attrs:
            return False
        if attrs["image_modality"].lower() not in MODALITY.keys():
            return False

        # TODO: check if this takes to long
        # check if datasets exists
        with h5py.File(fname, "r") as h5file:
            if "Image" not in h5file:
                return False
            if "pyramid" not in h5file:
                return False

        return PRIORITY


class FaDeformationFieldReader(FaHdf5Reader, DeformationFieldReaderBase):

    @instance_cache
    def read_metadata(self) -> ImageMetadata:
        meta = super().read_metadata()
        meta.additional_metadata["dfield_origin"] = self.origin
        return meta

    def read_image(self, accessor: ImageAccessor) -> np.ndarray:
        image = super().read_image(accessor)
        # TODO: check unit
        image *= 1000  # Convert mm to mu
        return image

    @cached_property
    def shape(self) -> tuple[int, int]:

        if "transform_target_width":
            # TODO: remove when metadata has been updated
            return (
                super().read_metadata().additional_metadata["transform_target_width"],
                super().read_metadata().additional_metadata["transform_target_height"],
            )

        return (
            super().read_metadata().additional_metadata["transform_target_pixel_height"],
            super().read_metadata().additional_metadata["transform_target_pixel_height"],
        )

    @cached_property
    def origin(self) -> tuple[float, float]:
        offset = super().read_metadata().additional_metadata.get("transform_offset", (0.0, 0.0))
        # TODO: probably not final name
        return offset

    @classmethod
    def check_file(cls, fname: pathlib.Path) -> bool | int | float:
        result = FaHdf5Reader.check_file(fname)
        if not result:
            return result

        attributes = get_attributes_from_json(fname.with_suffix(".json"))
        if "transform" != attributes.get("image_modality", "").lower():
            return False

        return PRIORITY + 1
