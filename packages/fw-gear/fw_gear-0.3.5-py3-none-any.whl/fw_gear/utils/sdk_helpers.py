import logging
import typing as t

if t.TYPE_CHECKING:
    import flywheel

TOP_DOWN_PARENT_HIERARCHY = ["group", "project", "subject", "session", "acquisition"]
BOTTOM_UP_PARENT_HIERARCHY = list(reversed(TOP_DOWN_PARENT_HIERARCHY))

log = logging.getLogger(__name__)


def get_container_from_ref(client: "flywheel.Client", ref: dict):
    """Returns the container from its reference.

    Args:
        client: Authenticated Flywheel SDK client
        ref: A dictionary with type and id keys defined.

    Returns:
        Container: A flywheel container.
    """
    container_type = ref.get("type")
    getter = getattr(client, f"get_{container_type}")
    return getter(ref.get("id"))


def get_parent(client: "flywheel.Client", container):
    """Returns parent container of container input."""
    if container.container_type == "analysis":
        return get_container_from_ref(client, container.parent)
    elif container.container_type == "file":
        return container.parent
    elif container.container_type == "group":
        raise TypeError("Group container does not have a parent.")
    else:
        for cont_type in BOTTOM_UP_PARENT_HIERARCHY:
            if not container.parents.get(cont_type):
                # not defined, parent must be up the hierarchy
                continue
            return get_container_from_ref(
                client, {"type": cont_type, "id": container.parents.get(cont_type)}
            )


def setup_gear_run(
    client: "flywheel.Client", gear_name: str, gear_args: dict
) -> t.Tuple["flywheel.GearDoc", dict, dict]:
    """Setup gear run for a specified gear with provided gear arguments.

    Args:
        client (flywheel.Client): Authenticated Flywheel SDK client.
        gear_name (str): Name of the gear to run.
        gear_args (dict): Dictionary of gear inputs and configuration.

    Raises:
        ValueError: If the specified gear does not exist.
        ValueError: If a required input / configuration for the gear is missing.

    Returns:
        Tuple: A tuple containing an object of the gear document, input dictionary, and configuration dictionary.
    """

    geardoc = client.gears.find_first(f"gear.name={gear_name}")
    if geardoc is None:
        raise ValueError(f"Gear {gear_name} does not exist.")

    # Gear Input Setup
    input_args_template = geardoc.gear.get("inputs").copy()
    input_args_template.pop("api-key", None)

    input_dict = {}

    for k, v in gear_args.items():
        if k in input_args_template:
            input_dict[k] = v

    for input_key, val in input_args_template.items():
        if not val["optional"] and input_key not in input_dict:
            raise ValueError(f"Missing required input for {gear_name}: {input_key}.")

    # Gear Configuration Setup
    geardoc_config = geardoc.gear.get("config")

    config_dict = {}
    for config_key, key_info in geardoc_config.items():
        config_default_val = key_info.get("default")
        config_dict[config_key] = (
            gear_args[config_key]
            if config_key in gear_args.keys()
            else config_default_val
        )
        if "optional" in key_info.keys() and not key_info.get("optional"):
            # Check required config is not empty or None
            if not config_dict[config_key]:
                raise ValueError(
                    f"{gear_name}'s {config_key} config should be provided prior to running."
                )

    return geardoc, input_dict, config_dict
