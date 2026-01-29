from dataclasses import dataclass
from pathlib import Path
import re

import pytest

from sysdi import ServiceUnit, TimedUnit, UnitManager

from .libs import testing


@pytest.fixture(autouse=True)
def m_core():
    with testing.mock_core() as core_mocks:
        yield core_mocks


def read(path: Path) -> str:
    return path.read_text()


def assert_has_line(text: str, pattern: str):
    escaped = re.escape(pattern)
    assert re.search(rf'^\s*{escaped}\s*$', text, re.MULTILINE), f'Missing line: {pattern}'


def assert_not_has_line(text: str, pattern: str):
    escaped = re.escape(pattern)
    assert not re.search(rf'^\s*{escaped}\s*$', text, re.MULTILINE), f'Unexpected line: {pattern}'


class TestSequentialChains:
    def test_chain_basic(self, tmp_path: Path):
        @dataclass
        class TimedPicard(TimedUnit):
            exec_bin: str = '/bin/picard'

        @dataclass
        class SvcPicard(ServiceUnit):
            exec_bin: str = '/bin/picard'

        um = UnitManager(unit_prefix='abc-')
        a = TimedPicard('Alpha', 'alpha', on_active_sec='1000s')
        b = SvcPicard('Beta', 'beta')
        c = SvcPicard('Gamma', 'gamma')

        um.chain('Test Chain', a, b, c)
        um.sync(linger=None, install_dpath=tmp_path)

        names = sorted(p.name for p in tmp_path.iterdir())
        assert names == [
            'abc-alpha.service',
            'abc-alpha.timer',
            'abc-beta.service',
            'abc-gamma.service',
            'abc-test-chain.target',
        ]

        a_svc = read(tmp_path / 'abc-alpha.service')
        b_svc = read(tmp_path / 'abc-beta.service')
        c_svc = read(tmp_path / 'abc-gamma.service')
        tgt = read(tmp_path / 'abc-test-chain.target')

        assert_has_line(a_svc, '[Unit]')
        assert_has_line(a_svc, 'OnSuccess=abc-beta.service')
        assert_not_has_line(a_svc, 'OnFailure=')

        assert_has_line(b_svc, 'OnSuccess=abc-gamma.service')
        assert_not_has_line(b_svc, 'OnFailure=')

        assert_not_has_line(c_svc, 'OnSuccess=')
        assert_not_has_line(c_svc, 'OnFailure=')

        assert_has_line(tgt, '[Unit]')
        assert_has_line(tgt, 'Wants=abc-alpha.timer')

    def test_empty_chain_errors(self):
        um = UnitManager(unit_prefix='abc-')
        with pytest.raises(ValueError):
            um.chain('Empty', *[])  # type: ignore[arg-type]

    def test_single_chain_ok(self, tmp_path: Path):
        @dataclass
        class TimedPicard(TimedUnit):
            exec_bin: str = '/bin/picard'

        um = UnitManager(unit_prefix='abc-')
        a = TimedPicard('Alpha', 'alpha', on_active_sec='1000s')
        um.chain('Single', a)
        um.sync(linger=None, install_dpath=tmp_path)

        names = sorted(p.name for p in tmp_path.iterdir())
        assert names == [
            'abc-alpha.service',
            'abc-alpha.timer',
            'abc-single.target',
        ]

        a_svc = read(tmp_path / 'abc-alpha.service')
        assert_not_has_line(a_svc, 'OnSuccess=')
        assert_not_has_line(a_svc, 'OnFailure=')

    def test_duplicate_instances_error(self):
        @dataclass
        class TimedPicard(TimedUnit):
            exec_bin: str = '/bin/picard'

        @dataclass
        class SvcPicard(ServiceUnit):
            exec_bin: str = '/bin/picard'

        um = UnitManager(unit_prefix='abc-')
        a = TimedPicard('Alpha', 'alpha', on_active_sec='1000s')
        b = SvcPicard('Beta', 'beta')
        with pytest.raises(ValueError):
            um.chain('Dupes', a, b, b)

    def test_on_failure_directive_supported(self, tmp_path: Path):
        @dataclass
        class TimedPicard(TimedUnit):
            exec_bin: str = '/bin/picard'

        @dataclass
        class SvcPicard(ServiceUnit):
            exec_bin: str = '/bin/picard'

        um = UnitManager(unit_prefix='abc-')
        a = TimedPicard('Alpha', 'alpha', on_active_sec='1000s')
        b = SvcPicard('Beta', 'beta')
        fail = SvcPicard('Failed', 'failed')
        # Explicitly assign OnFailure to Beta
        b.on_failure = [fail]

        um.chain('With Failure', a, b)
        um.sync(linger=None, install_dpath=tmp_path)

        b_svc = read(tmp_path / 'abc-beta.service')
        assert_has_line(b_svc, 'OnFailure=abc-failed.service')
