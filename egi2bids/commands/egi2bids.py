import argparse

from .. import mff2bids
from ..utils._logs import logger


def run():
    """Run egi2bids() command."""
    parser = argparse.ArgumentParser(
        prog=f"{__package__.split('.')[0]}",
        description="EGI to BIDS CLI converter.",
    )
    parser.add_argument(
        "mff_source",
        type=str,
        help=(
            "path to the input mff file. "
            "Can be a '.mff' folder or a '.mff.tar', "
            "or '.mff.zip' archive."
        ),
    )
    parser.add_argument(
        "bids_root",
        type=str,
        help="path to the BIDS root.",
    )
    parser.add_argument(
        "-sub",
        "--subject",
        type=str,
        metavar="str",
        help="Subject ID.",
        required=True,
    )
    parser.add_argument(
        "-ses",
        "--session",
        type=str,
        metavar="str",
        help="Session ID (int).",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--task",
        type=str,
        metavar="str",
        help="Task.",
        required=True,
    )
    parser.add_argument(
        "-run",
        "--run",
        type=int,
        metavar="int",
        help="Run ID (int).",
        required=True,
    )
    parser.add_argument(
        "--save_source",
        action="store_true",
        help="Either or not to save sourcedata.",
        required=False,
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrites existing data.",
        required=False,
    ),
    parser.add_argument(
        "-log",
        "--loglevel",
        default="warning",
        help="Provide logging level.",
    )

    args = parser.parse_args()

    logger.set_log_level(level=args.loglevel.upper())

    mff2bids(
        mff_source=args.mff_source,
        bids_root=args.bids_root,
        subject=args.subject,
        task=args.task,
        session=args.session,
        run=args.run,
        save_source=args.save_source,
        overwrite=args.overwrite,
    )
