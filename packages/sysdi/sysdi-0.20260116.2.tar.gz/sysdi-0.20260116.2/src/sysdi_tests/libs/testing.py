from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

from sysdi import core


units_dpath = Path(__file__).parent.parent.joinpath('systemd-units').resolve()


def mock_patch_obj(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch.object(*args, **kwargs)


def mock_patch(*args, **kwargs):
    kwargs.setdefault('autospec', True)
    kwargs.setdefault('spec_set', True)
    return mock.patch(*args, **kwargs)


@dataclass
class CoreMocks:
    sub_run: mock.MagicMock
    systemctl: mock.MagicMock
    linger_enable: mock.MagicMock
    linger_disable: mock.MagicMock


@contextmanager
def mock_core():
    with (
        mock_patch_obj(core, 'sub_run') as m_sub_run,
        mock_patch_obj(core, 'systemctl') as m_systemctl,
        mock_patch_obj(core, 'linger_enable') as m_linger_enable,
        mock_patch_obj(core, 'linger_disable') as m_linger_disable,
    ):
        yield CoreMocks(m_sub_run, m_systemctl, m_linger_enable, m_linger_disable)
