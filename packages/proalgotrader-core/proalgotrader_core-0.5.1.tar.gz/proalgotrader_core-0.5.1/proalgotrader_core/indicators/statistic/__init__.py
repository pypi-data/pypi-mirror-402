# Statistic Functions indicators package
from .beta import BETA
from .correl import CORREL
from .linearreg import LINEARREG
from .linearreg_angle import LINEARREG_ANGLE
from .linearreg_intercept import LINEARREG_INTERCEPT
from .linearreg_slope import LINEARREG_SLOPE
from .stddev import STDDEV
from .tsf import TSF
from .var import VAR

__all__: list[str] = [
    "BETA",
    "CORREL",
    "LINEARREG",
    "LINEARREG_ANGLE",
    "LINEARREG_INTERCEPT",
    "LINEARREG_SLOPE",
    "STDDEV",
    "TSF",
    "VAR",
]
