from .gbfutures import GBFutures
from .indexfutures import IndexFutures
from .indexoptions import IndexOptions
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('pycffex')
except PackageNotFoundError:
    __version__ = 'unknown'

__doc__ = '''
Implementation of CFFEX products
- GBFutures
- IndexFutures
- IndexOptions
'''

__all__ = [
    'GBFutures',
    'IndexFutures',
    'IndexOptions'
]
