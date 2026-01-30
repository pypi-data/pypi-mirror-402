"""Functions to read and parse osef files/streams."""
import pathlib
import time
from typing import Any, Optional, Iterator, Union, List, Dict

from osef.spec import _types
from osef.spec.osef_types import OsefKeys
from osef._logger import osef_logger
from osef.parsing.osef_stream import (
    OsefConnectionException,
    OsefStream,
    OsefStreamTcp,
    create_osef_stream,
)
from osef.parsing._parser_common import (
    get_tlv_iterator,
    read_next_tlv,
    MalformedTlvException,
    OsefParsingException,
    build_tree,
    _parse_tlv_from_blob,
    _TreeNode,
    _Tlv,
)

from osef.parsing._lazy_parser import parse_to_lazy_dict
from osef.parsing._parser import parse_to_dict, _parse_raw_to_tuple


def parse_timestamp(tlv: _Tlv) -> float:
    """
    Get the timestamp of a frame from its TLV.

    :param tlv: raw TLV blob of a frame.
    :raises ValueError: the frame doesn't contain any timestamp leaf.
    :return: timestamp value as a float
    """
    if tlv.osef_type == _types.OsefTypes.TIMESTAMPED_DATA.value:
        read = 0
        sub_size = 0
        while read < tlv.length:
            sub_tlv, sub_size = _parse_tlv_from_blob(tlv.value, read)
            if sub_tlv.osef_type == _types.OsefTypes.TIMESTAMP_MICROSECOND.value:
                res = _parse_raw_to_tuple(
                    _TreeNode(sub_tlv.osef_type, None, sub_tlv.value)
                )
                return res[1]
            read += sub_size
    raise ValueError("No timestamp found in frame.")


def get_frame_timestamps(
    path: Union[str, pathlib.Path],
    first: Optional[int] = None,
    last: Optional[int] = None,
) -> List[float]:
    """
    Parse the frame timestamps of an OSEF file without unpacking all the frame content.
    If timestamp is missing in a frame, the list will contain timestamps of the previous frames.

    :param path: Path of OSEF file.
    :param first: iterate only on N first frames of file.
    :param last: iterate only on M last frames of file.
        Can be used with first to get the range [(N-M), N].
    :return: List of timestamps as floats of each frame of the file.
    """
    timestamps = []
    with create_osef_stream(path) as osef_stream:
        iterator = get_tlv_iterator(osef_stream, first, last)
        for _, tlv in iterator:
            try:
                timestamps.append(parse_timestamp(tlv))
            except ValueError:
                osef_logger.warning(
                    "A frame without any timestamp has been found."
                    " List of timestamps will be stopped just before this frame."
                )
                break
        return timestamps


# pylint: disable=too-many-locals
def parse(
    path: Union[str, pathlib.Path],
    first: Optional[int] = None,
    last: Optional[int] = None,
    auto_reconnect: bool = True,
    real_frequency: bool = False,
    lazy: bool = True,
) -> Iterator[Dict[str, Any]]:
    """Iterator that opens and converts each tlv frame to a dict.
    Factorization for both legacy parse and lazy parse.
    TCP stream if path has form `tcp://hostname:port`.

    :param path: path to osef file or TCP stream.
    :param first: iterate only on N first frames of file.
    :param last: iterate only on M last frames of file.
        Can be used with first to get the range [(N-M), N].
    :param auto_reconnect: enable reconnection for tcp connections.
    :param real_frequency: processing is slowed at the same frequency as the osef file
    :param lazy: Flag for lazy parsing
    :return: next tlv dictionary
    """

    def get_timestamp_ms(cur_frame_dict: dict) -> Optional[int]:
        return cur_frame_dict.get(OsefKeys.TIMESTAMPED_DATA.value, {}).get(
            OsefKeys.TIMESTAMP_MICROSECOND.value
        )

    first_frame_timestamp = None
    while True:  # To reopen stream when Tlv is malformed (in auto reconnect mode)
        with create_osef_stream(path, auto_reconnect) as osef_stream:
            first_frame_counter = time.perf_counter()
            iterator = get_tlv_iterator(osef_stream, first, last, auto_reconnect)
            for _, tlv in iterator:
                try:
                    raw_tree = build_tree(tlv)
                except MalformedTlvException as exception:
                    osef_logger.error(f"{exception} (closing OSEF stream)")
                    break  # we disconnect OSEF stream as our reading
                    # head may not be at the beginning of the next frame

                frame_dict = (
                    parse_to_lazy_dict(raw_tree) if lazy else parse_to_dict(raw_tree)
                )

                if first_frame_timestamp is None:
                    first_frame_timestamp = get_timestamp_ms(frame_dict)
                yield frame_dict

                # Warning. In some cases, the TLV is not timestamped.
                if (
                    real_frequency
                    and not isinstance(osef_stream, OsefStreamTcp)
                    and first_frame_timestamp is not None
                ):
                    _sleep(
                        first_frame_counter,
                        first_frame_timestamp,
                        get_timestamp_ms(frame_dict),
                    )
            if not isinstance(osef_stream, OsefStreamTcp) or not auto_reconnect:
                break


def parse_next_frame(
    osef_stream: OsefStream,
    lazy: bool = True,
) -> Dict[str, Any]:
    """
    Try to parse the next frame. Assume the stream is already connected.

    :param osef_stream: the OsefStream we want to parse data from
    :param lazy: whether to use lazy-parsing
    :raises OsefParsingException: if the next frame could not be parsed.
    :return: next tlv dictionary

    """
    try:
        tlv = read_next_tlv(osef_stream)
        raw_tree = build_tree(tlv)
        frame_dict = parse_to_lazy_dict(raw_tree) if lazy else parse_to_dict(raw_tree)
        return frame_dict
    except (MalformedTlvException, EOFError, OsefConnectionException) as exp:
        raise OsefParsingException from exp


def _sleep(
    first_frame_counter: float,
    first_frame_timestamp: float,
    timestamp_microsecond: int,
):
    """Function to compute the pause duration required to process the parser in the frequency of the osef file"""
    current_frame_counter = time.perf_counter()
    pause = (timestamp_microsecond - first_frame_timestamp) - (
        current_frame_counter - first_frame_counter
    )

    if pause > 0.0:
        _sleep_ms(pause * 1000)


def _sleep_ms(duration: float):
    """Sleep for a precise duration.

    :param duration: Duration to sleep in seconds.
    """
    end_time = time.perf_counter_ns() + duration * 1000000
    while time.perf_counter_ns() < end_time:
        time.sleep(5e-4)
