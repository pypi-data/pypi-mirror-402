"""
Object Oriented Programming classes and helpers
to convert OSEF type-based data into object-based dataholders.
"""

# Standard imports
from __future__ import annotations
from typing import Optional, NamedTuple

# Third-party imports
import numpy as np
from numpy import typing as npt

# Local imports
from osef.spec import osef_types


# Sign matrix to apply to bounding box dimension matrix to get the vertices
_BBOX_SIGNS = np.array(
    [
        [1, 1, -1, -1, 1, 1, -1, -1],
        [1, -1, -1, 1, 1, -1, -1, 1],
        [-1, -1, -1, -1, 1, 1, 1, 1],
    ]
)
_BBOX_FOOTPRINT_SIGNS = _BBOX_SIGNS[:2, :4]


class Pose(NamedTuple):
    """Class to handle a Pose from OSEF data."""

    translation: npt.NDArray[np.float32]
    rotation: npt.NDArray[np.float32]

    def __eq__(self, other: Pose) -> bool:
        """Equality operator."""
        return (np.array_equal(self.rotation, other.rotation)) and (
            np.array_equal(self.translation, other.translation)
        )

    def __hash__(self) -> int:
        """Hash method."""
        return hash((self.translation, self.rotation))

    @property
    def matrix(self) -> npt.NDArray[np.float32]:
        """Get a Matrix 4x4 with the rotation and translation."""
        pose_matrix = np.identity(4)
        pose_matrix[:3, :3] = self.rotation
        pose_matrix[:3, 3] = self.translation
        return pose_matrix


class GeographicPose(NamedTuple):
    """Class to handle a Geographic Pose from OSEF data."""

    latitude: np.float64
    longitude: np.float64
    heading: np.float32


class GeographicSpeed(NamedTuple):
    """Class to handle a Geographic Speed from OSEF data."""

    speed: np.float32
    heading: np.float32


class EstimatedHeight(NamedTuple):
    """Class to handle an Estimated Height from OSEF data."""

    height: np.float32
    std: np.float32


class ObjectProperties(NamedTuple):
    """Class to handle the object properties."""

    oriented: bool
    is_seen: bool
    has_valid_slam_pose: bool
    is_static: bool
    has_a_priori_dimensions: bool
    is_controlled: bool


class ZoneBindings(NamedTuple):
    """Class to handle the zone bindings."""

    zone_index: int
    object_id: int

    def __repr__(self) -> str:
        """String representation of the Zone binding class."""
        return f"Binding [Zone {self.zone_index} - Object {self.object_id}]"


class ZoneDefinition(NamedTuple):
    """Class to handle zone definition."""

    name: str
    vertices: npt.NDArray[np.float32]
    vertical_limits: Optional[npt.NDArray[np.float32]] = None


class TrackedObjectData(NamedTuple):
    """Helper class for the data of one Tracked Object."""

    object_id: np.uint32
    class_id: np.int32
    speed_vector: npt.NDArray[np.float32]
    bbox_size: npt.NDArray[np.float32]
    translation: npt.NDArray[np.float32]
    rotation: npt.NDArray[np.float32]
    properties: Optional[ObjectProperties] = None
    geographic_pose: Optional[GeographicPose] = None
    geographic_speed: Optional[GeographicSpeed] = None
    classification_confidence: Optional[np.float32] = None
    estimated_height: Optional[EstimatedHeight] = None

    @property
    def class_name(self) -> str:
        """Name of the object class."""
        return osef_types.ClassId(self.class_id).name

    @property
    def bbox_footprint_vertices(self) -> npt.NDArray[np.float32]:
        """
        Compute the coordinates of the projected bounding box on the ground plane.
        The output array has a (4, 2) shape.
        """
        bbox_local_coordinates = self.bbox_size[:2][:, None] * _BBOX_FOOTPRINT_SIGNS / 2
        return (
            np.dot(self.rotation[:2, :2], bbox_local_coordinates)
            + self.translation[:2][:, None]
        ).T

    @property
    def bbox_vertices(self) -> npt.NDArray[np.float32]:
        """
        Compute the coordinates of the bounding box vertices.
        The output array has a (8, 3) shape.
        """
        bbox_local_coordinates = self.bbox_size[:, None] * _BBOX_SIGNS / 2
        return (
            np.dot(self.rotation, bbox_local_coordinates) + self.translation[:, None]
        ).T


class TimeInterval(NamedTuple):
    """Helper class for the data of a Time Interval"""

    start_timestamp: float
    end_timestamp: float
    time_domain: osef_types.TimeDomain
