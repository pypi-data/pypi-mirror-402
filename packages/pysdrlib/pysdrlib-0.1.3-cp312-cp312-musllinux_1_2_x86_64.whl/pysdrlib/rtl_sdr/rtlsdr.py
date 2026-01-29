from ..base.device import Device
from .. import err, warn

from .config import ConfigRTL_SDR as config

class RTLSDR(Device):
    NAME = "RTL-SDR"
    CONFIG = config
    CAN_TRANSMIT = False
    DUPLEX = False
