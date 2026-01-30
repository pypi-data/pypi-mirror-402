"""Packing/Unpacking functions and classes for OSEF types."""

# Standard imports
import uuid
from struct import Struct, calcsize
from typing import Callable, List, Optional

# Third party imports
import numpy as np
from numpy import typing as npt

# Project imports
from osef.spec import constants, _formats


class PackerBase:
    """Base class to define a packer.

    Each new packer should derive from this interface.
    In the child classes, assign in the constructor values for packer and unpacker functions,
    so they won't be evaluated/defined again.

    :param pack: Callable function to pack the data (Optional).
    :param unpack: Callable function to unpack the data (Optional).
    """

    def __init__(self) -> None:
        """Constructor."""

        # Init the pack and unpack callable as None.
        self.pack: Optional[Callable] = None
        self.unpack: Optional[Callable] = None


class ValuePacker(PackerBase):
    """Derived class to pack/unpack value."""

    def __init__(self, pack_format: str) -> None:
        """Constructor.

        :param pack_format:
        """
        super().__init__()
        self.pack = ValuePacker._get_value_packer(pack_format)
        self.unpack = ValuePacker._get_value_unpacker(pack_format)

    @staticmethod
    def _get_value_packer(pack_format: str) -> Callable:
        def _pack_value(value: object) -> bytes:
            return Struct(pack_format).pack(value)

        return _pack_value

    @staticmethod
    def _get_value_unpacker(pack_format: str) -> Callable:
        def _parse_value(value: bytes) -> object:
            return (Struct(pack_format).unpack(value))[0]

        return _parse_value


class ArrayPacker(PackerBase):
    """Derived class to pack/unpack array."""

    def __init__(self, dtype: np.dtype, cols: int = 0) -> None:
        """Constructor.

        :param dtype: Dtype of the numpy array.
        :param cols: Number of columns, default to 0.
        """
        super().__init__()
        self.pack = ArrayPacker._get_array_packer(dtype, cols)
        self.unpack = ArrayPacker._get_array_unpacker(dtype, cols)

    @staticmethod
    def _get_array_packer(dtype: np.dtype, cols: int = 0) -> Callable:
        def _array_packer(value: npt.NDArray) -> bytes:
            if value.dtype != dtype:
                raise TypeError(
                    f"Invalid array type to pack: expected = {dtype}, input = {value.dtype}"
                )

            # If the number of column is set, check it if the array is not empty
            # If it is not set, check that the array is one-dimensional
            if (cols == 0 and len(value.shape) > 1) or (
                cols >= 1 and value.shape[0] > 0 and value.shape[1] != cols
            ):
                raise ValueError(
                    f"Invalid number of columns to pack the array: expected = {cols}, input = {value.shape[1]}"
                )

            return value.tobytes()

        return _array_packer

    @staticmethod
    def _get_array_unpacker(dtype: np.dtype, cols: int = 0) -> Callable:
        def _parse_array(value: bytes) -> npt.NDArray[dtype]:
            array = np.frombuffer(value, dtype=dtype)
            if cols > 0:
                array = np.reshape(array, (int(array.shape[0] / cols), cols))
            return array

        return _parse_array


class StructuredArrayPacker(PackerBase):
    """Derived class to pack/unpack structured array."""

    def __init__(self, dtype: np.dtype) -> None:
        """Constructor.

        :param dtype: Dtype of the numpy array.
        :param cols: Number of cols, default to 0.
        """
        super().__init__()
        self.pack = ArrayPacker._get_array_packer(dtype)
        self.unpack = StructuredArrayPacker._get_structured_array_unpacker(dtype)

    @staticmethod
    def _get_structured_array_unpacker(dtype: np.dtype) -> Callable:
        def _parse_structured_array(value: bytes) -> npt.NDArray[dtype]:
            array = np.frombuffer(value, dtype=dtype)
            names = array.dtype.names
            if constants.ExtraOsefKeys._TO_DROP in names:
                names.remove(constants.ExtraOsefKeys._TO_DROP)
                array = array[names]
            return array

        return _parse_structured_array


class BytesPacker(PackerBase):
    """Derived class to pack/unpack bytes."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()

        # Packer/Unpacker for bytes just return the same value.
        self.pack = lambda value: value
        self.unpack = lambda value: value


class DictPacker(PackerBase):
    """Derived class to pack/unpack dictionary."""

    def __init__(self, pack_format: str, field_names: List[str]) -> None:
        """Constructor.

        :param pack_format: Format of the dict values.
        :param field_names: Names of the dict fields/keys.
        """
        super().__init__()
        self.pack = DictPacker._get_dict_packer(pack_format, field_names)
        self.unpack = DictPacker._get_dict_unpacker(pack_format, field_names)

    @staticmethod
    def _get_dict_packer(pack_format: str, fields_names: List[str]) -> Callable:
        def _pack_dict(value: dict) -> bytes:
            values = [value[k] for k in fields_names]
            array = Struct(pack_format).pack(*values)
            return array

        return _pack_dict

    @staticmethod
    def _get_dict_unpacker(pack_format: str, fields_names: List[str]) -> Callable:
        def _parse_dict(value: bytes) -> dict:
            array = list(Struct(pack_format).iter_unpack(value))
            return dict(zip(fields_names, array[0]))

        return _parse_dict


class TimestampPacker(PackerBase):
    """Derived class to pack/unpack timestamp."""

    def __init__(self, sub_seconds_order: int) -> None:
        """
        Constructor.
        `sub_seconds_order` is the order (power of 10) associated to the time decimals.
        """
        super().__init__()
        self.sub_seconds_order = sub_seconds_order
        self.pack = self._timestamp_packer
        self.unpack = self._timestamp_unpacker

    def _timestamp_packer(self, value: float) -> bytes:
        seconds = int(value)
        sub_seconds = int(round((value - seconds) * 10**self.sub_seconds_order))
        return Struct("<LL").pack(seconds, sub_seconds)

    def _timestamp_unpacker(self, value: bytes) -> float:
        seconds, sub_seconds = Struct("<LL").unpack(value)
        return seconds + sub_seconds * 10**-self.sub_seconds_order


class TimestampMicroPacker(TimestampPacker):
    """Derived class to pack/unpack timestamp using microseconds."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__(6)


class TimestampNanoPacker(TimestampPacker):
    """Derived class to pack/unpack timestamp using nanoseconds."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__(9)


class ProcessingBitfieldPacker(PackerBase):
    """Derived class for pack/unpack processing bitfield."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = ProcessingBitfieldPacker._processing_bitfield_packer
        self.unpack = ProcessingBitfieldPacker._processing_bitfield_unpacker

    @staticmethod
    def _processing_bitfield_packer(value: dict) -> bytes:
        return Struct("<Q").pack(value[constants.ExtraBackgroundKeys.DELETED])

    @staticmethod
    def _processing_bitfield_unpacker(value: bytes) -> dict:
        background_deleted = 0
        bitfield = Struct("<Q").unpack(value)[0]
        return {
            constants.ExtraBackgroundKeys.DELETED: (
                bitfield & (1 << background_deleted) != 0
            )
        }


class BoolBitfieldPacker(PackerBase):
    """Derived class for pack/unpack bool bitfield."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = BoolBitfieldPacker._bool_bitfield_packer
        self.unpack = BoolBitfieldPacker._bool_bitfield_unpacker

    @staticmethod
    def _bool_bitfield_packer(value: npt.NDArray[np.bool_]) -> bytes:
        return np.packbits(value, bitorder="little").tobytes()

    @staticmethod
    def _bool_bitfield_unpacker(value: bytes) -> npt.NDArray[np.bool_]:
        if len(value) == 0:
            return np.array([], dtype=np.bool_)
        np_8bit = np.frombuffer(value, dtype=np.uint8)
        return np.unpackbits(np_8bit, bitorder="little").astype(np.bool_)


class StringPacker(PackerBase):
    """Derived class for pack/unpack string."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = StringPacker._string_packer
        self.unpack = StringPacker._string_unpacker

    @staticmethod
    def _string_packer(value: str) -> bytes:
        return value.encode("ascii") + b"\x00"

    @staticmethod
    def _string_unpacker(value: bytes) -> str:
        return value.decode("ascii")[:-1]


class ImuPacker(PackerBase):
    """Derived class for pack/unpack IMU data."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = ImuPacker._imu_packer
        self.unpack = ImuPacker._imu_unpacker

    @staticmethod
    def _imu_packer(value: dict) -> bytes:
        return Struct("<LLffffff").pack(
            value[constants.ExtraTimestampKeys.TIMESTAMP][
                constants.ExtraTimestampKeys.UNIX_S
            ],
            value[constants.ExtraTimestampKeys.TIMESTAMP][
                constants.ExtraTimestampKeys.REMAINING_US
            ],
            value[constants.ExtraImuKeys.ACCELERATION][0],
            value[constants.ExtraImuKeys.ACCELERATION][1],
            value[constants.ExtraImuKeys.ACCELERATION][2],
            value[constants.ExtraImuKeys.ANGULAR_VELOCITY][0],
            value[constants.ExtraImuKeys.ANGULAR_VELOCITY][1],
            value[constants.ExtraImuKeys.ANGULAR_VELOCITY][2],
        )

    @staticmethod
    def _imu_unpacker(value: bytes) -> dict:
        value = Struct("<LLffffff").unpack(value)
        return {
            constants.ExtraTimestampKeys.TIMESTAMP: {
                constants.ExtraTimestampKeys.UNIX_S: value[0],
                constants.ExtraTimestampKeys.REMAINING_US: value[1],
            },
            constants.ExtraImuKeys.ACCELERATION: value[2:5],
            constants.ExtraImuKeys.ANGULAR_VELOCITY: value[5:8],
        }


class UuidPacker(PackerBase):
    """Derived class"""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = UuidPacker._uuid_packer
        self.unpack = UuidPacker._uuid_unpacker

    @staticmethod
    def _uuid_packer(value: uuid.UUID) -> bytes:
        return value.bytes

    @staticmethod
    def _uuid_unpacker(value: bytes) -> uuid.UUID:
        return uuid.UUID(bytes=value)


class ObjectPropertiesPacker(PackerBase):
    """Derived class for pack/unpack object properties."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self.pack = ObjectPropertiesPacker._object_properties_packer
        self.unpack = ObjectPropertiesPacker._object_properties_unpacker

    @staticmethod
    def _object_properties_packer(object_properties: npt.NDArray[np.bool_]) -> bytes:
        return (
            np.packbits(object_properties, bitorder="little").astype(np.uint8).tobytes()
        )

    @staticmethod
    def _object_properties_unpacker(value: bytes) -> npt.NDArray[np.bool_]:
        array = np.frombuffer(value, dtype=np.dtype(np.ubyte))

        # Use [:, None] trick to avoid to get a flatten array
        return np.unpackbits(array[:, None], axis=1, bitorder="little").astype(bool)


class OptimizedGMMDataPacker(PackerBase):
    """Derived class to pack/unpack GMM data in the "optimized" format."""

    _GMM_GAUSSIAN_NUMBER = 8
    """Number of gaussians per GMM container."""

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.pack = self._gmm_data_packer
        self.unpack = self._gmm_data_unpacker

        self.format = _formats.GMMDataFieldFormat.get_optimized_gmm_container_format(
            self._GMM_GAUSSIAN_NUMBER
        )

    def _gmm_data_packer(self, gmm_data: List[dict]) -> bytearray:
        """Pack the GMM data as a list of GMM containers with multiple gaussians."""

        def _build_container_tuple(container_dict: dict) -> tuple:
            """Convert one single container dict into a tuple with the right field order."""
            return (
                *container_dict[constants.GMMContainerFields.MEAN].tolist(),
                *container_dict[
                    constants.GMMContainerFields.INVERTED_VARIANCE
                ].tolist(),
                *container_dict[constants.GMMContainerFields.WEIGHT].tolist(),
                *container_dict[
                    constants.GMMContainerFields.BACKGROUND_PROBABILITY
                ].tolist(),
                *container_dict[constants.GMMContainerFields.COUNT].tolist(),
                *container_dict[constants.GMMContainerFields.PREVIOUS_VALUE].tolist(),
                *container_dict[constants.GMMContainerFields.CUMULATE_UPDATE].tolist(),
                container_dict[constants.GMMContainerFields.FURTHEST_BACKGROUND_MEAN],
                container_dict[constants.GMMContainerFields.LAST_UPDATE],
                container_dict[constants.GMMContainerFields.GAUSSIAN_NUMBER],
            )

        container_size = calcsize(self.format)
        gmm_data_bytes = bytearray(len(gmm_data) * container_size)

        for idx, container_dict in enumerate(gmm_data):
            Struct(self.format).pack_into(
                gmm_data_bytes,
                idx * container_size,
                *_build_container_tuple(container_dict),
            )

        return gmm_data_bytes

    def _gmm_data_unpacker(self, value: bytes) -> List[tuple]:
        """Unpack the GMM data into a list of container data."""

        def _build_container_dict(container_values: tuple) -> dict:
            """Convert the list of values of one container into a dict with the each field."""
            return {
                constants.GMMContainerFields.MEAN: np.array(
                    container_values[:8], dtype=np.float32
                ),
                constants.GMMContainerFields.INVERTED_VARIANCE: np.array(
                    container_values[8:16], dtype=np.float32
                ),
                constants.GMMContainerFields.WEIGHT: np.array(
                    container_values[16:24], dtype=np.float32
                ),
                constants.GMMContainerFields.BACKGROUND_PROBABILITY: np.array(
                    container_values[24:32], dtype=np.float32
                ),
                constants.GMMContainerFields.COUNT: np.array(
                    container_values[32:40], dtype=np.uint16
                ),
                constants.GMMContainerFields.PREVIOUS_VALUE: np.array(
                    container_values[40:48], dtype=np.float32
                ),
                constants.GMMContainerFields.CUMULATE_UPDATE: np.array(
                    container_values[48:56], np.uint8
                ),
                constants.GMMContainerFields.FURTHEST_BACKGROUND_MEAN: container_values[
                    56
                ],
                constants.GMMContainerFields.LAST_UPDATE: container_values[57],
                constants.GMMContainerFields.GAUSSIAN_NUMBER: container_values[58],
            }

        return [
            _build_container_dict(container_values)
            for container_values in Struct(self.format).iter_unpack(value)
        ]
