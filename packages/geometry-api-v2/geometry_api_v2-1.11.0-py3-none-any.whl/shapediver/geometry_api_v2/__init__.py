from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

# import custom classes into sdk package
from .client import *  # noqa: 403
from .client.rest import *  # noqa: 403
from .sd_client import *  # noqa: 403
from .sd_utils import *  # noqa: 403

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
