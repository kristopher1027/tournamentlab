"""Shared exceptions for TournamentLab."""


class TournamentError(Exception):
    """Base class for all TournamentLab domain errors."""


class ValidationError(TournamentError):
    """Raised when user input or loaded data violates a business rule."""


class FixtureError(TournamentError):
    """Raised for fixture-related rule violations (unknown/already played)."""