from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.models import JobPosting


class BaseCollector(ABC):
    source: str

    @abstractmethod
    def collect(self, query: str = "", max_pages: int = 1) -> List[JobPosting]:
        raise NotImplementedError
