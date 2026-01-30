"""Functions to read and parse osef files/streams."""
import struct
import traceback
from collections import deque
from itertools import islice
from struct import Struct
from typing import Any, Iterable, Optional, Tuple, Iterator

from osef.spec import _types
from osef._logger import osef_logger
from osef.spec.constants import _Tlv, _TreeNode, _STRUCT_FORMAT
from osef.parsing.osef_stream import OsefStream, OsefStreamTcp
from osef.spec import _packers


class MalformedTlvException(Exception):
    """Exception raised for TLV structures that are malformed or incorrectly shaped."""


class OsefParsingException(Exception):
    """Exception raised when failing to parse next dataframe."""


def unpack_value(
    value: bytes, node_packer: _packers.PackerBase, type_name: str = ""
) -> Any:
    """Unpack a leaf value to a python object (type depends on type of leaf).

    :param value: binary value to be unpacked.
    :param node_packer: Packer for unpacking and conversion to python object.
    :param type_name: (optional) provide type name
     to provide better feedback if an exception occurs
    :return: python object
    """
    try:
        if node_packer.unpack is not None:
            return node_packer.unpack(value)
        # unknown parser
        return value

    except Exception as err:
        raise type(err)(f'occurred while unpacking "{type_name}".') from err


def iter_file(osef_stream: OsefStream, auto_reconnect: bool = True) -> Iterator[_Tlv]:
    """Iterator function to iterate over each frame in osef file.

    :param osef_stream: opened binary file containing tlv frames.
    :param auto_reconnect: enable reconnection for tcp connections.
    :return frame_tlv: next tlv frame of the osef file.
    """
    while True:
        try:
            frame_tlv = read_next_tlv(osef_stream)
        except EOFError:
            if auto_reconnect and isinstance(osef_stream, OsefStreamTcp):
                osef_logger.warning("Connection lost: reopening socket")
                osef_stream.open_socket(auto_reconnect)
                continue
            break
        except Exception:  # pylint: disable=broad-except
            osef_logger.error(
                f"Error: cannot read next Tlv from file (malformed Tlv?).\n"
                f"Details: {traceback.format_exc()}\n"
            )
            break

        yield frame_tlv


def get_tlv_iterator(
    opened_file: OsefStream,
    first: Optional[int] = None,
    last: Optional[int] = None,
    auto_reconnect: Optional[bool] = True,
) -> Iterable[_Tlv]:
    """Get an iterator to iterate over each tlv frame in osef file.

    :param opened_file: opened binary file containing tlv frames.
    :param first: iterate only on N first frames of file.
    :param last: iterate only on M last frames of file.
    Can be used with first to get the range (N-M) -> N
    :param auto_reconnect: enable reconnection for tcp connections.
    :return: tlv frame iterator
    """
    if first is None and last is None:
        return enumerate(iter_file(opened_file, auto_reconnect))
    return deque(islice(enumerate(iter_file(opened_file, auto_reconnect)), first), last)


def build_tree(tlv: _Tlv) -> _TreeNode:
    """Recursive function to get a tree from a raw Tlv frame

    :param tlv: raw tlv frame read from file.
    :raises  MalformedTlvException when _parse_tlv_from_blob raises a struct.error
    :return: tree representation of the tlv frame
    """
    # If we know this type is an internal node (not a leaf)\
    if tlv.osef_type in _types.outsight_types and isinstance(
        _types.outsight_types[tlv.osef_type].node_info, _types.InternalNodeInfo
    ):
        read = 0
        children = []
        while read < tlv.length:
            try:
                sub_tlv, sub_size = _parse_tlv_from_blob(tlv.value, read)
            except struct.error as exception:
                raise MalformedTlvException(
                    "Malformed Tlv, unable to unpack values."
                ) from exception

            sub_tree = build_tree(sub_tlv)
            children.append(sub_tree)
            read += sub_size
        return _TreeNode(tlv.osef_type, children, None)
    return _TreeNode(tlv.osef_type, None, tlv.value)


def read_next_tlv(osef_stream: OsefStream) -> Optional[_Tlv]:
    """Read the next TLV from a binary stream (file or socket)"""
    # Read header
    structure = Struct(_STRUCT_FORMAT % 0)
    blob = _read_from_file(osef_stream, structure.size)
    # Parse Type and Length
    read_tlv = _Tlv._make(structure.unpack_from(blob))

    # Now that we know its length we can read the Value
    structure = Struct(_STRUCT_FORMAT % read_tlv.length)
    blob += _read_from_file(osef_stream, structure.size - len(blob))
    read_tlv = _Tlv._make(structure.unpack_from(blob))

    return read_tlv


def _align_size(size: int) -> int:
    """Returned aligned size from tlv size"""
    alignment_size = 4
    offset = size % alignment_size
    return size if not offset else size + alignment_size - offset


def _read_from_file(osef_stream: OsefStream, byte_number: int) -> bytes:
    """Read given number of bytes from readable stream"""
    blob = bytearray()
    while len(blob) < byte_number:
        blob_inc = osef_stream.read(byte_number - len(blob))
        # End of file
        if blob_inc is None or len(blob_inc) == 0:
            raise EOFError
        blob += blob_inc
    return blob


def _parse_tlv_from_blob(blob: bytes, offset=0) -> Tuple[_Tlv, int]:
    """Parse a TLV from a binary blob"""
    # Unpack a first time to get Type and Length
    structure = Struct(_STRUCT_FORMAT % 0)
    read_tlv = _Tlv._make(structure.unpack_from(blob, offset))

    # Then unpack the whole tlv
    structure = Struct(_STRUCT_FORMAT % read_tlv.length)
    read_tlv = _Tlv._make(structure.unpack_from(blob, offset))
    return read_tlv, _align_size(structure.size)
