import os.path as op
import shutil

import numpy as np
import pytest
from bids.layout import BIDSLayout
from mne.datasets.testing import data_path

from egi2bids.mff2bids import mff2bids

base_dir = op.join(op.dirname(op.abspath(__file__)), "data")
testing_path = data_path(download=True)
egi_path = op.join(testing_path, "EGI")
egi_mff_fname = op.join(egi_path, "test_egi.mff")


@pytest.mark.parametrize("filetype", ["tar", "zip", "gztar"])
def test_file_conversion(tmp_path, filetype):
    # create temporary directory and file for testing
    mff_path = op.join(tmp_path, "test.mff")
    bids_path = op.join(tmp_path, "bids")
    archive_path = shutil.make_archive(mff_path, filetype, egi_mff_fname)
    bids_root = mff2bids(
        archive_path,
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
    bids_path = op.join(tmp_path, "bids")
    bids_root = mff2bids(
        egi_mff_fname,
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
