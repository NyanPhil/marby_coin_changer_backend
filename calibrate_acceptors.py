"""Supervised pulse diagnostics for TB74 or Allan 1239.

Normal calibration requires verified inhibit control. --diagnostic-only reads
GPIO without driving the inhibit pin, crediting money, or moving any servo.
"""
import argparse
import json
import time
from gpiozero import DigitalInputDevice, OutputDevice
from coin_changer_hardware import pulse_counter_for, project_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['bill', 'coin'], required=True)
    parser.add_argument('--diagnostic-only', action='store_true',
                        help='Read GPIO only; acceptance cannot be disabled by this test.')
    args = parser.parse_args()
    config = json.loads(project_path('coin_changer_config.json').read_text(encoding='utf8'))
    if not args.diagnostic_only and not config['inhibit_verified'].get(args.source):
        raise SystemExit('Inhibit not verified. Use --diagnostic-only for supervised GPIO readings only.')

    counter = pulse_counter_for(config, args.source)
    line = None
    inp = None
    try:
        if not args.diagnostic_only:
            line = OutputDevice(
                config['inhibit_pin'][args.source],
                active_high=bool(config.get('inhibit_active_high', {}).get(args.source, True)),
                initial_value=False)
        inp = DigitalInputDevice(config['input_pin'][args.source], pull_up=True, bounce_time=None)

        def falling():
            first = counter.edge()
            if first and line is not None:
                line.off()  # Block the next insertion; retain current pulse group.

        inp.when_activated = falling
        inp.when_deactivated = counter.release
        print(f'{args.source.upper()} reader on GPIO{config["input_pin"][args.source]}')
        print(f'Report after {counter.gap_s:g} seconds quiet and an idle HIGH input.')
        if args.diagnostic_only:
            print('READ ONLY: INHIBIT is not controlled. Insert ONE item, then wait for the result.')
        else:
            print('Intake closes on the first pulse. Verify the current train is not truncated.')
        print('Ctrl+C to stop. No payout or credit is performed.', flush=True)
        if line is not None and not inp.is_active:
            line.on()
        last_count = 0
        while True:
            with counter.lock:
                count = counter.count
            if count and count != last_count:
                print(f'Processing: {count} pulse(s). Do not insert another.', flush=True)
                last_count = count
            frame = counter.drain(idle=not inp.is_active)
            if frame is not None:
                count, ambiguous = frame
                mapping = config.get('pulse_map', {}).get(args.source, {})
                value = mapping.get(str(count))
                print(f'Group complete: {count} pulse(s)' +
                      (' [AMBIGUOUS: inspect accepted cash]' if ambiguous else
                       f' => PHP {value}' if value is not None else ' [UNMAPPED]'), flush=True)
                last_count = 0
                if ambiguous:
                    print('Stopping. No denomination is inferred from a merged group.', flush=True)
                    break
            if (line is not None and not inp.is_active and
                    counter.is_quiet(counter.gap_s)):
                line.on()
            time.sleep(.05)
    except KeyboardInterrupt:
        print('Stopped.')
    finally:
        if line is not None:
            line.off()
        if inp is not None:
            inp.close()
        if line is not None:
            line.close()


if __name__ == '__main__':
    main()
