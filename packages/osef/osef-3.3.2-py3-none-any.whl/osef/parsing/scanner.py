"""Scanning tools to speed up OSEF frame access"""

# Standard imports
import pathlib
from struct import Struct
from typing import Union, List
from urllib.parse import urlparse

# Project imports
from osef._logger import osef_logger
from osef.spec import constants
from osef.parsing._parser_common import _read_from_file
from osef.parsing import osef_stream


def find_frame_file_offsets(
    osef_path: Union[str, pathlib.Path], log_period: int = -1
) -> List[int]:
    """Walk through OSEF file and find start position of each frame (frame_offset).
    The position in the file is useful to easily jump to a frame.

    :param osef_path: path to OSEF file to scan
    :param log_period: will print a log of the number of frames read (-1 by default which does not print)
    :return: frame_offsets: list of file offsets of each OSEF frame
    """
    frame_offsets = [0]
    if urlparse(str(osef_path)).scheme == osef_stream.TCP_SCHEME:
        raise ValueError(
            f"{find_frame_file_offsets.__name__} is not compatible with TCP streams"
        )

    with osef_stream.OsefStreamFile(osef_path) as stream:
        osef_logger.info(
            "Start scanning OSEF file (find each frame positions in file)."
        )
        while True:
            try:
                # Read header
                struct = Struct(constants._STRUCT_FORMAT % 0)
                blob = _read_from_file(stream, struct.size)

                # Unpack Type and Length and jump to next frame
                read_tlv = constants._Tlv._make(struct.unpack_from(blob))
                stream._io_stream.seek(stream._io_stream.tell() + read_tlv.length)
            except EOFError:
                break
            frame_offsets.append(stream._io_stream.tell())

            # Log every COUNT_FREQUENCY_UPDATE frames
            if log_period >= 0 and not len(frame_offsets) % log_period:
                osef_logger.info(
                    f"OSEF file indexing progress : {len(frame_offsets)} frames"
                )

        frame_offsets = frame_offsets[:-1]  # remove last offset

        osef_logger.info(
            f"Finished scanning OSEF, file size: {len(frame_offsets)} frames"
        )
        return frame_offsets


def count_frames(osef_path: Union[str, pathlib.Path], log_period: int = -1):
    """Count the number of frames in an OSEF file.

    :param osef_path: path to OSEF file to scan
    :param log_period: will print a log of the number of frames read (-1 by default which does not print)
    :return: the number of OSEF frames in the file
    """
    return len(find_frame_file_offsets(osef_path, log_period))
