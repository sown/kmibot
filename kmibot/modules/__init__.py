from .ferry import FerryModule
from .licence import LicenceModule
from .module import Module
from .pub import PubModule
from .sown_meeting import SOWNMeetingModule

MODULES = [FerryModule, LicenceModule, PubModule, SOWNMeetingModule]

__all__ = ["MODULES", "Module"]
