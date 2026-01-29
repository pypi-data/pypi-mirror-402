"""Flywheel gear context parser."""

import logging
import sys
import typing as t
from pathlib import Path

from fw_gear import GearContext
from fw_gear.utils.utils_helpers import install_requirements

from fw_gear_hierarchy_curator.utils import (
    check_script_version,
    handle_extra_packages,
    install_latest_flywheel_sdk,
)

log = logging.getLogger(__name__)


def parse_config(gear_context: GearContext) -> tuple[t.Any, Path, dict]:
    """Parse gear config.

    Args:
        gear_context (fw_gear.GearContext): context

    Returns:
        (tuple): tuple containing
            - parent container
            - curator path
            - dictionary of input files
    """
    analysis_id = gear_context.config.destination["id"]
    analysis = gear_context.client.get_analysis(analysis_id)

    get_parent_fn = getattr(gear_context.client, f"get_{analysis.parent.type}")
    parent = get_parent_fn(analysis.parent.id)

    curator_path = gear_context.config.get_input_path("curator")
    if not curator_path:
        log.error("No curation script provided. Exiting.")
        sys.exit(1)
    v3_check = check_script_version(curator_path)
    if not v3_check:
        # Logging happens in check_script_version
        sys.exit(1)

    input_file_one = gear_context.config.get_input_path("additional-input-one")
    input_file_two = gear_context.config.get_input_path("additional-input-two")
    input_file_three = gear_context.config.get_input_path("additional-input-three")
    input_files = {
        "additional_input_one": input_file_one,
        "additional_input_two": input_file_two,
        "additional_input_three": input_file_three,
    }

    # Install and update packages:

    # Check for EXTRA_PACKAGES global in script
    handle_extra_packages(Path(curator_path))

    # Install requirements.txt if input
    requirements = gear_context.config.get_input_path("requirements")
    if requirements:
        install_requirements(requirements)

    # Update Flywheel SDK if configured
    update_sdk = gear_context.config.opts.get("install-latest-flywheel-sdk", False)
    if update_sdk:
        install_latest_flywheel_sdk()

    return parent, Path(curator_path), input_files
