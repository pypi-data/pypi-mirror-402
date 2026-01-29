from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import shlex

from blazeutils.strings import (
    case_cw2us,
)

from sysdi.utils import slugify, sub_run


log = logging.getLogger(__name__)


def systemctl(*args, **kwargs):
    args = ('systemctl', '--user', *args)
    return sub_run(*args, **kwargs)


def daemon_reload():
    systemctl('daemon-reload')
    log.info('systemd daemon reloaded')


def linger_enable():
    sub_run('loginctl', 'enable-linger')
    log.info('Linger enabled')


def linger_disable():
    sub_run('loginctl', 'disable-linger')
    log.info('Linger disabled')


def list_units(prefix):
    result = systemctl(
        # There is a --output=json option but doesn't work with list-units on Ubuntu 20.04
        'list-units',
        '--all',
        '--plain',
        '--no-pager',
        '--no-legend',
        f'{prefix}*',
        capture_output=True,
    )
    return [line.split(maxsplit=4)[0] for line in result.stdout.strip().splitlines()]


class UnitManager:
    def __init__(self, *, unit_prefix: str, install_dpath: None | str | os.PathLike = None):
        self.unit_prefix: str = unit_prefix.rstrip('-') + '-'
        self.install_dpath: Path = (
            Path(install_dpath) if install_dpath else self._systemd_unit_dpath()
        )

        self.units = []

    @classmethod
    def _systemd_unit_dpath(self):
        return Path.home().joinpath('.config', 'systemd', 'user')

    def register(self, *unit_instances):
        # TODO: make sure unit_name of all units is unique.
        for unit in unit_instances:
            unit.unit_prefix = self.unit_prefix
            self.units.append(unit)

    def sync(self, *, linger: str | None, install_dpath: str | os.PathLike | None = None):
        """Install managed units and refresh daemon.  Remove stale units and files."""
        self.remove_stale()

        for unit in self.units:
            unit.install(install_dpath or self.install_dpath)

        assert linger in (None, 'enable', 'disable')
        if linger is None:
            return

        if linger == 'enable':
            linger_enable()
        else:
            linger_disable()

    def unit_names(self):
        names: list[str] = []
        for u in self.units:
            names.extend(u.managed_unit_names())
        return names

    def stale(self):
        managed_names = set(self.unit_names())
        systemd_names = set(list_units(self.unit_prefix))

        unit_fpaths = self.install_dpath.glob(f'{self.unit_prefix}*')
        systemd_names = systemd_names | {p.name for p in unit_fpaths}

        return sorted(systemd_names - managed_names)

    def remove_unit(self, name):
        unit_fpath = self.install_dpath / name
        if unit_fpath.exists():
            # TODO: systemd can get into a state where the unit shows up in list-units but the
            # unit files aren't actually there.  It would be ideal to remove/stop/enable those
            # references, but running disable when the files are gone errors out.
            systemctl('disable', '--now', name)
            unit_fpath.unlink()
            log.info(f'Removed unit: {name}')

    def remove_all(self):
        """Remove all unit files, services, and timers that match the prefix."""
        self.remove_stale()
        for unit in self.units:
            for name in unit.managed_unit_names():
                self.remove_unit(name)

        daemon_reload()

    def chain(self, chain_name: str, *units):
        if not units:
            raise ValueError('chain must include at least one unit')
        if len({id(u) for u in units}) != len(units):
            raise ValueError('chain units must be unique instances')

        self.register(*units)

        def _append_success(unit: object, next_unit: object):
            try:
                curr = unit.on_success  # type: ignore[attr-defined]
            except AttributeError:
                curr = None
            items: list[object]
            if curr is None:
                items = []
            elif isinstance(curr, str | bytes):
                items = [curr]
            else:
                items = list(curr)  # type: ignore[arg-type]
            items.append(next_unit)
            unit.on_success = items  # type: ignore[attr-defined]

        for i in range(len(units) - 1):
            _append_success(units[i], units[i + 1])

        # Create a target that wants the first trigger (timer or service)
        first = units[0]
        wants: list[str] = []
        try:
            wants.append(first.unit_name('timer'))  # type: ignore[arg-type]
        except AssertionError:
            wants.append(first.unit_name('service'))  # type: ignore[arg-type]

        tgt = TargetUnit(
            description=f'Chain: {chain_name}',
            unit_basename=slugify(chain_name),
            wants=wants,
        )
        tgt.unit_prefix = self.unit_prefix
        self.units.append(tgt)

    def remove_stale(self):
        """
        Remove any unit files, services, or timers that match the prefix but aren't being
        managed.
        """
        for unit_name in self.stale():
            self.remove_unit(unit_name)


class ExecWrap:
    bash_script = """
    if [ "$SERVICE_RESULT" = success ]; then
        {cmd_ok};
    else
        {cmd_fail};
    fi
    """.rstrip()

    def pre(self):
        raise NotImplementedError

    def post_ok(self):
        raise NotImplementedError

    def post_fail(self):
        raise NotImplementedError

    def post(self):
        script = self.bash_script.replace('\n', '\\\n').format(
            cmd_ok=self.post_ok(),
            cmd_fail=self.post_fail(),
        )
        return f"/usr/bin/env bash -ec '{script}'"


class WebPing(ExecWrap):
    curl_bin = '/usr/bin/env curl'
    curl_opts = (
        '--silent',
        '--show-error',
        '--connect-timeout',
        '5',
        '--max-time',
        '10',
        '--retry',
        '5',
        '--retry-delay',
        '1',
        '--retry-connrefused',
        '--retry-all-errors',
    )

    def pre_url(self):
        raise NotImplementedError

    def post_ok_url(self):
        raise NotImplementedError

    def post_fail_url(self):
        raise NotImplementedError

    def curl_exec(self, url: str):
        return (
            self.curl_bin
            + ' '
            + shlex.join(
                (
                    *self.curl_opts,
                    url,
                ),
            )
        )

    def pre(self):
        return self.curl_exec(self.pre_url())

    def post_ok(self):
        # Escape single quote since that's what we use in the unit to start the bash script
        return self.curl_exec(self.post_ok_url()).replace("'", "\\'")

    def post_fail(self):
        # Escape single quote since that's what we use in the unit to start the bash script
        return self.curl_exec(self.post_fail_url()).replace("'", "\\'")


@dataclass
class TimedUnit:
    description: str
    exec_args: str = ''
    exec_bin: str = ''

    # Type of service.
    # The systemd default "simple" results in ExecStartPost starting immediately after ExecStart,
    # instead of waiting for ExecStart to exit. Use oneshot as the default instead.
    service_type: str = 'oneshot'

    # How long after systemd service startup should the timer activate?  For a user unit, this
    # would be from systemd startup for the user.  But if linger is enabled, its essentially from
    # system startup too.
    # NOTE: unless you really want a timer that only starts after system start, prefer
    # on_active_sec.
    on_startup_sec: str = None

    # How long after the timer is started should the service unit activate?
    on_active_sec: str = None

    # Uses the last activation time of this timer's UNIT (not the timer).  If a unit is activated
    # by another means (e.g. systemctl start ...), the timer's next run time will be affected.
    # The unit's runtime DOES NOT affect the timer's next run time unless it's still running.
    on_unit_active_sec: str = None

    # Same as `on_unit_active_sec` but uses the unit's deactivation time.  The unit's runtime DOES
    # affect the timer's next run time.
    on_unit_inactive_sec: str = None

    # Run on a fixed schedule, more like Cron
    on_calendar: str = None

    # Run service immediately if last start time was missed
    persistent: bool | None = None

    # Specify the accuracy the timer shall elapse with.  The default is the same as systemd's we
    # are just making it explicit.
    accuracy_sec: str = '60s'

    # Delay the timer by a randomly selected, evenly distributed amount of time between 0 and the
    # specified time value.
    # https://www.freedesktop.org/software/systemd/man/systemd.timer.html#RandomizedDelaySec=
    randomized_delay_sec: str | None = None

    # Creates a fixed offset for an individual timer, reducing the jitter in firings of this timer,
    # while still avoiding firing at the same time as other similarly configured timers.
    # This setting has no effect if RandomizedDelaySec= is set to 0. Defaults to false.
    # Only available since 247 (Ubuntu 20.04 has 245).  Ignored when not recognized.
    fixed_random_delay: bool | None = None

    # Support retry interval/limit
    retry_interval_seconds: int = None
    retry_max_tries: int = None

    # Aliases
    start_delay: str = None
    run_every: str = None
    run_delay: str = None
    run_daily: bool = False

    # Exec Pre/Post support
    exec_wrap: ExecWrap | None = None

    # Chain/Dependency support (Unit options)
    on_success: str | object | Sequence[str | object] | None = None
    on_failure: str | object | Sequence[str | object] | None = None

    # Other Unit Config
    service_extra: list[str] | None = None
    timer_extra: list[str] | None = None

    # Other (internal)
    unit_basename: str = None
    unit_prefix: str = None

    def __post_init__(self):
        if not self.exec_bin:
            raise ValueError('exec_bin must be set')

        self.unit_basename = self.unit_basename or slugify(self.description)

        # Default fixed random delay true if using randomized delay sec.  Benefit of non-similar
        # starts without the unpredictibility of constantly random start times.
        if self.fixed_random_delay is None and self.randomized_delay_sec is not None:
            self.fixed_random_delay = True

        if self.start_delay:
            self.on_active_sec = self.start_delay

        if self.run_daily:
            assert not any((self.run_every, self.run_delay))
            # i.e. "12am daily"
            self.on_calendar = 'daily'
            # But give a 3 hour window (runs anytime from 12am - 3am) to avoid all tasks using
            # daily from starting at the same time.
            self.randomized_delay_sec = '3h'

        if self.on_calendar:
            if self.persistent is not False:
                # Run immediately if missed
                self.persistent = True
            if self.randomized_delay_sec and self.fixed_random_delay is not False:
                # By default use a fixed random delay so the start time is consistent
                self.fixed_random_delay = True

        if self.run_every:
            self.on_unit_active_sec = self.run_every

        if self.run_delay:
            self.on_unit_inactive_sec = self.run_delay

        if (self.on_unit_active_sec or self.on_unit_inactive_sec) and not self.on_active_sec:
            # A timer that depends on a unit's last run will never fire the first time on it's own.
            # Configure the timer to kick off the unit immediately upon timer activation so the
            # service unit runs once and then the other configurations will take care of how
            # often it is ran.
            self.on_active_sec = '1'

    @property
    def exec_start(self):
        return f'{self.exec_bin} {self.exec_args}'.strip()

    def option(self, lines, opt_name):
        attr_name = case_cw2us(opt_name)
        value = getattr(self, attr_name)

        if value is None:
            return

        if value is True or value is False:
            value = 'true' if value else 'false'

        lines.append(f'{opt_name}={value}')

    def _normalize_refs(self, refs: str | object | Sequence[str | object] | None) -> list[str]:
        if refs is None:
            return []
        if isinstance(refs, str | bytes):
            items: Iterable[str | object] = [refs]
        else:
            items = refs  # type: ignore[assignment]
        names: list[str] = []
        for r in items:
            if isinstance(r, str | bytes):
                names.append(r)
            else:
                try:
                    rpfx = getattr(r, 'unit_prefix', None)
                    spfx = getattr(self, 'unit_prefix', None)
                    if rpfx is None and spfx is not None and hasattr(r, 'unit_basename'):
                        names.append(f'{spfx}{r.unit_basename}.service')  # type: ignore[attr-defined]
                    else:
                        names.append(r.unit_name('service'))  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover - defensive
                    raise TypeError('Invalid unit reference for OnSuccess/OnFailure') from e
        return names

    def _unit_dependency_lines(self) -> list[str]:
        lines: list[str] = []
        succ = self._normalize_refs(self.on_success)
        fail = self._normalize_refs(self.on_failure)
        if succ:
            lines.append('OnSuccess=' + ' '.join(succ))
        if fail:
            lines.append('OnFailure=' + ' '.join(fail))
        return lines

    def timer(self):
        lines = []
        lines.extend(
            (
                '[Unit]',
                f'Description={self.description}',
                '',
                '[Timer]',
            ),
        )

        self.option(lines, 'AccuracySec')
        self.option(lines, 'OnCalendar')
        self.option(lines, 'Persistent')
        self.option(lines, 'OnActiveSec')
        self.option(lines, 'OnStartupSec')
        self.option(lines, 'OnUnitActiveSec')
        self.option(lines, 'OnUnitInactiveSec')
        self.option(lines, 'RandomizedDelaySec')
        self.option(lines, 'FixedRandomDelay')

        lines.extend(self.timer_extra or ())

        lines.extend(
            (
                '',
                '[Install]',
                'WantedBy=timers.target',
            ),
        )

        return '\n'.join(lines) + '\n'

    def service(self):
        lines = []
        lines.extend(
            (
                '[Unit]',
                f'Description={self.description}',
            ),
        )
        # Add chain dependencies if configured
        lines.extend(self._unit_dependency_lines())

        if self.retry_max_tries and self.retry_interval_seconds:
            # limit interval must be set to more than (tries * interval) to contain the burst
            limit_interval = (self.retry_max_tries * self.retry_interval_seconds) + 15
            lines.extend(
                (
                    f'StartLimitInterval={limit_interval}',
                    f'StartLimitBurst={self.retry_max_tries}',
                ),
            )

        lines.extend(
            (
                '',
                '[Service]',
                f'Type={self.service_type}',
            ),
        )
        if self.retry_interval_seconds:
            lines.extend(
                (
                    'Restart=on-failure',
                    f'RestartSec={self.retry_interval_seconds}',
                ),
            )

        self.option(lines, 'ExecStart')

        if self.exec_wrap:
            lines.append(f'ExecStartPre={self.exec_wrap.pre()}')
            lines.append(f'ExecStopPost={self.exec_wrap.post()}')

        lines.extend(self.service_extra or ())

        return '\n'.join(lines) + '\n'

    def install(self, install_dpath):
        install_dpath.mkdir(parents=True, exist_ok=True)

        timer_fname = self.unit_name('timer')
        timer_fpath = install_dpath.joinpath(timer_fname)

        service_fname = self.unit_name('service')
        service_fpath = install_dpath.joinpath(service_fname)

        timer_fpath.write_text(self.timer())
        log.info(f'(Re)installed {timer_fname}')

        service_fpath.write_text(self.service())
        log.info(f'(Re)installed {service_fname}')

        # Reload the daemon before the enable and start
        daemon_reload()

        # Enable and start the timer
        systemctl('enable', '--now', timer_fname)

    def unit_name(self, type_):
        assert type_ in ('service', 'timer')
        return f'{self.unit_prefix}{self.unit_basename}.{type_}'

    def managed_unit_names(self) -> list[str]:
        return [self.unit_name('timer'), self.unit_name('service')]


@dataclass
class ServiceUnit:
    description: str
    exec_args: str = ''
    exec_bin: str = ''

    service_type: str = 'oneshot'

    retry_interval_seconds: int | None = None
    retry_max_tries: int | None = None

    exec_wrap: ExecWrap | None = None

    on_success: str | object | Sequence[str | object] | None = None
    on_failure: str | object | Sequence[str | object] | None = None

    service_extra: list[str] | None = None

    unit_basename: str | None = None
    unit_prefix: str | None = None

    def __post_init__(self):
        if not self.exec_bin:
            raise ValueError('exec_bin must be set')
        self.unit_basename = self.unit_basename or slugify(self.description)

    @property
    def exec_start(self):
        return f'{self.exec_bin} {self.exec_args}'.strip()

    def _normalize_refs(self, refs: str | object | Sequence[str | object] | None) -> list[str]:
        if refs is None:
            return []
        if isinstance(refs, str | bytes):
            items: Iterable[str | object] = [refs]
        else:
            items = refs  # type: ignore[assignment]
        names: list[str] = []
        for r in items:
            if isinstance(r, str | bytes):
                names.append(r)
            else:
                try:
                    rpfx = getattr(r, 'unit_prefix', None)
                    spfx = getattr(self, 'unit_prefix', None)
                    if rpfx is None and spfx is not None and hasattr(r, 'unit_basename'):
                        names.append(f'{spfx}{r.unit_basename}.service')  # type: ignore[attr-defined]
                    else:
                        names.append(r.unit_name('service'))  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover
                    raise TypeError('Invalid unit reference for OnSuccess/OnFailure') from e
        return names

    def _unit_dependency_lines(self) -> list[str]:
        lines: list[str] = []
        succ = self._normalize_refs(self.on_success)
        fail = self._normalize_refs(self.on_failure)
        if succ:
            lines.append('OnSuccess=' + ' '.join(succ))
        if fail:
            lines.append('OnFailure=' + ' '.join(fail))
        return lines

    def service(self):
        lines: list[str] = []
        lines.extend(('[Unit]', f'Description={self.description}'))
        lines.extend(self._unit_dependency_lines())

        if self.retry_max_tries and self.retry_interval_seconds:
            limit_interval = (self.retry_max_tries * self.retry_interval_seconds) + 15
            lines.extend(
                (
                    f'StartLimitInterval={limit_interval}',
                    f'StartLimitBurst={self.retry_max_tries}',
                ),
            )

        lines.extend(('', '[Service]', f'Type={self.service_type}'))
        if self.retry_interval_seconds:
            lines.extend(('Restart=on-failure', f'RestartSec={self.retry_interval_seconds}'))

        lines.append(f'ExecStart={self.exec_start}')

        if self.exec_wrap:
            lines.append(f'ExecStartPre={self.exec_wrap.pre()}')
            lines.append(f'ExecStopPost={self.exec_wrap.post()}')

        lines.extend(self.service_extra or ())
        return '\n'.join(lines) + '\n'

    def install(self, install_dpath: Path):
        install_dpath.mkdir(parents=True, exist_ok=True)
        service_fname = self.unit_name('service')
        service_fpath = install_dpath.joinpath(service_fname)
        service_fpath.write_text(self.service())
        log.info(f'(Re)installed {service_fname}')
        daemon_reload()

    def unit_name(self, type_: str):
        assert type_ == 'service'
        return f'{self.unit_prefix}{self.unit_basename}.{type_}'

    def managed_unit_names(self) -> list[str]:
        return [self.unit_name('service')]


@dataclass
class TargetUnit:
    description: str
    unit_basename: str
    wants: list[str] | None = None
    unit_prefix: str | None = None

    def install(self, install_dpath: Path):
        install_dpath.mkdir(parents=True, exist_ok=True)
        fname = self.unit_name()
        fpath = install_dpath.joinpath(fname)
        lines = ['[Unit]', f'Description={self.description}']
        if self.wants:
            lines.append('Wants=' + ' '.join(self.wants))
        fpath.write_text('\n'.join(lines) + '\n')
        log.info(f'(Re)installed {fname}')
        daemon_reload()

    def unit_name(self) -> str:
        return f'{self.unit_prefix}{self.unit_basename}.target'

    def managed_unit_names(self) -> list[str]:
        return [self.unit_name()]
