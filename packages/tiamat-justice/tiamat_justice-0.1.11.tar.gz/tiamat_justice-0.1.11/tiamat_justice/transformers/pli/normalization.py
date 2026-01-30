"""
Affine transformers.
"""
import logging
from typing import Any, Dict, List

import numpy as np

from tiamat.io import ImageAccessor, ImageResult
from tiamat.metadata import ImageMetadata
from tiamat.transformers.protocol import Transformer


logger = logging.getLogger(__name__)


class PLIValueNormalizationTransformer(Transformer):

    def __init__(
            self,
            normalization_value = None,
        ):
        self.normalization_value = normalization_value

    def transform_access(self, accessor: ImageAccessor, metadata: ImageMetadata) -> ImageAccessor:
        return accessor

    def transform_metadata(self, metadata: ImageMetadata) -> ImageMetadata:
        from dataclasses import replace

        if self.normalization_value is None:
            assert "normalization_value" in metadata.additional_metadata.keys()
            norm_value = metadata.additional_metadata["normalization_value"]
        else:
            norm_value = self.normalization_value 

        new_metadata = replace(metadata)

        min_value, max_value = new_metadata.value_range

        min_value = min_value / norm_value if min_value is not None else None
        max_value = max_value / norm_value if max_value is not None else None

        new_metadata.value_range = (min_value, max_value)
        
        return new_metadata

    def transform_image(self, image: np.ndarray, metadata: ImageMetadata, accessor: ImageAccessor) -> np.ndarray:
        
        if self.normalization_value is None:
            assert "normalization_value" in metadata.additional_metadata.keys()
            norm_value = metadata.additional_metadata["normalization_value"]
        else:
            norm_value = self.normalization_value

        image = image / norm_value

        return image

    @classmethod
    def from_json(cls, args: Dict[str, Any]):
        return cls(
            normalization_value=args.get("normalization_value"),
        )
