import os
import os.path as op
import shutil
import tarfile
import zipfile
from pathlib import Path

import pytest
from bids.layout import BIDSLayout
from mne.datasets import testing

from egi2bids.mff2bids import mff2bids

base_dir = Path(op.join(op.dirname(op.abspath(__file__)), "data"))
testing_path = testing.data_path(download=True)
egi_path = testing_path / "EGI"
egi_mff_path = egi_path / "test_egi.mff"


@pytest.fixture(scope="session")
def make_output_path_zip(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("data")
    # ZIP
    output_path_zip = base_dir / "archive_flat"
    output_path_zip = shutil.make_archive(output_path_zip, "zip", egi_mff_path)
    return output_path_zip


@pytest.fixture(scope="session")
def make_output_path_zip_folder(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("data")
    # ZIP Folder
    output_path_zip_folder = base_dir / "archive_folder.mff.zip"
    with zipfile.ZipFile(
        output_path_zip_folder, "w", compression=zipfile.ZIP_DEFLATED
    ) as zipf:
        for root, dirs, files in os.walk(egi_mff_path):
            for file in files:
                zipf.write(
                    op.join(root, file),
                    op.join(
                        "archive_folder.mff",
                        op.relpath(op.join(root, file), egi_mff_path),
                    ),
                )
    return output_path_zip_folder


@pytest.fixture(scope="session")
def make_output_path_tar(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("data")
    # TAR
    output_path_tar = base_dir / "archive_flat"
    output_path_tar = shutil.make_archive(output_path_tar, "tar", egi_mff_path)
    return output_path_tar


@pytest.fixture(scope="session")
def make_output_path_tar_folder(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("data")
    # TAR folder
    output_path_tar_folder = base_dir / "archive_folder.mff.tar"
    with tarfile.open(output_path_tar_folder, "w") as tar:
        tar.add(egi_mff_path, arcname="archive_folder.mff")
    return output_path_tar_folder


@pytest.mark.parametrize(
    "file",
    [
        "make_output_path_zip",
        "make_output_path_zip_folder",
        "make_output_path_tar",
        "make_output_path_tar_folder",
    ],
)
def test_file_conversion(tmp_path, file, request):
    # create temporary directory and file for testing
    bids_path = tmp_path / "bids"
    # file
    file = request.getfixturevalue(file)
    bids_root = mff2bids(
        file,
        bids_path,
        "test",
        "test",
        "test",
        run=1,
        event_id=None,
        save_source=False,
        overwrite=False,
    )
    assert BIDSLayout(bids_root, validate=True)


def test_mff2bids_save_source(tmp_path):
    bids_path = tmp_path / "bids"
    bids_root = mff2bids(
        egi_mff_path,
        bids_path,
        "test",
        "test",
        "test",
        run=1,
        event_id=None,
        save_source=True,
        overwrite=False,
    )
    assert BIDSLayout(bids_root, validate=True)
