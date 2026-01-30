"""Types of the objects contained in the OSEF stream."""

# Standard imports
from typing import Dict, List, NamedTuple, Union

# Third party imports
import numpy as np

# Project imports
from osef.spec import _formats, _packers
from osef.spec.osef_types import OsefKeys, OsefTypes


class InternalNodeInfo(NamedTuple):
    """Internal node info, used for parent node.

    For now, only list or dict are defined.
    :param node_type: Type of the node.
    """

    node_type: Union[Dict, List]


class TypeInfo(NamedTuple):
    """Define the type info on an OSEF type.

    :param name: OSEF key.
    :param node_info: Information on the data type.
    """

    name: str
    node_info: Union[InternalNodeInfo, _packers.PackerBase]


outsight_types = {
    OsefTypes.AUGMENTED_CLOUD: TypeInfo(
        OsefKeys.AUGMENTED_CLOUD, InternalNodeInfo(dict)
    ),
    OsefTypes.NUMBER_OF_POINTS: TypeInfo(
        OsefKeys.NUMBER_OF_POINTS,
        _packers.ValuePacker(_formats.BinaryValueFormat.NB_POINTS),
    ),
    OsefTypes.SPHERICAL_COORDINATES: TypeInfo(
        OsefKeys.SPHERICAL_COORDINATES,
        _packers.StructuredArrayPacker(_formats.SphericalCoodinatesDType),
    ),
    OsefTypes.REFLECTIVITIES: TypeInfo(
        OsefKeys.REFLECTIVITIES,
        _packers.ArrayPacker(np.dtype(np.uint8)),
    ),
    OsefTypes._BACKGROUND_FLAGS: TypeInfo(
        OsefKeys._BACKGROUND_FLAGS,
        _packers.ArrayPacker(np.dtype(np.bool_)),
    ),
    OsefTypes.CARTESIAN_COORDINATES: TypeInfo(
        OsefKeys.CARTESIAN_COORDINATES,
        _packers.ArrayPacker(np.dtype(np.float32), 3),
    ),
    OsefTypes._BGR_COLORS: TypeInfo(
        OsefKeys._BGR_COLORS,
        _packers.BytesPacker(),
    ),
    OsefTypes._OBJECT_DETECTION_FRAME: TypeInfo(
        OsefKeys._OBJECT_DETECTION_FRAME, InternalNodeInfo(dict)
    ),
    OsefTypes._IMAGE_DIMENSION: TypeInfo(
        OsefKeys._IMAGE_DIMENSION,
        _packers.DictPacker(*_formats.ImageDimensionDictFormat),
    ),
    OsefTypes.NUMBER_OF_OBJECTS: TypeInfo(
        OsefKeys.NUMBER_OF_OBJECTS,
        _packers.ValuePacker(_formats.BinaryValueFormat.NB_OBJECTS),
    ),
    OsefTypes._CLOUD_FRAME: TypeInfo(OsefKeys._CLOUD_FRAME, InternalNodeInfo(dict)),
    OsefTypes.TIMESTAMP_MICROSECOND: TypeInfo(
        OsefKeys.TIMESTAMP_MICROSECOND,
        _packers.TimestampMicroPacker(),
    ),
    OsefTypes._AZIMUTHS_COLUMN: TypeInfo(
        OsefKeys._AZIMUTHS_COLUMN,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.NUMBER_OF_LAYERS: TypeInfo(
        OsefKeys.NUMBER_OF_LAYERS,
        _packers.ValuePacker(_formats.BinaryValueFormat.NB_LAYERS),
    ),
    OsefTypes._CLOUD_PROCESSING: TypeInfo(
        OsefKeys._CLOUD_PROCESSING,
        _packers.ProcessingBitfieldPacker(),
    ),
    OsefTypes._RANGE_AZIMUTH: TypeInfo(
        OsefKeys._RANGE_AZIMUTH,
        _packers.DictPacker(*_formats.RangeAzimuthDictFormat),
    ),
    OsefTypes._BOUNDING_BOXES_ARRAY: TypeInfo(
        OsefKeys._BOUNDING_BOXES_ARRAY,
        _packers.StructuredArrayPacker(
            _formats.BoundingBoxesDType,
        ),
    ),
    OsefTypes.CLASS_ID_ARRAY: TypeInfo(
        OsefKeys.CLASS_ID_ARRAY,
        _packers.ArrayPacker(np.dtype(np.int32)),
    ),
    OsefTypes._CONFIDENCE_ARRAY: TypeInfo(
        OsefKeys._CONFIDENCE_ARRAY,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.TIMESTAMPED_DATA: TypeInfo(
        OsefKeys.TIMESTAMPED_DATA, InternalNodeInfo(dict)
    ),
    OsefTypes._PERCEPT: TypeInfo(
        OsefKeys._PERCEPT,
        _packers.ArrayPacker(np.dtype(np.int32)),
    ),
    OsefTypes._BGR_IMAGE_FRAME: TypeInfo(
        OsefKeys._BGR_IMAGE_FRAME, InternalNodeInfo(dict)
    ),
    OsefTypes.POSE: TypeInfo(
        OsefKeys.POSE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.SCAN_FRAME: TypeInfo(OsefKeys.SCAN_FRAME, InternalNodeInfo(dict)),
    OsefTypes.TRACKED_OBJECTS: TypeInfo(
        OsefKeys.TRACKED_OBJECTS, InternalNodeInfo(dict)
    ),
    OsefTypes.BBOX_SIZES: TypeInfo(
        OsefKeys.BBOX_SIZES,
        _packers.ArrayPacker(np.dtype(np.float32), 3),
    ),
    OsefTypes.SPEED_VECTORS: TypeInfo(
        OsefKeys.SPEED_VECTORS,
        _packers.ArrayPacker(np.dtype(np.float32), 3),
    ),
    OsefTypes.POSE_ARRAY: TypeInfo(
        OsefKeys.POSE_ARRAY,
        _packers.ArrayPacker(*_formats.PoseArrayFormat),
    ),
    OsefTypes.OBJECT_ID: TypeInfo(
        OsefKeys.OBJECT_ID,
        _packers.ArrayPacker(np.dtype(np.ulonglong)),
    ),
    OsefTypes.CARTESIAN_COORDINATES_4F: TypeInfo(
        OsefKeys.CARTESIAN_COORDINATES_4F,
        _packers.StructuredArrayPacker(_formats.CartesianCoordinates4fDType),
    ),
    OsefTypes.SPHERICAL_COORDINATES_4F: TypeInfo(
        OsefKeys.SPHERICAL_COORDINATES_4F,
        _packers.StructuredArrayPacker(_formats.SphericalCoodinates4fDType),
    ),
    OsefTypes.ZONES_DEF: TypeInfo(OsefKeys.ZONES_DEF, InternalNodeInfo(list)),
    OsefTypes.ZONE: TypeInfo(OsefKeys.ZONE, InternalNodeInfo(dict)),
    OsefTypes.ZONE_VERTICES: TypeInfo(
        OsefKeys.ZONE_VERTICES,
        _packers.ArrayPacker(np.dtype(np.float32), 2),
    ),
    OsefTypes.ZONE_NAME: TypeInfo(
        OsefKeys.ZONE_NAME,
        _packers.StringPacker(),
    ),
    OsefTypes._ZONE_UUID: TypeInfo(
        OsefKeys._ZONE_UUID,
        _packers.UuidPacker(),
    ),
    OsefTypes.ZONES_OBJECTS_BINDING: TypeInfo(
        OsefKeys.ZONES_OBJECTS_BINDING,
        _packers.StructuredArrayPacker(_formats.ZoneObjectBindingDType),
    ),
    OsefTypes.OBJECT_PROPERTIES: TypeInfo(
        OsefKeys.OBJECT_PROPERTIES,
        _packers.ObjectPropertiesPacker(),
    ),
    OsefTypes._IMU_PACKET: TypeInfo(
        OsefKeys._IMU_PACKET,
        _packers.ImuPacker(),
    ),
    OsefTypes._TIMESTAMP_LIDAR_VELODYNE: TypeInfo(
        OsefKeys._TIMESTAMP_LIDAR_VELODYNE,
        _packers.DictPacker(*_formats.TimestampLidarVelodyneDictFormat),
    ),
    OsefTypes.POSE_RELATIVE: TypeInfo(
        OsefKeys.POSE_RELATIVE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._GRAVITY: TypeInfo(
        OsefKeys._GRAVITY,
        _packers.DictPacker(*_formats.GravityDictFormat),
    ),
    OsefTypes.EGO_MOTION: TypeInfo(OsefKeys.EGO_MOTION, InternalNodeInfo(dict)),
    OsefTypes._PREDICTED_POSITION: TypeInfo(
        OsefKeys._PREDICTED_POSITION,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.GEOGRAPHIC_POSE: TypeInfo(
        OsefKeys.GEOGRAPHIC_POSE,
        _packers.StructuredArrayPacker(_formats.GeographicPoseDType),
    ),
    OsefTypes.OBJECT_ID_32_BITS: TypeInfo(
        OsefKeys.OBJECT_ID_32_BITS,
        _packers.ArrayPacker(np.dtype(np.uint32)),
    ),
    OsefTypes.ZONES_OBJECTS_BINDING_32_BITS: TypeInfo(
        OsefKeys.ZONES_OBJECTS_BINDING_32_BITS,
        _packers.StructuredArrayPacker(_formats.ZoneObjectBinding32bDType),
    ),
    OsefTypes._BACKGROUND_BITS: TypeInfo(
        OsefKeys._BACKGROUND_BITS,
        _packers.BoolBitfieldPacker(),
    ),
    OsefTypes._GROUND_PLANE_BITS: TypeInfo(
        OsefKeys._GROUND_PLANE_BITS,
        _packers.BoolBitfieldPacker(),
    ),
    OsefTypes._AZIMUTHS: TypeInfo(
        OsefKeys._AZIMUTHS,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._ELEVATIONS: TypeInfo(
        OsefKeys._ELEVATIONS,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._DISTANCES: TypeInfo(
        OsefKeys._DISTANCES,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._LIDAR_MODEL: TypeInfo(
        OsefKeys._LIDAR_MODEL,
        _packers.ValuePacker(_formats.BinaryValueFormat.LIDAR_MODEL),
    ),
    OsefTypes.SLAM_POSE_ARRAY: TypeInfo(
        OsefKeys.SLAM_POSE_ARRAY,
        _packers.ArrayPacker(*_formats.PoseArrayFormat),
    ),
    OsefTypes.ZONE_VERTICAL_LIMITS: TypeInfo(
        OsefKeys.ZONE_VERTICAL_LIMITS,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.GEOGRAPHIC_POSE_PRECISE: TypeInfo(
        OsefKeys.GEOGRAPHIC_POSE_PRECISE,
        _packers.StructuredArrayPacker(_formats.GeographicPosePreciseDType),
    ),
    OsefTypes._ROAD_MARKINGS_BITS: TypeInfo(
        OsefKeys._ROAD_MARKINGS_BITS,
        _packers.BoolBitfieldPacker(),
    ),
    OsefTypes.SMOOTHED_POSE: TypeInfo(
        OsefKeys.SMOOTHED_POSE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._HEIGHT_MAP: TypeInfo(OsefKeys._HEIGHT_MAP, InternalNodeInfo(dict)),
    OsefTypes._HEIGHT_MAP_POINTS: TypeInfo(
        OsefKeys._HEIGHT_MAP_POINTS,
        _packers.ArrayPacker(np.dtype(np.float32), 3),
    ),
    OsefTypes.DIVERGENCE_INDICATOR: TypeInfo(
        OsefKeys.DIVERGENCE_INDICATOR,
        _packers.ValuePacker(_formats.BinaryValueFormat.DIVERGENCE),
    ),
    OsefTypes._CARLA_TAG_ARRAY: TypeInfo(
        OsefKeys._CARLA_TAG_ARRAY,
        _packers.ArrayPacker(np.dtype(np.uint32)),
    ),
    OsefTypes._BACKGROUND_SCENE_PARAMS: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_PARAMS, InternalNodeInfo(dict)
    ),
    OsefTypes._BACKGROUND_SCENE_PARAMS_GENERAL: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_PARAMS_GENERAL,
        _packers.StructuredArrayPacker(_formats.BackgroundSceneParamsDType),
    ),
    OsefTypes._BACKGROUND_SCENE_PARAMS_ELEVATIONS: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_PARAMS_ELEVATIONS,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._BACKGROUND_SCENE_FRAGMENT: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_FRAGMENT, InternalNodeInfo(dict)
    ),
    OsefTypes._BACKGROUND_SCENE_FRAGMENT_INFO: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_FRAGMENT_INFO,
        _packers.StructuredArrayPacker(_formats.BackgroundSceneFragmentInfoDType),
    ),
    OsefTypes._BACKGROUND_SCENE_FRAGMENT_DISTANCES: TypeInfo(
        OsefKeys._BACKGROUND_SCENE_FRAGMENT_DISTANCES,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.GEOGRAPHIC_POSE_ARRAY: TypeInfo(
        OsefKeys.GEOGRAPHIC_POSE_ARRAY,
        _packers.StructuredArrayPacker(_formats.GeographicPosePreciseDType),
    ),
    OsefTypes.GEOGRAPHIC_SPEED: TypeInfo(
        OsefKeys.GEOGRAPHIC_SPEED,
        _packers.StructuredArrayPacker(_formats.GeographicSpeedDType),
    ),
    OsefTypes.GEOGRAPHIC_SPEED_ARRAY: TypeInfo(
        OsefKeys.GEOGRAPHIC_SPEED_ARRAY,
        _packers.StructuredArrayPacker(_formats.GeographicSpeedDType),
    ),
    OsefTypes._INSTANTANEOUS_TRANSLATION_SPEED: TypeInfo(
        OsefKeys._INSTANTANEOUS_TRANSLATION_SPEED,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._INSTANTANEOUS_ROTATION_SPEED: TypeInfo(
        OsefKeys._INSTANTANEOUS_ROTATION_SPEED,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._FILTERED_TRANSLATION_SPEED: TypeInfo(
        OsefKeys._FILTERED_TRANSLATION_SPEED,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._FILTERED_ROTATION_SPEED: TypeInfo(
        OsefKeys._FILTERED_ROTATION_SPEED,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.REFERENCE_MAP_BITS: TypeInfo(
        OsefKeys.REFERENCE_MAP_BITS,
        _packers.BoolBitfieldPacker(),
    ),
    OsefTypes._CARTESIAN_COVARIANCE: TypeInfo(
        OsefKeys._CARTESIAN_COVARIANCE, _packers.ArrayPacker(np.dtype(np.float32))
    ),
    OsefTypes._CYLINDRICAL_COVARIANCE: TypeInfo(
        OsefKeys._CYLINDRICAL_COVARIANCE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes.COORDINATES_REFERENCE_SYSTEM: TypeInfo(
        OsefKeys.COORDINATES_REFERENCE_SYSTEM,
        _packers.ValuePacker(_formats.BinaryValueFormat.COORDINATES_REFERENCE_SYSTEM),
    ),
    OsefTypes.START_TIMESTAMP: TypeInfo(
        OsefKeys.START_TIMESTAMP,
        _packers.TimestampNanoPacker(),
    ),
    OsefTypes.END_TIMESTAMP: TypeInfo(
        OsefKeys.END_TIMESTAMP,
        _packers.TimestampNanoPacker(),
    ),
    OsefTypes.TIME_DOMAIN: TypeInfo(
        OsefKeys.TIME_DOMAIN,
        _packers.ValuePacker(_formats.BinaryValueFormat.TIME_DOMAIN),
    ),
    OsefTypes.TIME_INTERVAL: TypeInfo(OsefKeys.TIME_INTERVAL, InternalNodeInfo(dict)),
    OsefTypes.CLASSIFICATION_CONFIDENCE: TypeInfo(
        OsefKeys.CLASSIFICATION_CONFIDENCE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._CLASS_PROBABILITIES_ARRAY: TypeInfo(
        OsefKeys._CLASS_PROBABILITIES_ARRAY,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._CLASSIFIER_DEF: TypeInfo(
        OsefKeys._CLASSIFIER_DEF, InternalNodeInfo(dict)
    ),
    OsefTypes._ENABLED_CLASS_IDS_ARRAY: TypeInfo(
        OsefKeys._ENABLED_CLASS_IDS_ARRAY,
        _packers.ArrayPacker(np.dtype(np.uint32)),
    ),
    OsefTypes._REFLECTION_FEATURES_ARRAY: TypeInfo(
        OsefKeys._REFLECTION_FEATURES_ARRAY,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._REFLECTION_BITS: TypeInfo(
        OsefKeys._REFLECTION_BITS,
        _packers.BoolBitfieldPacker(),
    ),
    OsefTypes._GMM_BACKGROUND: TypeInfo(
        OsefKeys._GMM_BACKGROUND,
        InternalNodeInfo(dict),
    ),
    OsefTypes._GMM_AZIMUTH_BINS: TypeInfo(
        OsefKeys._GMM_AZIMUTH_BINS,
        _packers.ValuePacker(_formats.BinaryValueFormat.GMM_BINS),
    ),
    OsefTypes._GMM_ELEVATION_BINS: TypeInfo(
        OsefKeys._GMM_ELEVATION_BINS,
        _packers.ValuePacker(_formats.BinaryValueFormat.GMM_BINS),
    ),
    OsefTypes._GMM_TYPE_OPTIMIZED: TypeInfo(
        OsefKeys._GMM_TYPE_OPTIMIZED,
        _packers.ValuePacker(_formats.BinaryValueFormat.GMM_OPTIMIZED),
    ),
    OsefTypes._GMM_COLUMN_OFFSETS: TypeInfo(
        OsefKeys._GMM_COLUMN_OFFSETS, _packers.ArrayPacker(np.dtype(np.float32))
    ),
    OsefTypes._GMM_BYTE_SIZE_CONTAINER: TypeInfo(
        OsefKeys._GMM_BYTE_SIZE_CONTAINER,
        _packers.ValuePacker(_formats.BinaryValueFormat.GMM_SIZE_CONTAINER),
    ),
    OsefTypes._GMM_LEARNING_DURATION: TypeInfo(
        OsefKeys._GMM_LEARNING_DURATION,
        _packers.ValuePacker(_formats.BinaryValueFormat.GMM_LEARNING_DURATION),
    ),
    OsefTypes._GMM_DATA: TypeInfo(
        OsefKeys._GMM_DATA, _packers.OptimizedGMMDataPacker()
    ),
    OsefTypes._OBJECT_MATCHING_PAIRS: TypeInfo(
        OsefKeys._OBJECT_MATCHING_PAIRS,
        _packers.ArrayPacker(np.dtype(np.uint32), cols=2),
    ),
    OsefTypes._OBJECT_AGE_ARRAY: TypeInfo(
        OsefKeys._OBJECT_AGE_ARRAY, _packers.ArrayPacker(np.dtype(np.uint32))
    ),
    OsefTypes._OBJECT_PEAK_HEIGHT_ARRAY: TypeInfo(
        OsefKeys._OBJECT_PEAK_HEIGHT_ARRAY,
        _packers.ArrayPacker(np.dtype(np.float32), cols=3),
    ),
    OsefTypes._SUPPORT_FRAME: TypeInfo(OsefKeys._SUPPORT_FRAME, InternalNodeInfo(dict)),
    OsefTypes._OBJECT_PROPERTIES_COLLECTION: TypeInfo(
        OsefKeys._OBJECT_PROPERTIES_COLLECTION, InternalNodeInfo(list)
    ),
    OsefTypes._OBJECT_PROPERTIES_ARRAY: TypeInfo(
        OsefKeys._OBJECT_PROPERTIES_ARRAY, InternalNodeInfo(dict)
    ),
    OsefTypes._LIDAR_ID_ARRAY: TypeInfo(
        OsefKeys._LIDAR_ID_ARRAY,
        _packers.ArrayPacker(np.dtype(np.uint32)),
    ),
    OsefTypes._NB_POINTS_PER_LIDAR_ARRAY: TypeInfo(
        OsefKeys._NB_POINTS_PER_LIDAR_ARRAY,
        _packers.ArrayPacker(np.dtype(np.uint32)),
    ),
    OsefTypes._ASSOCIATED_CLUSTER_ID: TypeInfo(
        OsefKeys._ASSOCIATED_CLUSTER_ID,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._NB_POINTS_ASSOCIATED_CLUSTER: TypeInfo(
        OsefKeys._NB_POINTS_ASSOCIATED_CLUSTER,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._UNASSOCIATED_SINCE: TypeInfo(
        OsefKeys._UNASSOCIATED_SINCE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._MAX_Z: TypeInfo(
        OsefKeys._MAX_Z,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._PREDICTED_POSE: TypeInfo(
        OsefKeys._PREDICTED_POSE,
        _packers.ArrayPacker(np.dtype(np.float32), 3),
    ),
    OsefTypes._CLUSTER_PROPERTIES_COLLECTION: TypeInfo(
        OsefKeys._CLUSTER_PROPERTIES_COLLECTION, InternalNodeInfo(list)
    ),
    OsefTypes._CLUSTER_PROPERTIES_ARRAY: TypeInfo(
        OsefKeys._CLUSTER_PROPERTIES_ARRAY, InternalNodeInfo(dict)
    ),
    OsefTypes._CLUSTER_ID_32_BITS: TypeInfo(
        OsefKeys._CLUSTER_ID_32_BITS,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._CLUSTER_SIZE: TypeInfo(
        OsefKeys._CLUSTER_SIZE,
        _packers.ArrayPacker(np.dtype(np.float32)),
    ),
    OsefTypes._LIDAR_INTRINSICS: TypeInfo(
        OsefKeys._LIDAR_INTRINSICS,
        _packers.StructuredArrayPacker(_formats.LidarIntrinsicsDType),
    ),
    OsefTypes.PROCESSING_COMPLETION_TIMESTAMP: TypeInfo(
        OsefKeys.PROCESSING_COMPLETION_TIMESTAMP,
        _packers.TimestampMicroPacker(),
    ),
    OsefTypes.ESTIMATED_HEIGHT: TypeInfo(
        OsefKeys.ESTIMATED_HEIGHT,
        _packers.StructuredArrayPacker(_formats.EstimatedHeightDType),
    ),
}


def get_type_info_by_id(type_code: int):
    """Get TypeInfo for a given type code.

    :param type_code: Int value in OsefTypes
    :return:
    """
    if type_code in outsight_types:
        return outsight_types[type_code]

    return TypeInfo(f"Unknown type ({type_code})", _packers.PackerBase())


def get_type_info_by_key(type_name: str) -> TypeInfo:
    """Get TypeInfo for a given key/name.

    :param type_name: Int value in OsefTypes
    :return:
    """
    for value in outsight_types.values():
        if value.name == type_name:
            return value
    return TypeInfo(f"Unknown type ({type_name})", _packers.PackerBase())


def get_type_by_key(type_name: str) -> OsefTypes:
    """Get type index for a given key/name.

    :param type_name: Int value in OsefTypes
    :return:
    """
    try:
        return OsefTypes[OsefKeys(type_name).name]
    except KeyError as key_error:
        raise KeyError(f"No type found for type_name={type_name}") from key_error
