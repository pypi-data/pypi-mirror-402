from typing import Type, Generic
from .base import BArrayType, BDeviceType, BDtypeType, BRNGType

class ComputeBackendImplCls(Generic[BArrayType, BDeviceType, BDtypeType, BRNGType], Type):
    def __str__(self):
        return self.simplified_name
    
    def __repr__(self):
        return self.simplified_name