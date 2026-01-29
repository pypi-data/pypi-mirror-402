from os import environ
from pathlib import Path

import pytest

from sysdi import ExecWrap, TimedUnit, UnitManager
from sysdi.core import systemctl


class FileWrap(ExecWrap):
    def __init__(self, base_dpath: Path):
        self.base_dpath = base_dpath

    def pre(self):
        return f'/usr/bin/env touch {self.base_dpath}/exec-wrap-pre'

    def post_ok(self):
        return f'/usr/bin/env touch {self.base_dpath}/exec-wrap-ok'

    def post_fail(self):
        return f'/usr/bin/env touch {self.base_dpath}/exec-wrap-fail'


@pytest.fixture(scope='module')
def um():
    um = UnitManager(unit_prefix='sysdi-test')
    try:
        yield um
    finally:
        um.remove_all()


pytestmark = pytest.mark.skipif(bool(environ.get('CI')), reason='not run in CI')


class TestExecWrap:
    @pytest.fixture(autouse=True)
    def remove_all(self, um):
        um.remove_all()

    def test_ok(self, um: UnitManager, tmp_path: Path):
        um.register(
            TimedUnit(
                'Check exec wrap',
                exec_bin='/usr/bin/true',
                exec_wrap=FileWrap(tmp_path),
                on_active_sec='1000s',
            ),
        )
        um.sync(linger=None)
        systemctl('start', 'sysdi-test-check-exec-wrap', '--wait')

        assert tmp_path.joinpath('exec-wrap-pre').exists()
        assert tmp_path.joinpath('exec-wrap-ok').exists()
        assert not tmp_path.joinpath('exec-wrap-fail').exists()

    def test_fail(self, um: UnitManager, tmp_path: Path):
        um.register(
            TimedUnit(
                'Check exec wrap',
                exec_bin='/usr/bin/false',
                exec_wrap=FileWrap(tmp_path),
                on_active_sec='1000s',
            ),
        )
        um.sync(linger=None)
        systemctl('start', 'sysdi-test-check-exec-wrap', '--wait', check=False)

        assert tmp_path.joinpath('exec-wrap-pre').exists()
        assert not tmp_path.joinpath('exec-wrap-ok').exists()
        assert tmp_path.joinpath('exec-wrap-fail').exists()
