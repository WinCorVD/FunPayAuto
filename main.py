import Utils.config_loader as cfg_loader
from colorama import Fore, Style
import Utils.logger
import logging.config
import traceback
import colorama
import sys
import json
import os

from cardinal import Cardinal
import Utils.exceptions as excs


# Инициируем цветной текст и логгер.
colorama.init()
if not os.path.exists("logs"):
    os.mkdir("logs")

with open("configs/logger_config.json") as f:
    LOGGER_CONFIG = json.loads(f.read())
logging.config.dictConfig(LOGGER_CONFIG)
logging.raiseExceptions = False
logger = logging.getLogger("main")
logger.debug("-------------------Новый запуск.-------------------")

logo = """[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m"[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52m,[0m[38;5;52mi[0m[38;5;88m>[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52m,[0m[38;5;88m>[0m[38;5;9m1[0m[38;5;160m[[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m^[0m[38;5;52m:[0m[38;5;124m?[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;0m^[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52mI[0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;52m:[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52m,[0m[38;5;160m[[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;52mi[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m [0m[38;5;0ml[0m[38;5;60mt[0m[38;5;60m/[0m[38;5;60mt[0m[38;5;60m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;17m![0m[38;5;0m [0m[38;5;59m-[0m[38;5;60mt[0m[38;5;60m/[0m[38;5;60mt[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m/[0m[38;5;59m|[0m[38;5;59m[[0m[38;5;17mi[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0ml[0m[38;5;59m}[0m[38;5;60mf[0m[38;5;102mn[0m[38;5;102mn[0m[38;5;60mt[0m[38;5;59m}[0m[38;5;17m![0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52mI[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m)[0m[38;5;160m][0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m1[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;59m/[0m[38;5;0m [0m[38;5;145mL[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;188ma[0m[38;5;59m|[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;59m{[0m[38;5;146mq[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;59m-[0m[38;5;0m [0m[38;5;0m`[0m[38;5;9m1[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m1[0m[38;5;9m)[0m[38;5;9m)[0m[38;5;160m[[0m[38;5;167m([0m[38;5;168mc[0m[38;5;0m"[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m@[0m[38;5;15mB[0m[38;5;15m@[0m[38;5;188mM[0m[38;5;145mq[0m[38;5;146mp[0m[38;5;146mq[0m[38;5;146mq[0m[38;5;145mq[0m[38;5;146mq[0m[38;5;59m][0m[38;5;0m [0m[38;5;102mY[0m[38;5;15m@[0m[38;5;15mB[0m[38;5;15m@[0m[38;5;188mb[0m[38;5;145mO[0m[38;5;145mZ[0m[38;5;188md[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;59m)[0m[38;5;0m [0m[38;5;0m.[0m[38;5;103mY[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;188m#[0m[38;5;188ma[0m[38;5;188m*[0m[38;5;15m%[0m[38;5;15m$[0m[38;5;59m{[0m[38;5;0m [0m[38;5;52ml[0m[38;5;9m([0m[38;5;9m([0m[38;5;160m[[0m[38;5;95m{[0m[38;5;124m][0m[38;5;132mu[0m[38;5;188ma[0m[38;5;195m&[0m[38;5;182mb[0m[38;5;0m,[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;102mX[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m [0m[38;5;102mX[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;59m?[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;59m/[0m[38;5;15m$[0m[38;5;15mB[0m[38;5;15m@[0m[38;5;145mm[0m[38;5;0m [0m[38;5;60mt[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;109mU[0m[38;5;17mi[0m[38;5;0m`[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0mI[0m[38;5;59m\[0m[38;5;17m![0m[38;5;0m [0m[38;5;124m-[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m1[0m[38;5;125m}[0m[38;5;95mt[0m[38;5;188mo[0m[38;5;224mW[0m[38;5;203mu[0m[38;5;9m1[0m[38;5;160m{[0m[38;5;124m-[0m[38;5;52mi[0m[38;5;0m"[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;188m*[0m[38;5;145mC[0m[38;5;145mL[0m[38;5;145mC[0m[38;5;145mC[0m[38;5;145mC[0m[38;5;102mj[0m[38;5;0m.[0m[38;5;0m [0m[38;5;102mY[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;102mx[0m[38;5;59m~[0m[38;5;59m_[0m[38;5;59m][0m[38;5;145mZ[0m[38;5;15m@[0m[38;5;15mB[0m[38;5;15m$[0m[38;5;103mY[0m[38;5;0m [0m[38;5;188mh[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;145mQ[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;52m,[0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;160m[[0m[38;5;188ma[0m[38;5;15m$[0m[38;5;210mJ[0m[38;5;9m][0m[38;5;9m)[0m[38;5;9m)[0m[38;5;160m[[0m[38;5;124m-[0m[38;5;52m![0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;188ma[0m[38;5;0m [0m[38;5;0m [0m[38;5;102mY[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;188mh[0m[38;5;0m:[0m[38;5;0m.[0m[38;5;188m*[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;66mf[0m[38;5;0m [0m[38;5;0m`[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m^[0m[38;5;160m}[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m([0m[38;5;160m][0m[38;5;145mO[0m[38;5;15m$[0m[38;5;188mk[0m[38;5;210mC[0m[38;5;131m([0m[38;5;88m>[0m[38;5;52ml[0m[38;5;52m,[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;188mh[0m[38;5;102mv[0m[38;5;102mc[0m[38;5;102mc[0m[38;5;102mv[0m[38;5;102mc[0m[38;5;59m\[0m[38;5;0m.[0m[38;5;0m [0m[38;5;102mY[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;15m&[0m[38;5;188mM[0m[38;5;188mM[0m[38;5;188mo[0m[38;5;188md[0m[38;5;145mC[0m[38;5;59m([0m[38;5;0m`[0m[38;5;0m [0m[38;5;0m [0m[38;5;145mm[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;188mo[0m[38;5;0mI[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m^[0m[38;5;88m>[0m[38;5;160m}[0m[38;5;9m1[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;9m1[0m[38;5;9m)[0m[38;5;124m][0m[38;5;152mp[0m[38;5;15m@[0m[38;5;195m&[0m[38;5;195mB[0m[38;5;66mu[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m}[0m[38;5;15m$[0m[38;5;15mB[0m[38;5;15m$[0m[38;5;102mX[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m'[0m[38;5;0m [0m[38;5;102mX[0m[38;5;15m$[0m[38;5;15mB[0m[38;5;15m$[0m[38;5;59m)[0m[38;5;0m'[0m[38;5;0m^[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m'[0m[38;5;0m [0m[38;5;59m~[0m[38;5;15mB[0m[38;5;15m$[0m[38;5;15m@[0m[38;5;15m$[0m[38;5;15m%[0m[38;5;145m0[0m[38;5;102mx[0m[38;5;59m_[0m[38;5;88m~[0m[38;5;160m{[0m[38;5;9m)[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;9m1[0m[38;5;9m([0m[38;5;160m1[0m[38;5;167m)[0m[38;5;131m|[0m[38;5;131mf[0m[38;5;167mx[0m[38;5;52m<[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m'[0m[38;5;0m [0m[38;5;59m{[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;145mL[0m[38;5;0m [0m[38;5;0m`[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m [0m[38;5;109mU[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;59m1[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;59m+[0m[38;5;188mk[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;15m$[0m[38;5;224m*[0m[38;5;203mX[0m[38;5;9m([0m[38;5;9m1[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m}[0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m1[0m[38;5;9m1[0m[38;5;9m{[0m[38;5;9m}[0m[38;5;52m:[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m [0m[38;5;59m-[0m[38;5;188mh[0m[38;5;188mb[0m[38;5;188mh[0m[38;5;102mn[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;102mr[0m[38;5;188mh[0m[38;5;188mb[0m[38;5;188mh[0m[38;5;59m][0m[38;5;0m [0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m.[0m[38;5;59m][0m[38;5;174mL[0m[38;5;203mv[0m[38;5;160m][0m[38;5;160m][0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m[[0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m)[0m[38;5;88m<[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m^[0m[38;5;88mi[0m[38;5;160m?[0m[38;5;160m[[0m[38;5;160m1[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m[[0m[38;5;160m}[0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m)[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;160m][0m[38;5;52ml[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;52mi[0m[38;5;160m{[0m[38;5;9m([0m[38;5;160m1[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m[[0m[38;5;160m[[0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;160m}[0m[38;5;88m~[0m[38;5;52m;[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;52m,[0m[38;5;124m][0m[38;5;9m)[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m[[0m[38;5;160m][0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;9m([0m[38;5;160m}[0m[38;5;88m+[0m[38;5;52m;[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;88m>[0m[38;5;160m1[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m1[0m[38;5;160m}[0m[38;5;124m][0m[38;5;124m][0m[38;5;160m{[0m[38;5;9m([0m[38;5;9m([0m[38;5;9m1[0m[38;5;124m][0m[38;5;88m<[0m[38;5;52m,[0m[38;5;0m`[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m^[0m[38;5;124m?[0m[38;5;9m)[0m[38;5;160m1[0m[38;5;160m{[0m[38;5;160m{[0m[38;5;160m[[0m[38;5;160m][0m[38;5;160m[[0m[38;5;9m1[0m[38;5;9m([0m[38;5;160m{[0m[38;5;124m+[0m[38;5;52mI[0m[38;5;0m`[0m[38;5;0m.[0m[38;5;0m^[0m[38;5;0m [0m[38;5;0m`[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;52ml[0m[38;5;160m1[0m[38;5;9m([0m[38;5;160m}[0m[38;5;160m[[0m[38;5;160m[[0m[38;5;160m][0m[38;5;160m][0m[38;5;160m][0m[38;5;124m-[0m[38;5;52mi[0m[38;5;52m,[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m`[0m[38;5;0mI[0m[38;5;0m'[0m[38;5;0m^[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;88m<[0m[38;5;160m{[0m[38;5;124m_[0m[38;5;52mi[0m[38;5;88m<[0m[38;5;124m+[0m[38;5;88m<[0m[38;5;52m![0m[38;5;52m:[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;0m^[0m[38;5;0m"[0m[38;5;0m"[0m[38;5;0m`[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m'[0m[38;5;52m,[0m[38;5;0m'[0m[38;5;0m.[0m[38;5;0m"[0m[38;5;52m,[0m[38;5;0m`[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m [0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m
[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m[38;5;0m.[0m"""

print(logo)
print(f"{Fore.RED}{Style.BRIGHT}v0.0.7 dev{Style.RESET_ALL}")
print("\n")
print(f"{Fore.MAGENTA}{Style.BRIGHT}By {Fore.BLUE}{Style.BRIGHT}Woopertail{Style.RESET_ALL}\n")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * GitHub: {Fore.BLUE}{Style.BRIGHT}github.com/woopertail/FunPayCardinal{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * Telegram: {Fore.BLUE}{Style.BRIGHT}t.me/funpay_cardinal")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * VK: {Fore.BLUE}{Style.BRIGHT}vk.com/woopertail")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * ИНСТРУКЦИЯ: {Fore.BLUE}{Style.BRIGHT}woopertail.ru")
print("\n\n")


# Загружаем конфиги
e = None
try:
    logger.info("$MAGENTAЗагружаю конфиг _main.cfg...")
    MAIN_CONFIG = cfg_loader.load_main_config("configs/_main.cfg")

    logger.info("$MAGENTAЗагружаю конфиг auto_response.cfg...")
    AUTO_RESPONSE_CONFIG = cfg_loader.load_auto_response_config("configs/auto_response.cfg")
    RAW_AUTO_RESPONSE_CONFIG = cfg_loader.load_raw_auto_response_config("configs/auto_response.cfg")

    logger.info("$MAGENTAЗагружаю конфиг auto_delivery.cfg...")
    AUTO_DELIVERY_CONFIG = cfg_loader.load_auto_delivery_config("configs/auto_delivery.cfg")

except excs.ConfigParseError as e:
    logger.error(e)
    logger.error("Завершаю программу...")
    sys.exit()

except UnicodeDecodeError:
    logger.error("Произошла ошибка при расшифровке UTF-8. Убедитесь, что кодировка файла = UTF-8, "
                 "а формат конца строк = LF.")
    logger.error("Завершаю программу...")
    sys.exit()

except Exception as e:
    logger.critical("Произошла непредвиденная ошибка. Подробнее в файле logs/log.log.")
    logger.debug(traceback.format_exc())
    logger.error("Завершаю программу...")
    sys.exit()

# Запускаем основную программу Cardinal
try:
    main_program = Cardinal(
        MAIN_CONFIG,
        AUTO_DELIVERY_CONFIG,
        AUTO_RESPONSE_CONFIG,
        RAW_AUTO_RESPONSE_CONFIG
    )
    main_program.init()
    main_program.run()
except KeyboardInterrupt:
    logger.info("Завершаю программу...")
    sys.exit()
except:
    logger.critical("При работе Кардинала произошла необработанная ошибка. Подробнее в файле logs/log.log")
    logger.debug(traceback.format_exc())
    logger.critical("Завершаю программу...")
    sys.exit()
