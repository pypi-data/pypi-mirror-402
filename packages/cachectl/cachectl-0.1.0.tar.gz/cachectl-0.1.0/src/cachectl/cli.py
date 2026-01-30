import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


MANAGERS = ["pnpm", "uv", "pip", "yarn", "npm", "poetry"]

ENV_MANAGERS = {
    "uv": "UV_CACHE_DIR",
    "pip": "PIP_CACHE_DIR",
    "poetry": "POETRY_CACHE_DIR",
}

NPMRC_KEYS = {
    "pnpm": "store-dir",
    "npm": "cache",
}


def normalize_path(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_windows() -> bool:
    return platform.system().lower().startswith("win")


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(argv: list[str]) -> None:
    if "--elevated" not in argv:
        argv = argv + ["--elevated"]

    if argv[0].endswith(".py"):
        exe = sys.executable
        args = [argv[0]] + argv[1:]
    else:
        exe = argv[0]
        args = argv[1:]

    quoted_args = ", ".join(["'" + a.replace("'", "''") + "'" for a in args])
    ps_command = (
        f"$argList = @({quoted_args}); "
        f"Start-Process -Verb RunAs -FilePath '{exe}' -ArgumentList $argList"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_command],
        check=False,
    )


def npmrc_path() -> Path:
    return Path.home() / ".npmrc"


def read_npmrc_key(key: str) -> str | None:
    path = npmrc_path()
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(key) and "=" in stripped:
            return stripped.split("=", 1)[1].strip() or None
    return None


def write_npmrc_key(key: str, value: str) -> Path:
    path = npmrc_path()
    lines = []
    replaced = False
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(key) and "=" in stripped:
            updated.append(f"{key}={value}")
            replaced = True
        else:
            updated.append(line)

    if not replaced:
        updated.append(f"{key}={value}")

    path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return path


def read_yarn_cache() -> str | None:
    yarnrc_yml = Path.home() / ".yarnrc.yml"
    yarnrc = Path.home() / ".yarnrc"

    if yarnrc_yml.exists():
        for line in yarnrc_yml.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("cacheFolder:"):
                value = stripped.split(":", 1)[1].strip().strip('"')
                return value or None

    if yarnrc.exists():
        for line in yarnrc.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("cache-folder"):
                parts = stripped.split(None, 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"') or None

    return None


def write_yarn_cache(value: str) -> Path:
    yarnrc_yml = Path.home() / ".yarnrc.yml"
    yarnrc = Path.home() / ".yarnrc"

    if yarnrc_yml.exists() or not yarnrc.exists():
        lines = []
        replaced = False
        if yarnrc_yml.exists():
            lines = yarnrc_yml.read_text(encoding="utf-8").splitlines()

        updated = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("cacheFolder:"):
                updated.append(f"cacheFolder: \"{value}\"")
                replaced = True
            else:
                updated.append(line)

        if not replaced:
            updated.append(f"cacheFolder: \"{value}\"")

        yarnrc_yml.write_text("\n".join(updated) + "\n", encoding="utf-8")
        return yarnrc_yml

    lines = []
    replaced = False
    if yarnrc.exists():
        lines = yarnrc.read_text(encoding="utf-8").splitlines()

    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("cache-folder"):
            updated.append(f"cache-folder \"{value}\"")
            replaced = True
        else:
            updated.append(line)

    if not replaced:
        updated.append(f"cache-folder \"{value}\"")

    yarnrc.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return yarnrc


def set_user_env_var_windows(name: str, value: str) -> None:
    import ctypes
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)

    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        SMTO_ABORTIFHUNG,
        2000,
        None,
    )


def read_user_env_var_windows(name: str) -> str | None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value) if value else None
    except FileNotFoundError:
        return None


def detect_profile_file() -> Path:
    shell = os.environ.get("SHELL", "").lower()
    home = Path.home()
    if "zsh" in shell:
        return home / ".zshrc"
    if "bash" in shell:
        return home / ".bashrc"
    return home / ".profile"


def set_user_env_var_posix(name: str, value: str) -> Path:
    profile_path = detect_profile_file()
    lines = []
    replaced = False
    if profile_path.exists():
        lines = profile_path.read_text(encoding="utf-8").splitlines()

    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"export {name}=") or stripped.startswith(f"{name}="):
            updated.append(f'export {name}="{value}"')
            replaced = True
        else:
            updated.append(line)

    if not replaced:
        updated.append(f'export {name}="{value}"')

    profile_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return profile_path


def read_user_env_var_posix(name: str) -> str | None:
    profile_path = detect_profile_file()
    if not profile_path.exists():
        return None
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"export {name}="):
            return stripped.split("=", 1)[1].strip().strip('"') or None
        if stripped.startswith(f"{name}="):
            return stripped.split("=", 1)[1].strip().strip('"') or None
    return None


def read_user_env_var(name: str) -> str | None:
    if is_windows():
        return read_user_env_var_windows(name)
    return read_user_env_var_posix(name)


def set_user_env_var(name: str, value: str) -> None:
    if is_windows():
        set_user_env_var_windows(name, value)
    else:
        set_user_env_var_posix(name, value)


def get_current_path(manager: str) -> str | None:
    if manager in ENV_MANAGERS:
        return read_user_env_var(ENV_MANAGERS[manager])
    if manager in NPMRC_KEYS:
        return read_npmrc_key(NPMRC_KEYS[manager])
    if manager == "yarn":
        return read_yarn_cache()
    return None


def set_manager_path(manager: str, new_path: Path) -> Path | None:
    if manager in ENV_MANAGERS:
        set_user_env_var(ENV_MANAGERS[manager], str(new_path))
        return None
    if manager in NPMRC_KEYS:
        return write_npmrc_key(NPMRC_KEYS[manager], new_path.as_posix())
    if manager == "yarn":
        return write_yarn_cache(new_path.as_posix())
    return None


def migrate_cache(old_path: Path, new_path: Path) -> bool:
    if not old_path.exists():
        return False
    if old_path.resolve() == new_path.resolve():
        return False
    ensure_dir(new_path)
    if new_path.exists() and any(new_path.iterdir()):
        print("Target path is not empty; skipping migration.")
        return False
    shutil.move(str(old_path), str(new_path))
    return True


def maybe_migrate(manager: str, new_path: Path, force: bool) -> None:
    current = get_current_path(manager)
    if not current:
        return
    try:
        old_path = normalize_path(current.strip().strip('"'))
    except Exception:
        return
    if old_path == new_path:
        return

    if not force:
        answer = input(
            f"Found existing cache at {old_path}. Migrate to {new_path}? (y/N): "
        ).strip()
        if answer.lower() != "y":
            return

    migrated = migrate_cache(old_path, new_path)
    if migrated:
        print("Migration completed.")


def query_all() -> None:
    for manager in MANAGERS:
        value = get_current_path(manager)
        print(f"{manager}: {value or '(not set)'}")


def interactive_menu() -> tuple[str, str | None]:
    print("Select what you want to configure:")
    print("1) pnpm")
    print("2) uv")
    print("3) pip")
    print("4) yarn")
    print("5) npm")
    print("6) poetry")
    print("7) query current settings")
    print("8) exit")
    choice = input("Enter choice (1-8): ").strip()

    mapping = {
        "1": "pnpm",
        "2": "uv",
        "3": "pip",
        "4": "yarn",
        "5": "npm",
        "6": "poetry",
    }

    if choice in mapping:
        path = input(f"{mapping[choice]} cache path: ").strip()
        return (mapping[choice], path or None)
    if choice == "7":
        return ("query", None)
    return ("exit", None)


def run_interactive() -> int:
    manager, path_str = interactive_menu()

    if manager == "exit":
        print("No changes made.")
        return 0
    if manager == "query":
        query_all()
        return 0
    if not path_str:
        print("No changes made.")
        return 0

    new_path = normalize_path(path_str)
    ensure_dir(new_path)
    maybe_migrate(manager, new_path, force=False)
    config_path = set_manager_path(manager, new_path)

    if config_path:
        print(f"Updated {manager} config in {config_path}")
    else:
        print(f"Updated {manager} cache path.")

    print("Done. You may need to restart your shell for changes to take effect.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure cache directories for common package managers."
    )
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set", help="Set cache path")
    set_parser.add_argument("manager", choices=MANAGERS)
    set_parser.add_argument("path")
    set_parser.add_argument("--migrate", action="store_true")

    get_parser = subparsers.add_parser("get", help="Get current cache path")
    get_parser.add_argument("manager", choices=MANAGERS)

    subparsers.add_parser("query", help="Query all cache paths")

    migrate_parser = subparsers.add_parser("migrate", help="Migrate cache to new path")
    migrate_parser.add_argument("manager", choices=MANAGERS)
    migrate_parser.add_argument("path")

    subparsers.add_parser("interactive", help="Run in interactive mode")

    return parser


def run_command(args: argparse.Namespace) -> int:
    if not args.command or args.command == "interactive":
        return run_interactive()

    if args.command == "query":
        query_all()
        return 0

    if args.command == "get":
        value = get_current_path(args.manager)
        print(value or "(not set)")
        return 0

    if args.command in {"set", "migrate"}:
        new_path = normalize_path(args.path)
        ensure_dir(new_path)
        migrate = args.command == "migrate" or args.migrate
        if migrate:
            maybe_migrate(args.manager, new_path, force=True)
        config_path = set_manager_path(args.manager, new_path)
        if config_path:
            print(f"Updated {args.manager} config in {config_path}")
        else:
            print(f"Updated {args.manager} cache path.")
        print("Done. You may need to restart your shell for changes to take effect.")
        return 0

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return run_command(args)
    except PermissionError:
        if is_windows() and not args.elevated and not is_admin():
            relaunch_as_admin(sys.argv)
            return 0
        raise


if __name__ == "__main__":
    raise SystemExit(main())
