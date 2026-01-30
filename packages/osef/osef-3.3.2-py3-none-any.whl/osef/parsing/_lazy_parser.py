"""Functions to lazy read and parse osef files/streams."""

# Standard imports
from typing import Any, Tuple, NamedTuple, List, Optional

# Project imports
from osef.spec import _types as osef_types
from osef.spec import _packers
from osef.spec.constants import _TreeNode
from osef.parsing._parser_common import unpack_value


class BinaryLeaf(NamedTuple):
    """
    Wrapper for binary leaves.
    """

    osef_type: osef_types.OsefTypes
    leaf_value: bytes

    def __repr__(self) -> str:
        """High-level representation of a BinaryLeaf to avoid displaying all bytes of the leaf."""
        return "\x1B[3m(binary blob)\x1B[0m"


def _parse_osef_binary(value: BinaryLeaf) -> Any:
    """
    parse osef binary data

    :param: the binary leaf to be parsed
    :return: the unpacked value
    """

    type_info = osef_types.get_type_info_by_id(value.osef_type)
    return unpack_value(value.leaf_value, type_info.node_info, type_info.name)


class _LazyContainer:
    """Parent class to all lazy containers"""

    def __init__(self) -> None:
        self._unpacking_active: bool = True

    @property
    def unpacking(self) -> bool:
        """Whether unpacking is active or not"""
        return self._unpacking_active

    @unpacking.setter
    def unpacking(self, active: bool) -> None:
        """Switch on/off lazy unpacking (useful when packing)"""
        self._unpacking_active = active


class _LazyDict(dict, _LazyContainer):
    """
    dict with lazy [] operator
    data are stored in binary, and only parsed when the getter is called the first time.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _LazyContainer.__init__(self)

    def __getitem__(self, key: str) -> Any:
        """
        Override [] dict method with lazy parsing of the data
        The first time a data is accessed (ie it is still binary),
        it is parsed and the parsed value in written in place

        :param key: the key to search for in the dict
        :return Parsed value
        """

        value = super().__getitem__(key)
        # Only case we do something: it's a leaf AND it has not been parsed yet
        if self._unpacking_active and isinstance(value, BinaryLeaf):
            parsed_value = _parse_osef_binary(value)
            # The trick here is that [] in writing mode calls __setitem__
            # Any call to [] as __getitem__ would yield an endless recursion loop
            self[key] = parsed_value
            return parsed_value

        return value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Override get dict method with lazy parsing of the data
        The first time a data is accessed (ie it is still binary),
        it is parsed and the parsed value in written in place

        :param key: the key to search for in the dict
        :param default: default value if the key does not exist
        :return Parsed value
        """

        if key in self:
            return self[key]
        return default

    def items(self) -> List[Tuple[str, Any]]:
        """
        Override items dict method to return parsed (key, value) tuple.

        :return (key, parsed_value) tuple list
        """

        return [(key, self[key]) for key, _ in super().items()]

    def values(self) -> List[Any]:
        """
        Override values dict method to return parsed value list.

        :return Parsed value list
        """

        return [self[key] for key, _ in super().items()]


class _LazyList(list, _LazyContainer):
    """
    list with lazy [] operator
    data are stored in binary, and only parsed when the getter is called the first time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _LazyContainer.__init__(self)

    def __getitem__(self, index: int) -> Any:
        """
        Override [] list method with lazy parsing of the data
        The first time a data is accessed (ie it is still binary),
        it is parsed and the parsed value in written in place

        :param index: the index to search for in the list
        :return Parsed value
        """

        value = super().__getitem__(index)
        # Only case we do something: it's a leaf AND it has not been parsed yet
        if self._unpacking_active and isinstance(value, BinaryLeaf):
            parsed_value = _parse_osef_binary(value)
            # The trick here is that [] in writing mode calls __setitem__
            # Any call to [] as __getitem__ would yield an endless recursion loop
            self[index] = parsed_value
            return parsed_value

        return value

    def get(self, index: int, default: Optional[Any] = None) -> Any:
        """
        Override get list method with lazy parsing of the data
        The first time a data is accessed (ie it is still binary),
        it is parsed and the parsed value in written in place

        :param index: the index to search for in the list
        :param default: default value if the key does not exist
        :return Parsed value
        """
        if index in self:
            return self[index]
        return default


def _parse_tree_to_bin_tuple(raw_tree: _TreeNode) -> Tuple[str, Any]:
    """
    Parse a raw TLV tree and, recursively, build a dictionary where leaves are stored as BinaryLeaf
    """
    osef_type, children, leaf_value = raw_tree

    # Get leaf type info
    type_info = osef_types.get_type_info_by_id(osef_type)

    # For leaves, return a BinaryLeaf tuple which holds the binary blob and the osef type
    if isinstance(type_info.node_info, _packers.PackerBase):
        return (
            type_info.name,
            BinaryLeaf(osef_type, leaf_value),
        )

    # For non-leaves, add each child to a dictionary
    tree_bin = _LazyList() if type_info.node_info.node_type == list else _LazyDict()

    for child in children:
        child_name, child_tree_bin = _parse_tree_to_bin_tuple(child)

        if type_info.node_info.node_type == dict:
            tree_bin[child_name] = child_tree_bin
        elif type_info.node_info.node_type == list:
            tree_bin.append(_LazyDict({child_name: child_tree_bin}))
        else:
            raise ValueError("Unsupported internal node type.")

    return type_info.name, tree_bin


def parse_to_lazy_dict(binary_tlv_tree: _TreeNode):
    """Parse a whole frame tree to a _LazyDict.
    No value of the tree will be unpacked until direct access.

    :param binary_tlv_tree: raw tree of a tlv frame.
    :return: _LazyDict with all values in BinaryLeaf.
    """
    type_name, subtree_bin = _parse_tree_to_bin_tuple(binary_tlv_tree)
    return _LazyDict({type_name: subtree_bin})
