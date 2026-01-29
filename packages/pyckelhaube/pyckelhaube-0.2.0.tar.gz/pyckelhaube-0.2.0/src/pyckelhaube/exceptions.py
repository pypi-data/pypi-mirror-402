class PyckelhaubeError(Exception):
    """Base exception for all pyckelhaube errors."""

    pass


class InvalidChartError(PyckelhaubeError):
    """Raised when a Helm chart is invalid or malformed."""

    pass


class HelmChartError(PyckelhaubeError):
    """Raised when there's an error with Helm chart operations."""

    pass


class RenderError(PyckelhaubeError):
    """Raised when rendering a Helm chart fails."""

    pass


class HelmNotFoundError(PyckelhaubeError):
    """Raised when Helm binary is not found or not available."""

    pass
