import os
from typing import List

from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.ml_features_common.entities.feature_definition_type import (
    FeatureDefinitionType,
)
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    FeatureTablesForServing as ProtoFeatureTablesForServing,
)


class FeatureTablesForServing(_FeatureStoreObject):
    DATA_FILE = "feature_tables_for_serving.dat"

    def __init__(
        self,
        online_feature_tables: List[OnlineFeatureTable],
        feature_definition_type: FeatureDefinitionType,
    ):
        self._online_feature_tables = online_feature_tables
        self._feature_definition_type = feature_definition_type

    @property
    def online_feature_tables(self) -> List[OnlineFeatureTable]:
        return self._online_feature_tables

    @property
    def feature_definition_type(self) -> FeatureDefinitionType:
        """
        Returns the feature definition type indicating how features are defined.

        For DECLARATIVE_FEATURES, FeatureTablesForServing is the only source of information for the lookup client.
        For FEATURE_TABLE, the lookup client will depend on both FeatureTablesForServing and the model's FeatureSpec.
        """
        return self._feature_definition_type

    @classmethod
    def from_proto(cls, the_proto: ProtoFeatureTablesForServing):
        online_fts = [
            OnlineFeatureTable.from_proto(online_table)
            for online_table in the_proto.online_tables
        ]

        # Default to FEATURE_TABLE if the feature_definition_type is not set
        feature_definition_type = FeatureDefinitionType.FEATURE_TABLE
        if the_proto.HasField("feature_definition_type"):
            feature_definition_type = FeatureDefinitionType.from_proto_value(
                the_proto.feature_definition_type
            )
        return cls(
            online_feature_tables=online_fts,
            feature_definition_type=feature_definition_type,
        )

    @classmethod
    def load(cls, path: str):
        """
        Loads a binary serialized ProtoFeatureTablesForServing protocol buffer.

        :param path: Root path to the binary file.
        :return: :py:class:`~databricks.ml_features_common.entities.feature_tables_for_serving.FeatureTablesForServing`
        """
        proto = ProtoFeatureTablesForServing()
        # The load path may be None when the model is packaged by Feature Store, but did not use any
        # feature tables (eg just feature functions)
        if not path:
            return cls.from_proto(proto)
        with open(os.path.join(path, cls.DATA_FILE), "rb") as f:
            proto.ParseFromString(f.read())
        return cls.from_proto(proto)
