from .ferry import FerryModule
from .licence import LicenceModule
from .module import Module
from .pub import PubModule

MODULES = [FerryModule, LicenceModule, PubModule]

__all__ = ["MODULES", "Module"]
