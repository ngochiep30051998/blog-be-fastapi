

from typing import Generic, Optional, TypeVar, Any
from pydantic.generics import GenericModel

T = TypeVar('T')

class BaseResponse(GenericModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None