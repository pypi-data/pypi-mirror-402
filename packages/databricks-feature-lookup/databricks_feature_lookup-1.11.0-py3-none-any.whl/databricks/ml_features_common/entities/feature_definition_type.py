from typing import Any

from databricks.ml_features_common.entities._proto_enum_entity import _ProtoEnumEntity
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    FeatureDefinitionType as ProtoFeatureDefinitionType,
)


class FeatureDefinitionType(_ProtoEnumEntity):
    """Feature definition types supported when serving features."""

    # Should be handled the same way as FEATURE_TABLE
    FEATURE_DEFINITION_TYPE_UNSPECIFIED = ProtoFeatureDefinitionType.Value(
        "FEATURE_DEFINITION_TYPE_UNSPECIFIED"
    )
    # Lookup Client will depend on both serialized FeatureTablesForServing and the model's FeatureSpec.
    FEATURE_TABLE = ProtoFeatureDefinitionType.Value("FEATURE_TABLE")
    # Lookup Client will only depend on the serialized FeatureTablesForServing.
    DECLARATIVE_FEATURES = ProtoFeatureDefinitionType.Value("DECLARATIVE_FEATURES")

    @classmethod
    def _enum_type(cls) -> Any:
        return ProtoFeatureDefinitionType

    @classmethod
    def from_proto_value(cls, proto_value: int) -> int:
        cls.init()
        if proto_value not in cls._ENUM_TO_STRING:
            raise ValueError(
                f"Unsupported FeatureDefinitionType proto value: {proto_value}. "
                f"Valid values: {list(cls._ENUM_TO_STRING.keys())}"
            )
        return proto_value
