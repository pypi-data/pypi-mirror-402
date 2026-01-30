import os
from imputegap.tools import utils

def clean_imputegap_assets(root_path, security=True, check="imputegap/imputegap_assets"):
    """
    Delete all files under the imputegap assets directory, preserving only `.gitkeep` files.

    Parameters
    ----------
    root_path : str or Path-like
        Path to the root imputegap assets directory to be cleaned.

    security : bool, optional
        If True, abort cleaning unless `check` is found in `root_path`.
        This is a safety guard to avoid accidentally deleting unintended paths.
        Default is True.

    check : str, optional
        Substring that must be present in `root_path` for the cleaning to proceed.
        Default is "imputegap/imputegap_assets".
    """
    from pathlib import Path

    print("Cleaning imputegap assets...", root_path, "\n")

    root_path_p = Path(root_path).resolve()

    if security:
        if check not in root_path:
            print(f"[ABORT] Refusing to clean '{root_path}'.")
            print(f"The target directory's must have '{check}' in it.")
            return

    # Walk through all files under root_dir
    for path in root_path_p.rglob("*"):
        if path.is_file():
            # Keep only .gitkeep files
            if path.name == ".gitkeep":
                continue
            try:
                path.unlink()
                print(f"Deleted: {path}")
            except Exception as e:
                print(f"Failed to delete {path}: {e}")


here = os.path.dirname(os.path.abspath(__file__))
delete_path = os.path.join(here, "imputegap_assets")
clean_imputegap_assets(delete_path)