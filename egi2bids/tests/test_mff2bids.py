import os
import os.path as op
import shutil
import tarfile
import zipfile

import pytest
from bids.layout import BIDSLayout
from mne.datasets.testing import data_path

from egi2bids.mff2bids import mff2bids

base_dir = os.path.join(op.dirname(op.abspath(__file__)), "data")
testing_path = data_path(download=True)
egi_path = testing_path / "EGI"
egi_mff_path = egi_path / "test_egi.mff"


# ZIP
# flat
output_path_zip = shutil.make_archive("archive_flat", "zip", egi_mff_path)
# Folder
output_path_zip_folder = "archive_folder.mff.zip"
with zipfile.ZipFile(
    output_path_zip_folder, "w", compression=zipfile.ZIP_DEFLATED
) as zipf:
    for root, dirs, files in os.walk(egi_mff_path):
        for file in files:
            zipf.write(
                os.path.join(root, file),
                os.path.join(
                    "archive_folder.mff",
                    os.path.relpath(os.path.join(root, file), egi_mff_path),
                ),
            )

# TAR
# flat
output_path_tar = shutil.make_archive("archive_flat", "tar", egi_mff_path)
# folder
output_path_tar_folder = "archive_folder.mff.tar"
with tarfile.open(output_path_tar_folder, "w") as tar:
    tar.add(egi_mff_path, arcname="archive_folder.mff")


@pytest.mark.parametrize(
    "file",
    [
        output_path_zip,
        output_path_zip_folder,
        output_path_tar,
        output_path_tar_folder,
    ],
)
def test_file_conversion(tmp_path, file):
    # create temporary directory and file for testing
    bids_path = tmp_path / "bids"
    bids_root = mff2bids(
        file,
        bids_path,
        "test",
        "test",
        "test",
        run=1,
        event_id=None,
        line_frequency=50,
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
        line_frequency=50,
        save_source=True,
        overwrite=False,
    )
    assert BIDSLayout(bids_root, validate=True)
