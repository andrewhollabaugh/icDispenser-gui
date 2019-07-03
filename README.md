# icDispenser-gui
IC Dispenser Python Tkinter GUI Program
Written by Andrew Hollabaugh, started 1/27/19

Graphical interface for Integrated Circuit (IC) Dispenser project. Uses Tkinter (Tk) user interface library
for python.

Communicates with an ATMEGA328 microcontroller over serial, which runs the dispenser at a lower level.

Reads/writes inventory.csv, which keeps track of what part numbers are stored in what tube indexes, and other info.
Each row corresponds to a tube, and the line number in the file its index
Row Format:
PART_NUMBER,NUMBER_OF_ITEMS_LEFT

### Basic functionality
- Shows a list of IC part numbers, sorted by name or index
- Ability to select which ICs to dispense and dispense them
- Message log of things that happened
- Disable button - press if something bad happens

### Debug functionality
- Ability to execute send all possible commands to ATMEGA328 for full testing of its functinality

### Future Features
- Update items in csv through gui
- Serial port stuff
- Listbox column headers
- Items to dispense quantity of each item
- Menu to obscure debug features
- Not let you home dispenser if already homed
- Undo button
- Ability to deal with multiple tubes of the same IC
- Listbox tube type display
