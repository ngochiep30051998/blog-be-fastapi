from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Slug:
    """URL-friendly slug value object"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_slug(self.value):
            raise ValueError(f"Invalid slug: {self.value}")
    
    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return re.match(pattern, slug) is not None
    
    def __str__(self) -> str:
        return self.value