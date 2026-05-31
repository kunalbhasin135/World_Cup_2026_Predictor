"""Domain exceptions raised by services and mapped to HTTP errors in routes."""


class ServiceError(Exception):
    """Base class for service-layer errors."""


class TeamNotFoundError(ServiceError):
    def __init__(self, team_name: str) -> None:
        self.team_name = team_name
        super().__init__(f"Team not found: {team_name}")


class InvalidMatchupError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
