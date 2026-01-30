"""

Library containing utilities to read and parse a stream, live or recorded, retrieved from
**Shift**.

"""
# Import version
from osef._version import __version__

# Shortcuts for public functions/classes
from osef.frame_helper import osef_frame
from osef.parsing.parser import parse
from osef.packing.packer import pack
