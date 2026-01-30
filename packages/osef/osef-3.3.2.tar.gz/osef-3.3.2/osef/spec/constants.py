"""Constants used throughout project and that can be used by user"""

# Standard imports
from __future__ import annotations
from typing import List, NamedTuple, Optional

# Project imports
from osef.spec import osef_types

# Structure Format definition (see https://docs.python.org/3/library/struct.html#format-strings):
# Meant to be used as: _STRUCT_FORMAT % length

_STRUCT_FORMAT = "<"  # little endian
_STRUCT_FORMAT += "L"  # unsigned long        (field 'T' ie. 'Type')
_STRUCT_FORMAT += "L"  # unsigned long        (field 'L' ie. 'Length')
_STRUCT_FORMAT += "%ds"  # buffer of fixed size (field 'V' ie. 'Value')


class _Tlv(NamedTuple):
    """Type-Length-Value (TLV) definition.

    :param osef_type: Integer value for defining the OSEF type.
    :param length: Length of the data.
    :param value: Actual data.
    """

    osef_type: osef_types.OsefTypes
    length: int
    value: bytes


class _TreeNode(NamedTuple):
    """Tree representation of the TLV data.

    :param osef_type: Type of the data.
    :param children: Optional tree of data's child.
    :param leaf_value: Data's value if no child.
    """

    osef_type: osef_types.OsefTypes
    children: Optional[List[_TreeNode]]
    leaf_value: Optional[bytes]


class ExtraPoseKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the Pose.
    """

    ROTATION = "rotation"
    TRANSLATION = "translation"


class ExtraZoneBindingKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the zone bindings.
    """

    ZONE_INDEX = "zone_idx"
    OBJECT_ID = "object_id"


class ExtraTimestampKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the timestamp.
    """

    TIMESTAMP = "timestamp"
    UNIX_S = "unix_s"
    REMAINING_US = "remaining_us"


class ExtraImuKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the IMU.
    """

    ACCELERATION = "acceleration"
    ANGULAR_VELOCITY = "angular_velocity"


class ExtraBackgroundKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the background.
    """

    DELETED = "background_deleted"
    WIDTH = "width"
    HEIGHT = "height"
    FIRST_AZIMUTH = "first_azimuth"
    AZIMUTH_STEP = "azimuth_step"
    FIRST_INDEX = "firsr_index"
    CELLS_NUMBER = "cells_number"


class ExtraOsefKeys:
    """Keys for specifying some OSEF data/fields, which
    are not defined in the spec.
    """

    _TO_DROP = "__todrop"
    IMAGE_WIDTH = "image_width"
    IMAGE_HEIGHT = "image_height"
    AZIMUTH_BEGIN_DEG = "azimuth_begin_deg"
    AZIMUTH_END_DEG = "azimuth_end_deg"


class ExtraCoordinatesKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the several coordinates data.
    """

    X = "x"
    Y = "y"
    Z = "z"
    X_MIN = "x_min"
    X_MAX = "x_max"
    Y_MIN = "y_min"
    Y_MAX = "y_max"
    AZIMUTH = "azimuth"
    ELEVATION = "elevation"
    DISTANCE = "distance"
    LATITUDE = "lat"
    LONGITUDE = "long"
    HEADING = "heading"
    SPEED = "speed"


class ObjectPropertiesIndexes:
    """Class to define the object properties correspondance
    between index and property.
    """

    ORIENTED = 0
    IS_SEEN = 1
    HAS_VALID_SLAM_POSE = 2
    IS_STATIC = 3
    HAS_A_PRIORI_DIMENSIONS = 4
    IS_CONTROLLED = 5


class GMMContainerFields:
    """Class to define the GMM container field names."""

    MEAN = "mean"
    INVERTED_VARIANCE = "inverted_variance"
    WEIGHT = "weight"
    BACKGROUND_PROBABILITY = "background_probability"
    COUNT = "count"
    PREVIOUS_VALUE = "previous_value"
    CUMULATE_UPDATE = "cumulate_update"
    FURTHEST_BACKGROUND_MEAN = "furthest_background_mean"
    LAST_UPDATE = "last_update"
    GAUSSIAN_NUMBER = "gaussian_number"


class ExtraLidarIntrinsicsKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the lidar intrinsics.
    """

    NUMBER_OF_AZIMUTHS = "number_of_azimuths"
    NUMBER_OF_ELEVATIONS = "number_of_elevations"
    UPPER_BOUND_OF_FIELD_OF_VIEW = "upper_bound_of_field_of_view"
    LOWER_BOUND_OF_FIELD_OF_VIEW = "lower_bound_of_field_of_view"
    LEFT_BOUND_OF_FIELD_OF_VIEW = "left_bound_of_field_of_view"
    RIGHT_BOUND_OF_FIELD_OF_VIEW = "right_bound_of_field_of_view"


class ExtraEstimatedHeightKeys:
    """Class to define extra OSEF keys, not defined in the spec,
    relative to the estimated height.
    """

    HEIGHT = "height"
    STD = "std"
