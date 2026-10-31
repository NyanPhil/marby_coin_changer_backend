"""Simple read-only pulse counter for the Allan 1239 or TB74.

Run one source at a time. This test does not operate acceptance control.
"""
import argparse
import json
from pathlib import Path
from threading import Lock
from time import monotonic, sleep


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, choices=('coin', 'bill'))
    args = parser.parse_args()
    config = json.loads(Path(__file__).with_name('coin_changer_config.json').read_text(encoding='utf8'))
    pin = config['input_pin'][args.source]
    gap = float(config[args.source + '_pulse_gap_seconds'])

    from gpiozero import DigitalInputDevice
    lock = Lock()
    count = 0
    last_pulse = 0.0
    line = DigitalInputDevice(pin, pull_up=True, bounce_time=None)

    def pulse_detected():
        nonlocal count, last_pulse
        with lock:
            count += 1
            last_pulse = monotonic()

    try:
        line.when_activated = pulse_detected
        print(f'Monitoring {args.source} pulses on GPIO{pin}', flush=True)
        print(f'Report after {gap:g} seconds without another pulse.', flush=True)
        print('Leave idle for 10 seconds, then insert ONE item at a time.', flush=True)
        print('Read only: acceptance control is not operated. Ctrl+C to stop.', flush=True)
        while True:
            sleep(.05)
            result = None
            with lock:
                if count > 0 and monotonic() - last_pulse >= gap:
                    result, count = count, 0
            if result is not None:
                print(f'Pulse count: {result}', flush=True)
    except KeyboardInterrupt:
        print('\nStopped.', flush=True)
    finally:
        line.close()
        with lock:
            if count:
                print(f'Unfinished pulse group: {count}', flush=True)


if __name__ == '__main__':
    main()
