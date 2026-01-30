"""Module to define OSEF lib typing."""

# Third party imports
import numpy as np

# Project imports
from osef.spec import constants


class BinaryValueFormat:
    """Class to define the binary format for reading values."""

    NB_POINTS = "<L"
    NB_OBJECTS = "<L"
    NB_LAYERS = "<L"
    LIDAR_MODEL = "<B"
    DIVERGENCE = "<f"
    COORDINATES_REFERENCE_SYSTEM = "<B"
    TIME_DOMAIN = "<L"
    GMM_BINS = "<L"
    GMM_OPTIMIZED = "<?"
    GMM_SIZE_CONTAINER = "<L"
    GMM_LEARNING_DURATION = "<q"


class GMMDataFieldFormat:
    """Format of each field of the GMM data container."""

    MEAN = "f"
    INV_VAR = "f"
    WEIGHT = "f"
    BACKGROUND_PROBABILITY = "f"
    COUNT = "H"
    PREVIOUS_VALUE = "f"
    CUMULATE_UPDATE = "B"
    FURTHEST_BACKGROUND_MEAN = "f"
    LAST_UPDATE = "B"
    GAUSSIAN_NUMBER = "B"
    PAD_BYTE = "x"

    @classmethod
    def get_optimized_gmm_container_format(cls, number_of_gaussians: int) -> str:
        """Get the full format of the Struct used to unpack optimized GMM data.

        :param number_of_gaussians: Number of gaussians in the container.
        """
        return (
            "<"
            + number_of_gaussians * cls.MEAN
            + number_of_gaussians * cls.INV_VAR
            + number_of_gaussians * cls.WEIGHT
            + number_of_gaussians * cls.BACKGROUND_PROBABILITY
            + number_of_gaussians * cls.COUNT
            + number_of_gaussians * cls.PREVIOUS_VALUE
            + number_of_gaussians * cls.CUMULATE_UPDATE
            + cls.FURTHEST_BACKGROUND_MEAN
            + cls.LAST_UPDATE
            + cls.GAUSSIAN_NUMBER
            + cls.PAD_BYTE * 2
        )


# Define format for dictionary values.
# First value is the binary format, then the dict keys.
ImageDimensionDictFormat = (
    "<LL",
    [constants.ExtraOsefKeys.IMAGE_WIDTH, constants.ExtraOsefKeys.IMAGE_HEIGHT],
)

RangeAzimuthDictFormat = (
    "<ff",
    [
        constants.ExtraOsefKeys.AZIMUTH_BEGIN_DEG,
        constants.ExtraOsefKeys.AZIMUTH_END_DEG,
    ],
)

TimestampLidarVelodyneDictFormat = (
    "<LL",
    [constants.ExtraTimestampKeys.UNIX_S, constants.ExtraTimestampKeys.REMAINING_US],
)

GravityDictFormat = (
    "<fff",
    [
        constants.ExtraCoordinatesKeys.X,
        constants.ExtraCoordinatesKeys.Y,
        constants.ExtraCoordinatesKeys.Z,
    ],
)

# Define format for arrays.
# (typing, number of values)
PoseArrayFormat = (np.dtype(np.float32), 12)


SphericalCoodinatesDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.AZIMUTH, np.float32),
            (constants.ExtraCoordinatesKeys.ELEVATION, np.float32),
            (constants.ExtraCoordinatesKeys.DISTANCE, np.float32),
        ]
    ),
)

# 4th coordinate is not used.
SphericalCoodinates4fDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.AZIMUTH, np.float32),
            (constants.ExtraCoordinatesKeys.ELEVATION, np.float32),
            (constants.ExtraCoordinatesKeys.DISTANCE, np.float32),
            (constants.ExtraOsefKeys._TO_DROP, np.float32),
        ]
    ),
)

BoundingBoxesDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.X_MIN, np.float32),
            (constants.ExtraCoordinatesKeys.Y_MIN, np.float32),
            (constants.ExtraCoordinatesKeys.X_MAX, np.float32),
            (constants.ExtraCoordinatesKeys.Y_MAX, np.float32),
        ]
    ),
)

# 4th coordinate is not used.
CartesianCoordinates4fDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.X, np.float32),
            (constants.ExtraCoordinatesKeys.Y, np.float32),
            (constants.ExtraCoordinatesKeys.Z, np.float32),
            (constants.ExtraOsefKeys._TO_DROP, np.float32),
        ]
    ),
)

ZoneObjectBindingDType = np.dtype(
    (
        [
            (constants.ExtraZoneBindingKeys.OBJECT_ID, np.uint64),
            (constants.ExtraZoneBindingKeys.ZONE_INDEX, np.uint32),
        ]
    ),
)

ZoneObjectBinding32bDType = np.dtype(
    (
        [
            (constants.ExtraZoneBindingKeys.OBJECT_ID, np.uint32),
            (constants.ExtraZoneBindingKeys.ZONE_INDEX, np.uint32),
        ]
    ),
)

GeographicPoseDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.LATITUDE, np.float32),
            (constants.ExtraCoordinatesKeys.LONGITUDE, np.float32),
            (constants.ExtraCoordinatesKeys.HEADING, np.float32),
        ]
    )
)

GeographicPosePreciseDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.LATITUDE, np.float64),
            (constants.ExtraCoordinatesKeys.LONGITUDE, np.float64),
            (constants.ExtraCoordinatesKeys.HEADING, np.float32),
        ]
    )
)

GeographicSpeedDType = np.dtype(
    (
        [
            (constants.ExtraCoordinatesKeys.SPEED, np.float32),
            (constants.ExtraCoordinatesKeys.HEADING, np.float32),
        ]
    )
)


BackgroundSceneParamsDType = np.dtype(
    (
        [
            (constants.ExtraBackgroundKeys.WIDTH, np.uint32),
            (constants.ExtraBackgroundKeys.HEIGHT, np.uint32),
            (constants.ExtraBackgroundKeys.FIRST_AZIMUTH, np.float32),
            (constants.ExtraBackgroundKeys.AZIMUTH_STEP, np.float32),
        ]
    )
)

BackgroundSceneFragmentInfoDType = np.dtype(
    (
        [
            (constants.ExtraBackgroundKeys.FIRST_INDEX, np.uint32),
            (constants.ExtraBackgroundKeys.CELLS_NUMBER, np.uint32),
        ]
    )
)

LidarIntrinsicsDType = np.dtype(
    (
        [
            (constants.ExtraLidarIntrinsicsKeys.NUMBER_OF_AZIMUTHS, np.uint32),
            (constants.ExtraLidarIntrinsicsKeys.NUMBER_OF_ELEVATIONS, np.uint32),
            (
                constants.ExtraLidarIntrinsicsKeys.UPPER_BOUND_OF_FIELD_OF_VIEW,
                np.float32,
            ),
            (
                constants.ExtraLidarIntrinsicsKeys.LOWER_BOUND_OF_FIELD_OF_VIEW,
                np.float32,
            ),
            (
                constants.ExtraLidarIntrinsicsKeys.LEFT_BOUND_OF_FIELD_OF_VIEW,
                np.float32,
            ),
            (
                constants.ExtraLidarIntrinsicsKeys.RIGHT_BOUND_OF_FIELD_OF_VIEW,
                np.float32,
            ),
        ]
    )
)

EstimatedHeightDType = np.dtype(
    (
        [
            (constants.ExtraEstimatedHeightKeys.HEIGHT, np.float32),
            (constants.ExtraEstimatedHeightKeys.STD, np.float32),
        ]
    )
)
