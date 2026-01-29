import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .exceptions import HelmNotFoundError, RenderError
from .helm_chart import HelmChart
from .resource import KubernetesResource
from .template import HelmTemplate

_helm_executable_path: str | None = None


def _resolve_helm_path(given_path: str | Path) -> str:
    path_str = str(given_path)

    if not os.path.isdir(path_str):
        return path_str

    helm_filename = "helm.exe" if os.name == "nt" else "helm"
    return os.path.join(path_str, helm_filename)


def _validate_helm_path_exists(helm_path: str) -> None:
    if not os.path.exists(helm_path):
        raise ValueError(f"Helm executable not found at: {helm_path}")


def _validate_helm_path_executable(helm_path: str) -> None:
    if not os.access(helm_path, os.X_OK):
        raise ValueError(f"Helm executable is not executable: {helm_path}")


def _verify_helm_works(helm_path: str) -> None:
    try:
        subprocess.run(
            [helm_path, "version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError as e:
        raise RenderError(f"Helm binary not found at: {helm_path}") from e
    except subprocess.CalledProcessError as e:
        raise RenderError(f"Helm check failed at {helm_path}: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise RenderError(f"Helm version check timed out at {helm_path}") from e


def set_helm_executable_path(path: str | Path) -> None:
    """Set the path to the Helm executable.

    This allows you to specify a custom directory or full path where the Helm
    binary is located. This is useful in environments where Helm is not in the
    system PATH.

    :arg path: Full path to Helm executable or directory containing it.
    :type path: str | Path
    :raises ValueError: If the path does not exist or is not executable.
    :raises RenderError: If Helm cannot be found at the specified path.
    """
    global _helm_executable_path

    full_path = _resolve_helm_path(path)
    _validate_helm_path_exists(full_path)
    _validate_helm_path_executable(full_path)
    _verify_helm_works(full_path)

    _helm_executable_path = full_path


def get_helm_executable_path() -> str:
    """Get the Helm executable path (custom or default).

    :returns: The path to the Helm executable to use.
    :rtype: str
    """
    if _helm_executable_path:
        return str(_helm_executable_path)
    return "helm"


def reset_helm_executable_path() -> None:
    """Reset the Helm executable path to the system default.

    This is useful for testing or when you want to revert to using the Helm
    binary from the system PATH.
    """
    global _helm_executable_path
    _helm_executable_path = None


def _check_helm_installed() -> None:
    """Check if Helm is installed and available in PATH.

    :raises HelmNotFoundError: If Helm is not found.
    """
    helm_cmd = get_helm_executable_path()

    try:
        subprocess.run(
            [helm_cmd, "version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError as e:
        raise HelmNotFoundError("Helm binary not found. Please install Helm.") from e
    except subprocess.CalledProcessError as e:
        raise HelmNotFoundError(f"Helm check failed: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise HelmNotFoundError("Helm version check timed out") from e


def _get_or_create_chart_path(helm_chart: HelmChart | HelmTemplate) -> tuple[str, bool]:
    if isinstance(helm_chart, HelmChart) and helm_chart.path:
        return helm_chart.path, False
    return _create_temp_chart(helm_chart), True


def _write_values_to_temp_file(values: dict[str, Any]) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as values_file:
        yaml.dump(values, values_file)
        return values_file.name


def _run_helm_template(
    helm_cmd: str,
    release_name: str,
    chart_path: str,
    namespace: str,
    values_file_path: str,
) -> str:
    result = subprocess.run(
        [
            helm_cmd,
            "template",
            release_name,
            chart_path,
            f"--namespace={namespace}",
            f"--values={values_file_path}",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RenderError(f"Helm rendering failed: {result.stderr}")

    return result.stdout


def _cleanup_temporary_files(values_file_path: str, chart_path: str, is_temp_chart: bool) -> None:
    Path(values_file_path).unlink(missing_ok=True)
    if is_temp_chart:
        shutil.rmtree(chart_path, ignore_errors=True)


def render_chart(
    helm_chart: HelmChart | HelmTemplate,
    values: dict[str, Any] | None = None,
    release_name: str = "test-release",
    namespace: str = "default",
) -> list[KubernetesResource]:
    """Render a Helm chart or template and return a list of Kubernetes resources.

    :arg helm_chart: HelmChart or HelmTemplate instance to render.
    :arg values: Dictionary of values to pass to the chart/template.
    :arg release_name: Name of the Helm release (default: "test-release").
    :arg namespace: Kubernetes namespace for the resources (default: "default").
    :returns: List of KubernetesResource objects.
    :raises HelmNotFoundError: If Helm is not installed.
    :raises RenderError: If rendering fails.
    """
    _check_helm_installed()

    if values is None:
        values = {}

    helm_cmd = get_helm_executable_path()

    try:
        chart_path, is_temp_chart = _get_or_create_chart_path(helm_chart)
        values_file_path = _write_values_to_temp_file(values)

        try:
            rendered_output = _run_helm_template(
                helm_cmd,
                release_name,
                chart_path,
                namespace,
                values_file_path,
            )
            resources = _parse_rendered_output(rendered_output)
        finally:
            _cleanup_temporary_files(values_file_path, chart_path, is_temp_chart)

    except subprocess.TimeoutExpired as e:
        raise RenderError("Helm rendering timed out") from e
    except Exception as e:
        if isinstance(e, RenderError | HelmNotFoundError):
            raise
        raise RenderError(f"Unexpected error during rendering: {e}") from e

    return resources


def _write_chart_yaml(temp_dir: str, yaml_content: str) -> None:
    chart_yaml_path = Path(temp_dir) / "Chart.yaml"
    with open(chart_yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)


def _create_templates_directory(temp_dir: str) -> None:
    templates_dir = Path(temp_dir) / "templates"
    templates_dir.mkdir(exist_ok=True)


def _create_temp_chart(helm_chart: HelmChart | HelmTemplate) -> str:
    temp_dir = tempfile.mkdtemp()

    try:
        if isinstance(helm_chart, HelmTemplate):
            minimal_chart_yaml = """apiVersion: v2
name: temp-chart
version: 1.0.0
description: Temporary chart for template rendering
"""
            _write_chart_yaml(temp_dir, minimal_chart_yaml)
            _create_templates_directory(temp_dir)

            templates_dir = Path(temp_dir) / "templates"
            template_file = templates_dir / "template.yaml"
            with open(template_file, "w", encoding="utf-8") as f:
                f.write(helm_chart.yaml_content)
        else:
            if helm_chart.yaml_content is None:
                raise RenderError("HelmChart must have yaml_content to create temporary chart")
            _write_chart_yaml(temp_dir, helm_chart.yaml_content)
            _create_templates_directory(temp_dir)

        return temp_dir

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RenderError(f"Failed to create temporary chart: {e}") from e


def _split_yaml_documents(yaml_output: str) -> list[str]:
    return yaml_output.split("---")


def _is_non_empty_document(doc: str) -> bool:
    return bool(doc.strip())


def _parse_yaml_document(doc: str) -> Any:
    try:
        return yaml.safe_load(doc)
    except yaml.YAMLError as e:
        raise RenderError(f"Failed to parse resource YAML: {e}") from e


def _create_resource_from_data(data: Any) -> KubernetesResource | None:
    if isinstance(data, dict):
        return KubernetesResource(data)
    return None


def _parse_rendered_output(yaml_output: str) -> list[KubernetesResource]:
    resources = []

    try:
        documents = _split_yaml_documents(yaml_output)

        for doc in documents:
            if not _is_non_empty_document(doc):
                continue

            data = _parse_yaml_document(doc.strip())
            resource = _create_resource_from_data(data)

            if resource:
                resources.append(resource)

    except RenderError:
        raise
    except Exception as e:
        raise RenderError(f"Failed to parse rendered output: {e}") from e

    return resources
