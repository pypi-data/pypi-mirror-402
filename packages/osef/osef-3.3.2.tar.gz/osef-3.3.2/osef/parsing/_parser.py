"""Functions to read and parse osef files/streams."""
from typing import Tuple, Any

from osef.spec import _types
from osef.spec.constants import _TreeNode
from osef.parsing._parser_common import unpack_value
from osef.spec import _packers


def parse_to_dict(frame_tree: _TreeNode) -> dict:
    """Parse a whole frame tree to a python dictionary. All values of the tree will be unpacked.

    :param frame_tree: raw tree of a tlv frame.
    :return: dictionary with all values in osef frame.
    """
    type_name, subtree = _parse_raw_to_tuple(frame_tree)
    return {type_name: subtree}


def _parse_raw_to_tuple(raw_tree: _TreeNode) -> Tuple[str, Any]:
    """Parse a raw TLV tree, using OSEF types"""
    osef_type, children, leaf_value = raw_tree

    # Get leaf type info
    type_info = _types.get_type_info_by_id(osef_type)

    # For leaves or unknown, return value
    if isinstance(type_info.node_info, _packers.PackerBase):
        return (
            type_info.name,
            unpack_value(leaf_value, type_info.node_info, type_info.name),
        )

    # For non-leaves, add each child to a dictionary
    tree = [] if type_info.node_info.node_type == list else {}

    for child in children:
        child_name, child_tree = _parse_raw_to_tuple(child)

        if type_info.node_info.node_type == dict:
            tree[child_name] = child_tree
        elif type_info.node_info.node_type == list:
            tree.append({child_name: child_tree})
        else:
            raise ValueError("Unsupported internal node type.")

    return type_info.name, tree
