from pathlib import Path

import pytest

from sysd_example import um

from .libs import testing


@pytest.fixture(autouse=True)
def m_core():
    with testing.mock_core() as core_mocks:
        yield core_mocks


def test_sync(m_core: testing.CoreMocks, tmp_path: Path):
    um.sync(linger=None, install_dpath=tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        'utm-replicator-sanitization.service',
        'utm-replicator-sanitization.timer',
        'utm-transport-buffer-flush.service',
        'utm-transport-buffer-flush.timer',
        'utm-work-core-diagnostics.service',
        'utm-work-core-diagnostics.timer',
    ]
