from typing import Any, Dict, List

from typing_extensions import override

# Currently the following classes are defined in the fe-client folder. It can only be used in the fe-client.
# Meaning this file cannot be imported in the LookupClient.
from databricks.ml_features.entities.data_source import DataSource
from databricks.ml_features.entities.feature import Feature
from databricks.ml_features_common.entities._feature_spec_base import _FeatureSpecBase
from databricks.ml_features_common.entities.column_info import ColumnInfo
from databricks.ml_features_common.entities.feature_spec_constants import (
    DATA_SOURCES_FIELD_NAME,
    DATA_TYPE,
    FEATURE_STORE_CLIENT_VERSION_FIELD_NAME,
    FEATURES_FIELD_NAME,
    INCLUDE,
    INPUT_COLUMNS,
    SERIALIZATION_VERSION,
    SOURCE,
    TRAINING_DATA,
    WORKSPACE_ID_FIELD_NAME,
)
from databricks.ml_features_common.entities.source_data_column_info import (
    SourceDataColumnInfo,
)


def _get_source_data_column_info_dict(
    column_infos: List[ColumnInfo],
) -> List[Dict[str, Dict[str, Any]]]:
    # TODO[ML-60159]: deprecate SOURCE and DATA_TYPE from serialization.
    return [
        {
            column_info.info.name: {
                SOURCE: TRAINING_DATA,
                INCLUDE: column_info.include,
                DATA_TYPE: column_info.data_type,
            }
        }
        for column_info in column_infos
        if column_info.info is not None
    ]


def _get_column_infos_from_dict(spec_dict: Dict[str, Any]) -> List[ColumnInfo]:
    column_infos = []
    if INPUT_COLUMNS in spec_dict:
        for column_dict in spec_dict[INPUT_COLUMNS]:
            for column_name, column_spec in column_dict.items():
                if column_spec.get(SOURCE) == TRAINING_DATA:
                    column_info = ColumnInfo(
                        info=SourceDataColumnInfo(column_name),
                        include=column_spec.get(INCLUDE, True),
                        data_type=column_spec.get(DATA_TYPE),
                    )
                    column_infos.append(column_info)
    return column_infos


class FeatureSpecDeclarative(_FeatureSpecBase):
    """
    FeatureSpecDeclarative contains a group of declarative features.
    """

    def __init__(
        self,
        *,  # Force all arguments to be keyword-only
        features: List[Feature],
        column_infos: List[ColumnInfo],
        workspace_id: int,
        feature_store_client_version: str,
        serialization_version: int,
    ):
        super().__init__(
            serialization_version, workspace_id, feature_store_client_version
        )
        self._features = features
        self._column_infos = column_infos

    @property
    def column_infos(self):
        return self._column_infos

    @property
    def features(self):
        return self._features

    def _get_data_sources(self):
        return [feature.source for feature in self._features]

    @override
    def _to_dict(self):
        """
        Deprecated[ML-59811]: FeatureSpecDeclarative should be converted to
        _SerializableFeatureSpecDeclarative before serialization.
        """
        yaml_dict = {}
        if self._column_infos:
            yaml_dict[INPUT_COLUMNS] = _get_source_data_column_info_dict(
                self._column_infos
            )
        yaml_dict[FEATURES_FIELD_NAME] = {
            feature.full_name: feature._to_yaml_dict() for feature in self._features
        }
        yaml_dict[DATA_SOURCES_FIELD_NAME] = {
            data_source.full_name(): data_source._to_yaml_dict()
            for data_source in self._get_data_sources()
        }
        # For readability, place SERIALIZATION_VERSION_NUMBER last in the dictionary.
        yaml_dict[SERIALIZATION_VERSION] = self.serialization_version
        yaml_dict[WORKSPACE_ID_FIELD_NAME] = self._workspace_id
        yaml_dict[
            FEATURE_STORE_CLIENT_VERSION_FIELD_NAME
        ] = self._feature_store_client_version
        return yaml_dict

    @classmethod
    def _from_dict(cls, spec_dict):
        """Create a FeatureSpecDeclarative from a dictionary."""
        # Parse data sources first
        data_sources = {}
        for data_source_name, data_source_dict in spec_dict[
            DATA_SOURCES_FIELD_NAME
        ].items():
            data_sources[data_source_name] = DataSource._from_yaml_dict(
                data_source_dict
            )

        # Parse features, referencing the data sources by name
        features = []
        for feature_name, feature_dict in spec_dict[FEATURES_FIELD_NAME].items():
            feature = Feature._from_yaml_dict(
                feature_name,
                feature_dict,
                data_sources[feature_dict[Feature.DATA_SOURCE_FIELD_NAME]],
            )
            features.append(feature)

        # Get serialization version
        serialization_version = spec_dict[SERIALIZATION_VERSION]

        # Parse column_infos if present
        column_infos = _get_column_infos_from_dict(spec_dict)

        # Get workspace_id and feature_store_client_version if present
        workspace_id = spec_dict.get(WORKSPACE_ID_FIELD_NAME)
        feature_store_client_version = spec_dict.get(
            FEATURE_STORE_CLIENT_VERSION_FIELD_NAME
        )

        return cls(
            column_infos=column_infos,
            features=features,
            serialization_version=serialization_version,
            workspace_id=workspace_id,
            feature_store_client_version=feature_store_client_version,
        )


class _SerializableFeatureSpecDeclarative(_FeatureSpecBase):
    """
    A representation of a FeatureSpecDeclarative that can be serialized to a YAML file.

    This format stores the minimal set of fields that allow reconstruction of full feature spec;
    this minimal set is the UC declarative feature names and input columns. It can be
    inflated to a full FeatureSpecDeclarative object by feature_spec_utils.inflate_feature_spec_declarative.

    Data source fields are not serialized since they can be resolved from the feature in UC.
    Input columns are specific to training set semantics and cannot be rederived from the features alone.

    Example of a serialized Feature Spec with declarative features:

    input_columns:
    - user_id:
        source: training_data
        include: false
        data_type: int
    - transaction_time:
        source: training_data
        include: false
        data_type: timestamp
    - amount:
        source: training_data
        include: true
        data_type: double
    features:
    - ml.dev.avg_amount_7d
    - ml.dev.avg_amount_30d_7d_slide
    - ml.dev.user_id_count_continuous_1d
    workspace_id: 6051921418418893
    feature_store_client_version: 0.13.0.dev0
    serialization_version: 11
    """

    def __init__(
        self,
        input_columns: List[ColumnInfo],
        feature_names: List[str],
        workspace_id: int,
        feature_store_client_version: str,
        serialization_version: int,
    ):
        super().__init__(
            serialization_version, workspace_id, feature_store_client_version
        )
        self._input_columns = input_columns
        self._feature_names = feature_names

    @classmethod
    def _from_feature_spec_declarative(
        cls, feature_spec_declarative: FeatureSpecDeclarative
    ):
        return cls(
            input_columns=feature_spec_declarative.column_infos,
            feature_names=[
                feature.full_name for feature in feature_spec_declarative.features
            ],
            workspace_id=feature_spec_declarative.workspace_id,
            feature_store_client_version=feature_spec_declarative.feature_store_client_version,
            serialization_version=feature_spec_declarative.serialization_version,
        )

    @override
    def _to_dict(self):
        return {
            INPUT_COLUMNS: _get_source_data_column_info_dict(self._input_columns),
            FEATURES_FIELD_NAME: self._feature_names,
            WORKSPACE_ID_FIELD_NAME: self._workspace_id,
            FEATURE_STORE_CLIENT_VERSION_FIELD_NAME: self._feature_store_client_version,
            SERIALIZATION_VERSION: self.serialization_version,
        }

    @classmethod
    def _from_dict(cls, spec_dict):
        features_from_yaml = spec_dict[FEATURES_FIELD_NAME]
        if not isinstance(features_from_yaml, list):
            # The features field is expected to be a list of feature names.
            raise ValueError(f"Invalid features format: {features_from_yaml}")
        features_names = features_from_yaml
        return cls(
            input_columns=_get_column_infos_from_dict(spec_dict),
            feature_names=features_names,
            workspace_id=spec_dict[WORKSPACE_ID_FIELD_NAME],
            feature_store_client_version=spec_dict[
                FEATURE_STORE_CLIENT_VERSION_FIELD_NAME
            ],
            serialization_version=spec_dict[SERIALIZATION_VERSION],
        )
