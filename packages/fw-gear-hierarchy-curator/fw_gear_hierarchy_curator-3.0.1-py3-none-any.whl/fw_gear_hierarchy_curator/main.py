"""Hierarchy curator main interface."""

import importlib
import logging
import sys
import typing as t
from pathlib import Path

from fw_curation.config import CurationConfig
from fw_curation.curator import HierarchyCurator
from fw_curation.walker import Walker
from fw_gear import GearContext

from . import Container

sys.path.insert(0, str(Path(__file__).parents[1]))

log = logging.getLogger(__name__)


def main(
    parent: Container,
    curator_path: Path,
    gear_context: GearContext,
    input_files: dict = {},
) -> int:
    """Curates a flywheel project using a curator.

    Args:
        parent (datatypes.Container): A flywheel container.
        curator_path (Path): A path to a curator module.
        input_files: Input files to be set on curator
    """
    log.info(f"Getting curator from {curator_path}")
    curator_cls, cfg = load_curator(curator_path)
    log.info(f"Curator config: {str(cfg)}")
    curator = curator_cls(config=cfg, context=gear_context, **input_files)
    walker = Walker.from_container(parent, config=cfg)
    return curator.curate(walker)


def load_curator(
    curator_path: Path,
) -> tuple[HierarchyCurator, t.Optional[CurationConfig]]:
    """Load curator from the file, return the module.

    Args:
        curator_path (Path): Path to curator script.

    Returns:
        HierarchyCurator: the curator loaded from the script
        t.Optional[CurationConfig]: the configuration to be used for curation
    """
    old_syspath = sys.path[:]
    try:
        sys.path.append(str(curator_path.parent))
        ## Investigate import statement
        mod = importlib.import_module(curator_path.name.split(".")[0])
        mod.filename = str(curator_path)
    finally:
        sys.path = old_syspath

    curator_cls = getattr(mod, "Curator")
    config = None
    try:
        config = mod.set_config()
    except AttributeError:
        log.info(
            f"No function `set_config` defined in {mod.filename}. "
            "Curator will use default configuration. "
            "To pass a config to the curator, define a `set_config` function "
            "that returns a `CurationConfig` in your curator script. See "
            "documentation for additional guidance."
        )

    return curator_cls, config
