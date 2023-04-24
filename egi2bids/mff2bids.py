import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from shutil import copytree

import mne
import numpy as np
from mne_bids import (
    BIDSPath,
    make_dataset_description,
    update_sidecar_json,
    write_raw_bids,
)

from .utils._checks import _check_value
from .utils._logs import logger

# fmt:off
ch_names_egi = [
    "1", "F8", "3", "4", "F2", "6", "7", "8",
    "9", "AF8", "11", "AF4", "13", "14", "FCz", "16",
    "17", "FP2", "19", "20", "Fz", "22", "23", "FC1",
    "25", "FPz", "27", "28", "F1", "30", "31", "32",
    "33", "AF3", "35", "F3", "FP1", "38", "39", "40",
    "41", "FC3", "43", "C1", "45", "AF7", "F7", "F5",
    "FC5", "50", "51", "52", "53", "54", "55", "56",
    "57", "58", "C3", "60", "61", "FT7", "63", "C5",
    "65", "CP3", "FT9", "T9", "T7", "70", "71", "72",
    "73", "74", "75", "CP5", "77", "78", "CP1", "80",
    "81", "82", "83", "TP7", "85", "P5", "P3", "P1",
    "89", "CPz", "91", "92", "93", "TP9", "95", "P7",
    "PO7", "98", "99", "100", "Pz", "102", "103", "104",
    "105", "P9", "107", "108", "PO3", "110", "111", "112",
    "113", "114", "115", "O1", "117", "118", "POz", "120",
    "121", "122", "123", "124", "125", "Oz", "127", "128",
    "129", "130", "131", "132", "133", "134", "135", "136",
    "137", "138", "139", "PO4", "141", "P2", "CP2", "144",
    "145", "146", "147", "148", "149", "O2", "151", "152",
    "P4", "154", "155", "156", "157", "158", "159", "160",
    "PO8", "P6", "163", "CP4", "165", "166", "167", "168",
    "P10", "P8", "171", "CP6", "173", "174", "175", "176",
    "177", "178", "TP8", "180", "181", "182", "C4", "184",
    "C2", "186", "187", "188", "189", "TP10", "191", "192",
    "193", "C6", "195", "196", "197", "198", "199", "200",
    "201", "T8", "203", "204", "205", "FC4", "FC2", "208",
    "209", "T10", "FT8", "212", "FC6", "214", "215", "216",
    "217", "218", "FT10", "220", "221", "F6", "223", "F4",
    "225", "F10", "227", "228", "229", "230", "231", "232",
    "233", "234", "235", "236", "237", "238", "239", "240",
    "241", "242", "243", "244", "245", "246", "247", "248",
    "249", "250", "251", "F9", "253", "254", "255", "256",
    "Cz",
]


# fmt: on
def _extract_folder(file, dir=None):
    """Extracts a .mmf compressed folder to its original form"""
    # Get the path and file extension
    file = Path(file)
    ext = file.suffix
    _check_value(ext, (".tar", ".zip", ".mff"), "extension")
    # Dir
    if dir is None:
        dir = os.path.cwd()
    # Open the archive file based on its type
    if ext == ".tar":
        logger.info(f"Extracting zip archive {file} to {dir}")
        archive = tarfile.open(file)
        archive.extractall(dir)
        archive.close()

    elif ext == ".zip":
        logger.info(f"Extracting zip archive {file} to {dir}")
        archive = zipfile.ZipFile(file)
        archive.extractall(dir)
        archive.close()

    elif ext == ".mff":
        return file
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Check if archive contains mff subfolders
    for root, dirs, _ in os.walk(dir):
        if "Contents" in dirs:
            logger.info(f"mff file found in {root}")
            return Path(root)
    raise ('Archive does not contain a "Content" folder.')


def mff2bids(
    mff_source,
    bids_root,
    subject,
    session,
    task,
    run=None,
    event_id=None,
    line_frequency=50,
    save_source=False,
    overwrite=False,
    working_dir=None,
):
    with (
        working_dir
        if working_dir is not None
        else tempfile.TemporaryDirectory(suffix=".mff") as wd
    ):
        # mff_source
        logger.info(mff_source)
        # Extract
        mff_source = _extract_folder(mff_source, dir=wd)

        # BIDS path
        bids_root = Path(bids_root)
        bids_path = BIDSPath(root=bids_root)
        bids_path.update(
            subject=subject,
            session=session,
            task=task,
            datatype="eeg",
            run=run,
        )

        # load EEG data
        raw = mne.io.read_raw_egi(Path(mff_source), preload=True)
        raw.info["line_freq"] = line_frequency

        # rename channels
        new_chs = {}
        for i, ch in enumerate(raw.info["ch_names"]):
            if i > 256:
                break
            new_chs[ch] = ch_names_egi[i]
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

        # write BIDS
        write_raw_bids(
            raw,
            bids_path,
            format="BrainVision",
            events_data=events_data,
            event_id=event_id,
            allow_preload=True,
            overwrite=overwrite,
        )

        bpath = bids_path.copy()
        bpath.update(extension=".json")

        sidecar_dict = {
            "Manufacturer": "EGI",
            "EEGReference": "Cz",
            "InstitutionName": "Fondation Campus Biotech Geneva",
            "InstitutionalDepartmentName": "Human Neuroscience Platform - MEEG-BCI Facility",  # noqa: E501
            "DeviceSerialNumber": "HNP_GES400",
            "CapManufacturer": "EGI",
            "CapManufacturersModelName": "HydroCel GSN 256",
        }

        update_sidecar_json(bpath, sidecar_dict)
        make_dataset_description(
            path=bids_root, name="dataset_description.json", dataset_type="raw"
        )

        # save source
        if save_source:
            source_root = bids_root.joinpath("sourcedata")
            logger.info("Saving source data to %s", source_root)
            source_path = bids_path.copy()
            source_path.update(root=source_root)
            source_path = source_path.fpath.with_suffix(mff_source.suffix)
            copytree(mff_source, source_path, dirs_exist_ok=overwrite)
        return bids_root
