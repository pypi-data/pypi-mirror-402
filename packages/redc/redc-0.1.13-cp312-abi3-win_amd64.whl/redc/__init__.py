"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'redc.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from . import utils
from .callbacks import ProgressCallback, StreamCallback
from .client import Client
from .codes import HTTPStatus
from .exceptions import HTTPError
from .response import Response
from ._version import __version__, __copyright__, __license__

__all__ = [
    "utils",
    "ProgressCallback",
    "StreamCallback",
    "Client",
    "HTTPStatus",
    "HTTPError",
    "Response",
    "__version__",
    "__copyright__",
    "__license__",
]
