from tkinter import *
from tkinter import ttk
import serial
import numpy
import csv
import threading
import queue
#import tkSimpleDialog

global hasExited
global serialQueue 

class App:
    
    monoFont = ("Monospace", 9)
    monoFontBold = ("Monospace", 9, "bold")

    invFilePath = "/home/andrew/icDispenser-gui/inventory.csv"

    inventory = []
    formattedInventory = []
    selectedItems = []
    formattedSelectedItems = []
    dispense = []

    moveSelCommand = "M"
    homeSelCommand = "H"
    enableSelCommand = "E"
    enableDisCommand = "N"
    disableSelCommand = "D"
    disableDisCommand = "S"
    totalTubesCommand = "T"
    moveSelNextCommand = "O"
    dispenseCommand = "I"
    homeDisCommand = "R"
    dispenseNoHomeCommand = "Q"

    ser = None

    state = "none" #Possible states: none, moveToIndex, dispense, homing
    hasHomed = False
    global hasExited
    hasExited = False

    #App constructor
    #Initializes the interface; creates widgets and sets widget settings
    def __init__(s, root):

        root.title("IC Dispenser")

        #FRAME/IMPORTANT WIDGET HIERARCHY
        #commonFrame
        #   -itemSelectFrame
        #       -itemListBox
        #       -itemListBoxScrollbar
        #   -itemSelectFrame2
        #       -itemListBox2
        #       -itemListBox2Scrollbar
        #   -sortFrame
        #       -sortOptionMenu
        #   -addArrowButton
        #   -removeArrowButton
        #   -dispenseButton
        #   -undoButton
        #controlFrame
        #   -advancedFrame
        #       -debug/test buttons
        #   -disableButton
        #   -changeItemsButton
        #messageFrame
        #   -messageListBoxFrame
        #       -messageListBox
        #       -messageListBoxScrollbar
        #   -messageClearButton

        #TOP-LEVEL FRAMES
        s.commonFrame = Frame(root, relief=RIDGE, borderwidth=5)
        s.controlFrame = Frame(root)
        s.messageFrame = Frame(root)

        #toplevel frame grid
        s.commonFrame.grid(row=0, column=0)
        s.controlFrame.grid(row=0, column=1, sticky=N)
        s.messageFrame.grid(row=0, column=2, sticky=N)

        #COMMONFRAME STUFF

        #invFrame stuff
        s.invFrame = Frame(s.commonFrame)

        invTreeColumns = ("Part", "Index", "Qty", "Tube")
        s.invTree = ttk.Treeview(s.invFrame, columns=invTreeColumns, show="headings", selectmode="extended", height=20)
        s.invTree.column("Part", width=100, anchor='w')
        s.invTree.column("Index", width=50, anchor='w')
        s.invTree.column("Qty", width=50, anchor='w')
        s.invTree.column("Tube", width=70, anchor='w')

        for col in invTreeColumns:
           s.invTree.heading(col, text=col, command=lambda _col=col: s.treeviewSortColumn(s.invTree, _col, False)) 

        s.invTreeScroll = Scrollbar(s.invFrame, orient=VERTICAL)
        s.invTreeScroll.config(command=s.invTree.yview)
        s.invTree.configure(yscrollcommand=s.invTreeScroll.set)

        s.invTree.pack(side=LEFT)
        s.invTreeScroll.pack(side=RIGHT, fill=Y)
        #end invFrame stuff

        s.invLabel = Label(s.commonFrame, text="Select ICs to Dispense", font=s.monoFontBold)

        #disFrame stuff
        s.disFrame = Frame(s.commonFrame)

        disTreeColumns = ("Part", "Index", "Qty", "Tube")
        s.disTree = ttk.Treeview(s.disFrame, column=disTreeColumns, show="headings", selectmode="extended", height=14)
        s.disTree.column("Part", width=100, anchor='w')
        s.disTree.column("Index", width=50, anchor='w')
        s.disTree.column("Qty", width=50, anchor='w')
        s.disTree.column("Tube", width=70, anchor='w')

        for col in disTreeColumns:
           s.disTree.heading(col, text=col, command=lambda _col=col: s.treeviewSortColumn(s.disTree, _col, False)) 

        s.disTreeScroll = Scrollbar(s.disFrame, orient=VERTICAL)
        s.disTreeScroll.config(command=s.disTree.yview)
        s.disTree.configure(yscrollcommand=s.disTreeScroll.set)

        s.disTree.pack(side=LEFT)
        s.disTreeScroll.pack(side=RIGHT, fill=Y)
        #end disFrame stuff


        s.disLabel = Label(s.commonFrame, text="ICs To Dispense", font=s.monoFontBold)

        s.addButton = Button(s.commonFrame, text="Add Selected ICs", font=s.monoFont, bg="#497efc", command=lambda: s.addItem(s.invTree, s.disTree))

        s.deleteButton = Button(s.commonFrame, text="Remove Selected ICs", font=s.monoFont, bg="#f92529", command=lambda: s.removeItem(s.disTree))

        s.dispenseFrame = Frame(s.commonFrame, relief=RIDGE, borderwidth=5)
        s.dispenseButton = Button(s.dispenseFrame, text="Dispense", font=s.monoFont, bg="lime", command=s.initDispenseRoutine)
        s.dispenseButton.grid(row=0, column=0)

        #commonframe grid
        s.invLabel.grid(row=0, column=0)
        s.invFrame.grid(row=1, column=0, rowspan=2)
        s.addButton.grid(row=3, column=0, sticky=EW)
        s.disLabel.grid(row=0, column=1)
        s.disFrame.grid(row=1, column=1, sticky=N)
        s.deleteButton.grid(row=2, column=1, sticky=EW)
        s.dispenseFrame.grid(row=3, column=1, sticky=E)

        #CONTROLFRAME STUFF
        s.advancedFrame = LabelFrame(s.controlFrame, text="Advanced", font=s.monoFont, relief=RIDGE, borderwidth=5)

        #advancedFrame stuff
        s.enableSMButton = Button(s.advancedFrame, text="Enable Selector Motor", font=s.monoFont, command=s.enableSM)
        s.enableDMButton = Button(s.advancedFrame, text="Enable Dispenser Motor", font=s.monoFont, command=s.enableDM)
        s.disableSMButton = Button(s.advancedFrame, text="Disable Selector Motor", font=s.monoFont, command=s.disableSM)
        s.disableDMButton = Button(s.advancedFrame, text="Disable Dispenser Motor", font=s.monoFont, command=s.disableDM)
        s.homeSelectorButton = Button(s.advancedFrame, text="Home Selector", font=s.monoFont, command=s.homeSM)
        s.homeDispenserButton = Button(s.advancedFrame, text="Home Dispenser", font=s.monoFont, command=s.homeDM)
        s.moveOneButton = Button(s.advancedFrame, text="Move to next tube", font=s.monoFont, command=s.moveOne)
        s.moveToSelectedItemButton = Button(s.advancedFrame, text="Move to selected item", font=s.monoFont, command=s.moveToSelectedItem)

        s.enableSMButton.grid(row=0, column=0, sticky=W)
        s.enableDMButton.grid(row=2, column=0, sticky=W)
        s.disableSMButton.grid(row=1, column=0, sticky=W)
        s.disableDMButton.grid(row=3, column=0, sticky=W)
        s.homeSelectorButton.grid(row=4, column=0, sticky=W)
        s.homeDispenserButton.grid(row=5, column=0, sticky=W)
        s.moveOneButton.grid(row=6, column=0, sticky=W)
        s.moveToSelectedItemButton.grid(row=7, column=0, sticky=W)
        #end advancedFrame stuff

        s.disableButton = Button(s.controlFrame, text="STOP", font=s.monoFont, bg="red", fg="white", width=10, height=4, command=s.disableAll)

        s.undoButton = Button(s.controlFrame, text="Undo", font=s.monoFont, bg="orange", command=s.undoDispense)
        
        s.updateInvButton = Button(s.controlFrame, text="Update Inventory", font=s.monoFont, command=lambda: s.updateInvTree(s.invTree))

        #controlFrame grid
        s.advancedFrame.grid(row=0, column=0, rowspan=3)
        s.updateInvButton.grid(row=1, column=1)
        s.disableButton.grid(row=2, column=1)
        s.undoButton.grid(row=3, column=1)

        #MESSAGEFRAME STUFF
        s.messageListBoxFrame = Frame(s.messageFrame)

        #messageListBoxFrame stuff
        s.messageListBoxScroll = Scrollbar(s.messageListBoxFrame, orient=VERTICAL)
        s.messageListBox = Listbox(s.messageListBoxFrame, width=50, height=26, font=s.monoFont, yscrollcommand=s.messageListBoxScroll.set)
        s.messageListBoxScroll.config(command=s.messageListBox.yview)
        s.messageListBox.pack(side=LEFT)
        s.messageListBoxScroll.pack(side=RIGHT, fill=Y)
        #end messageListBoxFrame stuff

        s.messageClearButton = Button(s.messageFrame, text="Clear Messages", font=s.monoFont, command=s.clearMessageListBox)

        #messageFrame grid
        s.messageListBoxFrame.grid(row=0, column=0)
        s.messageClearButton.grid(row=1, column=0, sticky=W)


        #OTHER INIT STUFF
        s.updateInvTree(s.invTree)
        s.messageInsert("IC Dispenser Started")
        s.openSerial()

        global serialQueue
        serialQueue = queue.Queue()

        serialThread = SerialThread(s.ser)
        serialThread.start()
        s.processSerialRead()

    def messageInsert(s, message):
        s.messageListBox.insert(END, message)
        print("message: " + message)

    def clearMessageListBox(s):
        s.messageListBox.delete(0, END)

    def treeviewSortColumn(s, treeview, col, reverse):
        l = [(treeview.set(k, col), k) for k in treeview.get_children('')]
        l.sort(reverse=reverse)

        #rearrange the items in sorted positions
        for i, (val, k) in enumerate(l):
            treeview.move(k, '', i)

        #reverse sorting
        treeview.heading(col, command=lambda _col=col: s.treeviewSortColumn(treeview, _col, not reverse))

    def updateInvTree(s, treeview):
        inventory = s.getInventoryFromFile()
        treeview.delete(*treeview.get_children())
        for item in inventory:
            index = inventory.index(item)
            name = item[0]
            qty = item[1]
            tubeType = item[2]
            treeview.insert("", "end", iid=index, values=(name, index, qty, tubeType))
        treeview.selection_set(0)

    #Add item to list of selected items (itemListBox2), occurs when right arrow button is pressed
    #If no item is selected, it adds the first item (index 0)
    def addItem(s, treeviewFrom, treeviewTo):
        index = treeviewFrom.selection()[0]
        indexInt = int(index)

        values = treeviewFrom.set(index)
        name = values['Part']
        qtyLeft = values['Qty']
        tubeType = values['Tube']
        qty = 1

        if int(qtyLeft) > 0:
            indexesAlreadyIn = []
            for item in treeviewTo.get_children(""):
                indexesAlreadyIn.append(item)
            if index in indexesAlreadyIn:
                qtyAlreadyIn = treeviewTo.set(index)['Qty']
                qtyNew = int(qtyAlreadyIn) + int(qty)
                if qtyNew <= int(qtyLeft):
                    treeviewTo.set(index, column="Qty", value=qtyNew)
                    s.messageInsert("Added IC: " + name + " at index " + index)
                else:
                    s.messageInsert("error: not enough ICs")
            else:
                treeviewTo.insert("", "end", iid=index, values=(name, index, qty, tubeType))
                s.messageInsert("Added IC: " + name + " at index " + index)
        else:
            s.messageInsert("error: no ICs left in tube")

    #Remove item from list of selected items (itemListBox2), occurs when left arrow button is pressed
    def removeItem(s, treeview):
        selectedItems = treeview.selection()
        if len(selectedItems) > 0:
            index = selectedItems[0]
            name = treeview.set(index)['Part']
            treeview.delete(index)
            s.messageInsert("Removed IC: " + name + " at index " + index)

    #Update inventory list from inventory.csv file
    #First reads the file and puts contents in inventory list (sorted by index)
    #Creates a formattedInventory array, formatted for use in the itemListBox, using contents from inventory list
    def getInventoryFromFile(s):
        inventory = []
        with open(s.invFilePath, 'r') as invFile:
            itemData = csv.reader(invFile, delimiter=',')
            for item in itemData:
                inventory.append(item)

        print("inventory after reading: " + str(inventory))
        return inventory

    #Functionality for overwriting a single value to the inventory.csv file.
    #indexStr - string containing index of item to modify
    #valueType - string specifying the parameter to modify. Options are  "name", "qtyInTube" 
    #value - new value to write
    def writeInventory(s, indexStr, valueType, value):
        itemData = []
        
        #Read the inventory.csv file first and put into list
        with open(s.inventoryFilePath, 'r') as inventoryFile:
            itemFile = csv.reader(inventoryFile, delimiter=',')
            for item in itemFile:
                itemData.append(item)

        print("itemData when writing: " + str(itemData))

        index = int(indexStr)

        #Get row that will be modified
        itemRow = itemData[index]

        if valueType == "name":
            itemData[index] = [value, itemRow[1]]
        elif valueType == "qtyInTube":
            itemData[index] = [itemRow[0], value]

        print("itemData when writing2: " + str(itemData))

        #Write back the entire inventory to the file
        with open(s.inventoryFilePath, 'w') as inventoryFile:
            writer = csv.writer(inventoryFile, delimiter=',')
            for item in itemData:
                writer.writerow(item)

        s.updateInventory()
        #s.sortOptionMenuChange()

    #Open serial communications with microcontroller
    def openSerial(s):
        port = "/dev/USB-SERIAL-CABLE"
        baud = 9600

        try:
            s.ser = serial.Serial(port, baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
            s.messageInsert("serial connected")
        except:
            s.messageInsert("error: failed to open serial")

    #Send data over serial with added carriage return
    def sendSerial(s, data):
        print("serialT: " + data)
        data = data + "\n"
        try:
            s.ser.write(data.encode('utf-8'))
            return True
        except:
            s.messageInsert("error: serial port closed")
            return False

    #Enable selector motor
    def enableSM(s):
        success = s.sendSerial(s.enableSelCommand)
        if success: s.messageInsert("enabling selector motor")

    #Enable dispenser motor
    def enableDM(s):
        success = s.sendSerial(s.enableDisCommand)
        if success: s.messageInsert("enabling dispenser motor")

    #Disable selector motor
    def disableSM(s):
        success = s.sendSerial(s.disableSelCommand)
        if success: s.messageInsert("disabling selector motor")

    #Disable dispenser motor
    def disableDM(s):
        success: s.sendSerial(s.disableDisCommand)
        if success: s.messageInsert("disabling dispenser motor")

    #Disable both motors
    def disableAll(s):
        success1 = s.sendSerial(s.disableSelCommand)
        success2 = s.sendSerial(s.disableDisCommand)
        if success1 and success2: s.messageInsert("disabling all")
        s.resetDisR()

    #Home selector motor
    def homeSM(s):
        success = s.sendSerial(s.homeSelCommand)
        if success: s.messageInsert("homing selector")

    #Move selector to next tube (for testing)
    def moveOne(s):
        success = s.sendSerial(s.moveSelNextCommand)
        if success: s.messageInsert("moving to next item")

    #Home dispenser motor
    def homeDM(s):
        success = s.sendSerial(s.homeDisCommand)
        if success: s.messageInsert("homing dispenser")

    def initHome(s):
        s.state = "homing"
        s.hasHomed = True
        s.sendCommandWithArgument(s.dispenseCommand, -3)

    #Move selector to item selected in itemListBox, mainly for debug
    def moveToSelectedItem(s):
        #if s.hasHomed:
        name = s.itemListBox.get(ACTIVE)
        index = s.formattedInventory.index(name) #get the listbox index of the item
        s.sendCommandWithArgument(s.moveSelCommand, index)
        s.messageInsert("Moving to tube " + name)
        #else:
        #    s.initHome()

    #Send serial command that has a three-digit argument
    def sendCommandWithArgument(s, command, arg):
        argStr = ""

        #Add zeros to make sure argument is exactly three digits
        if int(arg) < 10:
            argStr = "00" + str(arg)
        elif int(arg) < 100:
            argStr = "0" + str(arg)
        else:
            argStr = str(arg)
        s.sendSerial(command + argStr)

    #Initiialze the dispense routine. How the dispense routine works:
    #This method is run whenever the dispense button is pressed. It adds the items in the selected items list
    #(listbox2) to the dispense list. The dispense list is a 2D list that contains the hardware index and
    #number of items to dispense in each row. When items are read from the selected items list, either a new
    #row in the dispense list is created (if that item's index not already in the dispense list) or add 1 to
    #the dispense amount in an existing row (if the item's index is already in the dispense list).
    #
    #disMoveToIndex() is called, then waits for a serial signal from the microcontroller to say it is done moving
    #to position. disDispense() is called, and it waits for another signal to say it is done dispensing.
    #disNext() is called, which updates stuff and either ends the dispense routine, or calls disMoveToIndex() again
    #if there is another item to dispense
    def initDispenseRoutine(s):
        #if there are any items selected to dispense
        if s.itemListBox2.size() > 0:
            listItems = s.itemListBox2.get(0, END)

            for item in listItems:
                #find the 'i' in the formatted listbox string. The item's index is the character after the 'i'
                iLocation = item.find('i')
                indexLocation = iLocation + 1

                #Set index by substringing the formmated listbox string
                index = item[indexLocation : indexLocation + 1]

                #determine if index is already in dispense list
                for item in s.dispense:
                    if item[0] == index:
                        alreadyIn = True
                        break
                    else:
                        alreadyIn = False

                if len(s.dispense) == 0:
                    alreadyIn = False

                if not alreadyIn:
                    s.dispense.append([index, '1'])
                else:
                    for item in s.dispense:
                        if item[0] == index:
                            #Add 1 to the item's quantity to dispense
                            item[1] = str(int(item[1]) + 1)
            print(s.dispense)
            
            s.disRMoveToIndex()

        else:
            s.messageInsert("error: no items to dispense")

    #Sends a moveToIndex command during the dispense routine based on the first index in the dispense list
    def disRMoveToIndex(s):
        index = s.dispense[0][0]
        s.sendCommandWithArgument(s.moveSelCommand, index)
        s.state = "moveToIndex"
        s.messageInsert("Dispense: Moving to index " + index)

    #Sends a dispense command during the dispense routine based on the dispense and inventory lists.
    #Calculates number of millimeters to dispense
    def disRDispense(s):
        qtyToDispense = int(s.dispense[0][1])
        s.sendCommandWithArgument(s.dispenseCommand, qtyToDispense)
        s.state = "dispense"
        s.messageInsert("Dispense: Dispensing " + str(qtyToDispense) + " items")

    #Updates inventory.csv file, dispense list, inventory list after a dispense action. Repeats the dispense
    #cycle by running disMoveToIndex if there are more items to dispense
    def disRNext(s):
        index = int(s.dispense[0][0])
        qtyDispensed = int(s.dispense[0][1])
        qtyInTube = int(s.inventory[index][1])

        #update inventory.csv file 
        s.writeInventory(s.dispense[0][0], "qtyInTube", str(qtyInTube - qtyDispensed))

        del s.dispense[0]

        print("dispenseList: " + str(s.dispense))

        if len(s.dispense) == 0:
            s.itemListBox2.delete(0, END)
            s.state = "none"
            s.messageInsert("Dispense: Done")
        else:
            s.disRMoveToIndex()

    def resetDisR(s):
        s.dispense = []

    def undoDispense(s):
        pass

    #Runs when window is closed. Used to update hasExited so SerialThread knows when to stop
    def onClosing(s):
        s.messageInsert("EXITING")
        global hasExited
        hasExited = True
        root.destroy()
    
    #Reads serialQueue and does things depending on what is read. Run in a loop once every 100 milliseconds
    def processSerialRead(s):
        global serialQueue
        while not serialQueue.empty():
            serialLine = serialQueue.get() #also removes item from queue
            print("serialR: " + serialLine)
             
            if serialLine == "done moving to index" and s.state == "moveToIndex":
                s.disRDispense()
            elif serialLine == "done homing dispenser":
                if s.state == "dispense":
                    s.disRNext()
                elif s.state == "homing":
                    s.homeSM()
            elif serialLine == "start sel home":
                s.messageInsert("Homing selector")
            elif serialLine == "done homing selector" and s.state == "homing":
                s.state = "none"
            elif serialLine == "dispenser already homed":
                s.messageInsert("dispenser already homed")

        root.after(100, s.processSerialRead)

#Reads serial port in a separate thread
class SerialThread(threading.Thread):

    def __init__(s, serial):
        threading.Thread.__init__(s)
        s.ser = serial

    def run(s):
        global hasExited
        global serialQueue
        while not hasExited and s.ser is not None:
            serBuffer = ""
            while True:
                c = s.ser.read().decode('ascii')
    
                if len(c) == 0:
                    break
    
                if c == '\n':
                    #print("serialR: " + serBuffer)
                    serialQueue.put(serBuffer)
    
                    serBuffer = ""
                elif c != '\r':
                    serBuffer += c

root = Tk()
app = App(root)
root.protocol("WM_DELETE_WINDOW", app.onClosing)
root.mainloop()
