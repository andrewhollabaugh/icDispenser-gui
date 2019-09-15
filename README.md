# icDispenser-gui
IC Dispenser Python Tkinter GUI Program
Written by Andrew Hollabaugh, started 1/27/19

Graphical interface for Integrated Circuit (IC) Dispenser project. Uses Tkinter (Tk) user interface library
for python.

Communicates with an ATMEGA328 microcontroller over serial, which runs the dispenser at a lower level.

Reads/writes inventory.csv, which keeps track which ICs are stored in which indexes, how many are left, and the type of tube. Each row corresponds to a tube, and the line number in the file its index.
Row Format: part-number, number-of-ics-left, tube-type

### Basic functionality
- Shows a list of IC part numbers, sorted by name or index
- Ability to select which ICs to dispense, adding them to a separate list
- Dispensing ICs
- Logging events
- STOP button

### Debug functionality
- Ability to send all possible commands to ATMEGA328 for full testing of its functinality

### Future Features
- Update items in inventory.csv through gui
- Menu to obscure debug features
