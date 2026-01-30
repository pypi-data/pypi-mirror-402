import argparse
import json
import pathlib
import time
import yaml

DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".config" / "skyset" / "latest.yml"
DEFAULTS = {
    "_version": "1.0",
    "origin": "unknown",
    "updated_at": lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "message": "",
    "submessage": "",
    "source_will_update": False,
    "theme": {"mode": "system", "brightness": "light", "accent": "#E0584E"},
    "palette": {"primary": "#FF5733", "secondary": "#33C1FF", "tertiary": "#75FF33"},
    "gradients": {
        "background": ["#000000", "#222222", "#444444"],
        "hero": ["#FFFFFF", "#AAAAAA"],
    },
}

ARGUMENT_SPECS = [
    ("--config-file", {"dest": "config_file", "help": "Explicit config file"}),
    ("--message", {"help": "Override message text"}),
    ("--submessage", {"help": "Override submessage text"}),
    ("--origin", {"help": "Override origin identifier"}),
    ("--mode", {"choices": ["dark", "light", "system"], "help": "Theme mode"}),
    ("--accent", {"help": "Override accent color"}),
    ("--primary", {"help": "Override palette primary color"}),
    ("--secondary", {"help": "Override palette secondary color"}),
    ("--tertiary", {"help": "Override palette tertiary color"}),
    ("--background1", {"help": "Override background gradient stop #1"}),
    ("--background2", {"help": "Override background gradient stop #2"}),
    ("--background3", {"help": "Override background gradient stop #3"}),
    ("--hero1", {"help": "Override hero gradient stop #1"}),
    ("--hero2", {"help": "Override hero gradient stop #2"}),
    (
        "--source-will-update",
        {"dest": "source_will_update", "help": "Override source_will_update (true/false)"},
    ),
    ("--oneline", {"action": "store_true", "help": "Print a one-line summary"}),
    ("--json", {"action": "store_true", "help": "Print JSON"}),
    ("--status", {"action": "store_true", "help": "Alias for --json"}),
    ("-s", {"dest": "status", "action": "store_true"}),
]

TEXT_OVERRIDES = {
    "origin": ("origin",),
    "message": ("message",),
    "submessage": ("submessage",),
    "mode": ("theme", "mode"),
}

COLOR_OVERRIDES = {
    "accent": ("theme", "accent"),
    "primary": ("palette", "primary"),
    "secondary": ("palette", "secondary"),
    "tertiary": ("palette", "tertiary"),
}

GRADIENT_OVERRIDES = {
    "background1": ("background", 0),
    "background2": ("background", 1),
    "background3": ("background", 2),
    "hero1": ("hero", 0),
    "hero2": ("hero", 1),
}

def normalize_config_path(path: str |pathlib.Path | None) -> pathlib.Path:
    if path is None:
        return DEFAULT_CONFIG_PATH
    expanded = pathlib.Path(path).expanduser()
    if expanded == pathlib.Path.home() or expanded == pathlib.Path.home() / ".config":
        return DEFAULT_CONFIG_PATH
    if expanded == pathlib.Path.home() / ".config" / "skyset":
        return DEFAULT_CONFIG_PATH
    if expanded.is_dir():
        return expanded / "latest.yml"
    return expanded


def deep_copy_defaults() -> dict:
    return {
        **{k: (v() if callable(v) else v) for k, v in DEFAULTS.items() if k not in {"theme", "palette", "gradients"}},
        "theme": dict(DEFAULTS["theme"]),
        "palette": dict(DEFAULTS["palette"]),
        "gradients": {
            "background": list(DEFAULTS["gradients"]["background"]),
            "hero": list(DEFAULTS["gradients"]["hero"]),
        },
    }


def deep_merge(base: dict, incoming: dict) -> dict:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: pathlib.Path) -> dict:
    try:
        content = yaml.safe_load(path.read_text()) or {}
    except FileNotFoundError:
        content = {}
    return deep_merge(deep_copy_defaults(), content)


def save_config(config: dict, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config))


def set_path(config: dict, path: tuple[str, ...], value: str) -> None:
    cursor = config
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def parse_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}


def ensure_list_len(values: list[str], length: int) -> None:
    while len(values) < length:
        values.append("#000000")


def apply_overrides(config: dict, args: argparse.Namespace) -> bool:
    updated = False
    for arg_name, path in {**TEXT_OVERRIDES, **COLOR_OVERRIDES}.items():
        value = getattr(args, arg_name)
        if value is None:
            continue
        set_path(config, path, value)
        updated = True

    if args.source_will_update is not None:
        config["source_will_update"] = parse_bool(args.source_will_update)
        updated = True

    for arg_name, (field, index) in GRADIENT_OVERRIDES.items():
        value = getattr(args, arg_name)
        if value is None:
            continue
        values = config["gradients"][field]
        ensure_list_len(values, index + 1)
        values[index] = value
        updated = True

    return updated


def print_oneline(config: dict, path: pathlib.Path) -> None:
    print(
        "{path} | msg=\"{message}\" | accent={accent} | palette={primary},{secondary},{tertiary} | "
        "background={background} | hero={hero}".format(
            path=path,
            message=config.get("message", ""),
            accent=config.get("theme", {}).get("accent", ""),
            primary=config.get("palette", {}).get("primary", ""),
            secondary=config.get("palette", {}).get("secondary", ""),
            tertiary=config.get("palette", {}).get("tertiary", ""),
            background=",".join(config.get("gradients", {}).get("background", []) or []),
            hero=",".join(config.get("gradients", {}).get("hero", []) or []),
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Skyset config helper")
    parser.add_argument("path", nargs="?", help="Path to config file or directory")
    for flag, options in ARGUMENT_SPECS:
        parser.add_argument(flag, **options)
    args = parser.parse_args()

    config_path = normalize_config_path(args.config_file or args.path)
    config = load_config(config_path)
    updated = apply_overrides(config, args)
    if updated:
        save_config(config, config_path)
    if args.oneline:
        print_oneline(config, config_path)
        return
    if args.json or args.status or not updated:
        print(json.dumps(config, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()