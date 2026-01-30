from .ebest import EBest
from .ls import LS, LSV
from .kis import Kis, KisV

from enum import Enum

class APIProvider(Enum):
    EBEST = "EBEST"
    LS = "LS"
    LSV = "LSV"
    KIS = "KIS"
    KISV = "KISV"

class APIFactory:
    @staticmethod
    def create_api(api_provider: APIProvider):
        if api_provider == APIProvider.EBEST:
            return EBest()
        elif api_provider == APIProvider.LS:
            return LS()
        elif api_provider == APIProvider.LSV:
            return LSV()
        elif api_provider == APIProvider.KIS:
            return Kis()
        elif api_provider == APIProvider.KISV:
            return KisV()
        else:
            raise ValueError("Unsupported API provider")