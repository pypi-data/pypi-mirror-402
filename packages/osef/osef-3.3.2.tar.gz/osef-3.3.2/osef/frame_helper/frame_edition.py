"""Module to edit the data of an OSEF frame."""

# Standard imports
from typing import Dict, Optional, Union

# Third-party imports
import numpy as np
from numpy import typing as npt

# Local imports
from osef._logger import osef_logger
from osef.spec import constants
from osef.frame_helper.exceptions import FieldError, ObjectIdError
from osef.spec.osef_types import OsefKeys

# Constants
SHAPE_2D = 2
SHAPE_3D = 3


def set_timestamp(frame_dict: Dict, timestamp: float) -> None:
    """Set the timestamp of an OSEF frame.

    :param frame_dict: OSEF frame dictionary to edit.
    :param timestamp: timestamp value to set (in seconds)
    """
    if not isinstance(timestamp, float):
        raise ValueError("Invalid type for setting timestamp")

    frame_dict[OsefKeys.TIMESTAMPED_DATA][OsefKeys.TIMESTAMP_MICROSECOND] = timestamp


def _get_scan_frame_dict(frame_dict: dict) -> Optional[Dict]:
    """Get the scan frame sub-dictionary of an OSEF frame.

    :param frame_dict: OSEF frame dictionary to get.
    :return: tracked objects sub-dictionary, None if the field is absent.
    """
    return frame_dict.get(OsefKeys.TIMESTAMPED_DATA, {}).get(OsefKeys.SCAN_FRAME)


def _get_aug_cloud_dict(frame_dict: dict) -> Optional[Dict]:
    """Get the AugmentedCloud sub-dictionary of an OSEF frame.

    :param frame_dict: OSEF frame dictionary.
    :return: augmented cloud sub-dictionary, None if the field is absent.
    """
    return (
        frame_dict.get(OsefKeys.TIMESTAMPED_DATA, {})
        .get(OsefKeys.SCAN_FRAME, {})
        .get(OsefKeys.AUGMENTED_CLOUD)
    )


def set_augmented_cloud_field(
    frame_dict: Dict, field_key: str, value: Union[int, np.ndarray]
) -> None:
    """
    Set the value of a field of the augmented cloud.

    This function will overwrite the previous value if the field already exists,
    else it will create the field.
    Warning:
    - Number of points cannot be set manually because it must reflect the content
    of the other augmented cloud fields.
    - Cartesian coordinates field must be an array with a (N, 3) shape

    :param frame_dict: OSEF frame dictionary to edit.
    :param field_key: Key of the field to set in the augmented cloud.
    :param value: value of the field to set.
    """
    if (aug_cloud_dict := _get_aug_cloud_dict(frame_dict)) is None:
        raise FieldError(OsefKeys.AUGMENTED_CLOUD.value)

    if field_key == OsefKeys.NUMBER_OF_POINTS:
        raise ValueError(f"Field {OsefKeys.NUMBER_OF_POINTS} cannot be set manually.")

    if isinstance(value, np.ndarray):
        expected_length = aug_cloud_dict[OsefKeys.NUMBER_OF_POINTS]
        if value.shape[0] != expected_length:
            raise ValueError(
                "'value' must have the same length as the number of points"
                + f" ({value.shape[0]} != {expected_length}"
            )
        if len(value.shape) == SHAPE_2D and value.shape[1] != SHAPE_3D:
            raise ValueError(
                f"Field {field_key} has not a valid shape."
                + f" ({value.shape} != {expected_length, SHAPE_3D})"
            )

    aug_cloud_dict[field_key] = value


def filter_cloud(frame_dict: Dict, condition: npt.NDArray[np.bool_]) -> None:
    """
    Filter the augmented cloud by keeping points on condition.

    This will filter all the fields contained in the augmented cloud and update the
    number of points automatically.

    :param frame_dict: OSEF frame dictionary to edit.
    :param condition: Array of boolean flags, if True the cooresponding point will be kept.
    """
    if (aug_cloud_dict := _get_aug_cloud_dict(frame_dict)) is None:
        raise FieldError(OsefKeys.AUGMENTED_CLOUD.value)

    expected_length = aug_cloud_dict[OsefKeys.NUMBER_OF_POINTS]
    if len(condition.shape) != 1 or condition.shape[0] != expected_length:
        raise ValueError(
            f"`condition` has not the right shape ({condition.shape} != ({expected_length},))"
        )

    aug_cloud_dict[OsefKeys.NUMBER_OF_POINTS] = np.count_nonzero(condition)
    for field_key, field_data in aug_cloud_dict.items():
        if isinstance(field_data, np.ndarray):
            # In the raw frame dict, the 'cartesian_coordinates' field has a (N, 3)
            # that can be filtered the same way
            set_augmented_cloud_field(frame_dict, field_key, field_data[condition])


def _get_tracked_objects_dict(frame_dict: dict) -> Dict:
    """Get the AugmentedCloud sub-dictionary of an OSEF frame.

    :param frame_dict: OSEF frame dictionary to get.
    :return: tracked objects sub-dictionary.
    :raises FieldError: if tracked_objects field is not present in the frame
    """
    try:
        return frame_dict.get(OsefKeys.TIMESTAMPED_DATA, {}).get(
            OsefKeys.SCAN_FRAME, {}
        )[OsefKeys.TRACKED_OBJECTS]
    except KeyError as exc:
        raise FieldError(OsefKeys.TRACKED_OBJECTS) from exc


def set_tracked_objects_field(
    frame_dict: Dict, field_key: str, value: np.ndarray
) -> None:
    """Set the value of a field of the tracked objects.

    Warning: the 'number_of_objects' field cannot be set manually, it must correspond
    to the length of the other fields.

    :param frame_dict: OSEF frame dictionary to edit.
    :param field_key: Key of the field to set in the tracked objects.
    :param value: value of the field to set.
    """
    tracked_object_dict = _get_tracked_objects_dict(frame_dict)

    if field_key == OsefKeys.NUMBER_OF_OBJECTS:
        raise ValueError(f"Field {OsefKeys.NUMBER_OF_OBJECTS} cannot be set manually.")

    expected_length = tracked_object_dict[OsefKeys.NUMBER_OF_OBJECTS]
    if value.shape[0] != expected_length:
        raise ValueError(
            "'value' must have the same length as the number of objects"
            + f" ({value.shape[0]} != {expected_length})"
        )

    tracked_object_dict[field_key] = value


def remove_object(frame_dict: Dict, object_id: int) -> None:
    """Remove a tracked object from an OSEF frame.

    :param frame_dict: OSEF frame dictionary to edit.
    :param object_id: ID of the object to remove from the tracked object list.
    """
    tracked_object_dict = _get_tracked_objects_dict(frame_dict)

    # Check if object is in the frame, and get its index.
    # Warning: If the frame contains duplicated object IDs, all of them will be removed
    object_indices = np.where(
        tracked_object_dict[OsefKeys.OBJECT_ID_32_BITS] == object_id
    )[0]
    if object_indices.shape[0] == 0:
        raise ObjectIdError(object_id)

    # Update the number of objects.
    tracked_object_dict[OsefKeys.NUMBER_OF_OBJECTS] -= object_indices.shape[0]

    # Remove zone bindings before removing the ID.
    if OsefKeys.ZONES_OBJECTS_BINDING_32_BITS in _get_scan_frame_dict(frame_dict):
        remove_object_binding(frame_dict, object_id)

    # Remove all data related to the object.
    for tracked_objects_key, tracked_object_field in tracked_object_dict.items():
        # Warning: All fields of the tracked objects will be filtered
        if isinstance(tracked_object_field, np.ndarray):
            new_field_value = np.delete(
                tracked_object_dict[tracked_objects_key], object_indices, axis=0
            )
            set_tracked_objects_field(frame_dict, tracked_objects_key, new_field_value)

    # Set the object ID to 0 in the augmented cloud
    if (
        aug_cloud_dict := _get_aug_cloud_dict(frame_dict)
    ) is not None and OsefKeys.OBJECT_ID_32_BITS in aug_cloud_dict:
        object_mask = aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS] == object_id

        # Check if the augmented_cloud field is writeable, else make a copy
        new_object_ids = (
            aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS]
            if aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS].flags.writeable
            else np.copy(aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS])
        )
        new_object_ids[object_mask] = 0
        set_augmented_cloud_field(
            frame_dict, OsefKeys.OBJECT_ID_32_BITS, new_object_ids
        )


def remove_objects(frame_dict: dict, mask: npt.NDArray[np.bool_]) -> None:
    """Remove tracked objects from an OSEF frame.

    :param frame_dict: OSEF frame dictionary to edit.
    :param mask: mask of object to keep (False: remove object, True: keep object)
    """
    tracked_object_dict = _get_tracked_objects_dict(frame_dict)

    if mask.size != tracked_object_dict[OsefKeys.NUMBER_OF_OBJECTS]:
        raise ValueError("Given mask must be of size number_of_objects")

    # Update the number of objects.
    tracked_object_dict[OsefKeys.NUMBER_OF_OBJECTS] = np.count_nonzero(mask)

    # Remove zone bindings before removing the ID.
    if OsefKeys.ZONES_OBJECTS_BINDING_32_BITS in _get_scan_frame_dict(frame_dict):
        for object_id in tracked_object_dict[OsefKeys.OBJECT_ID_32_BITS][mask]:
            remove_object_binding(frame_dict, object_id)

    # Set the object ID to 0 in the augmented cloud
    if (
        aug_cloud_dict := _get_aug_cloud_dict(frame_dict)
    ) is not None and OsefKeys.OBJECT_ID_32_BITS in aug_cloud_dict:
        object_mask = np.isin(
            aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS],
            np.invert(tracked_object_dict[OsefKeys.OBJECT_ID_32_BITS][mask]),
        )

        # Check if the augmented_cloud field is writeable, else make a copy
        new_object_ids = (
            aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS]
            if aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS].flags.writeable
            else np.copy(aug_cloud_dict[OsefKeys.OBJECT_ID_32_BITS])
        )
        new_object_ids[object_mask] = 0
        set_augmented_cloud_field(
            frame_dict, OsefKeys.OBJECT_ID_32_BITS, new_object_ids
        )

    # Filter-in only matching pairs related to object IDs to keep.
    if OsefKeys._OBJECT_MATCHING_PAIRS in tracked_object_dict:
        filter_object_matching_pairs(
            frame_dict, tracked_object_dict[OsefKeys.OBJECT_ID_32_BITS][mask]
        )

    # Remove all data related to the object.
    for tracked_objects_key, tracked_object_field in tracked_object_dict.items():
        # Warning: All fields of the tracked objects will be filtered except for the matching pairs.
        if (
            isinstance(tracked_object_field, np.ndarray)
            and tracked_objects_key != OsefKeys._OBJECT_MATCHING_PAIRS
        ):
            new_field_value = tracked_object_dict[tracked_objects_key][mask]
            set_tracked_objects_field(frame_dict, tracked_objects_key, new_field_value)


def remove_object_binding(frame_dict: Dict, object_id: int) -> None:
    """Remove zone-object bindings of a given object ID.

    :param frame_dict: OSEF frame dictionary to edit.
    :param object_id: ID of the object to remove from the zone binding field.
    """
    tracked_object_dict = _get_tracked_objects_dict(frame_dict)

    if object_id not in tracked_object_dict[OsefKeys.OBJECT_ID_32_BITS]:
        raise ObjectIdError(object_id)

    # Get all bindings of the object ID.
    scan_frame_dict = frame_dict[OsefKeys.TIMESTAMPED_DATA][OsefKeys.SCAN_FRAME]
    if OsefKeys.ZONES_OBJECTS_BINDING in scan_frame_dict:
        osef_logger.warning(
            f"'{OsefKeys.ZONES_OBJECTS_BINDING}' is deprecated, "
            + f"'field should be {OsefKeys.ZONES_OBJECTS_BINDING_32_BITS}' instead."
        )
        binding_key = OsefKeys.ZONES_OBJECTS_BINDING
    elif OsefKeys.ZONES_OBJECTS_BINDING_32_BITS in scan_frame_dict:
        binding_key = OsefKeys.ZONES_OBJECTS_BINDING_32_BITS
    else:
        raise FieldError(OsefKeys.ZONES_OBJECTS_BINDING_32_BITS)

    zone_bindings = scan_frame_dict.get(binding_key)
    remaining_binding_msk = (
        zone_bindings[constants.ExtraZoneBindingKeys.OBJECT_ID] != object_id
    )
    scan_frame_dict[binding_key] = zone_bindings[remaining_binding_msk]


def filter_object_matching_pairs(
    frame_dict: Dict, object_ids: npt.NDArray[np.uint32]
) -> None:
    """Filter object matching pairs of object IDs.

    :param frame_dict: OSEF frame dictionary to edit.
    :param object_ids: object IDs to keep in the object matching pairs.
    """
    tracked_object_dict = _get_tracked_objects_dict(frame_dict)

    # Get all object matching pairs.
    object_matching_pairs = np.array(
        tracked_object_dict.get(OsefKeys._OBJECT_MATCHING_PAIRS)
    )
    if object_matching_pairs.size == 0:
        return

    # Keep matching pairs that contain the object ID.
    new_object_matching_pairs = []
    for pair in object_matching_pairs:
        if pair[0] in object_ids or pair[1] in object_ids:
            new_object_matching_pairs.append(pair)

    tracked_object_dict[OsefKeys._OBJECT_MATCHING_PAIRS] = np.array(
        new_object_matching_pairs, dtype=np.uint32
    )
