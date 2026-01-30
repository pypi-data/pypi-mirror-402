"""Functions to pack data to osef format"""
import traceback
from struct import Struct
from typing import Any, Union

from osef.spec import _types
from osef._logger import osef_logger
from osef.spec.constants import _Tlv, _TreeNode, _STRUCT_FORMAT
from osef.parsing._parser_common import _align_size
from osef.parsing._lazy_parser import _LazyDict, _LazyList, BinaryLeaf
from osef.spec import _packers


# -- Public functions --
def pack(frame: dict) -> bytes:
    """Encode an osef frame content to a TLV

    :param frame: osef frame dict to be packed in the OSEF format (TLV)
    :raise KeyError: Raises exception on unknown type
    :return: bytes tlv
    """
    # Get the root OSEF type and the rest of the tree data
    root_tlv_data = next(iter(frame.items()))
    tree = _pack_to_tree(*root_tlv_data)
    return _tree_to_bin(tree)


def _encode_tlv(tlv: _Tlv) -> bytes:
    """Encode a single TLV to bytes sequence"""
    return Struct(_STRUCT_FORMAT % _align_size(tlv.length)).pack(*tlv)


def _tree_to_bin(
    tree: _TreeNode,
) -> bytes:
    """Encode a whole tree to binary TLVs"""
    # Go through the tree and encode to TLV->bin each branch/leaf
    if tree.leaf_value is not None:
        tlv = _Tlv(tree.osef_type, len(tree.leaf_value), tree.leaf_value)
    else:
        out = bytearray()
        for child in tree.children:
            out += _tree_to_bin(child)
        tlv = _Tlv(tree.osef_type, len(out), out)
    return _encode_tlv(tlv)


def _pack_to_tree(osef_type: Union[_types.OsefTypes, str], value: Any) -> _TreeNode:
    """Parse an item and generate a TreeNode, using OSEF types"""
    # deactivate unpacking to avoid unpacking binary values
    if isinstance(value, (_LazyDict, _LazyList)):
        value.unpacking = False
    if isinstance(osef_type, str):
        osef_type = _types.get_type_by_key(osef_type)
    type_info = _types.get_type_info_by_id(osef_type.value)

    # For leaves or unknown, return value
    if isinstance(type_info.node_info, _packers.PackerBase):
        packed_value = _pack_value(value, type_info.node_info, osef_type)
        return _TreeNode(osef_type.value, None, packed_value)

    # For non-leaves, add each child to a list
    children = []
    if type_info.node_info.node_type == list:
        for child in value:
            child_k, child_v = list(child.items())[0]
            children.append(_pack_to_tree(child_k, child_v))
    elif type_info.node_info.node_type == dict:
        for child_k, child_v in value.items():
            children.append(_pack_to_tree(child_k, child_v))
    else:
        raise ValueError("Unsupported internal node type.")

    # reactivate unpacking
    if isinstance(value, (_LazyDict, _LazyList)):
        value.unpacking = True

    return _TreeNode(osef_type.value, children, None)


def _pack_value(
    value: Any, node_packer: _packers.PackerBase, osef_type: _types.OsefTypes
) -> bytes:
    """Pack a leaf value to a python object (type depends on type of leaf).

    :param value: object to be packed.
    :param node_packer: Packer for packing and conversion to python object.
    :param osef_type: Type of OSEF leaf to be packed (only used for logs).
    :return: packed value of the leaf as bytes
    """
    try:
        if isinstance(value, BinaryLeaf):
            return value.leaf_value
        if node_packer.pack is not None:
            return node_packer.pack(value)
        # unknown parser
        return value

    except Exception:  # pylint: disable=broad-except
        osef_logger.error(
            f"Exception occurred while packing value of type {osef_type.name}:\n"
            f"Details: {traceback.format_exc()}"
        )
        return value
