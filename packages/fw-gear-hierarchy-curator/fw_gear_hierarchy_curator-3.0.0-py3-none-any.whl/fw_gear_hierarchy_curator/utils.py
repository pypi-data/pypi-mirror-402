"""Utilities for running the curator."""

import ast
import importlib
import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import flywheel
from fw_gear import GearContext
from fw_gear.utils.wrapper.command import exec_command

log = logging.getLogger(__name__)


def update_analysis_label(destination, curator_path):
    """Update the analysis label to include the curator script name."""
    script_name = os.path.basename(curator_path)
    now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    analysis_label = f"hierarchy-curator - {script_name} - {now}"
    destination.update(label=analysis_label)


def install_latest_flywheel_sdk():
    """Reloading latest flywheel-sdk modules."""
    log.info("Installing latest flywheel-sdk")

    command = (
        f"{sys.executable} -m pip --disable-pip-version-check install -U flywheel-sdk"
    )
    args = shlex.split(command)
    exec_command(args)

    # Reload flywheel modules
    packages = [x for x in sys.modules.keys() if x.startswith("flywheel")]
    for m in packages:
        try:
            module = importlib.import_module(m)
            importlib.reload(module)
        except ModuleNotFoundError:
            pass


def init_fw_client(gear_context: GearContext) -> flywheel.Client:
    """Initialize flywheel client.

    Arguments:
        gear_context (GearToolkitContext): The gear context

    Returns:
        flywheel.Client: The flywheel client
    """
    # Access the flywheel API
    fw = gear_context.get_client()
    if not fw:
        raise RuntimeError("Failed to get Flywheel client from gear context")

    log.info("Initializing the Flywheel client")
    # Check user Info
    user_info = fw.get_current_user()

    log.info(
        "You are logged in as:\nFirstname: %s\nLastname: %s\nEmail: %s",
        user_info.firstname,
        user_info.lastname,
        user_info.email,
    )

    return fw


# This is for `from x import y` import statements, where x is flywheel_gear_toolkit
# (and flywheel_gear_toolkit submodules like flywheel_gear_toolkit.curator)
# and y is the IMPORT_MAPPING key.
IMPORT_MAPPING = {
    "HierarchyCurator": "from fw_curation.curator import HierarchyCurator",
    "LogRecord": "from fw_curation.reporters import DefaultLogRecord",
    "BaseLogRecord": "from pydantic import BaseModel",
    "GearToolkitContext": "from fw_gear import GearContext",
    "curator": "from fw_curation import curator",
}


def check_if_importing_from_gtk(node: ast.AST) -> list[str]:
    """Checks imports for `flywheel_gear_toolkit` and returns found incompatibilities.

    Args:
        node: An AST yielded by walking the ast tree

    Returns:
        list[str]: Messages to be logged about found incompatibilities
    """

    incompatibilities = []
    if isinstance(node, ast.Import):
        # ast.Import blocks are `import x` imports
        for im in node.names:
            if im.name == "flywheel_gear_toolkit":
                incompatibilities.append(
                    "`flywheel_gear_toolkit` is not supported by this version of "
                    "Hierarchy Curator. Please update to `fw_curation`. See "
                    "migration guide for additional details."
                )
    elif isinstance(node, ast.ImportFrom) and "flywheel_gear_toolkit" in str(
        node.module
    ):
        # ast.ImportFrom blocks are `from x import y` imports
        for im in node.names:
            if im.name in IMPORT_MAPPING:
                incompatibilities.append(
                    f"`{im.name}` import must be updated to `{IMPORT_MAPPING[im.name]}`."
                )
            else:
                incompatibilities.append(
                    "`flywheel_gear_toolkit` is not supported by this version of "
                    "Hierarchy Curator. Please update to `fw_curation`. See "
                    "migration guide for additional details."
                )
    return incompatibilities


def check_if_using_open_input(node: ast.AST) -> list[str]:
    """Checks for `self.open_input()` call.

    Args:
        node: An AST yielded by walking the ast tree

    Returns:
        list[str]: Messages to be logged about found incompatibilities
    """
    incompatibilities = []
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == "open_input"
    ):
        incompatibilities.append(
            "The thread-safe `open_input()` method has been renamed to `open()`. "
            "Please update python script to utilize `open()` instead of `open_input()`."
        )
    return incompatibilities


def check_if_extra_packages_arg(node: ast.AST) -> list[str]:
    """Checks for `extra_packages` arg being used in Curator init.

    Args:
        node: An AST yielded by walking the ast tree

    Returns:
        list[str]: Messages to be logged about found incompatibilities
    """
    incompatibilities = []
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        for kw in node.value.keywords:
            if kw.arg == "extra_packages":
                incompatibilities.append(
                    "Extra packages to install are now passed via a `requirements.txt` "
                    "file as `requirements` input to the Hierarchy Curator gear or by "
                    "defining `EXTRA_PACKAGES` as a global list. "
                    "Please update to remove `extra_packages` from the Curator init in favor "
                    "of either supplying a `requirements.txt` file or defining "
                    "`EXTRA_PACKAGES`."
                )
    return incompatibilities


def check_if_config_opts(node: ast.AST) -> list[tuple[str, Any]]:
    """Checks for `self.config.<opt>` being set in Curator init.

    Args:
        node: An AST yielded by walking the ast tree

    Returns:
        list[tuple[str, Any]]: List of tuples of config and values
    """
    config_opts = []
    if isinstance(node, ast.Assign):
        conf, val = None, None
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Attribute)
                and target.value.attr == "config"
            ):
                # Should be looking for `self.config`, NOT `config`
                # (in case user is using `config` as a variable separate from
                # the CuratorConfig configuration options)
                conf = target.attr
        if isinstance(node.value, ast.Constant):
            # Booleans, numerals, strings
            val = node.value.value
        elif isinstance(node.value, ast.Name):
            # i.e format = BaseLogRecord
            val = node.value.id
        if conf and val:
            # If either values are None, don't retain.
            config_opts.append((conf, val))
    return config_opts


def check_if_curator_subclass_init(node) -> tuple[list[str], Optional[str]]:
    """Checks Curator subclass and returns found incompatibilities.

    Args:
        node: An AST yielded by walking the ast tree

    Returns:
        list[str]: Messages to be logged about found incompatibilities
        Optional[str]: CurationConfig migration guide text, if applicable
    """
    incompatibilities = []
    config_opts = []
    config_opt_msg = None
    if isinstance(node, ast.ClassDef) and node.name == "Curator":
        for n in node.body:
            if isinstance(n, ast.FunctionDef) and n.name == "__init__":
                for sub_n in n.body:
                    incompatibilities.extend(check_if_extra_packages_arg(sub_n))
                    config_opts.extend(check_if_config_opts(sub_n))
    if config_opts:
        incompatibilities.append(
            "Curator configuration is now passed through the `CurationConfig` "
            "instead of being set in the `__init__()` with `self.config`. "
        )
        config_opt_msg = process_config_opts(config_opts)

    return incompatibilities, config_opt_msg


def process_config_opts(config_opts: list[tuple[str, Any]]) -> str:
    """Converts the config_opts list into a string to be used for informative logging.

    Args:
        config_opts: The config opts identified by check_if_config_opts

    Returns:
        str: A formatted log message to be used as a migration guide for CurationConfig
    """
    log_msg_start = (
        "In V3, curator configuration is passed through the "
        "`CurationConfig`. The following is a quick migration guide for how to "
        "translate the previous configuration options into `CurationConfig`. "
        "Please note that this automated guide does not cover all cases; "
        "refer to the documentation for additional detail:\n"
        "https://gitlab.com/flywheel-io/scientific-solutions/gears/hierarchy-curator/-/blob/main/README.md"
    )
    warns = []
    opts = []
    for conf, val in config_opts:
        if conf == "format" and val == "LogRecord":
            warns.append(
                "For a default log format, `LogRecord` has been replaced with "
                "`fw_curation.config.DefaultLogRecord`."
            )
            opts.append(f"{conf}=DefaultLogRecord,")
        elif conf == "format":
            warns.append(
                "Custom log formats must be updated to be a subclass of `pydantic.BaseModel` "
                "instead of a subclass of `BaseLogRecord`."
            )
            opts.append(f"{conf}={val},")
        elif conf == "multi":
            warns.append(
                "`multi` is no longer utilized in configuration. To utilize multithreading, "
                "set `workers` to a value greater than 0."
            )
            # DO NOT APPEND MULTI TO OPTS
        elif conf in [
            "workers",
            "depth_first",
            "reload",
            "callback",
            "report",
        ]:
            # These are ints, bools, functions, val should not be wrapped in quotes
            opts.append(f"{conf}={val},")
        elif conf in ["stop_level", "path"]:
            # These are strings, val must be wrapped in quotes
            opts.append(f"{conf}='{val}',")
        else:
            warns.append(f"Unknown config opt: {conf}")

    opt_str = "\n\t\t".join(opts)
    example = (
        "```\nfrom fw_curation.config import CurationConfig\n\n"
        f"def set_config():\n\treturn CurationConfig(\n\t\t{opt_str}\n\t)\n```"
    )

    log_msg_end = (
        "Additionally, new configuration options have been added to "
        "CurationConfig: `deserialize`, `exclude_analyses`, `exclude_files`, and "
        "`subject_warn_limit`. See documentation for more information. "
        "`deserialize=True` is recommended for scripts that utilize the Flywheel SDK."
    )

    config_log_msg = (
        f"{log_msg_start}\n{example}\nNotes: {' '.join(warns)}\n{log_msg_end}"
    )

    return config_log_msg


def check_script_version(input_script: Path) -> bool:
    """Checks input curation script for compatibility issues, logs findings.

    Args:
        input_script: Path to curator python script

    Returns:
        bool: Whether script appears compatible with V3
    """
    incompatibilities = []
    config_log_msg = None

    with open(input_script, "r", encoding="utf-8") as f:
        source_code = f.read()
    tree = ast.parse(source_code)

    for node in ast.walk(tree):
        incompatibilities.extend(check_if_importing_from_gtk(node))
        incompatibilities.extend(check_if_using_open_input(node))
        incompatibilities.extend(check_if_extra_packages_arg(node))
        init_incompatibilities, log_msg = check_if_curator_subclass_init(node)
        incompatibilities.extend(init_incompatibilities)
        if log_msg:
            config_log_msg = log_msg

    if incompatibilities:
        # TODO Update link to Hierarchy Curator migration guide when merged to main
        log.error(
            "Curation script not compatible with Hierarchy Curator version 3+. "
            "Please update script or use an older version of Hierarchy Curator."
            "See Hierarchy Curator Migration Guide for more details: "
            "https://gitlab.com/flywheel-io/scientific-solutions/gears/hierarchy-curator/-/blob/GEAR-2620-fw-curation-update/docs/migration_guide_v3.md"
        )
        for warn in incompatibilities:
            log.warning(warn)
        if config_log_msg:
            log.info(config_log_msg)
        return False

    return True


def handle_extra_packages(curator_path: Path):
    """Load curation script to look for EXTRA_PACKAGES, install if defined

    Args:
        curator_path (Path): Path to curator script.
    """
    old_syspath = sys.path[:]
    try:
        sys.path.append(str(curator_path.parent))
        mod = importlib.import_module(curator_path.name.split(".")[0])
        if hasattr(mod, "EXTRA_PACKAGES"):
            log.info("Installing extra packages defined in curator script...")
            cmd = [sys.executable, "-m", "pip", "install"]
            cmd.extend(mod.EXTRA_PACKAGES)
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                log.error(f"Failed to install extra packages: {e}")
                sys.exit(1)

    finally:
        sys.path = old_syspath
