"""
Плагин-затычка.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal
import logging

NAME = "Test Plugin"
VERSION = "0.0.1"
DESCRIPTION = "Тестовый плагин."
CREDITS = "@woopertail"
UUID = "9f09a878-aa02-4e87-aaec-eba23693503a"

logger = logging.getLogger(f"FPC.{__name__}")


def wow(cardinal: Cardinal, *args):
    logger.info("$MAGENTA[PASS PLUGIN]$RESET Я СУЩЕСТВУЮ! А ЗНАЧИТ МЫСЛЮ!")


BIND_TO_POST_INIT = [wow]