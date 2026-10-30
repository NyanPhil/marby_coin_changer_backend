"""Hardware backend for Marby Raspberry Pi kiosk.

Real money mode requires a calibrated pulse map, verified inhibit circuits,
a coin-exit sensor, and five PCA9685 servo channels. GPIO numbers are BCM.
Never connect an acceptor's 12V signal directly to Raspberry Pi GPIO.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
COINS = (0.25, 1, 5, 10, 20)


class HardwareFault(RuntimeError):
    pass


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf8') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def project_path(path):
    p = Path(path).expanduser()
    return p if p.is_absolute() else BASE / p


class Storage:
    """Crash-visible journal. Unfinished transactions require an operator."""
    def __init__(self, cfg):
        self.path = project_path(cfg.get('journal_file', 'transaction_state.json'))
        self.inventory_path = project_path(cfg.get('inventory_file', 'inventory.json'))
        self._lock = threading.Lock()
        self.state = json.loads(self.path.read_text(encoding='utf8')) if self.path.exists() else {}
        self.inventory = (
            json.loads(self.inventory_path.read_text(encoding='utf8'))
            if self.inventory_path.exists() else {str(c): 0 for c in COINS}
        )
        for c in COINS:
            n = self.inventory.get(str(c), 0)
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                raise HardwareFault('Invalid inventory count for PHP ' + str(c))
        if not self.inventory_path.exists():
            atomic_json(self.inventory_path, self.inventory)

    @property
    def unresolved(self):
        return self.state.get('status') in ('paid', 'dispensing', 'fault')

    def receive(self, source, value):
        with self._lock:
            if self.state.get('status') not in ('paid', None, 'completed', 'reconciled'):
                raise HardwareFault('Another transaction requires operator review.')
            if self.state.get('status') == 'paid' and self.state.get('source') != source:
                raise HardwareFault('Mixed input sources in a single transaction.')
            if self.state.get('status') != 'paid':
                self.state = {'status': 'paid', 'source': source, 'credit': 0,
                              'received': [], 'dispensed': {}, 'started_at': time.time()}
            self.state['credit'] += value
            self.state['received'].append({'source': source, 'value': value, 'time': time.time()})
            atomic_json(self.path, self.state)

    def can_pay(self, plan):
        return all(self.inventory.get(str(c), 0) >= n for c, n in plan.items())

    def can_make_exact(self, amount):
        """Bounded coin-stock solver in integer centavos, cached per inventory."""
        if not isinstance(amount, int) or amount < 1 or amount > 100:
            return False
        key = tuple(self.inventory.get(str(v), 0) for v in COINS)
        if getattr(self, '_reachability_key', None) != key:
            reachable = {0}
            for value, available in zip(COINS, key):
                cents = int(value * 100)
                count = min(10000 // cents, available)
                block = 1
                while count:
                    take = min(block, count)
                    increment = take * cents
                    reachable |= {n + increment for n in tuple(reachable)
                                  if n + increment <= 10000}
                    count -= take
                    block *= 2
            self._reachable = reachable
            self._reachability_key = key
        return amount * 100 in self._reachable

    def ready_for_source(self, source, mapped_values):
        if source == 'bill':
            return all(self.can_make_exact(v) for v in mapped_values)
        if source == 'coin':
            # Any running total from 1 to 100 must remain returnable.
            return all(self.can_make_exact(a) for a in range(1, 101))
        return False

    def start(self, plan):
        with self._lock:
            if self.state.get('status') != 'paid':
                raise HardwareFault('No recorded funds available for payment.')
            if sum(c * n for c, n in plan.items()) != self.state.get('credit'):
                raise HardwareFault('Payout value is not equal to recorded credit.')
            if not self.can_pay(plan):
                raise HardwareFault('Insufficient coins. Select another combination.')
            self.state['status'] = 'dispensing'
            self.state['plan'] = {str(c): n for c, n in plan.items()}
            self.state['dispensed'] = {}
            atomic_json(self.path, self.state)

    def confirmed(self, coin):
        with self._lock:
            if self.state.get('status') != 'dispensing':
                raise HardwareFault('Dispensing journal is not active.')
            if self.inventory.get(str(coin), 0) <= 0:
                raise HardwareFault('Inventory exhausted during payout.')
            self.inventory[str(coin)] -= 1
            self.state['dispensed'][str(coin)] = self.state['dispensed'].get(str(coin), 0) + 1
            # If power is lost between writes, pending journal prevents another payout.
            atomic_json(self.path, self.state)
            atomic_json(self.inventory_path, self.inventory)

    def complete(self):
        with self._lock:
            if self.state.get('status') != 'dispensing':
                raise HardwareFault('Payout not active.')
            if self.state.get('dispensed') != self.state.get('plan'):
                raise HardwareFault('Payout count does not match requested plan.')
            self.state['status'] = 'completed'
            self.state['completed_at'] = time.time()
            atomic_json(self.path, self.state)

    def fault(self, detail):
        with self._lock:
            self.state['status'] = 'fault'
            self.state['fault'] = str(detail)
            self.state['fault_at'] = time.time()
            atomic_json(self.path, self.state)


class PulseCounter:
    """Group falling edges into pulse frames; access from callbacks and UI."""
    def __init__(self, min_edge_s=.018, gap_s=1.0, max_pulses=100):
        self.lock = threading.Lock()
        self.min_edge_s = min_edge_s
        self.gap_s = gap_s
        self.max_pulses = max_pulses
        self.count = 0
        self.last = 0.0
        self.overflow = False

    def edge(self):
        now = time.monotonic()
        with self.lock:
            if self.count and now - self.last < self.min_edge_s:
                return False
            if self.count and now - self.last > self.gap_s:
                # Missing UI poll means frame boundary was ambiguous.
                self.overflow = True
            first_pulse = self.count == 0
            self.count += 1
            self.last = now
            if self.count > self.max_pulses:
                self.overflow = True
            return first_pulse

    def drain(self):
        with self.lock:
            if not self.count or time.monotonic() - self.last < self.gap_s:
                return None
            count, overflow = self.count, self.overflow
            self.count, self.overflow = 0, False
            return count, overflow


class RealHardware:
    def __init__(self, cfg):
        self.cfg = cfg
        for field in ('bill', 'coin'):
            if not cfg.get('inhibit_verified', {}).get(field, False):
                raise HardwareFault(f'{field} inhibit circuit not verified. Block money entry until verified.')
        if cfg.get('drop_sensor_pin') is None:
            raise HardwareFault('Coin-exit sensor required in real-money mode.')
        for coin in COINS:
            if not cfg.get('servo_verified', {}).get(str(coin), False):
                raise HardwareFault(f'Servo channel for PHP {coin} not marked calibrated.')
        pins = list(cfg['input_pin'].values()) + list(cfg['inhibit_pin'].values()) + [cfg['drop_sensor_pin']]
        if len(pins) != len(set(pins)) or any(pin in (0, 1, 2, 3) for pin in pins):
            raise HardwareFault('GPIO pin conflict or pin reserved for I2C detected.')
        self.maps = {}
        for source, allowed in [('bill', {50, 100}), ('coin', {1, 5, 10, 20})]:
            raw = cfg.get('pulse_map', {}).get(source, {})
            try:
                mapping = {int(k): int(v) for k, v in raw.items()}
            except (TypeError, ValueError) as e:
                raise HardwareFault('Bad pulse mapping: ' + source) from e
            if not mapping or any(k <= 0 or v not in allowed for k, v in mapping.items()):
                raise HardwareFault('Calibrate ' + source + ' pulses before enabling hardware.')
            if len(set(mapping.values())) != len(mapping):
                raise HardwareFault('Duplicate denominations in ' + source + ' pulse map.')
            self.maps[source] = mapping
        self.storage = Storage(cfg)
        if self.storage.unresolved:
            raise HardwareFault('Unresolved transaction in transaction_state.json; operator must reconcile.')
        self.accepting = None
        self._accept_lock = threading.RLock()
        self.frame_permission = {'bill': None, 'coin': None}
        self.stopping = threading.Event()
        self.pulses = {s: PulseCounter(gap_s=float(cfg.get('pulse_gap_seconds', 1.0)))
                       for s in ('bill', 'coin')}
        self.drop_count = 0
        self.drop_time = 0
        self.drop_lock = threading.Lock()
        try:
            from gpiozero import DigitalInputDevice, OutputDevice
            from adafruit_servokit import ServoKit
        except ImportError as e:
            raise HardwareFault('Install gpiozero and adafruit-circuitpython-servokit') from e
        self.inhibits = {}
        self.inputs = {}
        self.drop_sensor = None
        self.kit = None
        try:
            self.kit = ServoKit(channels=16, address=int(cfg.get('pca9685_address', '0x40'), 0))
            for source in ('bill', 'coin'):
                pin = cfg['inhibit_pin'][source]
                self.inhibits[source] = OutputDevice(
                    pin, active_high=bool(cfg.get('inhibit_active_high', {}).get(source, True)),
                    initial_value=False)
            for source in ('bill', 'coin'):
                inp = DigitalInputDevice(cfg['input_pin'][source], pull_up=True)
                inp.when_activated = self._make_pulse_callback(source)
                self.inputs[source] = inp
            self.drop_sensor = DigitalInputDevice(cfg['drop_sensor_pin'], pull_up=True)
            self.drop_sensor.when_activated = self._on_drop
        except Exception:
            self.close()
            raise

    def _make_pulse_callback(self, source):
        def callback():
            first = self.pulses[source].edge()
            if first:
                # One physical insertion is already underway: close intake
                # immediately so a second bill/coin cannot arrive before
                # the final pulse has been decoded by the UI.
                with self._accept_lock:
                    self.frame_permission[source] = (self.accepting == source)
                    try:
                        self.set_acceptance(None)
                    except Exception:
                        self.frame_permission[source] = False
                        self.stopping.set()
        return callback

    def _on_drop(self):
        now = time.monotonic()
        with self.drop_lock:
            if now - self.drop_time > float(self.cfg.get('sensor_debounce_seconds', .08)):
                self.drop_time = now
                self.drop_count += 1

    def set_acceptance(self, source=None):
        with self._accept_lock:
            self.accepting = None
            for output in self.inhibits.values():
                output.off()
            if source in ('bill', 'coin') and not self.stopping.is_set():
                self.inhibits[source].on()
                self.accepting = source

    def poll(self):
        events = []
        for source in ('bill', 'coin'):
            frame = self.pulses[source].drain()
            if frame is None:
                continue
            pulses, overflow = frame
            with self._accept_lock:
                allowed_at_first_pulse = self.frame_permission[source]
                self.frame_permission[source] = None
            value = self.maps[source].get(pulses)
            if overflow or value is None:
                events.append(('fault', f'Unknown {source} pulse train: {pulses} pulses. Operator required.'))
            elif not allowed_at_first_pulse:
                events.append(('fault', f'Unexpected {source} acceptance outside deposit mode: PHP {value}.'))
            else:
                events.append((source, value))
        return events

    def dispense_one(self, coin):
        if coin not in COINS:
            raise HardwareFault('Unsupported payout coin.')
        if self.stopping.is_set():
            raise HardwareFault('Emergency stop / shutdown requested.')
        setting = self.cfg.get('servos', {}).get(str(coin))
        if not setting or not setting.get('enabled', True):
            raise HardwareFault(f'No calibrated servo for PHP {coin}.')
        channel = int(setting['channel'])
        home = float(setting['home_angle'])
        release = float(setting['release_angle'])
        hold = float(setting.get('hold_seconds', .45))
        settle = float(setting.get('settle_seconds', .3))
        timeout = float(self.cfg.get('drop_timeout_seconds', 2.0))
        with self.drop_lock:
            before = self.drop_count
        servo = self.kit.servo[channel]
        try:
            servo.angle = home
            time.sleep(.15)
            servo.angle = release
            time.sleep(hold)
            servo.angle = home
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self.stopping.is_set():
                    raise HardwareFault('Dispensing interrupted.')
                with self.drop_lock:
                    passed = self.drop_count - before
                if passed == 1:
                    time.sleep(settle)
                    with self.drop_lock:
                        if self.drop_count - before != 1:
                            raise HardwareFault('Extra coin detected during sensor settling.')
                    return
                if passed > 1:
                    raise HardwareFault('Multiple sensor crossings for one commanded coin.')
                time.sleep(.025)
            raise HardwareFault(f'No coin detected after PHP {coin} servo cycle (possible empty tube/jam).')
        finally:
            try:
                servo.angle = home
            except Exception:
                pass

    def close(self):
        self.stopping.set()
        for output in getattr(self, 'inhibits', {}).values():
            try: output.off(); output.close()
            except Exception: pass
        for inp in getattr(self, 'inputs', {}).values():
            try: inp.close()
            except Exception: pass
        if getattr(self, 'drop_sensor', None) is not None:
            try: self.drop_sensor.close()
            except Exception: pass
