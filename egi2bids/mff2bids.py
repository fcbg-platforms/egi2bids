import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from shutil import copytree
from typing import Union

import mne
import numpy as np
from mne_bids import (
    BIDSPath,
    make_dataset_description,
    update_sidecar_json,
    write_raw_bids,
)

from .constants import _CH_NAMES_EGI
from .utils._checks import check_value, ensure_path
from .utils.logs import logger, verbose


def _extract_folder(file: Union[str, Path], dir_: Union[str, Path] = None) -> Path:
    """Extract a .mff compressed folder to its original form."""
    # check paths and file extension
    file = ensure_path(file, must_exist=True)
    ext = file.suffix
    check_value(ext, (".tar", ".zip", ".mff"), "extension")
    dir_ = Path.cwd() if dir_ is None else dir_
    dir_ = ensure_path(dir_, must_exist=True)
    # open the archive if needed
    archive_readers = {
        ".tar": tarfile.open,
        ".zip": zipfile.ZipFile,
    }
    if ext in (".tar", ".zip"):
        logger.info("Extracting '%s' archive %s to %s.", ext, file, dir_)
        with archive_readers[ext](file, "r") as archive:
            archive.extractall(dir_)
        for root, dirs, _ in os.walk(dir_):
            if "Contents" in dirs:
                logger.info("MFF file found in %s", root)
                return Path(root)
        else:
            raise (f"The '{ext}' archive does not contain a 'Content' folder.")

    elif ext == ".mff":
        return file


@verbose
def mff2bids(
    mff_source: Union[str, Path],
    bids_root: Union[str, Path],
    subject,
    session,
    task,
    run=None,
    event_id=None,
    save_source: bool = False,
    working_dir=None,
    *,
    overwrite: bool = False,
    verbose=None,
):
    logger.info("Processing %s", mff_source)
    working_dir = (
        tempfile.TemporaryDirectory(suffix=".mff")
        if working_dir is None
        else working_dir
    )
    with working_dir as wd:
        mff_source = _extract_folder(mff_source, dir_=wd)

        # BIDS root
        bids_root = ensure_path(bids_root, must_exist=False)
        eeg_bids_path = BIDSPath(
            root=bids_root,
            subject=subject,
            session=session,
            task=task,
            datatype="eeg",
            run=run,
        )
        # JSON sidecar path
        json_bids_path = eeg_bids_path.copy()
        json_bids_path.update(extension=".json")
        # Source path.
        if save_source:
            source_bids_root = bids_root.joinpath("sourcedata")
            logger.info("Saving source data to %s", source_bids_root)
            source_bids_path = eeg_bids_path.copy()
            source_bids_path.update(root=source_bids_root)
            source_bids_path = source_bids_path.fpath.with_suffix(mff_source.suffix)
            if source_bids_path.exists() and overwrite is False:
                raise ValueError(
                    f"Cannot write source data. Source data {source_bids_path}"
                    "already exists but overwrite is set to False."
                )

        # load EEG data
        raw = mne.io.read_raw_egi(mff_source, preload=True)
        raw.info["line_freq"] = 50  # Hz, hard-coded for campus biotech/Europe.

        # rename channels
        new_chs = dict()
        for i, ch in enumerate(raw.info["ch_names"]):
            if i > 256:
                break
            new_chs[ch] = _CH_NAMES_EGI[i]
        raw.rename_channels(new_chs)

        # find events in stim channel
        stim_channel = "STI 014"
        if stim_channel in raw.ch_names:
            events_data = mne.find_events(raw, stim_channel=stim_channel)
            # if event_id are not provided
            if event_id is None:
                event_ids = np.unique(events_data[:, 2])
                event_id = {}
                for event in event_ids:
                    event_id[f"Unkown_{event}"] = event
            # TODO: check is provided events match events_data
        else:
            events_data = None
            event_id = None

        # update sidecar json
        sidecar_dict = {
            "Manufacturer": "EGI",
            "EEGReference": "Cz",
            "InstitutionName": "Fondation Campus Biotech Geneva",
            "InstitutionalDepartmentName": "Human Neuroscience Platform - MEEG-BCI Facility",  # noqa: E501
            "DeviceSerialNumber": "HNP_GES400",
            "CapManufacturer": "EGI",
            "CapManufacturersModelName": "HydroCel GSN 256",
        }

        # write eeg
        write_raw_bids(
            raw,
            eeg_bids_path,
            format="BrainVision",
            events_data=events_data,
            event_id=event_id,
            allow_preload=True,
            overwrite=overwrite,
        )
        update_sidecar_json(json_bids_path, sidecar_dict)
        make_dataset_description(
            path=bids_root, name="dataset_description.json", dataset_type="raw"
        )
        # write source
        if save_source:
            copytree(mff_source, source_bids_path, dirs_exist_ok=overwrite)

    return bids_root
