from kmibot.modules.module import Module

from .ferry import FerryModule
from .pub import PubModule
from .sown_meeting import SOWNMeetingModule

MODULES = [FerryModule, PubModule, SOWNMeetingModule]

__all__ = ["MODULES", "Module"]
