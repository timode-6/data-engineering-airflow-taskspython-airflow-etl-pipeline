from __future__ import annotations

from abc import ABC, abstractmethod


class ReportQuery(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def sql(self) -> str:
        pass

    def __repr__(self) -> str:  
        return f"<{type(self).__name__} {self.name}>"


class SqlReportQuery(ReportQuery):

    NAME: str = ""
    SQL: str = ""

    @property
    def name(self) -> str:
        return self.NAME

   
    @property
    def sql(self) -> str:
        return self.SQL
