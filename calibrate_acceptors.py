"""Supervised pulse counter for TB74 or Allan 1239.

Run only after verifying 12V-to-3.3V optoisolation and inhibit wiring.
Press Ctrl+C to disable the acceptor and exit.
"""
import argparse
import json
import time
from gpiozero import DigitalInputDevice, OutputDevice
from coin_changer_hardware import PulseCounter, project_path

p = argparse.ArgumentParser()
p.add_argument('--source', choices=['bill', 'coin'], required=True)
a = p.parse_args()
config = json.loads(project_path('coin_changer_config.json').read_text())
if not config['inhibit_verified'].get(a.source):
    raise SystemExit('Inhibit not yet verified; calibration is blocked.')
counter = PulseCounter(gap_s=float(config.get('pulse_gap_seconds', 1.0)))
line = OutputDevice(config['inhibit_pin'][a.source],
                    active_high=bool(config.get('inhibit_active_high', {}).get(a.source, True)),
                    initial_value=False)
inp = DigitalInputDevice(config['input_pin'][a.source], pull_up=True)
inp.when_activated = counter.edge
print(f'{a.source.upper()} pulse reader ready. Use one known denomination at a time.')
print('Wait until each pulse count appears before inserting another. Ctrl+C to stop.')
try:
    line.on()
    while True:
        frame = counter.drain()
        if frame:
            count, overflow = frame
            print(f'Read {count} pulse(s)' + (' [AMBIGUOUS, RETEST]' if overflow else ''), flush=True)
        time.sleep(.05)
except KeyboardInterrupt:
    pass
finally:
    line.off()
    inp.close()
    line.close()
