__version__ = '0.5.3.1'

from .api_fcatory import APIFactory, APIProvider
from . import model
from .model import *
from .ebest import *
from .ls import *
from .kis import *

__all__ = ['APIFactory','APIProvider', 'model',] + model.__all__

def print_version_info():
    print(f"The version of this stock finance API is {__version__}.")

def create_api(api_provider: APIProvider):
    return APIFactory.create_api(api_provider)