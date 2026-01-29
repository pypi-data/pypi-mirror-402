import os
import shutil
from .types import Type
from .logger import get_logger

log = get_logger()


def _is_dangerous_path(path: str) -> bool:
    path = os.path.abspath(path)

    dangerous = {
        os.path.abspath(os.sep),
        os.path.abspath("."),
        os.path.abspath(".."),
        os.path.expanduser("~"),
        os.getcwd()
    }

    if path in dangerous:
        return True

    # слишком короткий путь (например /data или C:\data)
    if len(path.split(os.sep)) < 3:
        return True

    return False


def create(obj_type: Type, name: str, path: str | None = None):
    full_path = name if path is None else os.path.join(path, name)

    if obj_type == Type.folder:
        os.makedirs(full_path, exist_ok=True)
        log.info(f"Folder created: {full_path}")
        return True

    if obj_type == Type.file:
        if path:
            os.makedirs(path, exist_ok=True)
        with open(full_path, "w"):
            pass
        log.info(f"File created: {full_path}")
        return True

    raise ValueError("Unknown type")


def exists(path: str) -> bool:
    result = os.path.exists(path)
    log.debug(f"Exists check: {path} -> {result}")
    return result


def rename(old_path: str, new_path: str):
    if not os.path.exists(old_path):
        log.warning(f"Rename failed, not found: {old_path}")
        return False

    parent = os.path.dirname(new_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    os.rename(old_path, new_path)
    log.info(f"Renamed: {old_path} -> {new_path}")
    return True


def delete(path: str, safe: bool = True):
    if not os.path.exists(path):
        log.warning(f"Delete failed, not found: {path}")
        return False

    if safe and _is_dangerous_path(path):
        log.warning(f"Dangerous path blocked: {path}")
        raise PermissionError("Dangerous path blocked by safe mode")

    if os.path.isfile(path):
        os.remove(path)
        log.info(f"File deleted: {path}")
        return True

    if os.path.isdir(path):
        shutil.rmtree(path)
        log.info(f"Folder deleted: {path}")
        return True

    return False