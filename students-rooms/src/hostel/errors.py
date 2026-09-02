from __future__ import annotations


class HostelError(Exception):
    """Base class for every error raised by this application."""


class ConfigurationError(HostelError):
    """Invalid or missing configuration."""


class SourceError(HostelError):
    """The input file is missing, unreadable or malformed."""


class MappingError(HostelError):
    """A record from the input file cannot be mapped onto a domain object."""


class DatabaseError(HostelError):
    """Any failure reported by the database driver."""


class DuplicateObjectError(DatabaseError):
    """DDL tried to create an object (index, table) that already exists."""


class UnknownObjectError(DatabaseError):
    """DDL tried to drop an object that does not exist."""


class UnsupportedFormatError(HostelError):
    """No exporter is registered for the requested output format."""
