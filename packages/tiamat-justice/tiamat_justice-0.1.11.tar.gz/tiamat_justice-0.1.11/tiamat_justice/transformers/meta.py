"""
Metadata transformers.
"""

from typing import Any, Dict, List

from tiamat.transformers.protocol import Transformer
from tiamat.io import ImageResult, ImageAccessor
from tiamat.metadata import ImageMetadata

import numpy as np


class SiibraTransformJsonTransformer(Transformer):

    def __init__(
            self,
            transform: np.array | List[List[float]],
        ):
        self.transform = np.array(transform)
        assert self.transform.shape == (4, 4), "Transform matrix needs to be 4x4"


    def transform_access(self, accessor: ImageAccessor, metadata: ImageMetadata) -> ImageAccessor:
        return accessor


    def transform_metadata(self, metadata: ImageMetadata) -> ImageMetadata:
        from dataclasses import replace

        metadata = replace(metadata)
        metadata.additional_metadata["transform.json"] = self.transform.tolist()

        return metadata


    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        return image


    @classmethod
    def from_json(cls, args: Dict[str, Any]):
        return cls(
            transform=args["transform"],
        )


class SiibraMetaJsonTransformer(Transformer):

    def __init__(
            self,
            transform: np.array | List[List[float]],
            preferred_colormap: str | List[str] = None,
            version: int = 1,
            best_view_point: List[np.array] | List[List[float]] = None,
        ):
        self.transform = np.array(transform)
        assert self.transform.shape == (4, 4), f"Transform matrix needs to be 4x4"

        if hasattr(preferred_colormap, "__iter__") and not isinstance(preferred_colormap, str):
            self.preferred_colormap = [p for p in preferred_colormap]
        else:
            self.preferred_colormap = [preferred_colormap]
        self.version = version

        if best_view_point is not None:
            assert len(best_view_point) == 4, "Best view point needs to configure a bounding box"
            self.best_view_point = [np.array(p) for p in best_view_point]
        else:
            self.best_view_point = None


    def transform_access(self, accessor: ImageAccessor, metadata: ImageMetadata) -> ImageAccessor:
        """
        Applies a transformation that affects accessing the image.

        Note: If this method modifies the incoming accessor,
        it has to return a __copy__ of the incoming object.
        The copy can be created using datalcasses.replace.
        """
        return accessor


    def transform_metadata(self, metadata: ImageMetadata) -> ImageMetadata:
        from dataclasses import replace

        meta_json = {
            "$schema": "https://raw.githubusercontent.com/FZJ-INM1-BDA/siibra-explorer/refs/heads/maint_shaderspec/.ngVolumeMetaSpec/meta.schema.v1.json",
            "version": self.version,
            "transform": self.transform.tolist(),
        }
        if self.preferred_colormap is not None:
            meta_json["preferredColormap"] = self.preferred_colormap
        if self.best_view_point is not None:
            meta_json["bestViewPoints"] = [{
                "type": "enclosed",
                "points": [
                    {"type": "point", "value": point.tolist()}
                    for point in self.best_view_point
                ]
            }]

        metadata = replace(metadata)
        metadata.additional_metadata["meta.json"] = meta_json

        return metadata


    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        """
        Transform an incoming image.
        """
        return image


    @classmethod
    def from_json(cls, args: Dict[str, Any]):
        return cls(
            transform=args["transform"],
            preferred_colormap=args.get("preferred_colormap"),
            version=int(args["version"]),
            best_view_point=args.get("best_view_point")
        )


class SiibraSectionIDOffsetTransformer(Transformer):

    def __init__(
            self,
            axis: str,
            section_id_regex: str = r".*_(\d{4}).*",
            offset: float = 0.,
        ):
        from tiamat.metadata.dimensions import META_DIMENSIONS

        assert axis.lower() in META_DIMENSIONS
        self.axis = axis.lower()

        self.section_id_regex = section_id_regex
        self.offset = offset


    def get_section_id(self, fname):
        import re

        match = re.search(self.section_id_regex, fname)

        return int(match.group(1))


    def transform_access(self, accessor: ImageAccessor, metadata: ImageMetadata) -> ImageAccessor:
        return accessor


    def transform_metadata(self, metadata: ImageMetadata) -> ImageMetadata:
        from dataclasses import replace
        from tiamat.metadata.dimensions import META_DIMENSIONS

        axis_index = META_DIMENSIONS.index(self.axis)
        axis_spacing = metadata.spacing[axis_index]  # [um]

        section_id = self.get_section_id(metadata.file_path)
        section_offset = section_id * axis_spacing * 1e3 + self.offset  # [nm]

        metadata = replace(metadata)

        if "meta.json" in metadata.additional_metadata.keys():
            meta_json = metadata.additional_metadata["meta.json"].copy()

            meta_json["transform"][axis_index][-1] = meta_json["transform"][axis_index][-1] + section_offset
            if meta_json.get("bestViewPoints") is not None:
                for box in meta_json["bestViewPoints"]:
                    for b in box["points"]:
                        b["value"][axis_index] = b["value"][axis_index] + section_offset / 1e6

            metadata.additional_metadata["meta.json"] = meta_json

        if "transform.json" in metadata.additional_metadata.keys():
            transform_json = metadata.additional_metadata["transform.json"].copy()
            transform_json[axis_index][-1] = transform_json[axis_index][-1] + section_offset

            metadata.additional_metadata["transform.json"] = transform_json

        return metadata


    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        """
        Transform an incoming image.
        """
        return image


    @classmethod
    def from_json(cls, args: Dict[str, Any]):
        return cls(
            axis=args["axis"],
            section_id_regex=args.get("section_id_regex", r".*_(\d{4}).*"),
            offset=float(args.get("offset", 0)),
        )
