class HelmTemplate:
    """Represents a Helm template (Kubernetes resource with Helm syntax).

    This class stores raw YAML content that contains Helm template directives.
    The content is NOT parsed until after Helm renders it - this preserves
    all template syntax including {{- if }}, {{- range }}, etc.
    """

    yaml_content: str

    def __init__(self, yaml_content: str) -> None:
        """Initialize a HelmTemplate instance.

        :arg yaml_content: Raw YAML content as a string (can contain Helm template directives).
        """
        self.yaml_content = yaml_content

    def __str__(self) -> str:
        """Return the raw YAML content."""
        return self.yaml_content

    def __repr__(self) -> str:
        """Return a representation of the HelmTemplate."""
        lines = self.yaml_content.strip().split("\n")
        preview = lines[0] if lines else ""
        return f"HelmTemplate(content={preview!r}...)"
