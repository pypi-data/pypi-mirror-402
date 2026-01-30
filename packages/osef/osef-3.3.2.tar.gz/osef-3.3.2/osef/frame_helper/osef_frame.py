"""Helpers to easily access data in OSEF frame dict."""

# Standard imports
from typing import Dict, List, Optional, Tuple, Union

# Third-party imports
import numpy as np
from numpy import typing as npt

# Osef imports
from osef.spec import constants
from osef.frame_helper.exceptions import FieldError
from osef.frame_helper.field_classes import (
    EstimatedHeight,
    TrackedObjectData,
    Pose,
    GeographicPose,
    GeographicSpeed,
    ObjectProperties,
    TimeInterval,
    ZoneBindings,
    ZoneDefinition,
    _BBOX_SIGNS,
    _BBOX_FOOTPRINT_SIGNS,
)
from osef.spec.osef_types import ClassId, OsefKeys


class OsefFrame:
    """Base class for the OSEF frame helper."""

    __slots__ = ("_osef_frame",)

    def __init__(self, osef_frame: dict):
        """Constructor."""
        self._osef_frame: Dict = osef_frame

    @property
    def timestamp(self) -> float:
        """Timestamp property."""
        return self._osef_frame[OsefKeys.TIMESTAMPED_DATA][
            OsefKeys.TIMESTAMP_MICROSECOND
        ]

    @property
    def time_interval(self) -> TimeInterval:
        """TimeInterval property."""
        return TimeInterval(
            self._osef_frame[OsefKeys.TIMESTAMPED_DATA][OsefKeys.TIME_INTERVAL][
                OsefKeys.START_TIMESTAMP
            ],
            self._osef_frame[OsefKeys.TIMESTAMPED_DATA][OsefKeys.TIME_INTERVAL][
                OsefKeys.END_TIMESTAMP
            ],
            self._osef_frame[OsefKeys.TIMESTAMPED_DATA][OsefKeys.TIME_INTERVAL][
                OsefKeys.TIME_DOMAIN
            ],
        )

    @property
    def osef_frame_dict(self) -> dict:
        """Property to get the raw dict OSEF frame."""
        return self._osef_frame


class ScanFrame(OsefFrame):
    """Helper class for Scan frame."""

    __slots__ = ("_scan_frame",)

    def __init__(self, osef_frame: dict):
        """Constructor."""
        super().__init__(osef_frame)

        if OsefKeys.SCAN_FRAME not in self._osef_frame.get(OsefKeys.TIMESTAMPED_DATA):
            raise FieldError(OsefKeys.SCAN_FRAME)

        self._scan_frame = osef_frame.get(OsefKeys.TIMESTAMPED_DATA).get(
            OsefKeys.SCAN_FRAME
        )

    @property
    def pose(self) -> Optional[Pose]:
        """Get the Lidar pose."""
        if (pose_values := self._scan_frame.get(OsefKeys.POSE.value)) is None:
            return None
        translation, rotation = _build_pose(pose_values)
        return Pose(translation, rotation)

    @property
    def geographic_pose(self) -> Optional[GeographicPose]:
        """Get the Lidar geographic pose."""
        if (
            geo_pose := self._scan_frame.get(
                OsefKeys.GEOGRAPHIC_POSE_PRECISE.value,
                self._scan_frame.get(OsefKeys.GEOGRAPHIC_POSE.value),
            )
        ) is None:
            return None

        return GeographicPose(
            latitude=geo_pose[0][0],
            longitude=geo_pose[0][1],
            heading=geo_pose[0][2],
        )

    @property
    def geographic_speed(self) -> Optional[GeographicSpeed]:
        """Get the Lidar geographic speed."""
        if (geo_speed := self._scan_frame.get(OsefKeys.GEOGRAPHIC_SPEED.value)) is None:
            return None

        return GeographicSpeed(
            speed=geo_speed[0][0],
            heading=geo_speed[0][1],
        )

    def __getitem__(self, key: str):
        """Standard method to get an element from ScanFrame with [] operator."""
        return self._scan_frame[key]


class AugmentedCloud(ScanFrame):
    """Helper class for augmented cloud."""

    __slots__ = ("_augmented_cloud",)

    def __init__(self, osef_frame: dict):
        """Constructor."""
        super().__init__(osef_frame)

        if OsefKeys.AUGMENTED_CLOUD not in self._scan_frame:
            raise FieldError(OsefKeys.AUGMENTED_CLOUD)

        self._augmented_cloud = self._scan_frame.get(OsefKeys.AUGMENTED_CLOUD)

    def __getitem__(self, key: str):
        """Standard method to get an element from AugmentedCloud with [] operator."""
        return self._augmented_cloud[key]

    @property
    def number_of_points(self) -> int:
        """Get number of points in the point cloud."""
        return self._augmented_cloud[OsefKeys.NUMBER_OF_POINTS]

    @property
    def number_of_layers(self) -> int:
        """Get number of layers in the point cloud."""
        return self._augmented_cloud[OsefKeys.NUMBER_OF_LAYERS]

    @property
    def cartesian_coordinates(self) -> Optional[npt.NDArray[np.float32]]:
        """Cartesian coordinates of the point cloud"""
        cartesian_coordinates = self._augmented_cloud.get(
            OsefKeys.CARTESIAN_COORDINATES
        )
        return cartesian_coordinates.T if cartesian_coordinates is not None else None

    @property
    def reflectivities(self) -> Optional[npt.NDArray[np.uint8]]:
        """Reflectivities of the point cloud"""
        return self._augmented_cloud.get(OsefKeys.REFLECTIVITIES)

    @property
    def object_ids(self) -> Optional[npt.NDArray[np.uint32]]:
        """Get the object IDs corresponding to every points of the point cloud."""
        return self._augmented_cloud.get(OsefKeys.OBJECT_ID_32_BITS)

    @property
    def _road_markings_bits(self) -> Optional[npt.NDArray[np.bool_]]:
        """Contains a padded list of bits, one bit per point of the cloud.
        If the bit is set, the point is part of road markings."""
        return self._augmented_cloud.get(OsefKeys._ROAD_MARKINGS_BITS)

    @property
    def _ground_plane_bits(self) -> Optional[npt.NDArray[np.bool_]]:
        """Contains a padded list of bits, 1 bit per point of the cloud.
        If the bit is set, the point is part of the ground plane."""
        return self._augmented_cloud.get(OsefKeys._GROUND_PLANE_BITS)

    @property
    def _background_bits(self) -> Optional[npt.NDArray[np.bool_]]:
        """Contains a padded list of bits, one bit per point of the cloud.
        If the bit is set, the point is a background point."""
        return self._augmented_cloud.get(OsefKeys._BACKGROUND_BITS)

    @property
    def reference_map_bits(self) -> Optional[npt.NDArray[np.bool_]]:
        """Contains a padded list of bits, one bit per point of the cloud.
        If the bit is set, the point is part of the reference map."""
        return self._augmented_cloud.get(OsefKeys.REFERENCE_MAP_BITS)


class EgoMotion(ScanFrame):
    """Helper class for Egomotion."""

    __slots__ = ("_ego_motion",)

    def __init__(self, osef_frame: dict):
        """Constructor."""
        super().__init__(osef_frame)

        if OsefKeys.EGO_MOTION not in self._scan_frame:
            raise FieldError(OsefKeys.EGO_MOTION)

        self._ego_motion = self._scan_frame[OsefKeys.EGO_MOTION]

    def __getitem__(self, key: str):
        """Standard method to get an element from EgoMotion with [] operator."""
        return self._ego_motion[key]

    @property
    def pose_relative(self) -> Pose:
        """Get the relative pose."""
        translation, rotation = _build_pose(self._ego_motion[OsefKeys.POSE_RELATIVE])
        return Pose(translation, rotation)

    @property
    def smoothed_pose(self) -> Optional[Pose]:
        """Get the smoothed pose."""
        if (
            smoothed_pose_values := self._ego_motion.get(OsefKeys.SMOOTHED_POSE.value)
        ) is None:
            return None
        translation, rotation = _build_pose(smoothed_pose_values)
        return Pose(translation, rotation)

    @property
    def divergence_indicator(self) -> Optional[float]:
        """Get the SLAM divergence indicator."""
        return self._ego_motion.get(OsefKeys.DIVERGENCE_INDICATOR)


class TrackedObjects(ScanFrame):  # pylint: disable=too-many-public-methods
    """Helper class for Tracked objects."""

    __slots__ = ("_tracked_objects",)

    def __init__(self, osef_frame: dict):
        """Constructor."""
        super().__init__(osef_frame)

        if OsefKeys.TRACKED_OBJECTS not in self._scan_frame:
            raise FieldError(OsefKeys.TRACKED_OBJECTS)

        self._tracked_objects = self._scan_frame.get(OsefKeys.TRACKED_OBJECTS)

    def __getitem__(self, key: str):
        """Standard method to get an element from TrackedObjects with [] operator."""
        return self._tracked_objects[key]

    @property
    def number_of_objects(self) -> int:
        """Get the number of tracked objects."""
        return self._tracked_objects[OsefKeys.NUMBER_OF_OBJECTS]

    @property
    def object_ids(self) -> npt.NDArray[np.uint32]:
        """Get numpy array of object IDs."""
        # Handle the 32 bits objects.
        return self._tracked_objects.get(
            OsefKeys.OBJECT_ID_32_BITS,
            self._tracked_objects.get(OsefKeys.OBJECT_ID),
        )

    @property
    def class_ids(self) -> npt.NDArray[np.int32]:
        """Get numpy array of class IDs"""
        return self._tracked_objects.get(OsefKeys.CLASS_ID_ARRAY)

    @property
    def class_names(self) -> List[str]:
        """Get the list of class names."""
        return [ClassId(class_id).name for class_id in self.class_ids]

    @property
    def speed_vectors(self) -> npt.NDArray[np.float32]:
        """Get numpy array of object speeds."""
        return self._tracked_objects.get(OsefKeys.SPEED_VECTORS)

    # TODO. Make this kind of properties lazy.
    @property
    def speed_norms(self) -> npt.NDArray[np.float32]:
        """Get the array of speed norms of each tracked object.

        The 3 components of the speed vector are used to compute the speed norm.
        """
        return np.linalg.norm(self.speed_vectors, axis=1)

    @property
    def poses(self) -> List[Pose]:
        """Get object poses."""
        pose_array_values = self._tracked_objects.get(OsefKeys.POSE_ARRAY)
        translations, rotations = _build_pose_array(pose_array_values)
        return [
            Pose(translation, rotation)
            for translation, rotation in zip(translations, rotations)
        ]

    @property
    def position_vectors(self) -> npt.NDArray[np.float32]:
        """Get numpy array of object positions."""
        pose_array_values = self._tracked_objects.get(OsefKeys.POSE_ARRAY)
        return pose_array_values[:, :3]

    @property
    def rotation_matrices(self) -> npt.NDArray[np.float32]:
        """
        Get array of rotation matrices for each tracked object
        The output array has a shape (N, 3, 3) for N tracked objects.
        """
        pose_array_values = self._tracked_objects.get(OsefKeys.POSE_ARRAY)
        return _build_rotations(pose_array_values)

    @property
    def estimated_height(self) -> Optional[List[EstimatedHeight]]:
        """Get numpy structured array of estimated heights with standard deviations."""
        if OsefKeys.ESTIMATED_HEIGHT in self._tracked_objects:
            return [
                EstimatedHeight(estimated_height_array[0], estimated_height_array[1])
                for estimated_height_array in self._tracked_objects.get(
                    OsefKeys.ESTIMATED_HEIGHT
                )
            ]
        return None

    @property
    def slam_poses(self) -> Optional[List[Pose]]:
        """Get object poses from SLAM."""
        if (
            slam_pose_values := self._tracked_objects.get(
                OsefKeys.SLAM_POSE_ARRAY.value
            )
        ) is None:
            return None
        translations, rotations = _build_pose_array(slam_pose_values)
        return [
            Pose(translation, rotation)
            for translation, rotation in zip(translations, rotations)
        ]

    @property
    def geographic_poses(self) -> Optional[List[GeographicPose]]:
        """Get object geographic poses."""
        if OsefKeys.GEOGRAPHIC_POSE_ARRAY in self._tracked_objects:
            return [
                GeographicPose(
                    latitude=geo_pose[0],
                    longitude=geo_pose[1],
                    heading=geo_pose[2],
                )
                for geo_pose in self._tracked_objects.get(
                    OsefKeys.GEOGRAPHIC_POSE_ARRAY
                )
            ]
        return None

    @property
    def geographic_speeds(self) -> Optional[List[GeographicSpeed]]:
        """Get object geographic speeds."""
        if OsefKeys.GEOGRAPHIC_SPEED_ARRAY in self._tracked_objects:
            return [
                GeographicSpeed(
                    speed=geo_speed[0],
                    heading=geo_speed[1],
                )
                for geo_speed in self._tracked_objects.get(
                    OsefKeys.GEOGRAPHIC_SPEED_ARRAY
                )
            ]
        return None

    @property
    def bbox_sizes(self) -> npt.NDArray[np.float32]:
        """Get bounding boxe dimension arrays.

        Each dimension is defined as an array of 3 values, one for each axis.
        """
        return self._tracked_objects.get(OsefKeys.BBOX_SIZES)

    @property
    def object_properties(self) -> List[ObjectProperties]:
        """Get the object properties."""
        property_values = self._tracked_objects.get(OsefKeys.OBJECT_PROPERTIES)
        return [
            ObjectProperties(
                oriented,
                is_seen,
                has_valid_slam_pose,
                is_static,
                has_a_priori_dimensions,
                is_controlled,
            )
            for (
                oriented,
                is_seen,
                has_valid_slam_pose,
                is_static,
                has_a_priori_dimensions,
                is_controlled,
            ) in zip(
                property_values[:, constants.ObjectPropertiesIndexes.ORIENTED],
                property_values[:, constants.ObjectPropertiesIndexes.IS_SEEN],
                property_values[
                    :, constants.ObjectPropertiesIndexes.HAS_VALID_SLAM_POSE
                ],
                property_values[:, constants.ObjectPropertiesIndexes.IS_STATIC],
                property_values[
                    :, constants.ObjectPropertiesIndexes.HAS_A_PRIORI_DIMENSIONS
                ],
                property_values[:, constants.ObjectPropertiesIndexes.IS_CONTROLLED],
            )
        ]

    @property
    def classification_confidence(self) -> Optional[npt.NDArray[np.float32]]:
        """Get the classification confidence."""
        return self._tracked_objects.get(OsefKeys.CLASSIFICATION_CONFIDENCE)

    @property
    def bbox_footprint_vertices(self) -> npt.NDArray[np.float32]:
        """Get the coordinates of the projected bounding boxes.

        The output array has a shape of (N, 4, 2) with 4 2D-vertices for each object.
        Note that all bounding boxes will be considered as a cuboid.
        """
        num_of_vertices = 4
        bbox_local_coordinates = np.repeat(
            self.bbox_sizes[:, :2] / 2, num_of_vertices, axis=1
        ).reshape((self.number_of_objects, 2, num_of_vertices))

        bbox_local_coordinates *= _BBOX_FOOTPRINT_SIGNS

        pose_array_values = self._tracked_objects.get(OsefKeys.POSE_ARRAY)
        translations, rotations = _build_pose_array(pose_array_values)
        bbox_coordinates = (
            np.matmul(rotations[:, :2, :2], bbox_local_coordinates)
            + translations[:, :2][:, :, None]
        )

        return np.transpose(bbox_coordinates, axes=(0, 2, 1))

    @property
    def bbox_vertices(self) -> npt.NDArray[np.float32]:
        """Get the coordinates of the 3D bounding boxes.

        The output array has a shape of (N, 8, 3) with 8 3D-vertices for each object.
        Note that all bounding boxes will be considered as a cuboid.
        """
        num_of_vertices = 8
        bbox_local_coordinates = np.repeat(
            self.bbox_sizes / 2, num_of_vertices, axis=1
        ).reshape((self.number_of_objects, 3, num_of_vertices))

        bbox_local_coordinates *= _BBOX_SIGNS

        pose_array_values = self._tracked_objects.get(OsefKeys.POSE_ARRAY)
        translations, rotations = _build_pose_array(pose_array_values)
        bbox_coordinates = (
            np.matmul(rotations, bbox_local_coordinates) + translations[:, :, None]
        )

        return np.transpose(bbox_coordinates, axes=(0, 2, 1))

    @property
    def object_matching_pairs(self) -> Optional[npt.NDArray[np.uint32]]:
        """Get numpy array of object matching pairs.

        Each pair represents a re-identification event where:
        - Column 0 (`from_id`): The ID of the object that is re-identified.
        - Column 1 (`to_id`): The ID of the object it is matched to.

        Format:
        - 2D numpy array of shape (N, 2), where N is the number of matching pairs.
        - Returns `None` if no matching pairs are available.

        Example:
        [[20200, 19475], [12345, 67890], ...]
        """
        return self._tracked_objects.get(
            OsefKeys._OBJECT_MATCHING_PAIRS,
        )

    @property
    def object_ages(self) -> Optional[npt.NDArray[np.uint32]]:
        """Get the array of object ages defined as the number of frames objects have been seen."""
        return self._tracked_objects.get(OsefKeys._OBJECT_AGE_ARRAY)

    @property
    def object_peak_heights(self) -> Optional[npt.NDArray[np.float32]]:
        """Get the array of coordinates of the object peak heights.

        This corresponds to the coordinate of the heighest point of the object cluster,
        which can be different than the center of the object.
        """
        return self._tracked_objects.get(OsefKeys._OBJECT_PEAK_HEIGHT_ARRAY)

    def extract_object_data(
        self,
        condition: Optional[npt.NDArray[np.bool_]] = None,
        with_properties: bool = False,
    ) -> List[TrackedObjectData]:
        """
        Parse type-based tracked objects into object-based dataholders.

        :param condition: Array of booleans of the same size as the number of objects.
            If False, the object will not be kept in the output list.
        :param with_properties: if True, the field corresponding to the object properties
            will be added to the TrackedObjectData objects.
        :return: List of tracked object data
        """

        def _filter_field(
            object_field: Union[List, np.ndarray], condition: npt.NDArray[np.bool_]
        ):
            """Filter a tracked objects field whether it is an array or a list."""
            if isinstance(object_field, np.ndarray):
                return object_field[condition]
            return [value for value, flag in zip(object_field, condition) if flag]

        if condition is not None and condition.shape[0] != self.number_of_objects:
            raise ValueError(
                "'condition' must have the same length as the number of objects"
                + f" ({condition.shape[0]} != {self.number_of_objects})"
            )

        object_fields = [
            self.object_ids,
            self.class_ids,
            self.speed_vectors,
            self.bbox_sizes,
            *_build_pose_array(self._tracked_objects.get(OsefKeys.POSE_ARRAY)),
        ]

        # Optional fields will be replaced by arrays of None if not required
        object_fields += (
            [self.object_properties]
            if with_properties
            else [np.full(self.number_of_objects, None)]
        )
        object_fields += (
            [self.geographic_poses, self.geographic_speeds]
            if (
                OsefKeys.GEOGRAPHIC_POSE_ARRAY in self._tracked_objects
                and OsefKeys.GEOGRAPHIC_SPEED_ARRAY in self._tracked_objects
            )
            else [np.full(self.number_of_objects, None)] * 2
        )
        object_fields += (
            [self.classification_confidence]
            if OsefKeys.CLASSIFICATION_CONFIDENCE in self._tracked_objects
            else [np.full(self.number_of_objects, None)]
        )
        object_fields += (
            [self.estimated_height]
            if OsefKeys.ESTIMATED_HEIGHT in self._tracked_objects
            else [np.full(self.number_of_objects, None)]
        )

        return [
            TrackedObjectData(
                object_id,
                class_id,
                speed_vector,
                bbox,
                translation,
                rotation,
                properties,
                geographic_pose,
                geographic_speed,
                classification_confidence,
                estimated_height,
            )
            for (
                object_id,
                class_id,
                speed_vector,
                bbox,
                translation,
                rotation,
                properties,
                geographic_pose,
                geographic_speed,
                classification_confidence,
                estimated_height,
            ) in zip(
                *object_fields
                if condition is None
                else (_filter_field(field, condition) for field in object_fields)
            )
        ]

    def extract_object_cloud(
        self, object_id: int, return_reflectivities: bool = False
    ) -> Union[
        npt.NDArray[np.float32], Tuple[npt.NDArray[np.float32], npt.NDArray[np.uint8]]
    ]:
        """
        Extract the point cloud, and optionally the reflectivity, of a given tracked object
        from the augmented cloud data of the frame.

        :param object_id: ID of the object to extract the cloud data
        :param return_reflectivities: If True, reflectivity values of the object filtered cloud will be returned
        :return: (3, N) array containing the points corresponding to the object
        :return: Optional, array containing the corresponding reflectivity values
        """
        aug_cloud = AugmentedCloud(self._osef_frame)
        field_check_list = [
            OsefKeys.OBJECT_ID_32_BITS,
            OsefKeys.CARTESIAN_COORDINATES,
        ]
        if return_reflectivities:
            field_check_list.append(OsefKeys.REFLECTIVITIES)

        for field_name in field_check_list:
            if field_name not in aug_cloud._augmented_cloud:
                raise FieldError(field_name)

        mask = aug_cloud.object_ids == object_id

        if return_reflectivities:
            return (
                aug_cloud.cartesian_coordinates[:, mask],
                aug_cloud.reflectivities[mask],
            )
        return aug_cloud.cartesian_coordinates[:, mask]


class Zones(ScanFrame):
    """Helper class to easily access data in zone data."""

    __slots__ = "_zones_def", "_zones_binding"

    def __init__(self, osef_frame: dict):
        """Constructor."""
        super().__init__(osef_frame)

        if OsefKeys.ZONES_DEF not in self._scan_frame:
            raise FieldError(OsefKeys.ZONES_DEF)

        if (
            OsefKeys.ZONES_OBJECTS_BINDING_32_BITS not in self._scan_frame
            and OsefKeys.ZONES_OBJECTS_BINDING not in self._scan_frame
        ):
            raise FieldError(OsefKeys.ZONES_OBJECTS_BINDING_32_BITS)

    @property
    def bindings(self) -> List[ZoneBindings]:
        """List of zone-object bindings"""
        zone_bindings = self._scan_frame.get(
            OsefKeys.ZONES_OBJECTS_BINDING_32_BITS,
            self._scan_frame.get(OsefKeys.ZONES_OBJECTS_BINDING),
        )
        return [
            ZoneBindings(
                zone_index=binding[constants.ExtraZoneBindingKeys.ZONE_INDEX],
                object_id=binding[constants.ExtraZoneBindingKeys.OBJECT_ID],
            )
            for binding in zone_bindings
        ]

    @property
    def definitions(self) -> List[ZoneDefinition]:
        """Get the definition of each zone"""
        zones_def = self._scan_frame.get(OsefKeys.ZONES_DEF)
        return [
            ZoneDefinition(
                name=zone.get(OsefKeys.ZONE).get(OsefKeys.ZONE_NAME),
                vertices=zone.get(OsefKeys.ZONE).get(OsefKeys.ZONE_VERTICES),
                vertical_limits=zone.get(OsefKeys.ZONE).get(
                    OsefKeys.ZONE_VERTICAL_LIMITS
                ),
            )
            for zone in zones_def
        ]


def _build_pose(
    pose_values: npt.NDArray[np.float32],
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Build tranlsation and rotation of a pose from its array of values.

    :param pose_values: raw pose values defined as Tx Ty Tz Vxx Vyx Vzx Vxy Vyy Vzy Vxz Vyz Vzz
    :return: position vector
    :return: rotation matrix
    """
    return pose_values[:3], np.transpose(np.reshape(pose_values[3:], (3, 3)))


def _build_rotations(
    pose_array: npt.NDArray[np.float32],
) -> npt.NDArray[np.float32]:
    """Build rotations of an array of poses from the raw values.

    :param pose_values: array of raw pose values of shape (N, 12)
    :return: array of rotation matrices of shape (N, 3, 3)
    """
    return np.transpose(
        np.reshape(pose_array[:, 3:], (len(pose_array), 3, 3)), axes=(0, 2, 1)
    )


def _build_pose_array(
    pose_array: npt.NDArray[np.float32],
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Build tranlsation and rotation of an array of poses from the raw values.

    :param pose_values: array of raw pose values of shape (N, 12)
    :return: array of position vectors of shape (N, 3)
    :return: array of rotation matrices of shape (N, 3, 3)
    """
    translations = pose_array[:, :3]
    rotations = _build_rotations(pose_array)
    return translations, rotations
