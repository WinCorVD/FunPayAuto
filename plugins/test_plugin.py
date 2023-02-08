"""
Плагин затычка
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

import logging

logger = logging.getLogger(f"FPC.{__name__}")


def wow(cardinal: Cardinal, *args):
    logger.info("$MAGENTA[PASS PLUGIN]$RESET Я СУЩЕСТВУЮ! А ЗНАЧИТ МЫСЛЮ!")


BIND_TO_POST_INIT = [wow]