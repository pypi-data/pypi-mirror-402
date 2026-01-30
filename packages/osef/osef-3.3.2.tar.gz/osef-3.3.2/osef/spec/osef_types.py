"""OSEF private types definition."""

__version__ = "1.27.0"

# pylint:disable=line-too-long

# Standard imports
from enum import Enum, IntEnum

# !!! Warning !!!
# !!! This file has been auto generated, do not attempt to edit it !!!
# Important: all words use little-endian representation, unless specified otherwise


class OsefTypes(IntEnum):
    """OSEF types."""

    AUGMENTED_CLOUD = 1
    NUMBER_OF_POINTS = 2
    SPHERICAL_COORDINATES = 3
    REFLECTIVITIES = 4
    _BACKGROUND_FLAGS = 5
    CARTESIAN_COORDINATES = 6
    _BGR_COLORS = 7
    _OBJECT_DETECTION_FRAME = 8
    _IMAGE_DIMENSION = 9
    NUMBER_OF_OBJECTS = 10
    _CLOUD_FRAME = 11
    TIMESTAMP_MICROSECOND = 12
    _AZIMUTHS_COLUMN = 13
    NUMBER_OF_LAYERS = 14
    _CLOUD_PROCESSING = 15
    _RANGE_AZIMUTH = 16
    _BOUNDING_BOXES_ARRAY = 17
    CLASS_ID_ARRAY = 18
    _CONFIDENCE_ARRAY = 19
    TIMESTAMPED_DATA = 20
    _PERCEPT = 21
    _BGR_IMAGE_FRAME = 23
    POSE = 24
    SCAN_FRAME = 25
    TRACKED_OBJECTS = 26
    BBOX_SIZES = 27
    SPEED_VECTORS = 28
    POSE_ARRAY = 29
    OBJECT_ID = 30
    CARTESIAN_COORDINATES_4F = 31
    SPHERICAL_COORDINATES_4F = 32
    ZONES_DEF = 33
    ZONE = 34
    ZONE_VERTICES = 35
    ZONE_NAME = 36
    _ZONE_UUID = 37
    ZONES_OBJECTS_BINDING = 38
    OBJECT_PROPERTIES = 39
    _IMU_PACKET = 40
    _TIMESTAMP_LIDAR_VELODYNE = 41
    POSE_RELATIVE = 42
    _GRAVITY = 43
    EGO_MOTION = 44
    _PREDICTED_POSITION = 45
    GEOGRAPHIC_POSE = 46
    OBJECT_ID_32_BITS = 47
    ZONES_OBJECTS_BINDING_32_BITS = 48
    _BACKGROUND_BITS = 49
    _GROUND_PLANE_BITS = 50
    _AZIMUTHS = 51
    _ELEVATIONS = 52
    _DISTANCES = 53
    _LIDAR_MODEL = 54
    SLAM_POSE_ARRAY = 55
    ZONE_VERTICAL_LIMITS = 56
    GEOGRAPHIC_POSE_PRECISE = 57
    _ROAD_MARKINGS_BITS = 58
    SMOOTHED_POSE = 59
    _INTERACTIVE_REQUEST = 60
    _INTERACTIVE_RESPONSE = 61
    _INTERACTIVE_REQUEST_ID = 62
    _INTERACTIVE_REQUEST_BACKGROUND_HEADER = 63
    _INTERACTIVE_RESPONSE_BACKGROUND_HEADER = 64
    _INTERACTIVE_REQUEST_BACKGROUND_DATA = 65
    _INTERACTIVE_RESPONSE_BACKGROUND_DATA = 66
    _INTERACTIVE_REQUEST_PINGPONG = 67
    _INTERACTIVE_RESPONSE_PINGPONG = 68
    _HEIGHT_MAP = 69
    _HEIGHT_MAP_POINTS = 70
    DIVERGENCE_INDICATOR = 71
    _CARLA_TAG_ARRAY = 72
    _BACKGROUND_SCENE_PARAMS = 73
    _BACKGROUND_SCENE_PARAMS_GENERAL = 74
    _BACKGROUND_SCENE_PARAMS_ELEVATIONS = 75
    _BACKGROUND_SCENE_FRAGMENT = 76
    _BACKGROUND_SCENE_FRAGMENT_INFO = 77
    _BACKGROUND_SCENE_FRAGMENT_DISTANCES = 78
    GEOGRAPHIC_POSE_ARRAY = 79
    GEOGRAPHIC_SPEED = 80
    GEOGRAPHIC_SPEED_ARRAY = 81
    _INSTANTANEOUS_TRANSLATION_SPEED = 82
    _INSTANTANEOUS_ROTATION_SPEED = 83
    _FILTERED_TRANSLATION_SPEED = 84
    _FILTERED_ROTATION_SPEED = 85
    REFERENCE_MAP_BITS = 86
    _CARTESIAN_COVARIANCE = 87
    _CYLINDRICAL_COVARIANCE = 88
    COORDINATES_REFERENCE_SYSTEM = 89
    START_TIMESTAMP = 90
    END_TIMESTAMP = 91
    TIME_DOMAIN = 92
    TIME_INTERVAL = 93
    CLASSIFICATION_CONFIDENCE = 94
    _CLASS_PROBABILITIES_ARRAY = 95
    _CLASSIFIER_DEF = 96
    _ENABLED_CLASS_IDS_ARRAY = 97
    _REFLECTION_FEATURES_ARRAY = 98
    _REFLECTION_BITS = 99
    _GMM_BACKGROUND = 100
    _GMM_AZIMUTH_BINS = 101
    _GMM_ELEVATION_BINS = 102
    _GMM_TYPE_OPTIMIZED = 103
    _GMM_COLUMN_OFFSETS = 104
    _GMM_BYTE_SIZE_CONTAINER = 105
    _GMM_LEARNING_DURATION = 106
    _GMM_DATA = 107
    _GMM_ELEVATIONS = 108
    _GMM_AZIMUTHS = 109
    _GMM_INDEXING_BY_LINE = 110
    _GMM_CONTAINER_LAYOUT_VERSION = 111
    _OBJECT_MATCHING_PAIRS = 112
    _OBJECT_AGE_ARRAY = 113
    _OBJECT_PEAK_HEIGHT_ARRAY = 114
    _SUPPORT_FRAME = 115
    _OBJECT_PROPERTIES_COLLECTION = 116
    _OBJECT_PROPERTIES_ARRAY = 117
    _LIDAR_ID_ARRAY = 118
    _NB_POINTS_PER_LIDAR_ARRAY = 119
    _ASSOCIATED_CLUSTER_ID = 120
    _NB_POINTS_ASSOCIATED_CLUSTER = 121
    _UNASSOCIATED_SINCE = 122
    _MAX_Z = 123
    _PREDICTED_POSE = 124
    _CLUSTER_PROPERTIES_COLLECTION = 125
    _CLUSTER_PROPERTIES_ARRAY = 126
    _CLUSTER_ID_32_BITS = 127
    _CLUSTER_SIZE = 128
    _LIDAR_INTRINSICS = 129
    PROCESSING_COMPLETION_TIMESTAMP = 130
    ESTIMATED_HEIGHT = 131


class OsefKeys(str, Enum):
    """OSEF type keys."""

    def __repr__(self) -> str:
        """Override repr method to display OsefKeys directly as strings."""
        return f"'{self.value}'"

    AUGMENTED_CLOUD = "augmented_cloud"
    """
    Augmented Cloud
    **Output when**: Augmented Cloud is enabled.
    **Purpose**: An augmented cloud represents a cloud of points. Each point can have attributes, all of which are
    optional, which describe its position, physical property, movement, etc...
    Contains following sub-TLVs:
    - exactly one:     Number of Points               (NUMBER_OF_POINTS)
    - exactly one:     Number of Layers               (NUMBER_OF_LAYERS)
    - none or one:     Spherical Coordinates          (SPHERICAL_COORDINATES) [DEPRECATED USAGE]
    - none or one:     Reflectivities                 (REFLECTIVITIES)
    - none or one:     Background Flags               (BACKGROUND_FLAGS) [DEPRECATED USAGE]
    - none or one:     Cartesian Coordinates          (CARTESIAN_COORDINATES)
    - none or one:     BGR Colors                     (BGR_COLORS)
    - none or one:     Azimuths Column                (AZIMUTHS_COLUMN)
    - none or one:     Cloud Processing               (CLOUD_PROCESSING)
    - none or one:     Percept                        (PERCEPT) [DEPRECATED USAGE]
    - none or one:     Object ID 32 Bits              (OBJECT_ID_32_BITS)
    - none or one:     Cartesian Coordinates 4F       (CARTESIAN_COORDINATES_4F) [DEPRECATED USAGE]
    - none or one:     Background Bits                (BACKGROUND_BITS)
    - none or one:     Ground Plane Bits              (GROUND_PLANE_BITS)
    - none or one:     Azimuths                       (AZIMUTHS)
    - none or one:     Elevations                     (ELEVATIONS)
    - none or one:     Distances                      (DISTANCES)
    - none or one:     Road Markings Bits             (ROAD_MARKINGS_BITS) [DEPRECATED USAGE]
    - none or one:     Carla Tag Array                (CARLA_TAG_ARRAY)
    - none or one:     Reference Map Bits             (REFERENCE_MAP_BITS)
    - none or one:     Coordinates Reference System   (COORDINATES_REFERENCE_SYSTEM)
    - none or one:     Reflection Bits                (REFLECTION_BITS)
    """

    NUMBER_OF_POINTS = "number_of_points"
    """
    Number of Points
    **Output when**: Augmented Cloud is enabled.
    **Format**: Contains 32 bits unsigned int value.
    **Purpose**: Represents the number of points in the point cloud.
    """

    SPHERICAL_COORDINATES = "spherical_coordinates"
    """
    Spherical Coordinates [DEPRECATED USAGE]
    Contains list of spherical single-precision float coordinates, three per point:
    * azimuth : degrees, range [ 0.0 .. 360.0 ]
    * elevation : degrees, range [ -90.0 .. +90.0 ]
    * distance : meters, range [ 0.0 ..  +inf ]
    """

    REFLECTIVITIES = "reflectivities"
    """
    Reflectivities
    **Output when**: Augmented Cloud is enabled.
    **Format**: List of unsigned 8-bits integers.
    **Purpose**: Contains list of reflectivity values.
    Diffuse reflectors report values from 0 to 100 for reflectivities from 0% to 100%.
    Retroreflectors report values from 101 to 255, where 255 represents an ideal reflection.
    """

    _BACKGROUND_FLAGS = "background_flags"
    """
    Background Flags [DEPRECATED USAGE]
    **Instead, use**: "Background bits" (type 49)
    Contains a list of boolean values encoded on an unsigned 8-bits integer:
    * 0 means the point is not part of the background
    * all other values mean the point is part of the background
    The background is defined as the objects which were frequently detected in the past.
    On the contrary the foreground is composed of objects that were not seen before (i.e. they appeared recently and/or
    they are moving).
    """

    CARTESIAN_COORDINATES = "cartesian_coordinates"
    """
    Cartesian Coordinates
    **Output when**: Augmented Cloud is enabled.
    Contains list of Cartesian single-precision float coordinates, three per point:
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    * z : meters, range [ -inf .. +inf ]
    **Coordinate Frame**:
    - Passthrough & Mobile: Relative to LiDAR Coordinate Frame.
    - Static: in Absolute/World Frame, which is:
        - Single-LiDAR: On-Ground LiDAR Coordinate Frame.
        - Multi-LiDARs: Map Coordinate Frame.
    """

    _BGR_COLORS = "bgr_colors"
    """
    BGR Colors
    Contain list of BGR colors, encoded as three consecutive unsigned 8-bits integers:
    * blue  : range [ 0 .. 255 ]
    * green : range [ 0 .. 255 ]
    * red   : range [ 0 .. 255 ]
    """

    _OBJECT_DETECTION_FRAME = "object_detection_frame"
    """
    Object Detection Frame
    Group all classification results relative to an image.
    Contains following sub-TLVs:
    - exactly one:     Number of Objects              (NUMBER_OF_OBJECTS)
    - none or one:     Timestamp Microsecond          (TIMESTAMP_MICROSECOND)
    - exactly one:     Bounding Boxes Array           (BOUNDING_BOXES_ARRAY)
    - exactly one:     Class ID Array                 (CLASS_ID_ARRAY)
    - none or one:     Confidence Array               (CONFIDENCE_ARRAY)
    """

    _IMAGE_DIMENSION = "image_dimension"
    """
    Image Dimension
    Contain following concatenated data:
    * image_width   : in pixel, unsigned 32-bits integer, range [ 0 .. 2^32 [
    * image_height  : in pixel, unsigned 32-bits integer, range [ 0 .. 2^32 [
    """

    NUMBER_OF_OBJECTS = "number_of_objects"
    """
    Number of Objects
    **Output when**: Tracking is enabled.
    **Purpose**: Number of tracked objects.
    **Format**: Unsigned 32-bits integer, range [ 0 .. 2^32 [
    """

    _CLOUD_FRAME = "cloud_frame"
    """
    Cloud Frame
    Contains following sub-TLVs:
    - exactly one:     Augmented Cloud                (AUGMENTED_CLOUD)
    - exactly one:     Range Azimuth                  (RANGE_AZIMUTH)
    - none or one:     Timestamp Lidar Velodyne       (TIMESTAMP_LIDAR_VELODYNE)
    - none or one:     LiDAR Model                    (LIDAR_MODEL)
    - none or one:     LiDAR Intrinsics               (LIDAR_INTRINSICS)
    """

    TIMESTAMP_MICROSECOND = "timestamp_microsecond"
    """
    Timestamp Microsecond
    **Output when**: Always.
    **Purpose**: Describes a unix timestamp with microsecond precision, same as struct timeval of UNIX <sys/time.h>.
    **Format**: Contains concatenation of:
    * UNIX time in seconds,   unsigned 32-bits integer, range [ 0 .. 2^32 [
    * remaining microseconds, unsigned 32-bits integer, range [ 0 .. 1000000 [
    """

    _AZIMUTHS_COLUMN = "azimuths_column"
    """
    Azimuths Column
    Contains list of azimuth values in degrees expressed as single-precision floats.
    This azimuth value is computed before corrections due to:
      * The time between each laser firing
      * The correction when lasers of the same firing sequence are not aligned
    The range is [ 0.0 .. 360.0 [.
    """

    NUMBER_OF_LAYERS = "number_of_layers"
    """
    Number of Layers
    **Output when**: Augmented Cloud is enabled.
    **Format**: Contains 32 bits unsigned int value.
    **Purpose**: Represents the number of layers of the point cloud.
    0 indicates that this cloud does not have a 2D structure.
    """

    _CLOUD_PROCESSING = "cloud_processing"
    """
    Cloud Processing
    Contains a 64 bits bitfield, representing the processing that have been applied.
    If no bit are set this means that no processing have been done on this cloud.
    * Bit 0 : The background points have been removed
    """

    _RANGE_AZIMUTH = "range_azimuth"
    """
    Range Azimuth
    Range of azimuth values for the points contained in a given lidar packet.
    Contains exactly two 32 bits floats. The first one marks the beginning of the range, the second the end.
      The range is [ 0.0 .. 360.0 [.
    """

    _BOUNDING_BOXES_ARRAY = "bounding_boxes_array"
    """
    Bounding Boxes Array
    Contains list of bounding boxes dimensions, four per box:
    * x_min : percentage of the image size, 32-bits floating-point, range [ 0 .. 1 ]
    * y_min : percentage of the image size, 32-bits floating-point, range [ 0 .. 1 ]
    * x_max : percentage of the image size, 32-bits floating-point, range [ 0 .. 1 ]
    * y_max : percentage of the image size, 32-bits floating-point, range [ 0 .. 1 ]
    """

    CLASS_ID_ARRAY = "class_id_array"
    """
    Class ID Array
    **Output when**: Tracking is enabled.
    **Format**: List of signed 32 bits integers, using enum CLASS ID.
    **Purpose**: Contains list of class IDs. For further details, see:
    [Classification](https://docs.outsight.ai/software-integration/shift-perception-api/data-interface/understanding-osef-data/object-tracking-data#classification)
    """

    _CONFIDENCE_ARRAY = "confidence_array"
    """
    Confidence Array
    Contains list of confidences, one per element:
    32-bits floating-point, range [ 0.0 .. 1.0 ]
    """

    TIMESTAMPED_DATA = "timestamped_data"
    """
    Timestamped Data
    **Output when**: Always.
    Contains following sub-TLVs:
    - exactly one:     Timestamp Microsecond          (TIMESTAMP_MICROSECOND)
    - none or one:     Object Detection Frame         (OBJECT_DETECTION_FRAME)
    - none or one:     Cloud Frame                    (CLOUD_FRAME)
    - none or one:     Scan Frame                     (SCAN_FRAME)
    - zero to many:    Time interval                  (TIME_INTERVAL)
    """

    _PERCEPT = "percept"
    """
    Percept [DEPRECATED USAGE]
    Contains list of percept classes represented as unsigned 16-bits integer, using enum PERCEPT ID.
    """

    _BGR_IMAGE_FRAME = "bgr_image_frame"
    """
    BGR Image Frame
    Contains following sub-TLVs:
    - exactly one:     BGR Colors                     (BGR_COLORS)
    - exactly one:     Image Dimension                (IMAGE_DIMENSION)
    """

    POSE = "pose"
    """
    Pose
    **Output when**: Slam is enabled.
    **Purpose**: Pose of the LiDAR.
    **Format**: Concatenation of 12 floats of 32-bits each, in this order:
    - Tx, Ty and Tz, representing the translation vector T to get the position coordinates in meters
    - Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz and Rzz represent the rotation matrix R (given column-wise) defining the
    orientation
    As a consequence, considering a device in a pose defined by T and R, you can compute the coordinates Xabs in the
    absolute referential from the coordinates Xrel in device referential using the vectorial formula:
    ```
    Xabs = R * Xrel + T
    ```
    with:
    ```
        [Rxx Rxy Rxz]
    R = [Ryx Ryy Ryz]
        [Rzx Rzy Rzz]
        [Tx]
    T = [Ty]
        [Tz]
    ```
    **Coordinate Frame**:
    Absolute/World Frame, which is:
    - Ego-Motion: Initial pose of the LiDAR.
    - Relocalization: Map Coordinate Frame.
    """

    SCAN_FRAME = "scan_frame"
    """
    Scan Frame
    **Output when**: Always.
    Contains following sub-TLVs:
    - none or one:     Augmented Cloud                (AUGMENTED_CLOUD)
    - none or one:     Pose                           (POSE)
    - none or one:     Geographic Pose                (GEOGRAPHIC_POSE) [DEPRECATED USAGE]
    - none or one:     Geographic Pose Precise        (GEOGRAPHIC_POSE_PRECISE)
    - none or one:     Geographic Speed               (GEOGRAPHIC_SPEED)
    - none or one:     Ego Motion                     (EGO_MOTION)
    - none or one:     Tracked Objects                (TRACKED_OBJECTS)
    - none or one:     Zones Def                      (ZONES_DEF)
    - none or one:     Zones Objects Binding          (ZONES_OBJECTS_BINDING) [DEPRECATED USAGE]
    - none or one:     Zones Objects Binding 32 Bits  (ZONES_OBJECTS_BINDING_32_BITS)
    - none or one:     Height Map                     (HEIGHT_MAP)
    - none or one:     Classifier Def                 (CLASSIFIER_DEF)
    - exactly one:     Processing Completion Timestamp (PROCESSING_COMPLETION_TIMESTAMP)
    """

    TRACKED_OBJECTS = "tracked_objects"
    """
    Tracked Objects
    **Output when**: Tracking is enabled.
    **Purpose**: Properties of tracked objects, which includes centroid, bbox, speed...
    For further details, see: [Object Tracking
    Data](https://docs.outsight.ai/software-integration/shift-perception-api/data-interface/understanding-osef-data/object-tracking-data).
    Contains following sub-TLVs:
    - exactly one:     Number of Objects              (NUMBER_OF_OBJECTS)
    - exactly one:     Object ID 32 Bits              (OBJECT_ID_32_BITS)
    - exactly one:     Class ID Array                 (CLASS_ID_ARRAY)
    - exactly one:     Bbox Sizes                     (BBOX_SIZES)
    - exactly one:     Speed Vectors                  (SPEED_VECTORS)
    - exactly one:     Pose Array                     (POSE_ARRAY)
    - none or one:     Slam Pose Array                (SLAM_POSE_ARRAY) [DEPRECATED USAGE]
    - exactly one:     Object Properties              (OBJECT_PROPERTIES)
    - none or one:     Geographic Pose Array          (GEOGRAPHIC_POSE_ARRAY)
    - none or one:     Geographic Speed Array         (GEOGRAPHIC_SPEED_ARRAY)
    - none or one:     Classification confidence      (CLASSIFICATION_CONFIDENCE)
    - none or one:     Class probabilities Array      (CLASS_PROBABILITIES_ARRAY)
    - none or one:     Reflection features array      (REFLECTION_FEATURES_ARRAY)
    - none or one:     Object Matching Pairs          (OBJECT_MATCHING_PAIRS)
    - none or one:     Object Age Array               (OBJECT_AGE_ARRAY)
    - none or one:     Object Peak Height Array       (OBJECT_PEAK_HEIGHT_ARRAY)
    - none or one:     Estimated Height               (ESTIMATED_HEIGHT)
    """

    BBOX_SIZES = "bbox_sizes"
    """
    Bbox Sizes
    **Output when**: Tracking is enabled.
    **Purpose**: Define bounding boxes around each tracked object.
    The bounding box is extended/cropped in a way to always touch the ground along the z axis.
    A bounding box is defined by its 3 dimensions, on x, y, z axes, centered on Pose Array.
    **Format**: Array of bounding box sizes, three single-precision floats per object:
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    * z : meters, range [ -inf .. +inf ]
    """

    SPEED_VECTORS = "speed_vectors"
    """
    Speed Vectors
    **Output when**: Tracking is enabled.
    **Purpose**: Speed vectors, one for each tracked object.
    Speed vectors are defined on x, y, z axes, centered on Pose Array.
    **Format**: Array of speed vectors, three single-precision floats per object:
    * x : meters per second, range [ -inf .. +inf ]
    * y : meters per second, range [ -inf .. +inf ]
    * z : meters per second, range [ -inf .. +inf ]
    """

    POSE_ARRAY = "pose_array"
    """
    Pose Array
    **Output when**: Tracking is enabled.
    **Purpose**: Contains the poses defining the bounding box of a tracked object.
    **Format**: 12 floats of 32-bits per object:
    * Tx, Ty and Tz represent the translation vector T to get the position coordinates in meters.
    * Rxx, Rxy, Rxz, Ryx, Ryy, Ryz, Rzx, Rzy and Rzz represent the rotation matrix R defining the orientation.
    As a consequence, considering a device in a pose defined by T and R, you can compute the coordinates Xabs in the
    absolute referential from the coordinates Xrel in device referential using the vectorial formula:
    Xabs = R * Xrel + T
    **Coordinate Frame**:
    Absolute/World Frame, which is:
    - Single-LiDAR configuration: On-Ground LiDAR Coordinate Frame.
    - Multi-LiDARs configuration: Map Coordinate Frame.
    """

    OBJECT_ID = "object_id"
    """
    Object ID [DEPRECATED USAGE]
    **Instead, use**: "Object ID 32 bits" (type 47)
    """

    CARTESIAN_COORDINATES_4F = "cartesian_coordinates_4f"
    """
    Cartesian Coordinates 4F [DEPRECATED USAGE]
    **Instead, use**: "Cartesian Coordinates" (type 6)
    Alternative way to represent coordinates, where a fourth float is added.
    It can be more efficient to construct if an application aligns the points to use SIMD on 128 bits words.
    Contains list of cartesian single-precision float coordinates, four per point:
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    * z : meters, range [ -inf .. +inf ]
    * w : unused, for 128 bits alignment only
    """

    SPHERICAL_COORDINATES_4F = "spherical_coordinates_4f"
    """
    Spherical Coordinates 4F [DEPRECATED USAGE]
    Alternative way to represent coordinates, where a fourth float is added.
    It can be more efficient to construct if an application aligns the points to use SIMD on 128 bits words.
    Contains list of spherical single-precision float coordinates, four per point:
    * azimuth   : degrees, range [ 0.0 .. 360.0 ]
    * elevation : degrees, range [ -90.0 .. +90.0 ]
    * distance  : meters,  range [ 0.0 ..  +inf ]
    * w         : unused, for 128 bits alignment only
    """

    ZONES_DEF = "zones_def"
    """
    Zones Def
    **Output when**: Tracking is enabled, and at least a zone is defined.
    **Purpose**: Definition of the event zones. They represent spatial areas of interest.
    Their order is important, since the index is used to identify a zone in type 48.
    Contains following sub-TLVs:
    - zero to many:    Zone                           (ZONE)
    """

    ZONE = "zone"
    """
    Zone
    **Output when**: Tracking is enabled, and at least a zone is defined.
    **Purpose**: Defines one zone.
    Contains following sub-TLVs:
    - exactly one:     Zone Vertices                  (ZONE_VERTICES)
    - exactly one:     Zone Name                      (ZONE_NAME)
    - none or one:     Zone UUID                      (ZONE_UUID)
    - none or one:     Zone Vertical Limits           (ZONE_VERTICAL_LIMITS)
    """

    ZONE_VERTICES = "zone_vertices"
    """
    Zone Vertices
    **Output when**: Tracking is enabled, and a zone has been defined.
    **Purpose**: Vertices of the polygon defining the zone.
    They are defined on the ground, so the z coordinate is absent.
    **Format**: Contains list of cartesian single-precision float coordinates, two per point.
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    There must be at least 3 vertices, so at least 6 floats.
    """

    ZONE_NAME = "zone_name"
    """
    Zone Name
    **Output when**: Tracking is enabled, and at least a zone is defined.
    **Purpose**: User-defined name to the zone, do not use as unique identifier.
    **Format**: It is UTF-8 encoded and null-terminated.
    """

    _ZONE_UUID = "zone_uuid"
    """
    Zone UUID
    128 bits UUID of the zone in BIG-endian representation.
    UUID 00112233-4455-6677-8899-aabbccddeeff is encoded as the bytes 00 11 22 33 44 55 66 77 88 99 aa bb cc dd ee ff.
    It enables to keep the identity of a zone across renaming or resizing.
    """

    ZONES_OBJECTS_BINDING = "zones_objects_binding"
    """
    Zones Objects Binding [DEPRECATED USAGE]
    **Instead, use**: "Zones Objects Binding 32 bits" (type 48)
    Concatenation of 0 to N couples of:
    * an unsigned 64-bits integer, representing the ID of an object (see type 30)
    * an unsigned 32-bits integer, representing the index of the zone (the n-th type 34 of type 33)
    Each object-zone couple means that the object is considered by the algorithm to be in the zone.
    """

    OBJECT_PROPERTIES = "object_properties"
    """
    Object Properties
    **Output when**: Tracking is enabled.
    **Purpose**: Properties of the object.
    **Format**: One byte per object, each bit of this can represent different properties.
    * 1st bit: is_oriented: 1 if the object has a proper orientation (like a cuboid), 0 otherwise (like a cylinder).
    * 2nd bit: is_seen: 1 if the object has been seen in the last scan, 0 if it was not seen.
    * 3rd bit: has_valid_slam_pose: 1 if the object has a valid slam pose, 0 otherwise. See type 55 (Slam Pose Array)
    for more information.
    * 4th bit: is_static_object: 1 if the object is static (e.g. traffic signs, poles...), 0 otherwise
    * 5th bit: has_a_priori_dimensions: 1 if an a priori estimation of the object dimensions has been given as input, 0
    otherwise
    * 6th bit: is_controlled: 1 if the object has been declared controlled by a system taking Shift Perception data as
    input
    * 7th bit: is_standing_still: 1 if the object, although capable of moving, has not moved for a defined period of
    time, 0 otherwise.
    * 8th bit: reserved for later use
    """

    _IMU_PACKET = "imu_packet"
    """
    IMU Packet
    Contains the following data:
    * Time when the IMU packet was received
    * Byte [0,3]: UNIX time in seconds,   unsigned 32-bits integer, range [ 0 .. 2^32 [
    * Byte [4,7]: remaining microseconds, unsigned 32-bits integer, range [ 0 .. 1000000 [
    * Acceleration vector
    * Byte [8,11] x : meters / second^2, 32 bits float, range [ -inf .. +inf ]
    * Byte [12,15] y : meters / second^2, 32 bits float, range [ -inf .. +inf ]
    * Byte [16,19] z : meters / second^2, 32 bits float, range [ -inf .. +inf ]
    * Angular velocity vector
    * Byte [20,23] x : radians / second, 32 bits float, range [ -inf .. +inf ]
    * Byte [24,27] y : radians / second, 32 bits float, range [ -inf .. +inf ]
    * Byte [28,31] z : radians / second, 32 bits float, range [ -inf .. +inf ]
    """

    _TIMESTAMP_LIDAR_VELODYNE = "timestamp_lidar_velodyne"
    """
    Timestamp Lidar Velodyne
    Describes a timestamp with microsecond precision. This timestamp is in the lidar reference system, and uses the
    Velodyne format. This means that this timestamp is the time spent since the beginning of the hour.
    Contains concatenation of:
    * UNIX time in seconds,   unsigned 32-bits integer, range [ 0 .. 2^32 [
    * remaining microseconds, unsigned 32-bits integer, range [ 0 .. 1000000 [
    """

    POSE_RELATIVE = "pose_relative"
    """
    Pose Relative
    **Output when**: Slam is enabled.
    **Purpose**: This pose represents the movement of the device between two scans.
    So the position of the current scan can be computed from the one of the previous scan using the following vectorial
    formula:
    ```
    Xcurrent = R * Xprevious + T
    ```
    with:
    ```
        [Rxx Rxy Rxz]
    R = [Ryx Ryy Ryz]
        [Rzx Rzy Rzz]
        [Tx]
    T = [Ty]
        [Tz]
    ```
    **Format**: Concatenation of 12 floats of 32-bits each, in this order:
    - Tx, Ty and Tz, representing the translation vector T to get the position coordinates in meters
    - Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz and Rzz, representing the rotation matrix R (given column-wise) defining
    the orientation
    **Coordinate Frame**: relative to the pose of the previous scan.
    """

    _GRAVITY = "gravity"
    """
    Gravity
    Concatenation of 3 floats of 32-bits each [x, y, z], this is the direction of the gravity in the acquisition sensor
    reference frame.
    The vector is either normalised if valid, or [0, 0, 0] if invalid.
    """

    EGO_MOTION = "ego_motion"
    """
    Ego Motion
    **Output when**: SLAM is enabled.
    Contains following sub-TLVs:
    - exactly one:     Pose Relative                  (POSE_RELATIVE)
    - none or one:     Predicted Position             (PREDICTED_POSITION)
    - none or one:     Smoothed Pose                  (SMOOTHED_POSE)
    - none or one:     Divergence Indicator           (DIVERGENCE_INDICATOR)
    - none or one:     Instantaneous Translation Speed (INSTANTANEOUS_TRANSLATION_SPEED)
    - none or one:     Instantaneous Rotation Speed   (INSTANTANEOUS_ROTATION_SPEED)
    - none or one:     Filtered Translation Speed     (FILTERED_TRANSLATION_SPEED)
    - none or one:     Filtered Rotation Speed        (FILTERED_ROTATION_SPEED)
    - none or one:     Cartesian covariance           (CARTESIAN_COVARIANCE)
    - none or one:     Cylindrical covariance         (CYLINDRICAL_COVARIANCE)
    """

    _PREDICTED_POSITION = "predicted_position"
    """
    Predicted Position
    **Output when**: Slam is enabled.
    **Purpose**: Cartesian coordinates of the predicted position in slam.
    The time of prediction is set at startup, and defaults to 1 second.
    **Format**: Contains 3 floats.
    **Coordinate Frame**: relative to the LiDAR Coordinate Frame.
    """

    GEOGRAPHIC_POSE = "geographic_pose"
    """
    Geographic Pose [DEPRECATED USAGE]
    **Deprecated since**: 5.3
    **Instead, use**: "Geographic Pose Precise" (type 57)
    **Purpose**: Represents the geographic pose, output from the relocalization processing, expressed in decimal
    degrees notation (latitude, longitude & heading).
    **Format**: Concatenation of 3 single-precision (32 bits) floats [lat, long, heading].
    * Single-precision floating-point (float32) : latitude in decimal degrees, range [ -90.0 .. 90.0 ]
    * Single-precision floating-point (float32) : longitude in decimal degrees, range [ -180.0 .. 180.0 ]
    * Single-precision floating-point (float32) : heading in decimal degrees, range [ 0.0 .. 360.0 [
    """

    OBJECT_ID_32_BITS = "object_id_32_bits"
    """
    Object ID 32 Bits
    **Output when**: Tracking is enabled.
    * Standard behavior: output as leaf of Tracked Objects.
    * Optional & internal behavior: output also as leaf of Augmented Cloud when object_id is listed in
    cloud_fields_to_stream.
    **Format**: Array of unsigned 32-bits integers. Each element of the array is an Object ID.
    **Purpose**: Give a unique identifier (ID) to each detected object.
    Optionally, this ID can also be used to establish a link between detected objects
    and the defined Zones, or the points from an Augmented Cloud.
    When used as leaf of Tracked Objects:
    - The number of elements of the array is equal to the Number of Objects (type 10).
    - Each ID represents a distinct detected object.
    - The affectation of an ID to an object is arbitrary and permanent,
      it remains the same throughout the tracking phase.
    When used as leaf of Augmented Cloud:
    - The number of elements of the array is equal to the Number of Points (type 2).
    - Each specified ID indicates to which object the point belongs.
    - The special value 0 is used to mean 'no object'.
      For instance, if the object ID of a point is 0,
      it means that this point does not belong to any object.
    The Object ID is also used in Zones Objects Binding 32 Bits (type 48), combined with Zone identifier.
    """

    ZONES_OBJECTS_BINDING_32_BITS = "zones_objects_binding_32_bits"
    """
    Zones Objects Binding 32 Bits
    **Output when**: Tracking is enabled, and at least one zone has been defined.
    **Purpose**: This type is used to know with tracked objects are in which event zones.
    The binary payload is the concatenation of 0 to N couples of:
    * an unsigned 32-bits integer, representing the ID of an object (see 47)
    * an unsigned 32-bits integer, representing the index of the event zone (the n-th type 34 of type 33)
    Each object-zone couple means that the object is considered by the algorithm to be in the zone.
    """

    _BACKGROUND_BITS = "background_bits"
    """
    Background Bits
    Contains a padded list of bits, 1 bit per point of the cloud. If the bit is set, the point is a background point.
    The background is defined as the objects which were frequently detected in the past.
    On the contrary the foreground is composed of objects that were not seen before (i.e. they appeared recently and/or
    they are moving).
    """

    _GROUND_PLANE_BITS = "ground_plane_bits"
    """
    Ground Plane Bits
    Contains a padded list of bits, 1 bit per point of the cloud. If the bit is set, the point belongs to the ground.
    """

    _AZIMUTHS = "azimuths"
    """
    Azimuths
    Contains list of azimuth coordinates.
    The azimuths are in degrees and expressed as single-precision floats. Several values are concatenated so the
    information of n points are given at once.
    The range of each value is [ 0.0 .. 360.0 [. 360.0 [.
    """

    _ELEVATIONS = "elevations"
    """
    Elevations
    Contains list of elevation values in degrees expressed as single-precision floats.
    The range is [ -90.0 .. +90.0 [.
    """

    _DISTANCES = "distances"
    """
    Distances
    Contains list of distance values in meters expressed as single-precision floats.
    The range is [ 0.0 .. +inf [.
    """

    _LIDAR_MODEL = "lidar_model"
    """
    LiDAR Model
    One unsigned 8-bits integer representing a model of LiDAR, using enum LIDAR MODEL ID.
    """

    SLAM_POSE_ARRAY = "slam_pose_array"
    """
    Slam Pose Array [DEPRECATED USAGE]
    **Output when**: Tracking/objects_super_resolution is enabled.
    **Purpose**: Pose of tracked objects. It is similar to type 29 "Pose Array", but it is more accurate since
    it uses a SLAM algorithm and not just a box fitting algorithm.
    The position part follows an arbitrary point on the object, which is not necessarily its center.
    The orientation part is arbitrary for the first predicted pose, then follows the rotation of the object.
    The SLAM algorithm may not run on all tracked objects. When the SLAM does not run on an object,
    let say on object number 5, all floats of the related pose in this array, e.g. the fifth, are equal to zero.
    Moreover, the related element of type 39 "Object properties", e.g. the fifth, has its third bit equal to zero.
    For further details see: [Spatial Data / Static
    Tracking](https://docs.outsight.ai/software-integration/shift-perception-api/data-interface/understanding-osef-data/spatial-data-tracking).
    **Format**: The binary payload is a repetition of the following content, one per tracked object:
    * single-precision floats Tx, Ty and Tz represent the translation vector T to get the position coordinates in
    meters.
    * single-precision floats Rxx, Rxy, Rxz, Ryx, Ryy, Ryz, Rzx, Rzy and Rzz represent the rotation matrix R defining
    the orientation.
    **Coordinate Frame**:
    Absolute/world, which is:
    - Single-LiDAR: On-Ground LiDAR Coordinate Frame.
    - Multi-LiDARs: Map Coordinate Frame.
    """

    ZONE_VERTICAL_LIMITS = "zone_vertical_limits"
    """
    Zone Vertical Limits
    **Output when**: Tracking is enabled, and at least a zone has been defined with Vertical Limits.
    **Format**: The binary value is the concatenation of:
    * one single-precision float, elevation, in meters
    * one single-precision float, height, in meters
    **Purpose**: Optional zone configuration which adds a filtering depending on the vertical position of objects.
    It is part of the definition of the zone.
    Only objects whose altitude is between elevation and elevation + height will be considered in the zone.
    """

    GEOGRAPHIC_POSE_PRECISE = "geographic_pose_precise"
    """
    Geographic Pose Precise
    **Output when**: Relocalization in a reference map and georeferencing are enabled.
    So in processing config: slam.enable set to true, slam.reference_map defined and georeferencing.enable set to true.
    **Purpose**: Represents the geographic pose, output from the relocalization processing, expressed in decimal
    degrees notation (latitude, longitude & heading).
    **Format**: Concatenation of 2 double-precision (64 bits) and a single-precision (32 bits) floats [lat, long,
    heading].
    * Double-precision floating-point (float64) : latitude in decimal degrees, range [ -90.0 .. 90.0 ]
    * Double-precision floating-point (float64) : longitude in decimal degrees, range [ -180.0 .. 180.0 ]
    * Single-precision floating-point (float32) : heading in decimal degrees, range [ 0.0 .. 360.0 [
    """

    _ROAD_MARKINGS_BITS = "road_markings_bits"
    """
    Road Markings Bits [DEPRECATED USAGE]
    Contains a padded (up to a byte) list of bits, 1 bit per point of the cloud. If the bit is set, the point belongs
    to a road marking.
    """

    SMOOTHED_POSE = "smoothed_pose"
    """
    Smoothed Pose
    **Output when**: SLAM is enabled.
    **Purpose**: Smoothed pose of the absolute LiDAR pose will introduce a slight delay.
    **Format**: Concatenation of 12 floats of 32-bits each, see type Pose for more details.
    """

    _INTERACTIVE_REQUEST = "interactive_request"
    """
    Interactive Request
    A Request to a device, where a Timestamp and a Request ID are mandatory.
    """

    _INTERACTIVE_RESPONSE = "interactive_response"
    """
    Interactive Response
    A Response made by a device.
    """

    _INTERACTIVE_REQUEST_ID = "interactive_request_id"
    """
    Interactive Request ID
    An ID to identify to which request is associated the response.
    **Format**: Unsigned 32-bits integer.
    """

    _INTERACTIVE_REQUEST_BACKGROUND_HEADER = "interactive_request_background_header"
    """
    Interactive Request Background Header
    Request background header.
    """

    _INTERACTIVE_RESPONSE_BACKGROUND_HEADER = "interactive_response_background_header"
    """
    Interactive Response Background Header
    Response background header.
    """

    _INTERACTIVE_REQUEST_BACKGROUND_DATA = "interactive_request_background_data"
    """
    Interactive Request Background Data
    Request background data.
    """

    _INTERACTIVE_RESPONSE_BACKGROUND_DATA = "interactive_response_background_data"
    """
    Interactive Response Background Data
    Response background data.
    """

    _INTERACTIVE_REQUEST_PINGPONG = "interactive_request_pingpong"
    """
    Interactive Request PingPong
    Request pingpong.
    **Format**: Binary payload
    """

    _INTERACTIVE_RESPONSE_PINGPONG = "interactive_response_pingpong"
    """
    Interactive Response PingPong
    Response pingpong.
    **Format**: The same binary payload as in the request
    """

    _HEIGHT_MAP = "height_map"
    """
    Height Map
    Height map of a configurable zone of interest.
    **Output when**: generated by height_map app.
    """

    _HEIGHT_MAP_POINTS = "height_map_points"
    """
    Height Map Points
    Points that define the height map and provide the height data.
    The height map is defined as a two-dimensional horizontal grid in the Lidar frame, with given dimensions and number
    of cells.
    The properties of the height map, such as size, number of cells, height offset, etc, are defined by the height_map
    app configuration.
    Every points of the augmented cloud are used to build the height map, with no distinction if it is a point of the
    ground, a motion point or any other flag.
    A point of the cloud is associated with a cell if its projected point on the grid is in the cell.
    The height map provides one height information per cell, the height value depends on the way it is computed by the
    app (a cell with no points will have a nan value).
    The Height Map Points is defined as an array of points, with one point per cell of the height map.
    The x and y coordinates represent the center of the cell in the Lidar frame, the third value is the height of the
    cell computed by the app with the points of the cell.
    **Format**: Contains list of Cartesian single-precision float coordinates, three per point:
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    * z : meters, range [ -inf .. +inf ]
    """

    DIVERGENCE_INDICATOR = "divergence_indicator"
    """
    Divergence Indicator
    **Since**: 5.6.0
    **Output when**: Ego-Motion or Relocalization is enabled.
    **Format**: One float value.
    **Purpose**: Indicates if SLAM seems to have diverged.
    - 0 means SLAM algorithm does not seem to have diverged.
    - 1 means SLAM algorithm seems to have diverged, the associated pose is not trustworthy.
    """

    _CARLA_TAG_ARRAY = "carla_tag_array"
    """
    Carla Tag Array
    **Output when**: generated by Carla Scenario Generator.
    **Format**: List of unsigned 8-bits integers, using enum Carla Tag enum.
    **Purpose**: keeps the tag value, attributed by the Carla Simulator, to each point of the point cloud.
    """

    _BACKGROUND_SCENE_PARAMS = "background_scene_params"
    """
    Background Scene Params [DEPRECATED USAGE]
    **Output when**: Multi-LiDARS Tracking is enabled, in the background stream between edge and fusion.
    **Purpose**: All params to initialize the background scene and be able to interpret Background Stream Fragment
    (type 76) packets
    """

    _BACKGROUND_SCENE_PARAMS_GENERAL = "background_scene_params_general"
    """
    Background Scene Params General [DEPRECATED USAGE]
    **Output when**: Multi-LiDARS Tracking is enabled, in the background stream between edge and fusion.
    **Format**: The following concatenated values:
      * width: 32-bits unsigned integer, number of columns of the background scene array
      * height: 32-bits unsigned integer, number of rows of the background scene array
      * first azimuth: single-precision float, azimuth of the first column of the background scene array, in degrees
      * azimuth step: single-precision float, difference between the azimuths of two consecutive columns of the
    background scene array, in degrees
    """

    _BACKGROUND_SCENE_PARAMS_ELEVATIONS = "background_scene_params_elevations"
    """
    Background Scene Params Elevations [DEPRECATED USAGE]
    **Output when**: generated by Carla Scenario Generator.
    **Format**: List of single-precision floats, each one representing the elevation of a row in the background scene
    array, in degrees
    """

    _BACKGROUND_SCENE_FRAGMENT = "background_scene_fragment"
    """
    Background Scene Fragment [DEPRECATED USAGE]
    **Output when**: Multi-LiDARS Tracking is enabled, in the background stream between edge and fusion.
    **Purpose**: A fragment of the background scene array
    """

    _BACKGROUND_SCENE_FRAGMENT_INFO = "background_scene_fragment_info"
    """
    Background Scene Fragment Info [DEPRECATED USAGE]
    **Output when**: in background stream between edge and fusion, in tracking mode
    **Format**: The following concatenated values:
      * first_index: 32-bites unsigned integer, index of the first cell in background scene array, computed as x *
    height + y, the second cell index is first_index+1, etc., with a rollover on width * height
      * cells_number: 32-bites unsigned integer, number of cells contained in the fragment
    """

    _BACKGROUND_SCENE_FRAGMENT_DISTANCES = "background_scene_fragment_distances"
    """
    Background Scene Fragment Distances [DEPRECATED USAGE]
    **Output when**: Multi-LiDARS Tracking is enabled, in the background stream between edge and fusion.
    **Format**: List of single-precision floats, each one representing the farthest background distance for the
    corresponding cell
    """

    GEOGRAPHIC_POSE_ARRAY = "geographic_pose_array"
    """
    Geographic Pose Array
    **Output when**: Tracking is enabled and georeferencing is activated.
    **Purpose**: Represents the geographic pose, output from the relocalization processing, expressed in decimal
    degrees notation (latitude, longitude & heading) of each tracked object.
    **Format**: Concatenation of 2 double-precision (64 bits) and a single-precision (32 bits) floats [lat, long,
    heading], one for each tracked object.
    * Double-precision floating-point (float64): latitude in decimal degrees, range [ -90.0 .. 90.0 ]
    * Double-precision floating-point (float64): longitude in decimal degrees, range [ -180.0 .. 180.0 ]
    * Single-precision floating-point (float32): heading in decimal degrees, range [ 0.0 .. 360.0 [
    """

    GEOGRAPHIC_SPEED = "geographic_speed"
    """
    Geographic Speed
    **Output when**: Georeferencing is activated.
    **Purpose**: Represents speed of mobile platform (on which LiDAR is mounted) as speed in m/s and geographic heading
    in decimal degrees.
    **Format**: Concatenation of two single-precision (32-bits) floats per object:
    * v: absolute speed in meters per second, range [ 0 .. +inf ]
    * heading: speed vector heading in decimal degrees, range [ 0.0 .. 360.0 [
    """

    GEOGRAPHIC_SPEED_ARRAY = "geographic_speed_array"
    """
    Geographic Speed Array
    **Output when**: Tracking is enabled and georeferencing is activated.
    **Purpose**: Represents speed of tracked objects represented as speed in m/s and geographic heading in decimal
    degrees.
    **Format**: Array of geographic speeds, two single-precision (32 bits) floats per object:
    * v: absolute speed in meters per second, range [ 0 .. +inf ]
    * heading: speed vector heading in decimal degrees, range [ 0.0 .. 360.0 [
    """

    _INSTANTANEOUS_TRANSLATION_SPEED = "instantaneous_translation_speed"
    """
    Instantaneous Translation Speed
    **Output when**: SLAM is enabled and its speed_measurement module is enabled.
    **Purpose**: Represents the instantaneous translation speed of the device (m/s).
    **Format**: Array of 3 single-precision (32 bits) floats, representing the translation speed on each direction.
    """

    _INSTANTANEOUS_ROTATION_SPEED = "instantaneous_rotation_speed"
    """
    Instantaneous Rotation Speed
    **Output when**: SLAM is enabled and its speed_measurement module is enabled.
    **Purpose**: Represents the instantaneous rotation speed of the device (rad/s).
    **Format**: Array of 3 single-precision (32 bits) floats, representing the rotation speed around each axis.
    """

    _FILTERED_TRANSLATION_SPEED = "filtered_translation_speed"
    """
    Filtered Translation Speed
    **Output when**: SLAM is enabled and its speed_measurement module is enabled.
    **Purpose**: Represents the filtered translation speed of the device (m/s). An averaging filter smooths the
    evolution of the speed. A short delay will appear due to the filtering (usually around 1 sec).
    **Format**: Array of 3 single-precision (32 bits) floats, representing the translation speed on each direction.
    """

    _FILTERED_ROTATION_SPEED = "filtered_rotation_speed"
    """
    Filtered Rotation Speed
    **Output when**: SLAM is enabled and its speed_measurement module is enabled.
    **Purpose**: Represents the filtered rotation speed of the device (rad/s). An averaging filter smooths the
    evolution of the speed. A short delay will appear due to the filtering (usually around 1 sec).
    **Format**: Array of 3 single-precision (32 bits) floats, representing the rotation speed around each axis.
    """

    REFERENCE_MAP_BITS = "reference_map_bits"
    """
    Reference Map Bits
    **Output when**: SLAM is enabled and its mapping module is enabled.
    **Purpose**: SLAM identifies potential points of interest within the point cloud, and the mapping module selects
    some of them to build the map. These bits identify the points that are selected to generate the output map.
    **Format**: Padded list of bits, 1 bit per point of the cloud. If the bit is set, the point is part of the
    reference map.
    """

    _CARTESIAN_COVARIANCE = "cartesian_covariance"
    """
    Cartesian covariance
    **Output when**: SLAM is enabled and compute_covariance option is set to true.
    **Purpose**: Represents the cartesian covariances (m²). It estimates the confidence of the algorithm, and how
    trustworthy is the position.
    **Format**: Array of 3 single-precision (32 bits) floats, representing the covariance of x, y and z measurements.
    """

    _CYLINDRICAL_COVARIANCE = "cylindrical_covariance"
    """
    Cylindrical covariance
    **Output when**: SLAM is enabled and compute_covariance option is set to true.
    **Purpose**: Represents the cylindrical covariances (°²). It estimates the confidence of the algorithm, and how
    trustworthy is the orientation.
    **Format**: Array of 3 single-precision (32 bits) floats, representing the covariance of roll (rotation around X
    axis), pitch (rotation around Y axis) and yaw (rotation around Z axis) measurements.
    """

    COORDINATES_REFERENCE_SYSTEM = "coordinates_reference_system"
    """
    Coordinates Reference System
    **Output when**: Augmented Cloud is enabled.
    **Purpose**: The coordinates of the augmented cloud may be expressed in an absolute or relative coordinate system.
    The latter usually being relative to the sensor. This field indicates the reference system in use.
    **Format**: Enumerate COORDINATES REFERENCE SYSTEM
    """

    START_TIMESTAMP = "start_timestamp"
    """
    Start timestamp
    **Purpose**: Start of the time interval. The start timestamp is included in the interval. Unix timestamp with
    **nanosecond** precision.
    **Format**: Contains concatenation of:
    * UNIX time in seconds, unsigned 32-bits integer, range [ 0 .. 2^32 [
    * remaining nanoseconds, unsigned 32-bits integer, range [ 0 .. 1'000'000'000 [
    """

    END_TIMESTAMP = "end_timestamp"
    """
    End timestamp
    **Purpose**: End of the time interval. The end timestamp is not included in the interval. Unix timestamp with
    **nanosecond** precision.
    **Format**: Contains concatenation of:
    * UNIX time in seconds, unsigned 32-bits integer, range [ 0 .. 2^32 [
    * remaining nanoseconds, unsigned 32-bits integer, range [ 0 .. 1'000'000'000 [
    """

    TIME_DOMAIN = "time_domain"
    """
    Time domain
    **Purpose**: Time domain used to generate the timestamps:
       * Reception time: timestamps are generated when the data is received by the system,
       * Sensor time: timestamps are generated by the LiDAR, when the data is acquired
    Warning: Mixing timestamps of different domains is not advised.
    **Format**: Unsigned 32-bits enumerate TIME DOMAIN
    """

    TIME_INTERVAL = "time_interval"
    """
    Time interval
    **Output when**: Scan Maker is time-based.
    **Purpose**: A duration between a start timestamp and an end timestamp. Depending on the time domain Sub-TLV, the
    data is guaranteed to have been either acquired or received during this duration.
    Contains following sub-TLVs:
    - exactly one:     Start timestamp                (START_TIMESTAMP)
    - exactly one:     End timestamp                  (END_TIMESTAMP)
    - exactly one:     Time domain                    (TIME_DOMAIN)
    """

    CLASSIFICATION_CONFIDENCE = "classification_confidence"
    """
    Classification confidence
    **Output when**: Tracking is enabled.
    **Purpose**: Represents a level of confidence, from 0 to 1, regarding the class ID assigned to each tracked object.
    **Format**: A single-precision (32 bits) float for each tracked object, range [ 0 .. 1 ].
    """

    _CLASS_PROBABILITIES_ARRAY = "class_probabilities_array"
    """
    Class probabilities Array
    **Output when**: Tracking and class probabilities are enabled.
    **Purpose**: Normalized distribution over enabled class IDs, expressing, for each tracked object, its
    classification probability.
    **Format**: Array containing a single-precision (32 bits) float per class id for each tracked object with range [ 0
    .. 1 ].
    """

    _CLASSIFIER_DEF = "classifier_def"
    """
    Classifier Def
    **Output when**: Tracking is enabled.
    **Purpose**: Definition of classifier settings
    Contains following sub-TLVs:
    - exactly one:     Enabled class IDs Array        (ENABLED_CLASS_IDS_ARRAY)
    """

    _ENABLED_CLASS_IDS_ARRAY = "enabled_class_ids_array"
    """
    Enabled class IDs Array
    **Output when**: Tracking and class probabilities are enabled.
    **Purpose**: List class IDs that can be assigned to tracked objects.
    **Format**: Array of signed 32 bits integers, using enum CLASS ID. Use TLV length to determine the number of class
    IDs.
    The order is important as it is respected for other fields like type 95.
    """

    _REFLECTION_FEATURES_ARRAY = "reflection_features_array"
    """
    Reflection features array
    **Output when**: Tracking is enabled and option is enabled in configuration
    **Purpose**: Internal only: Reflections filtering - values of features for each object used by the reflection
    filtering. Used for debug and/or retraining.
    **Format**: Array of single precision floats, 6 per objects, concatenated for all objects.
    """

    _REFLECTION_BITS = "reflection_bits"
    """
    Reflection Bits
    Contains a padded list of bits, 1 bit per point of the cloud. If the bit is set, the point is an unwanted
    reflection, generated by ricochet on an overly reflective surface.
    """

    _GMM_BACKGROUND = "gmm_background"
    """
    GMM background
    **Output when**: A GMM (Gaussian Mixture Model) background save is performed. This is typically saved on disk.
    **Purpose**: Internal use only: contains various variables representing the state of the GMM used for background
    separation.
    Contains following sub-TLVs:
    - exactly one:     GMM azimuth bins               (GMM_AZIMUTH_BINS)
    - exactly one:     GMM elevation bins             (GMM_ELEVATION_BINS)
    - none or one:     GMM column offsets             (GMM_COLUMN_OFFSETS)
    - exactly one:     GMM byte size container        (GMM_BYTE_SIZE_CONTAINER)
    - exactly one:     GMM learning duration          (GMM_LEARNING_DURATION)
    - exactly one:     GMM data                       (GMM_DATA)
    - exactly one:     GMM elevations                 (GMM_ELEVATIONS)
    - exactly one:     GMM azimuths                   (GMM_AZIMUTHS)
    - exactly one:     GMM indexing by line           (GMM_INDEXING_BY_LINE)
    - exactly one:     GMM container layout version   (GMM_CONTAINER_LAYOUT_VERSION)
    - none or one:     Pose                           (POSE)
    """

    _GMM_AZIMUTH_BINS = "gmm_azimuth_bins"
    """
    GMM azimuth bins
    **Purpose**: Part of the background GMM state. Represents the number of azimuth bins in the spherical GMM grid, or
    in other words the horizontal size, in bins, of the 2D GMM grid.
    **Format**: An unsigned integer encoded over 32 bits.
    """

    _GMM_ELEVATION_BINS = "gmm_elevation_bins"
    """
    GMM elevation bins
    **Purpose**: Part of the background GMM state. Represents the number of elevation bins in the spherical GMM grid,
    or in other words the vertical size, in bins, of the 2D GMM grid.
    **Format**: An unsigned integer encoded over 32 bits.
    """

    _GMM_TYPE_OPTIMIZED = "gmm_type_optimized"
    """
    GMM type optimized [DEPRECATED USAGE]
    **Purpose**: Part of the background GMM state. A boolean stating whether the considered GMM is optimized or
    unoptimized.
    **Format**: A boolean encoded over 8 bits: 1 if the considered GMM is optimized, else 0
    **Note**: This field is deprecated and replaced by the field "GMM container layout version" (type 111).
    A "GMM container layout version" of 0 replaces a "GMM type optimized" of 0.
    A "GMM container layout version" of 1 replaces a "GMM type optimized" of 1.
    The GMM container layout version can be extended to other values.
    """

    _GMM_COLUMN_OFFSETS = "gmm_column_offsets"
    """
    GMM column offsets
    **Purpose**: Part of the background GMM state. A list of azimuths offsets in degrees, one offset per elevation.
    Those offsets represent the azimuth deviation from the centre of the firing column for a given lidar.
    **Format**: List of floating point numbers, each encoded over 4 bytes. The size of this list is specified by the
    "GMM elevation bins" (type 102).
    """

    _GMM_BYTE_SIZE_CONTAINER = "gmm_byte_size_container"
    """
    GMM byte size container
    **Purpose**: Part of the background GMM state. The size in bytes of a single GMM container.
    **Format**: An unsigned integer encoded over 32 bits.
    """

    _GMM_LEARNING_DURATION = "gmm_learning_duration"
    """
    GMM learning duration
    **Purpose**: Part of the background GMM state. The duration during which the considered GMM algorithm has been
    active.
    **Format**: A signed integer encoded over 64 bits, representing a duration in nanoseconds.
    """

    _GMM_DATA = "gmm_data"
    """
    GMM data
    **Purpose**: Part of the background GMM state. The GMM containers data, where each container contains means,
    covariances, etc ...
    **Format**: There is a total of "GMM elevation bins" (type 102) * "GMM azimuth bins" (type 101) containers, each
    encoded over "GMM byte size gaussian" (type 105) bytes.
    The precise data layout depends on the "GMM type optimized" (type 103), and is considered an implementation detail.
    """

    _GMM_ELEVATIONS = "gmm_elevations"
    """
    GMM elevations
    **Purpose**: List of possible elevation values, part of the background GMM state. Note that the GMM data is a grid,
    where each cell is characterized by an elevation/azimuth angle.
    **Format**: List of floating point numbers, each encoded over 4 bytes. The size of this list is specified by the
    "GMM elevation bins" (type 102).
    """

    _GMM_AZIMUTHS = "gmm_azimuths"
    """
    GMM azimuths
    **Purpose**: List of possible azimuth values, part of the background GMM state. Note that the GMM data is a grid,
    where each cell is characterized by an elevation/azimuth angle.
    **Format**: List of floating point numbers, each encoded over 4 bytes. The size of this list is specified by the
    "GMM azimuth bins" (type 101).
    """

    _GMM_INDEXING_BY_LINE = "gmm_indexing_by_line"
    """
    GMM indexing by line
    **Purpose**: Specifies the order in which the element are written in the "GMM data" (type 107) field, which is a
    grid. It is a part of the background GMM state.
    This field is a boolean: if it is true, it means that we are indexing by line order, if it is false, it means we
    are indexing by column order.
    Let us consider a small array of GMM cells, numbered from 0 to 3, expressed in what would be the "natural" order
    (i.e., elevations are vertical, azimuths are horizontal):
    0 1
    2 3
    * An indexing by line order would mean that the GMM cells are stored in the following order: 0 1 2 3.
      This matches an indexing scheme of: index = elevation_index * number_of_azimuths + azimuth_index
    * An indexing by column order would mean that the GMM cells are stored in the following order: 0 2 1 3.
      This matches an indexing scheme of: index = azimuth_index * number_of_elevations + elevation_index
    **Format**: A boolean encoded over 8 bits: 1 if the GMM data is in line indexing order, else 0 if the GMM data is
    in column indexing order.
    """

    _GMM_CONTAINER_LAYOUT_VERSION = "gmm_container_layout_version"
    """
    GMM container layout version
    **Purpose**: The version of the layout of a single GMM container.
    The field "GMM data" (107) contains one or more GMM containers.
    The number of GMM containers is the multiplication of "GMM azimuth bins" (101) by "GMM elevation bins" (102).
    The size of a single GMM container is provided in "GMM byte size container" (105). It complies with a fixed
    container layout.
    The content of a single GMM container complies to a layout that is versioned.
    Layout for version 0: deprecated.
    Layout for version 1:
      * mean                    : Array of 8 single-precision (32 bits) floats
      * inv_var                 : Array of 8 single-precision (32 bits) floats
      * weight                  : Array of 8 single-precision (32 bits) floats
      * background_probability  : Array of 8 single-precision (32 bits) floats
      * count                   : Array of 8 unsigned 16-bits integers
      * previous_value          : Array of 8 single-precision (32 bits) floats
      * cumulate_update         : Array of 8 unsigned 8-bits integers
      * furthest_background_mean: Single-precision (32 bits) float
      * last_update             : Unsigned 8-bits integer
      * gaussian_number         : Unsigned 8-bits integer
      * padding                 : Unsigned 16-bits integer
    **Format**: Unsigned 8-bits integer.
    """

    _OBJECT_MATCHING_PAIRS = "object_matching_pairs"
    """
    Object Matching Pairs
    **Output when**: Generated by the Superfusion application upon detecting reidentification matching events.
    * Behaviour: Each matching pair persists for `N` OSEF frames,
    where `N` is configurable within the Superfusion application.
    **Purpose**: Provide the reid matching events
    **Format**: Array of ID pairs, formatted as:
    List of arrays:
    - `previous_id`: 32-bit unsigned integer (ID of the object that just disappeared)
    - `new_id`: 32-bit unsigned integer (ID of the object which replaces `previous_id`)
    Each pair denotes a reidentification event where `previous_id` is matched to `new_id`.
    Example:
    ```
    [[47, 32], [58, 24], ...]
    ```
    """

    _OBJECT_AGE_ARRAY = "object_age_array"
    """
    Object Age Array
    **Output when**: Tracking is enabled.
    **Purpose**: Give the age, in number of frames since birth, of the tracked object.
    **Format**: 32-bit unsigned integer.
    """

    _OBJECT_PEAK_HEIGHT_ARRAY = "object_peak_height_array"
    """
    Object Peak Height Array
    **Output when**: Tracking is enabled.
    **Purpose**: Give the peak height of the tracked object if found.
    **Format**: Contains 3 floats single-precision representing the coordinate of the point (x,y,z).
    """

    _SUPPORT_FRAME = "support_frame"
    """
    Support Frame
    **Output when**: Tracking is enabled.
    **Purpose**: Give more information about the pobjs and clusters for:
      - Diagnose complex issues directly on the field
      - Understand scenario behavior and improve algorithms
      - Run live evaluation metrics with more available data
    """

    _OBJECT_PROPERTIES_COLLECTION = "object_properties_collection"
    """
    Object Properties Collection
    **Output when**: Tracking is enabled and a Object is detected in a support_stream zone.
    **Purpose**: Provide a container.
    """

    _OBJECT_PROPERTIES_ARRAY = "object_properties_array"
    """
    Object Properties Array
    **Output when**: Tracking is enabled.
    **Purpose**: Encapsulate the different properties of a single object
    """

    _LIDAR_ID_ARRAY = "lidar_id_array"
    """
    Lidar ID Array
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: List the different Lidar indexes that hit an object.
    **Format**: Array of Unsigned 32-bits integer.
    """

    _NB_POINTS_PER_LIDAR_ARRAY = "nb_points_per_lidar_array"
    """
    Nb Points Per Lidar Array
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: List the number of hits of each lidar listed in the Lidar ID array.
    **Format**: Array of Unsigned 32-bits integer.
    """

    _ASSOCIATED_CLUSTER_ID = "associated_cluster_id"
    """
    Associated Cluster ID
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone and
    a cluster is associated to an object.
    **Purpose**: Give the associated cluster index of an object.
    **Format**: Unsigned 32-bits integer.
    """

    _NB_POINTS_ASSOCIATED_CLUSTER = "nb_points_associated_cluster"
    """
    Nb points Associated Cluster
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: Give the number of instantanteous hits on a object.
    **Format**: Unsigned 32-bits integer.
    """

    _UNASSOCIATED_SINCE = "unassociated_since"
    """
    Unassociated Since
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: Give the number of consecutive scans without observation.
    **Format**: Unsigned 32-bits integer.
    """

    _MAX_Z = "max_z"
    """
    Max Z
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: Give the highest point of the cluster associated to the object.
    **Format**: Single-precision (32 bits) float.
    """

    _PREDICTED_POSE = "predicted_pose"
    """
    Predicted Pose
    **Output when**: Tracking is enabled and Object is detected in a support_stream zone.
    **Purpose**: Give the predicted pose of an object.
    **Format**: Contains list of Cartesian single-precision float coordinates, three per object:
    * x : meters, range [ -inf .. +inf ]
    * y : meters, range [ -inf .. +inf ]
    * z : meters, range [ -inf .. +inf ]
    """

    _CLUSTER_PROPERTIES_COLLECTION = "cluster_properties_collection"
    """
    Cluster Properties Collection
    **Output when**: Tracking is enabled and one Cluster is detected in a support_stream zone.
    **Purpose**: Provide a container.
    """

    _CLUSTER_PROPERTIES_ARRAY = "cluster_properties_array"
    """
    Cluster Properties Array
    **Output when**: Tracking is enabled and Cluster is detected in a support_stream zone.
    **Purpose**: Encapsulate the different properties of a single cluster.
    """

    _CLUSTER_ID_32_BITS = "cluster_id_32_bits"
    """
    Cluster ID 32 bits
    **Output when**: Tracking is enabled and Cluster is detected in a support_stream zone.
    **Purpose**: Give a unique identifier (ID) to each cluster.
    **Format**: Unsigned 32-bits integer.
    """

    _CLUSTER_SIZE = "cluster_size"
    """
    Cluster Size
    **Output when**: Tracking is enabled and Cluster is detected in a support_stream zone.
    **Purpose**: Give the number of points of a cluster.
    **Format**: Unsigned 32-bits integer.
    """

    _LIDAR_INTRINSICS = "lidar_intrinsics"
    """
    LiDAR Intrinsics
    **Purpose**: Give the intrinsics of the lidar.
    **Format**: Set of 32-bits values, ordered as listed below:
    * Number of azimuths: 32-bit unsigned integer
    * Number of elevations: 32-bit unsigned integer
    * Upper-bound of the field of view (in degrees): 32-bit single-precision float
    * Lower-bound of the field of view (in degrees): 32-bit single-precision float
    * Left-bound of the field of view (in degrees): 32-bit single-precision float
    * Right-bound of the field of view (in degrees): 32-bit single-precision float
    """

    PROCESSING_COMPLETION_TIMESTAMP = "processing_completion_timestamp"
    """
    Processing Completion Timestamp
    **Output when**: Always.
    **Purpose**: Indicates when the frame processing was completed.
    Can be used to monitor potential processing latency.
    **Format**: Contains concatenation of:
    * UNIX time in seconds,   unsigned 32-bits integer, range [ 0 .. 2^32 [
    * remaining microseconds, unsigned 32-bits integer, range [ 0 .. 1000000 [
    """

    ESTIMATED_HEIGHT = "estimated_height"
    """
    Estimated Height
    **Output when**: Tracking is enabled.
    **Purpose**: Give the most probable height of an object. Provides also the standard deviation, based on the history
    of height measurements.
    For example, as people may sit, we want this value to be stable in time and always return the real size of a
    person, not the one observed at a specific frame.
    **Format**: Array of height value and its associated standard deviation, two single-precision floats per object:
    * value : meters, range [ 0 .. +inf ]
    * standard deviation : standard deviation, range [ 0 .. +inf ]
    """


class ClassId(IntEnum):
    """Tracked object class ID"""

    UNKNOWN = 0
    PERSON = 1
    LUGGAGE = 2
    TROLLEY = 3
    DEPRECATED = 4
    TRUCK = 5
    CAR = 6
    VAN = 7
    TWO_WHEELER = 8
    MASK = 9
    NO_MASK = 10
    LANDMARK = 11
    TRAILER = 12
    TRACTOR_HEAD = 13
    GATE = 14
    TUGGER_TRAIN = 15
    WHEELCHAIR = 16


class PerceptId(IntEnum):
    """Percept class ID"""

    DEFAULT = 0
    ROAD = 1
    VEGETATION = 2
    GROUND = 3
    SIGN = 4
    BUILDING = 5
    FLAT_GND = 6
    UNKNOWN = 7
    MARKING = 8
    OBJECT = 9
    WALL = 10


class LidarModelId(IntEnum):
    """Lidar model ID"""

    UNKNOWN = 0
    VELODYNE_VLP16 = 1
    VELODYNE_VLP32 = 2
    VELODYNE_VLS128 = 3
    VELODYNE_HDL32 = 4
    ROBOSENSE_BPEARL_V1 = 5
    ROBOSENSE_BPEARL_V2 = 6
    ROBOSENSE_RS32 = 7
    ROBOSENSE_HELIOS = 8
    LIVOX_HORIZON = 9
    LIVOX_AVIA = 10
    LIVOX_MID70 = 11
    OUSTER = 12
    OUTSIGHT_SA01 = 13
    HESAI_PANDARXT32 = 14
    HESAI_PANDARQT64 = 15
    FAKE_LIDAR = 16
    HESAI_PANDARXT32M2X = 17
    ROBOSENSE_M1 = 18
    HESAI_PANDAR128E3X = 19
    LEISHEN_C32A = 20
    LEISHEN_C32C = 21
    LIVOX_HAP_TX = 22
    INNOVIZ_ONE_EAGLE = 23
    INNOVIZ_ONE_FALCON = 24
    HESAI_PANDAR_64 = 25
    HESAI_QT128 = 26
    INNOVUSION_FALCON_PRIME = 27
    LIVOX_MID360 = 28
    ROBOSENSE_BPEARL_V3 = 29
    ROBOSENSE_BPEARL_V4 = 30
    HESAI_PANDAR128E4X = 31
    SEYOND_ROBIN_W = 32
    ROBOSENSE_AIRY = 33
    HESAI_JT128 = 34
    ROBOSENSE_AIRY_PRO = 35


class CarlaTag(IntEnum):
    """Carla Tag"""

    UNLABELED = 0
    BUILDING = 1
    FENCE = 2
    OTHER = 3
    PEDESTRIAN = 4
    POLE = 5
    ROADLINE = 6
    ROAD = 7
    SIDEWALK = 8
    VEGETATION = 9
    VEHICLES = 10
    WALL = 11
    TRAFFICSIGN = 12
    SKY = 13
    GROUND = 14
    BRIDGE = 15
    RAILTRACK = 16
    GUARDRAIL = 17
    TRAFFICLIGHT = 18
    STATIC = 19
    DYNAMIC = 20
    WATER = 21
    TERRAIN = 22


class CoordinatesReferenceSystem(IntEnum):
    """Coordinates Reference System"""

    UNDEFINED = 0
    WORLD = 1
    SENSOR = 2


class TimeDomain(IntEnum):
    """Time domain"""

    LOCAL = 0
    SENSOR = 1
