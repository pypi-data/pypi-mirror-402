"""Functions to read and parse osef files/streams."""
from __future__ import annotations
from abc import ABC, abstractmethod
import pathlib
import socket
import time
from typing import Union, Optional
from io import BufferedReader
import urllib

from osef._logger import osef_logger

# Constants
TCP_SCHEME = "tcp"
TCP_TIMEOUT = 3


class OsefConnectionException(Exception):
    """Exception raised when failing to connect to a tcp stream/failing to open a file."""


def path_to_str(path: Union[str, pathlib.Path]) -> str:
    """If path is a pathlib.Path instance, convert to str"""
    if isinstance(path, pathlib.Path):
        return str(path.absolute())
    return path


class OsefStream(ABC):
    """Context manager class to open file path or tcp socket, then read its values.
    Delegate actual implementation to child classes
    """

    @abstractmethod
    def __enter__(self) -> OsefStream:
        """Context manager interface. Implementation is delegated to the child class."""

    @abstractmethod
    def __exit__(self, *_) -> None:
        """Context manager interface. Implementation is delegated to the child class."""

    @abstractmethod
    def read(self, _: int) -> bytes:
        """read interface. Implementation is delegated to the child class."""

    @abstractmethod
    def connect(self) -> None:
        """read interface. Implementation is delegated to the child class."""

    @abstractmethod
    def disconnect(self) -> None:
        """read interface. Implementation is delegated to the child class."""


def create_osef_stream(
    path: Union[str, pathlib.Path], auto_reconnect: bool = True
) -> OsefStream:
    """
    Factory for creating an OsefStream
    Instantiate an OsefStreamTcp if given path is tcp, else an OsefStreamFile
    TCP stream if path has form `tcp://hostname:port`.

    :param path: path to osef file or TCP stream.
    :param auto_reconnect: activate auto reconnection in case of connection loss (tcp only)
    """

    if urllib.parse.urlparse(path_to_str(path)).scheme == TCP_SCHEME:
        return OsefStreamTcp(path, auto_reconnect)

    return OsefStreamFile(path)


class OsefStreamTcp(OsefStream):
    """Context manager class to open tcp socket, then read its values.
    TCP stream if path has form `tcp://hostname:port`.

    :param path: path to osef file or TCP stream.
    The server may close the socket if client is too late.
    """

    def __init__(self, path: Union[str, pathlib.Path], auto_reconnect: bool = True):
        """Constructor.
        TCP stream with form `tcp://hostname:port`.

        :param path: TCP stream.
        :param auto_reconnect: activate auto reconnection in case of connection loss
        """
        self._path: urllib.parse.ParseResult = urllib.parse.urlparse(path_to_str(path))
        self._tcp_socket: Optional[socket.socket] = None
        self._auto_reconnect = auto_reconnect

    def __enter__(self) -> OsefStreamTcp:
        """Context manager"""
        self.open_socket(self._auto_reconnect)
        return self

    def __exit__(self, *_) -> None:
        """Context manager"""
        self.disconnect()

    def read(self, size: int = 4096) -> bytes:
        """Read `size` bytes from socket.

        :param size: of binary value to be read
        :raises EOFError: if no value can be read or if it is empty.
        :raises OsefConnectionException: If no TCP socket.
        :return: Read binary value
        """
        msg = b""
        if self._tcp_socket is None:
            raise OsefConnectionException(
                f"TCP socket ({self._path.netloc}) has not been initialized"
            )

        try:
            msg = self._tcp_socket.recv(size)
        except socket.timeout:
            osef_logger.warning(
                f"Received timeout. Closing socket ({self._path.netloc})."
            )
            self.disconnect()
        except ConnectionResetError:
            osef_logger.warning(
                f"Socket reset error. Closing socket ({self._path.netloc})."
            )
            self.disconnect()
        return msg

    def connect(self) -> None:
        """Try to open the socket

        :raises OsefConnectionException: if the connection failed.
        """
        try:
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.settimeout(TCP_TIMEOUT)
            self._tcp_socket.connect((self._path.hostname, self._path.port or 11120))
            osef_logger.warning(
                "Connected to %s:%d",
                self._path.hostname,
                self._path.port or 11120,
            )
        except OSError as exp:
            raise OsefConnectionException(f"{exp} ({self._path.netloc})") from exp

    def disconnect(self) -> None:
        """Close the socket"""
        if self._tcp_socket is not None:
            self._tcp_socket.close()

    def open_socket(
        self,
        auto_reconnect: bool = True,
        reconnection_frequency_hz: float = 200,
        log_frequency_hz: float = 2,
    ) -> None:
        """Open tcp socket on provided path.
        Tries to connect again if the connection fails
        """

        if reconnection_frequency_hz < 0:
            raise ValueError(
                f"Invalid reconnection frequency {reconnection_frequency_hz} Hz, should be strictly positive."
            )
        if log_frequency_hz > reconnection_frequency_hz:
            raise ValueError(
                f"Invalid log frequency {log_frequency_hz} Hz,"
                f" should be smaller than the reconnection frequency ({reconnection_frequency_hz} Hz)."
            )

        # Count the retries, to avoid flooding the log
        retry = 0
        waiting_time = 1 / reconnection_frequency_hz
        nb_iteration_between_logs = reconnection_frequency_hz / log_frequency_hz

        while True:
            try:
                self.connect()
                break
            except OsefConnectionException as exp:
                if not retry % nb_iteration_between_logs:
                    osef_logger.error(exp)

            if not auto_reconnect:
                break
            if not retry % nb_iteration_between_logs:
                osef_logger.warning(
                    "Retrying to connect to %s:%d",
                    self._path.hostname,
                    self._path.port or 11120,
                )
            retry = retry + 1
            time.sleep(waiting_time)


class OsefStreamFile(OsefStream):
    """Context manager class to open an osef file, then read its values."""

    def __init__(self, path: Union[str, pathlib.Path]):
        """
        Constructor
        :param path: path to osef file
        """
        self._path: str = path_to_str(path)
        self._io_stream: Optional[BufferedReader] = None

    def connect(self) -> None:
        """Open the file

        :raises OsefConnectionException: if the file could not be opened.
        """
        try:
            self._io_stream = open(  # pylint: disable=consider-using-with
                self._path, "rb"
            )
        except OSError as exp:
            raise OsefConnectionException(f"{exp} ({self._path})") from exp

    def disconnect(self) -> None:
        """Close the file"""
        if self._io_stream is not None:
            self._io_stream.close()

    def __enter__(self) -> OsefStreamFile:
        """Context manager"""
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        """Context manager"""
        self.disconnect()

    def read(self, size: int = 4096) -> bytes:
        """Read `size` bytes from file.

        :param size: of binary value to be read
        :raises EOFError: if no value can be read or if it is empty.
        :raises OsefConnectionException: IOStream not opened.
        :return: Read binary value
        """

        if self._io_stream is None:
            raise OsefConnectionException(
                f"File IOStream has not been opened ({self._path})"
            )

        return self._io_stream.read(size)
