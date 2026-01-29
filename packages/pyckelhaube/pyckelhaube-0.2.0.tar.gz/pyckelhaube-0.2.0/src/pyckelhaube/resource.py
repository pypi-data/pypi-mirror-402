from typing import Any


class AttrDict(dict):
    """A fluent-friendly dict-like class."""

    def __getattr__(self, name: str) -> Any:
        """Get an item as an attribute (like d.name instead of d['name']).

        :returns: The value associated with the attribute name.
        :rtype: Any
        :raises AttributeError: Attribute does not exist.
        """
        try:
            value = self[name]

            if isinstance(value, dict) and not isinstance(value, AttrDict):
                value = AttrDict(value)
                self[name] = value

            elif isinstance(value, list):
                value = [
                    (
                        AttrDict(item)
                        if isinstance(item, dict) and not isinstance(item, AttrDict)
                        else item
                    )
                    for item in value
                ]
                self[name] = value
            return value
        except KeyError as e:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'") from e

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an item as an attribute.

        :arg name: Attribute name.
        :arg value: Value to set.
        """
        self[name] = value

    def __delattr__(self, name: str) -> None:
        """Delete an item as an attribute.

        :arg name: Attribute name.
        """
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'") from e


class KubernetesResource(AttrDict):
    """Represents a Kubernetes resource with attribute access to fields."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """Initialize a KubernetesResource.

        :arg data: Dictionary representation of the Kubernetes resource.
        :type data: Optional[dict]
        """
        if data is None:
            data = {}

        super().__init__(data)
