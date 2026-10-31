# Marby Coin Changer — Raspberry Pi hardware deployment

This package preserves the original 800×480 Tkinter UI and adds Raspberry Pi hardware control. **The code is not a substitute for physically verifying validator firmware, isolated wiring, coin delivery, and acceptor inhibition.**


## Coin and bill input update on 31 October 2026

The calibrated profile stores **coin pulses 1, 5, 10, 20 = PHP 1, 5, 10, 20**, and **bill pulses 5 = PHP 50 and 10 = PHP 100**. These are separate maps: 5 coin pulses credit PHP 5, while 5 bill pulses credit PHP 50. Bills use a **3-second quiet period after the last falling or rising transition**, with the input returned HIGH. Coins use their own 2-second quiet period, matching the latest standalone coin counter. A bill frame that lasts 45 seconds without completing is treated as ambiguous.

The backend commands both acceptors disabled on the first pulse. A one-bill lock prevents screen redraws or repeated enable requests from reopening intake during counting or after bill credit. The lock is released only after the payout is committed; the customer must start another exchange. The deposit screen displays a processing message while the bill is being counted.

**Fast repeat insertions:** a merged group of 15, 20, or 21 pulses produces a persistent service-required fault. The program does not round 21 to 20, split a merged group into assumed notes, or credit PHP 200. Existing recorded credit remains in the journal; an operator must inspect the physical cash and settle any additional amount. `marby_service.py` is used only after that reconciliation.

**Physical prevention requires working INHIBIT.** The previously unwired inhibit circuit cannot be replaced by a longer timeout. Pulse counts alone do not uniquely identify note boundaries: 10 pulses can be one PHP 100 note or two PHP 50 notes. Verify that inhibition rejects the next bill while allowing all pulses for the current accepted bill to finish. If another note can be accepted before the first credit pulse, the pulse-only interface needs a verified busy/escrow signal or a different supported protocol before unattended use.

### Apply this update to the existing project

Stop the kiosk and back up your current Marby folder. Extract `Marby_Update.zip` into `~/Marby`, replacing the matching program/configuration files and adding `count_acceptor_pulses.py`. The archive contains the wiring guide and updated hardware backend, connected UI, configuration, calibration utility, tests and this guide. It does not contain inventory or transaction journals, so it cannot overwrite the physical coin counts or incident record.

The supplied configuration now contains both pulse maps. Hardware-verification flags remain false until the actual inhibit and dispensing circuits pass their checks. Preserve or merge any additional measured settings from your actual machine; do not mark an unwired inhibit circuit as verified. In `inhibit_active_high`, true means the enable-driver command is driven HIGH when `.on()` is called. Match this to the verified external driver; it is not the TB74 DIP-switch polarity by itself.

```bash
cd ~/Marby
.venv/bin/python -m unittest -v test_marby.py
.venv/bin/python count_acceptor_pulses.py --source coin
# Stop with Ctrl+C before running the other source.
.venv/bin/python count_acceptor_pulses.py --source bill
# To inspect decoded groups using the backend reader:
.venv/bin/python calibrate_acceptors.py --source coin --diagnostic-only
.venv/bin/python calibrate_acceptors.py --source bill --diagnostic-only
```

The read-only counters use GPIO17 for coins and GPIO27 for bills. They do not operate INHIBIT, credit money or run a servo. The simple counter reproduces the working falling-edge test; the calibration utility also reports the mapped denomination and ambiguous groups. Insert one bill and wait for the result before the next. It reports overlapping/over-limit groups as ambiguous. Normal calibration (`--source bill` without `--diagnostic-only`) requires verified inhibit control and disables intake during each frame.

A working inhibit driver is reserved on **GPIO23 / physical pin 16** for TB74 control. That is a control-interface connection, not permission to attach the TB74's 12V inhibit wires directly to GPIO23. Pulse sensing remains on **GPIO27 / physical pin 13**. See `Marby_Acceptor_Wiring.docx` for both pulse circuits, the pull-up diagram and the conditional TB74 inhibit proposal. The Allan inhibit terminal is not established: GPIO24 remains reserved and unconnected. A spare HY-M158 channel is not automatically a 3.3V-compatible inhibit driver.

### Pulse reader settings

`bill_min_edge_seconds` and `coin_min_edge_seconds` are explicitly `0.0`, matching the successful standalone counter that counts every falling edge. No debounce or pulse ranges are introduced. Correct idle readings must remain at zero. The real backend also waits for an idle HIGH input and restarts the quiet timer after either edge. This is stricter framing than the simple counter, which times silence after falling edges only.

The supplied tests use simulated GPIO and time; they do not verify electrical isolation, the physical inhibit polarity, coin delivery, or UI appearance on the Pi.

## 0. Hardware interpretation and limits

- **UI host:** Raspberry Pi running Raspberry Pi OS Desktop. If the UI instead runs on a Windows PC with a separate ESP32 or Arduino, this wiring/backend will need a different transport.
- **Bill input:** TB74 **pulse-mode** validator with **Philippine-peso firmware**. Only **₱50** and **₱100** are credited. Different TB74 country builds, pulse ratios, and interface modes have different behavior. Do **not** assume a generic TB74 supports PHP. Configure the actual unit to physically reject all other notes; confirm the manual and test.
- **Coin input:** Allan **1239A** programmable validator. Configure and calibrate **only the denominations it can reliably recognize** (for example ₱1, ₱5, ₱10; include ₱20 only after verifying its recognition). The package **does not accept 25-centavo inputs** until you deliberately add and calibrate that input path.
- **Payout:** five hobby-servo gates, one per coin tube, **₱0.25, ₱1, ₱5, ₱10, ₱20**. The fifth channel (₱0.25) is available on the custom-mix screen, with a schematic icon (not an official coin photo).
- **Credit:** one note per bill transaction, or multiple calibrated whole-peso coins. In real-hardware mode, whole-peso totals **₱1–₱100** can be exchanged so a non-preset coin sum is not trapped. No bills are dispensed.
- **For real-money mode you must also have:** an optical **coin-exit sensor**, working hardware **inhibit/enable** control for **both** acceptors, a calibrated inventory, and a PCA9685 16-channel I²C servo driver. This is a conservative choice: servo motion alone cannot prove a coin left the tube.

## 1. Package contents

- `coin_changer_connected.py`: your Tkinter interface, updated for hardware, five payout types, and simulation.
- `coin_changer_hardware.py`: pulse counting, cash-acceptance inhibition, five servos, coin-exit confirmation, inventory, and transaction journal.
- `coin_changer_config.json`: GPIO, pulse-to-denomination mappings and servo calibration.
- `inventory.json`: **physical** coin counts; all zero in the original template. Preserve the actual loaded counts when applying this update.
- `calibrate_acceptors.py`: supervised pulse decoder for one acceptor at a time.
- `count_acceptor_pulses.py`: simple read-only falling-edge counter for either acceptor.
- `Marby_Acceptor_Wiring.docx`: combined acceptor wiring, pull-up connections and inhibit status.
- `marby_service.py`: audited reconciliation of interrupted transactions. **Does not refund or dispense coins.**
- `run_marby.sh`: kiosk start command with log capture.
- `test_marby.py`: local tests. 

The original `coin_changer_ui.py` remains untouched, so you can compare/restore it.

## 2. Wire safely: GPIO numbers are BCM, not physical pin numbers

**Turn all power off before wiring.** The Raspberry Pi GPIO pins take 3.3V signals, **not 12V**. Isolate *both* acceptor pulse outputs through appropriately designed **opto-isolator/input conditioner circuits**; output GPIO from an optocoupler should pull its assigned Pi input to GND when a pulse arrives. The software uses `DigitalInputDevice(..., pull_up=True)` so **LOW = active pulse**. Do not copy wire colors from another unit without checking your own TB74/Allan harness schematic and measured output behavior. Do not power servo motors from the Pi 5V pin.

| Function | Pi GPIO (BCM) | Pi physical pin | External path |
|---|---:|---:|---|
| Allan 1239 coin pulse input | GPIO17 | 11 | Verified 12V-to-3.3V isolated active-low pulse interface |
| TB74 bill pulse input | GPIO27 | 13 | Verified isolated active-low pulse interface |
| Coin-exit optical sensor | GPIO22 | 15 | 3.3V-compatible active-low, one pulse **per actual coin** |
| TB74 enable/inhibit control | GPIO23 | 16 | Conditional driver proposal in the wiring guide; verify before enabling |
| Allan enable/inhibit control | GPIO24 | 18 | Reserved only; exact Allan inhibit input and driver remain to be established |
| PCA9685 SDA | GPIO2 | 3 | PCA9685 SDA (3.3V logic) |
| PCA9685 SCL | GPIO3 | 5 | PCA9685 SCL (3.3V logic) |
| PCA9685 VCC | 3.3V | 1 | **Logic supply only**, not servo power |
| PCA9685 GND | Ground | 6 | Pi logic ground / appropriate common control reference |
| PCA9685 V+ | **Separate regulated 5–6V supply** | — | Power for the five servos; current sized for servo stall demand |

The TB74 and Allan are typically **12V DC** devices, but refer to your exact unit's label/manual. The isolator input circuits connect on the validator side of the 12V circuit. Isolation must be designed to suit the pulse output type (some are open-collector rather than 12V push-pull). Connect the servo power supply's ground to the PCA9685 controller's common reference as required by its documentation. Avoid unqualified mains-power wiring; use a properly enclosed, certified DC power supply and have the electrical hookup inspected.

PCA9685 servo allocation (zero-based channel numbers):

| Channel | Tube and coin |
|---:|---|
| 0 | 25 centavos / ₱0.25 |
| 1 | ₱1 |
| 2 | ₱5 |
| 3 | ₱10 |
| 4 | ₱20 |

Use one **sensor crossing per actually released coin**. Position the sensor so that it detects coins from **all** five tubes at the common output chute. An obstructed sensor, bounced pulse, or two coins released together must result in a fault.

**Inhibit fail-safe:** test that acceptors *physically reject cash* when the Pi is off, the application is stopped, or the input supply fails. A software flag is not sufficient if the validator accepts cash when its inhibit line floats. Verify whether the unit's inhibit is active-low or active-high, and match the `inhibit_active_high` value to your output-interface design, not to an unverified web wiring diagram. Do not mark `inhibit_verified` as true until this works.

## 3. Prepare Raspberry Pi OS and install files

Choose Raspberry Pi OS **Desktop**, set it to boot to the desktop, then copy or unzip the package into `~/Marby`.

```bash
sudo apt update
sudo apt install -y python3-tk python3-venv python3-pip python3-gpiozero python3-lgpio i2c-tools
mkdir -p ~/Marby
unzip ~/Downloads/marby_hardware_bundle.zip -d ~/Marby
cd ~/Marby
python3 -m venv --system-site-packages .venv
.venv/bin/pip install adafruit-circuitpython-servokit
```

Enable I²C using `sudo raspi-config` → Interface Options → I2C → Enable, then restart if prompted. Verify that the PCA9685 appears at its **actual** I²C address:

```bash
sudo i2cdetect -y 1
```

For the default board address, look for `40` (hexadecimal). If absent, correct wiring/address before proceeding. The UI cannot operate the servos without a detected PCA9685.

## 4. Start with a simulation (no acceptors / no servos needed)

```bash
cd ~/Marby
.venv/bin/python -m unittest -v test_marby.py
.venv/bin/python coin_changer_connected.py --windowed
```

In this mode, **tap the onscreen denomination pictures**; dispensing is simulated. Quit the simulation before hardware tests. The original `coin_changer_ui.py` can still be run separately.

## 5. Program and verify acceptor denomination restrictions

1. Consult the **exact** TB74 label, currency firmware, harness manual and pulse DIP settings. **Pulse mode** is required by this backend, not RS232 or ccTalk mode. Only allow notes ₱50 and ₱100; a ₱200/₱500/₱1000 note must be **physically rejected** by the validator, not just ignored by Python.
2. Train/program the Allan 1239A with the coins it can reliably discriminate. Different sellers advertise old/new ₱1/₱5/₱10; do not advertise a ₱20 capability until you have tested it on your unit. The validator's **maximum of five types** is not proof that it recognizes all five Philippine denominations.
3. With the isolated pulse inputs verified and acceptors manually shown to reject cash while inhibited, set **only the relevant** `inhibit_verified` entry to `true` for calibration.
4. Run the pulse monitor for each source, one at a time:

```bash
cd ~/Marby
.venv/bin/python calibrate_acceptors.py --source coin
.venv/bin/python calibrate_acceptors.py --source bill
```

5. Insert **one** known item and wait until its pulse count is printed before trying the next item. Repeat each denomination at least several times, including older/newer coin series if they are accepted. Record the observed stable **pulse-count → peso-value** mapping.
6. The supplied maps are `pulse_map.bill = {"5": 50, "10": 100}` and `pulse_map.coin = {"1": 1, "5": 5, "10": 10, "20": 20}`. Recheck every denomination using the deployed wiring and then with inhibit active. Keys are pulse counts as strings, values are peso amounts as integers. For example, `{"2": 50}` means **two measured pulses represented ₱50 in your own test**; it is not a manufacturer-guaranteed example. Repeated/ambiguous pulse counts cannot be mapped to two values.
7. Test that the acceptors refuse wrong denominations, coin doubles, oversized credit, and cash offered while in idle/review/dispensing. Only proceed when inhibition is physically reliable.

There is an intentional quiet period after the last transition: 3 seconds for bills and 2 seconds for coins. LOW input prevents normal completion; an overlong frame faults. Bills accept exactly the configured 5/10 pulse mappings, with one bill per exchange. The backend inhibits intake on the first pulse and refuses re-enable requests during an unfinished frame or a consumed bill session. **Physically verify that inhibition rejects the next item without truncating the current pulse train.**

## 6. Calibrate the five servo gates

Do this with a **non-public test assembly**. Disconnect customer cash acceptance or leave acceptors inhibited throughout servo commissioning. Ensure each gate is clear of fingers and that the output path cannot eject coins unexpectedly.

The `servos` object has **five entries** (`0.25`, `1`, `5`, `10`, `20`). Each entry specifies a `channel`, `home_angle`, `release_angle`, `hold_seconds`, and optional `settle_seconds`. These angles are **initial placeholders**, not guaranteed mechanical settings. Test one channel at a time, adjusting its gate angle and cycle duration so it releases **exactly one** correctly sized coin and returns to its closed state.

For a simple bench check of channel 1 (₱1), with acceptors OFF and **the tube empty**, run:

```bash
cd ~/Marby
.venv/bin/python - <<'PY'
from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels=16)
s = kit.servo[1]
s.angle = 0
# Change the tested release angle only after verifying the mechanism has clearance.
s.angle = 65
time.sleep(0.4)
s.angle = 0
PY
```

Repeat with channels **0, 2, 3, 4** by changing only the numeric channel. Then test each with real coins in a contained bench rig. Confirm the exit sensor detects **one** crossing for each actual coin. Set the matching `servo_verified` entry to `true` only after it passes. This is a practical commissioning checkbox, not an electronic self-test.

## 7. Load and record actual inventory

Physically count each tube, then enter those exact quantities into `inventory.json`. Example **only**:

```json
{"0.25": 40, "1": 120, "5": 40, "10": 20, "20": 10}
```

The program rejects payout plans exceeding stock and conservatively disables acceptor input when it cannot guarantee an exact payout for allowed amounts. **Never inflate the inventory numbers to make a disabled acceptor start.** A tube with zero real coins must have a zero count. Check enough inventory for both ₱50 and ₱100 bills before allowing the bill validator.

## 8. Enable and launch real hardware mode

After the wiring, inhibit behavior, pulse maps, five servos, common drop sensor, and inventory have all been verified:

```bash
cd ~/Marby
.venv/bin/python coin_changer_connected.py --hardware --windowed
```

If any required check is missing, startup is intentionally blocked. This is not an invitation to bypass the checks. For kiosk fullscreen, omit `--windowed`:

```bash
cd ~/Marby
.venv/bin/python coin_changer_connected.py --hardware
```

### Expected behavior

1. Select **Change bills** or **Change coins**.
2. The selected acceptor is enabled only in the deposit screen and only when stock is sufficient.
3. Insert a supported item; the acceptor's pulses are counted and translated using your measured mapping. The actual accepted value appears on the screen (the pictures cannot add credit in hardware mode).
4. Choose a preset or **custom** payout. The five custom types include 25-centavo coins.
5. Confirm the exact payment plan. The UI disables both acceptors.
6. **One servo at a time** rotates from its home angle to the release angle and back. A coin-exit sensor must detect one coin before the journal/inventory is updated and the next gate is actuated.
7. The UI displays the collect screen only after the full requested value has been sensor-confirmed and the transaction is committed.

## 9. Error handling and interrupted transactions

| Error | Behavior |
|---|---|
| Unmapped pulse count, noise, extra pulse or pulse train ambiguity | Latch service-required fault; inhibit cash; do not guess a denomination |
| Unsupported note or coin | Must be **rejected by the validator itself**; an accepted but unmapped value causes service fault |
| Wrong mode or over-limit coin event | Service fault, do not discard accepted value silently |
| No inventory for requested payout | Block the plan, and require a different exact combination or operator resolution |
| No coin-exit sensor crossing after servo movement | Halt; possible jam/empty tube; do not count that coin as dispensed |
| More than one crossing | Halt for a double-release / sensor problem |
| Power failure mid-transaction | On restart, journal blocks new cash acceptance until operator reconciles the actual balance |
| Failed GPIO/I²C initialization | Startup blocked, leaving acceptors inhibited by the required fail-closed physical interface |

**Recovery procedure:** Lock access to the kiosk; read `transaction_state.json` to determine recorded credit, plan and sensor-confirmed coins. Count physical output and contents, reconcile with customer/operator, and update `inventory.json` based on actual remaining coins. Only after resolving the obligation use:

```bash
cd ~/Marby
.venv/bin/python marby_service.py --operator "Technician ID" --reason "Physical cash counted; customer refund/settlement details"
```

Type `RECONCILED` when prompted to append the incident to `reconciliations.jsonl` and unlock the next startup. The service script **does not dispense, assume delivery, or refund coins**. Maintain backup copies of incident logs and review cash mismatches before leaving the machine unattended.

## 10. Auto-start only after bench testing passes

Use Raspberry Pi OS Desktop auto-login. First verify `run_marby.sh` works from a terminal and the machine is safe to accept money. Then:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/marby.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Marby Coin Changer
Exec=$HOME/Marby/run_marby.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
```

Restart and watch the screen. Logs are stored in `~/Marby/marby.log`:

```bash
tail -f ~/Marby/marby.log
```

To temporarily disable auto-start while servicing, rename `~/.config/autostart/marby.desktop` to `marby.desktop.disabled`. Always verify the **hardware** acceptor-inhibit state when the kiosk is stopped; software shutdown alone is not sufficient to guarantee cash rejection.

## References

- ICT/TOPVME TB74 documentation: https://www.topvme.com/index.php/en/pi-en/ba-en/tb74
- Allan 1239A product/specification examples: https://makerlab.ph/products/allan-universal-coin-slot-coinslot-selector-with-anti-hooking-anti-theft-design-multi-1238-1239-piso-wifi-vendo-machine-1
- Adafruit PCA9685 Raspberry Pi setup: https://learn.adafruit.com/16-channel-pwm-servo-driver/python-circuitpython
- Adafruit ServoKit Python API: https://docs.circuitpython.org/projects/servokit/en/latest/api.html
