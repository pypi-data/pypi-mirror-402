import os
import re
from typing import Any

import yaml

from .exceptions import HelmChartError, InvalidChartError


class HelmTemplatePreservingLoader(yaml.SafeLoader):
    """Custom YAML loader that preserves Helm template directives."""

    pass


def _helm_template_constructor(loader: Any, node: Any) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return node


HelmTemplatePreservingLoader.add_implicit_resolver(
    "tag:yaml.org,2002:str",
    re.compile(r".*\{\{.*\}\}.*", re.DOTALL),
    None,
)


class HelmChart:
    """Represents a Helm chart loaded from file or YAML string."""

    path: str | None
    yaml_content: str | None
    _chart_data: dict[str, Any]

    def __init__(
        self,
        path: str | None = None,
        yaml_content: str | None = None,
    ) -> None:
        """Initialize a HelmChart instance.

        :arg path: Path to the chart.yaml file.
        :arg yaml_content: YAML content as a string.
        :raises HelmChartError: If neither path nor yaml_content is provided.
        :raises InvalidChartError: If the chart YAML is invalid or missing required fields.
        """
        if path is None and yaml_content is None:
            raise HelmChartError("Either 'path' or 'yaml_content' must be provided")

        if path is not None and yaml_content is not None:
            raise HelmChartError("Cannot provide both 'path' and 'yaml_content'")

        self.path = path
        self.yaml_content = yaml_content
        self._chart_data = {}

        self._parse_chart()

    def _parse_chart(self) -> None:
        try:
            if self.path:
                if not os.path.exists(self.path):
                    raise InvalidChartError(f"Chart file not found: {self.path}")

                with open(self.path, encoding="utf-8") as f:
                    yaml_content_str: str = f.read()
            else:
                yaml_content_str = self.yaml_content if self.yaml_content else ""

            loaded_data = yaml.load(yaml_content_str, Loader=HelmTemplatePreservingLoader)
            self._chart_data = loaded_data

            self._validate_deserialised_chart_type()
            self._validate_required_resources_fields()

        except yaml.YAMLError as e:
            raise InvalidChartError(f"Failed to parse chart YAML: {e}") from e

    def _validate_deserialised_chart_type(self) -> None:
        if not isinstance(self._chart_data, dict):
            raise InvalidChartError("Chart YAML must be a valid YAML mapping")

    def _validate_required_resources_fields(self) -> None:
        if "apiVersion" not in self._chart_data:
            raise InvalidChartError("Chart is missing required 'apiVersion' field")

        if "name" not in self._chart_data:
            raise InvalidChartError("Chart is missing required 'name' field")

        if "version" not in self._chart_data:
            raise InvalidChartError("Chart is missing required 'version' field")

    @property
    def chart_data(self) -> dict[str, Any]:
        """Get the full chart data as a dictionary."""
        return self._chart_data

    @property
    def name(self) -> Any:
        """Get the chart name."""
        return self._chart_data.get("name")

    @property
    def version(self) -> Any:
        """Get the chart version."""
        return self._chart_data.get("version")

    @property
    def api_version(self) -> Any:
        """Get the chart API version."""
        return self._chart_data.get("apiVersion")
