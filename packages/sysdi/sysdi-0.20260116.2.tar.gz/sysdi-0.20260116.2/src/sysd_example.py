from dataclasses import dataclass

from sysdi import ServiceUnit, TimedUnit, UnitManager
from sysdi.contrib import cronitor


@dataclass
class Starship(TimedUnit):
    exec_bin: str = '/bin/starship'


um = UnitManager(
    # WARNING: Unit manager will clear out any unknown unit files with the given prefix so make sure
    # it's unique.  Also, if you change it, make sure you remove all the units first or the next
    # time you sync you will have new and old units both running.
    unit_prefix='utm',
)
um.register(
    Starship(
        # Unit description; also sluggified to get unit name
        'Work Core Diagnostics',
        # Exec args:  results in `/bin/starship warp-core diagnostics` as the unit command
        'warp-core diagnostics',
        # How long after user login / system start should this get kicked off?
        start_delay='30s',
        # Run every 15m regardless of how long the unit itself takes to run.  If the unit takes 2m
        # to run, then 13m will elapse before the unit is started again.
        #
        # If someone manually runs the diagnostics service, the next start time WILL NOT be
        # affected.
        run_every='15m',
        # Ping cronitor at start and finish indicating state completed or failed
        exec_wrap=cronitor.WebPing(api_key='abc-123', monitor_key='warp-core-diagnostics'),
    ),
    Starship(
        'Transport Buffer Flush',
        'transporter buffer flush --all',
        # Regardless of unit runtime
        run_every='1m',
        # Systemd default accuracy is 60s which is too much for a 1m recurrance
        accuracy_sec='5s',
    ),
    Starship(
        'Replicator Sanitization',
        'replicator sanitize',
        # Runs four hours after the last time the system unit was ran.  If someone manually runs
        # the service, the next start time WILL be affected.
        run_delay='4h',
        # On error retry after 2 minutes (The default is to NOT retry)
        retry_interval_seconds=120,
        # Only try four times total (initial try plus three retries on error)
        retry_max_tries=4,
    ),
)


# Service-only (no timer) unit for chaining
@dataclass
class SvcStarship(ServiceUnit):
    exec_bin: str = '/bin/starship'


# Chain: A runs on a schedule; on success triggers B; on success triggers C
um_chain = UnitManager(unit_prefix='utm-chain-')
alpha = Starship(
    'Diagnostics Head',
    'diagnostics run',
    start_delay='30s',
    run_every='15m',
)
beta = SvcStarship('Diagnostics Beta', 'beta stage')
gamma = SvcStarship('Diagnostics Gamma', 'gamma stage')
um_chain.chain('Diagnostics Chain', alpha, beta, gamma)


# Call this in a cli command (or something) to:
# - Write units to disk
# - Reload systemd daemon
# - Enable timer units
# - Enable login linger: which indicates timers should run even when the user is logged out
# um.sync(linger='enable')
# um_chain.sync(linger=None)
