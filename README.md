# Marby — Cash Exchange and GCash Cash-In Machine

Marby is a Raspberry Pi-based prototype designed to exchange bills or higher-value coins into smaller coins, combine smaller coins into higher-value coins, and support GCash cash-in. It combines a touchscreen interface with cash acceptors, inventory management, and servo-controlled coin dispensing.

## Main Functions

1. **Larger denomination to smaller coins** — Exchange bills or higher-value coins for lower-value coins in user-selected combinations.
2. **Smaller coins to bigger coins** — Combine lower-value coins and exchange them for higher-value coins.
3. **GCash cash-in** — Deposit cash to add funds to a GCash account. This service supports cash-in only.

## Key Features

- Accepts ₱1, ₱5, ₱10, and ₱20 coins, plus ₱50 and ₱100 bills.
- Offers preset and custom coin payout combinations.
- Controls five coin dispensers for ₱1, ₱5, ₱10, and ₱20.
- Tracks coin inventory and transaction progress.
- Handles ambiguous pulse counts and payout errors.
- Includes simulation mode and automated backend tests.

## Technologies Used

**Software:** Python, Tkinter, GPIO Zero, and Adafruit ServoKit.

**Hardware:** Raspberry Pi, TB74 bill acceptor, Allan 1239 coin acceptor, HY-M158 optocoupler, PCA9685 servo driver, and five servo motors.

## Skills Demonstrated

- Hardware and software integration
- GPIO and I²C communication
- Touchscreen interface development
- Event-driven programming
- Transaction state management and error handling

## Project Status

Prototype in development. Acceptor pulse mappings have been tested; acceptance control and coin dispensing still require physical verification.
