from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import pytest

from sysdi import core
from sysdi.contrib.cronitor import WebPing
from sysdi.core import UnitManager, daemon_reload, linger_disable, linger_enable, list_units

from .libs import testing
from .libs.testing import CoreMocks, units_dpath


@pytest.fixture(autouse=True)
def m_core():
    with testing.mock_core() as core_mocks:
        yield core_mocks


def assert_same(content: str, fname: str):
    file_lines = units_dpath.joinpath(fname).read_text().strip().splitlines()
    content_lines = content.strip().splitlines()
    assert content_lines == file_lines


@dataclass
class TimedUnit(core.TimedUnit):
    exec_bin: str = '/bin/picard'


class TestTimedUnit:
    def test_exec_start(self):
        tu = TimedUnit('foo', 'bar')
        assert tu.exec_start == '/bin/picard bar'

    @pytest.mark.xfail(reason='What API do we want for supporting an exec prefix?')
    def test_exec_start_cron_sentry(self):
        tu = TimedUnit(
            'foo',
            'bar',
            cron_sentry_bin='/fake/cron-sentry',
            sentry_dsn='abcdsn',
        )
        cmd = '/fake/cron-sentry --dsn abcdsn /bin/picard bar'
        assert tu.exec_start == cmd

    def test_defaults(self):
        tu = TimedUnit(
            'check defaults',
            'foo bar',
            on_active_sec='15m',
            on_unit_active_sec='2h',
            randomized_delay_sec='5m',
        )

        assert_same(tu.timer(), 'defaults.timer')
        assert_same(tu.service(), 'defaults.service')

    def test_defaults_inherited(self):
        @dataclass
        class CustomTU(TimedUnit):
            on_active_sec: str = '15m'
            randomized_delay_sec: str = '5m'

        tu = CustomTU(
            'check defaults',
            'foo bar',
            on_unit_active_sec='2h',
        )

        assert_same(tu.timer(), 'defaults.timer')
        assert_same(tu.service(), 'defaults.service')

    def test_aliases(self):
        tu = TimedUnit(
            'Harvest Sync',
            'marshal harvest sync',
            start_delay='5s',
            run_delay='30s',
            run_every='5m',
        )

        assert_same(tu.timer(), 'aliases.timer')

    def test_install(self, m_core: CoreMocks, tmp_path):
        target_dpath = tmp_path.joinpath('.config/systemd/user')
        tu = TimedUnit('Harvest Sync', 'bar', unit_prefix='abc-')
        tu.install(target_dpath)

        service_fpath = target_dpath.joinpath('abc-harvest-sync.service')
        timer_fpath = target_dpath.joinpath('abc-harvest-sync.timer')

        service_text = service_fpath.read_text()
        assert '[Service]' in service_text
        assert 'Type=oneshot' in service_text
        assert 'Restart' not in service_text
        assert '[Timer]' in timer_fpath.read_text()

        assert m_core.systemctl.mock_calls == [
            mock.call('daemon-reload'),
            mock.call('enable', '--now', 'abc-harvest-sync.timer'),
        ]

        # Sad path
        foo_fpath = target_dpath.joinpath('foo')
        foo_fpath.write_text('')

    def test_install_specified_type(self, tmp_path):
        target_dpath = tmp_path.joinpath('.config/systemd/user')
        tu = TimedUnit('Harvest Sync', 'bar', unit_prefix='abc-', service_type='forked')
        tu.install(target_dpath)

        service_fpath = target_dpath.joinpath('abc-harvest-sync.service')

        service_text = service_fpath.read_text()
        assert '[Service]' in service_text
        assert 'Type=forked' in service_text

    def test_install_with_retries(self, tmp_path):
        target_dpath = tmp_path.joinpath('.config/systemd/user')
        tu = TimedUnit(
            'Harvest Sync',
            'bar',
            unit_prefix='abc-',
            retry_interval_seconds=15,
            retry_max_tries=4,
        )
        tu.install(target_dpath)

        service_fpath = target_dpath.joinpath('abc-harvest-sync.service')

        service_text = service_fpath.read_text()
        assert '[Service]' in service_text
        assert 'StartLimitInterval=75' in service_text
        assert 'StartLimitBurst=4' in service_text
        assert 'Restart=on-failure' in service_text
        assert 'RestartSec=15' in service_text

    def test_exec_wrap(self):
        class Wrap(core.ExecWrap):
            def pre(self):
                return '/usr/bin/exec-pre'

            def post_ok(self):
                return '/usr/bin/exec-post-ok'

            def post_fail(self):
                return '/usr/bin/exec-post-fail'

        tu = TimedUnit(
            'Check exec wrap',
            exec_wrap=Wrap(),
        )

        assert_same(tu.service(), 'exec-wrap.service')

    def test_daily_timer(self):
        tu = TimedUnit(
            'Daily Example',
            run_daily=True,
        )

        assert_same(tu.timer(), 'daily.timer')

    def test_extra_config(self):
        tu = TimedUnit(
            'Extra Config',
            service_extra=['WorkingDirectory=foo'],
            timer_extra=['OnUnitInactiveSec=10'],
        )

        assert_same(tu.service(), 'extra-config.service')
        assert_same(tu.timer(), 'extra-config.timer')

    def test_startup_sec_default(self):
        tu = TimedUnit('foo', run_every='15m')
        assert tu.on_active_sec == '1'

        tu = TimedUnit('foo', run_delay='15m')
        assert tu.on_active_sec == '1'


class TestManager:
    @testing.mock_patch_obj(core, 'list_units')
    def test_stale(self, m_list_units, tmp_path: Path):
        timer_fpath = tmp_path.joinpath('abc-foo.timer')
        stale_fpath = tmp_path.joinpath('abc-biz.timer')
        timer_fpath.touch()
        stale_fpath.touch()

        m_list_units.return_value = ['abc-foo.timer', 'abc-bar.service']

        um = UnitManager(unit_prefix='abc-', install_dpath=tmp_path)
        um.register(TimedUnit('foo', '123'))
        assert um.stale() == [
            'abc-bar.service',
            'abc-biz.timer',
        ]

    def test_remove_unit(self, m_core: CoreMocks, tmp_path: Path):
        unit_fpath = tmp_path.joinpath('abc-foobar.timer')
        unit_fpath.touch()

        um = UnitManager(unit_prefix='abc-', install_dpath=tmp_path)
        um.remove_unit('abc-foobar.timer')

        assert not unit_fpath.exists()
        m_core.systemctl.assert_called_once_with(
            'disable',
            '--now',
            'abc-foobar.timer',
        )

        # Calling with the file not there should not throw an error.
        um.remove_unit('foobar.timer')

    @testing.mock_patch_obj(UnitManager, 'remove_unit')
    @testing.mock_patch_obj(UnitManager, 'stale')
    def test_remove_stale(self, m_stale, m_remove_unit):
        m_stale.return_value = ['abc-foo.service', 'abc-foo.timer']

        um = UnitManager(unit_prefix='abc-')
        um.remove_stale()

        assert m_remove_unit.mock_calls == [
            mock.call(um, 'abc-foo.service'),
            mock.call(um, 'abc-foo.timer'),
        ]

    @testing.mock_patch_obj(UnitManager, 'remove_unit')
    @testing.mock_patch_obj(UnitManager, 'stale')
    def test_remove_all(self, m_stale, m_remove_unit):
        m_stale.return_value = ['abc-foo.service', 'abc-foo.timer']

        um = UnitManager(unit_prefix='abc-')
        um.register(
            TimedUnit('bar', '123'),
            TimedUnit('baz', '123'),
        )
        um.remove_all()

        assert m_remove_unit.mock_calls == [
            mock.call(um, 'abc-foo.service'),
            mock.call(um, 'abc-foo.timer'),
            mock.call(um, 'abc-bar.timer'),
            mock.call(um, 'abc-bar.service'),
            mock.call(um, 'abc-baz.timer'),
            mock.call(um, 'abc-baz.service'),
        ]

    @testing.mock_patch_obj(UnitManager, 'remove_stale')
    def test_sync(self, m_remove_stale, m_core):
        um = UnitManager(unit_prefix='abc-')
        um.register(
            TimedUnit('foo', '123'),
            TimedUnit('bar', '123'),
        )
        um.sync(linger=None)

        m_remove_stale.assert_called_once_with(um)
        assert m_core.systemctl.mock_calls == [
            mock.call('daemon-reload'),
            mock.call('enable', '--now', 'abc-foo.timer'),
            mock.call('daemon-reload'),
            mock.call('enable', '--now', 'abc-bar.timer'),
        ]


class TestSubProc:
    def test_daemon_reload(self, m_core):
        daemon_reload()

        m_core.systemctl.assert_called_once_with('daemon-reload')

    def test_linger_enable(self, m_core):
        linger_enable()
        m_core.sub_run.assert_called_once_with('loginctl', 'enable-linger')

    def test_linger_disable(self, m_core):
        linger_disable()
        m_core.sub_run.assert_called_once_with('loginctl', 'disable-linger')

    def test_list_units(self, m_core):
        m_core.systemctl.return_value.stdout = units_dpath.joinpath('list-units.txt').read_text()
        assert list_units('abc-') == [
            'gpg-agent-extra.socket',
            'gpg-agent-ssh.socket',
            'gpg-agent.socket',
        ]
        m_core.systemctl.assert_called_once_with(
            'list-units',
            '--all',
            '--plain',
            '--no-pager',
            '--no-legend',
            'abc-*',
            capture_output=True,
        )


class TestWebPing:
    def test_it(self):
        wp = WebPing(api_key='abc-123', monitor_key='nightly-job')
        pre_url = 'https://cronitor.link/p/abc-123/nightly-job/run'
        post_ok_url = 'https://cronitor.link/p/abc-123/nightly-job/complete'
        post_fail_url = 'https://cronitor.link/p/abc-123/nightly-job/fail'

        assert wp.pre_url() == pre_url
        assert wp.post_ok_url() == post_ok_url
        assert wp.post_fail_url() == post_fail_url

        tu = TimedUnit(
            'Cronitor WebPing',
            exec_bin='/bin/picard',
            exec_wrap=wp,
        )

        assert_same(tu.service(), 'cronitor-webping.service')

        wp = WebPing(monitor_key='nightly-job')
        assert wp.pre_url() == 'https://cronitor.link/nightly-job/run'
