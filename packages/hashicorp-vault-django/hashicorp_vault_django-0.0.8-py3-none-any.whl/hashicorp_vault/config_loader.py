import os
import yaml


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge override into base.
    Override values always win.
    """
    for k, v in override.items():
        if (
                k in base
                and isinstance(base[k], dict)
                and isinstance(v, dict)
        ):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def resolve_client(base_config: dict) -> Optional[str]:
    return (
            os.getenv("CLIENT")
            or base_config.get("client")
            or base_config.get("app", {}).get("client")
    )


def load_config(base_dir: str) -> dict:
    config_dir = os.path.join(base_dir, "config")
    base_path = os.path.join(config_dir, "application.yml")

    config = load_yaml(base_path) if os.path.exists(base_path) else {}

    client = resolve_client(config)

    if client:
        client_path = os.path.join(
            config_dir, f"application-{client}.yml"
        )
        if os.path.exists(client_path):
            client_cfg = load_yaml(client_path)
            config = deep_merge(config, client_cfg)

    config.setdefault("app", {})
    if "client" in config:
        config["app"]["client"] = config["client"]

    return config
