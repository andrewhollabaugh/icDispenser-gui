from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial
import csv
import threading
import queue
import time

global hasExited
global serialQueue 

class App:
    
    monoFont = ("Monospace", 9)
    monoFontBold = ("Monospace", 9, "bold")

    invFilePath = "/home/andrew/icDispenser-gui/inventory.csv"
    logFilePath = "/home/andrew/icDispenser-gui/log.txt"
    
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
    global hasExited
    hasExited = False

    #App constructor
    #Initializes the interface; creates widgets and sets widget settings
    def __init__(s, root):

        root.title("IC Dispenser")
        
        #WIDGET HIERARCHY
        #commonFrame
        #   -invLabel
        #   -invFrame
        #       -invTree
        #       -invTreeScroll
        #   -disLabel
        #   -disFrame
        #       -disTree
        #       -disTreeScroll
        #   -addButton
        #   -removeButton
        #   -dispenseFrame
        #       -dispenseButton
        #controlFrame
        #   -advancedFrame
        #       -enableSMButton
        #       -enableDMButton
        #       -disableSMButton
        #       -disableDMButton
        #       -homeSelectorDMButton
        #       -homeDispenserButton
        #       -moveOneButton
        #       -moveToSelectedItemButton
        #       -dontCareCheckbutton
        #       -dontUpdateInvCheckbutton
        #   -miscFrame
        #       -disableButton
        #       -changeItemsButton
        #messageFrame
        #   -messageListBoxFrame
        #       -messageListBox
        #       -messageListBoxScrollbar
        #       -messageClearButton

        #TOP-LEVEL FRAMES
        s.commonFrame = Frame(root, relief=RIDGE, borderwidth=5)
        s.controlFrame = Frame(root)
        s.messageFrame = Frame(root, relief=RIDGE, borderwidth=5)

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
        s.invTree.column("Index", width=50, anchor='c')
        s.invTree.column("Qty", width=50, anchor='c')
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
        s.disTree = ttk.Treeview(s.disFrame, column=disTreeColumns, show="headings", selectmode="extended", height=17)
        s.disTree.column("Part", width=100, anchor='w')
        s.disTree.column("Index", width=50, anchor='c')
        s.disTree.column("Qty", width=50, anchor='c')
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


        s.addFrame = Frame(s.commonFrame, relief=SUNKEN, borderwidth=2)
        s.addButton = Button(s.addFrame, text="Add Selected IC", font=s.monoFont, bg="#497efc", width=25, command=lambda: s.addItem(s.invTree, s.disTree, s.addSpinbox.get(), dontCare.get()))
        s.addQtyLabel = Label(s.addFrame, text="Qty: ", font=s.monoFont)

        s.addSpinbox = Spinbox(s.addFrame, from_=1, to=99, width=2)
        s.addQtyLabel.grid(row=0, column=0)
        s.addSpinbox.grid(row=0, column=1)
        s.addButton.grid(row=0, column=2)

        s.deleteFrame = Frame(s.commonFrame, relief=SUNKEN, borderwidth=2)
        s.deleteButton = Button(s.deleteFrame, text="Remove Selected IC", font=s.monoFont, bg="#f95c61", width=25, command=lambda: s.removeItem(s.disTree, s.deleteSpinbox.get()))
        s.deleteAllButton = Button(s.deleteFrame, text="Remove All ICs", font=s.monoFont, bg="#ff0000", command=lambda: s.removeAllItems(s.disTree))
        s.deleteQtyLabel = Label(s.deleteFrame, text="Qty: ", font=s.monoFont)
        s.deleteSpinbox = Spinbox(s.deleteFrame, from_=1, to=99, width=2)

        s.deleteQtyLabel.grid(row=0, column=0)
        s.deleteSpinbox.grid(row=0, column=1)
        s.deleteButton.grid(row=0, column=2)
        s.deleteAllButton.grid(row=1, column=0, columnspan=3, sticky=EW)

        s.dispenseFrame = Frame(s.commonFrame, relief=RIDGE, borderwidth=5)
        s.dispenseButton = Button(s.dispenseFrame, text="Dispense", font=s.monoFont, bg="lime", width=36, command=lambda: s.disRInit(s.disTree))
        s.dispenseButton.grid(row=0, column=0)

        #commonframe grid
        s.invLabel.grid(row=0, column=0)
        s.invFrame.grid(row=1, column=0, rowspan=2)
        s.addFrame.grid(row=3, column=0)
        s.disLabel.grid(row=0, column=1)
        s.disFrame.grid(row=1, column=1, sticky=N)
        s.deleteFrame.grid(row=2, column=1)
        s.dispenseFrame.grid(row=3, column=1, sticky=EW)

        #CONTROLFRAME STUFF
        s.advancedFrame = LabelFrame(s.controlFrame, text="Advanced", font=s.monoFont, relief=RIDGE, borderwidth=5)
        s.miscFrame = LabelFrame(s.controlFrame, text="Misc", font=s.monoFont, relief=RIDGE, borderwidth=5)

        #advancedFrame stuff
        s.enableSMButton = Button(s.advancedFrame, text="Enable Selector Motor", font=s.monoFont, command=s.enableSM)
        s.enableDMButton = Button(s.advancedFrame, text="Enable Dispenser Motor", font=s.monoFont, command=s.enableDM)
        s.disableSMButton = Button(s.advancedFrame, text="Disable Selector Motor", font=s.monoFont, command=s.disableSM)
        s.disableDMButton = Button(s.advancedFrame, text="Disable Dispenser Motor", font=s.monoFont, command=s.disableDM)
        s.homeSelectorButton = Button(s.advancedFrame, text="Home Selector", font=s.monoFont, command=s.homeSM)
        s.homeDispenserButton = Button(s.advancedFrame, text="Home Dispenser", font=s.monoFont, command=s.homeDM)
        s.moveOneButton = Button(s.advancedFrame, text="Move to next tube", font=s.monoFont, command=s.moveOne)
        s.moveToSelectedItemButton = Button(s.advancedFrame, text="Move to selected tube", font=s.monoFont, command=lambda: s.moveToSelectedItem(s.invTree))

        dontCare = IntVar()
        s.dontCareCheckbutton = Checkbutton(s.advancedFrame, text="Don't care if there aren't enough ICs left", variable=dontCare)

        s.dontUpdateInv = IntVar()
        s.dontUpdateInvCheckbutton = Checkbutton(s.advancedFrame, text="Don't update inventory after dispensing", variable=s.dontUpdateInv)

        s.enableSMButton.grid(row=0, column=0, sticky=W)
        s.enableDMButton.grid(row=2, column=0, sticky=W)
        s.disableSMButton.grid(row=1, column=0, sticky=W)
        s.disableDMButton.grid(row=3, column=0, sticky=W)
        s.homeSelectorButton.grid(row=4, column=0, sticky=W)
        s.homeDispenserButton.grid(row=5, column=0, sticky=W)
        s.moveOneButton.grid(row=6, column=0, sticky=W)
        s.moveToSelectedItemButton.grid(row=7, column=0, sticky=W)
        s.dontCareCheckbutton.grid(row=8, column=0, sticky=W)
        s.dontUpdateInvCheckbutton.grid(row=9, column=0, sticky=W)
        #end advancedFrame stuff

        #miscFrame stuff
        s.disableButton = Button(s.miscFrame, text="STOP", font=s.monoFont, bg="red", fg="white", width=10, height=4, command=s.disableAll)
        s.updateInvButton = Button(s.miscFrame, text="Update Inventory", font=s.monoFont, bg="orange", command=lambda: s.updateInvButtonPress(s.invTree))
        s.reconnectSerialButton = Button(s.miscFrame, text="Reconnect Serial", font=s.monoFont, bg="teal", command=s.reconnectSerial)

        s.disableButton.grid(row=0, column=0, sticky=W)
        s.updateInvButton.grid(row=1, column=0, sticky=W)
        s.reconnectSerialButton.grid(row=2, column=0, sticky=W)
        #end miscFrame stuff

        #controlFrame grid
        s.advancedFrame.grid(row=0, column=0)
        s.miscFrame.grid(row=1, column=0, sticky=EW)

        #MESSAGEFRAME STUFF
        s.messageListBoxFrame = Frame(s.messageFrame)

        #messageListBoxFrame stuff
        s.messageListBoxScroll = Scrollbar(s.messageListBoxFrame, orient=VERTICAL)
        s.messageListBox = Listbox(s.messageListBoxFrame, width=70, height=28, font=s.monoFont, yscrollcommand=s.messageListBoxScroll.set)
        s.messageListBoxScroll.config(command=s.messageListBox.yview)
        s.messageListBox.pack(side=LEFT)
        s.messageListBoxScroll.pack(side=RIGHT, fill=Y)
        #end messageListBoxFrame stuff

        s.messageClearButton = Button(s.messageFrame, text="Clear Messages", font=s.monoFont, command=s.clearMessageListBox)

        #messageFrame grid
        s.messageListBoxFrame.grid(row=0, column=0)
        s.messageClearButton.grid(row=1, column=0, sticky=W)


        #OTHER INIT STUFF
        s.openSerial()
        s.updateInvFromFile(updateTotalTubes=True)
        s.updateInvTree(s.invTree)

        global serialQueue
        serialQueue = queue.Queue()

        serialThread = SerialThread(s.ser)
        serialThread.start()
        s.processSerialRead()


    def askHomeOnStartup(s):
        if messagebox.askyesno("Home?", "The IC Dispenser must be homed before use. Would you like to home?"):
            s.homeSM()

    def messageInsert(s, message):
        localtime = time.asctime(time.localtime(time.time()))
        message = "[" + localtime + "] " + message
        s.messageListBox.insert(END, message)
        s.messageListBox.yview_moveto(1)
        print("message: " + message)
	
        with open(s.logFilePath, 'a') as logFile:
            logFile.write(message + "\n")

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

    def updateInvButtonPress(s, treeview):
        s.updateInvFromFile(updateTotalTubes=True)
        s.updateInvTree(treeview)

    #Updates the inventory treeview based on the inventory file
    def updateInvTree(s, treeview):
        treeview.delete(*treeview.get_children())
        for item in s.inventory:
            index = s.inventory.index(item)
            name = item[0]
            qty = item[1]
            tubeType = item[2]
            treeview.insert("", "end", iid=index, values=(name, index, qty, tubeType))

    #Add selected item from invTree to disTree
    def addItem(s, treeviewFrom, treeviewTo, qty, dontCare):
        if len(treeviewFrom.selection()) > 0:
            index = treeviewFrom.selection()[0]
        else:
            s.messageInsert("error: no tube selected")
            return

        indexInt = int(index)

        values = treeviewFrom.set(index)
        name = values['Part']
        qtyLeft = values['Qty']
        tubeType = values['Tube']

        if int(qtyLeft) > 0 or dontCare:
            indexesAlreadyIn = []
            for item in treeviewTo.get_children(""): #determine which tubes (indexes) are already in disTree
                indexesAlreadyIn.append(item)
            if index in indexesAlreadyIn: #if already in, get the already in quantity and add new quantity
                qtyAlreadyIn = treeviewTo.set(index)['Qty']
                qtyNew = int(qtyAlreadyIn) + int(qty)
                if qtyNew <= int(qtyLeft) or dontCare:
                    treeviewTo.set(index, column="Qty", value=qtyNew)
                    s.messageInsert("Added IC: " + name + " at index " + index + " qty of " + qty)
                else:
                    s.messageInsert("error: not enough ICs")
            else:
                treeviewTo.insert("", "end", iid=index, values=(name, index, qty, tubeType))
                s.messageInsert("Added IC: " + name + " at index " + index + " qty of " + qty)
        else:
            s.messageInsert("error: not enough ICs")

    #Remove selected item from disTree
    def removeItem(s, treeview, qty):
        selectedItems = treeview.selection()
        if len(selectedItems) > 0:
            index = selectedItems[0]
            name = treeview.set(index)['Part']
            qtyPresent = treeview.set(index)['Qty']
            qtyToRemove = int(qty)
            qtyLeft = qtyPresent - qtyToRemove
            if qtyLeft >= 0:
                if qtyLeft == 0:
                    treeview.delete(index)
                else:
                    treeview.set(index, column="Qty", value=qtyLeft)
                s.messageInsert("Removed IC: " + name + " at index " + index + " qty of " + qty)
            else:
                s.messageInsert("not enough ICs")
        else:
            s.messageInsert("error: nothing seleced")

    def removeAllItems(s, treeview):
        treeview.delete(*treeview.get_children())
        s.messageInsert("Removed all ICs")

    #Get inventory list based on inventory.csv file
    def updateInvFromFile(s, updateTotalTubes=False):
        s.inventory = []
        with open(s.invFilePath, 'r') as invFile:
            itemData = csv.reader(invFile, delimiter=',')
            for item in itemData:
                s.inventory.append(item)

        #send the inventory length (# of indexes) to controller so it can position correctly
        if updateTotalTubes and s.ser is not None:
            s.sendCommandWithArg(s.totalTubesCommand, len(s.inventory))

        print("inventory after reading: " + str(s.inventory))

    #Functionality for overwriting a single value to the inventory.csv file.
    #index - index of item to modify
    #valueType - string specifying the parameter to modify. Options are "name", "qty", "tubeType" 
    #value - new value to write
    def writeInv(s, index, valueType, value):
        print("inventory before writing: " + str(s.inventory))

        indexInt = int(index)

        #Get row that will be modified
        row = s.inventory[index]

        if valueType == "name":
            s.inventory[index] = [value, row[1], row[2]]
        elif valueType == "qty":
            s.inventory[index] = [row[0], value, row[2]]
        elif valueType == "tubeType":
            s.inventory[index] = [row[0], row[1], value]

        print("s.inventory after writing: " + str(s.inventory))

        #Write back the entire inventory to the file
        with open(s.invFilePath, 'w') as invFile:
            writer = csv.writer(invFile, delimiter=',')
            for item in s.inventory:
                writer.writerow(item)

    #Open serial communications with microcontroller
    def openSerial(s):
        port = "/dev/USB-SERIAL-CABLE"
        baud = 9600

        try:
            s.ser = serial.Serial(port, baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
            s.messageInsert("serial connected")
        except:
            s.messageInsert("error: failed to open serial")

    #Send data over serial with \n
    def sendSerial(s, data):
        print("serialT: " + data)
        data = data + "\n"
        try:
            s.ser.write(data.encode('utf-8'))
            return True
        except:
            s.messageInsert("error: serial port closed")
            return False

    def reconnectSerial(s):
        s.openSerial()
        s.askHomeOnStartup()

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
        s.resetDisR()

    #Disable dispenser motor
    def disableDM(s):
        success = s.sendSerial(s.disableDisCommand)
        if success: s.messageInsert("disabling dispenser motor")
        s.resetDisR()

    #Disable both motors
    def disableAll(s):
        success1 = s.sendSerial(s.disableSelCommand)
        success2 = s.sendSerial(s.disableDisCommand)
        if success1 and success2: s.messageInsert("disabling all")
        s.resetDisR()

    #Home selector motor
    def homeSM(s):
        s.sendSerial(s.homeSelCommand)

    #Move selector to next tube (for testing)
    def moveOne(s):
        success = s.sendSerial(s.moveSelNextCommand)
        if success: s.messageInsert("moving to next item")

    #Home dispenser motor
    def homeDM(s):
        success = s.sendSerial(s.homeDisCommand)
        if success: s.messageInsert("homing dispenser")

    #Move selector to item selected in itemListBox, mainly for debug
    def moveToSelectedItem(s, treeview):
        index = treeview.selection()[0]
        s.sendCommandWithArg(s.moveSelCommand, index)
        #s.messageInsert("Moving to tube " + name)

    #Send serial command that has a three-digit argument
    def sendCommandWithArg(s, command, arg):
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
    def disRInit(s, treeview):
        s.dispense = []
        indexesToDispense = treeview.get_children("")

        if len(indexesToDispense) > 0:
            for index in indexesToDispense:
                qty = treeview.set(index)['Qty']
                s.dispense.append([int(index), qty])
            print("dispenseList: " + str(s.dispense))
            s.disRMoveToIndex(treeview)
        else:
            s.messageInsert("error: no items to dispense")

    #Sends a moveToIndex command during the dispense routine based on the first index in the dispense list
    def disRMoveToIndex(s, treeview):
        index = s.dispense[0][0]
        s.sendCommandWithArg(s.moveSelCommand, index)
        s.state = "moveToIndex"
        treeview.selection_set(index)
        s.messageInsert("Dispense: moving to index " + str(index))

    #Sends a dispense command during the dispense routine based on the dispense and inventory lists.
    #Calculates number of millimeters to dispense
    def disRDispense(s):
        qty = s.dispense[0][1]
        s.sendCommandWithArg(s.dispenseCommand, qty)
        s.state = "dispense"
        s.messageInsert("Dispense: dispensing " + str(qty) + " items")

    def disRUpdate(s, treeview, dontUpdateInv):
        index = s.dispense[0][0]

        if not dontUpdateInv:
            qtyDispensed = s.dispense[0][1]
            qtyInTube = int(s.inventory[index][1])
            s.writeInv(s.dispense[0][0], "qty", str(qtyInTube - int(qtyDispensed)))

        del s.dispense[0]
        treeview.delete(index)
        print("dispenseList: " + str(s.dispense))

    #Updates inventory.csv file, dispense list, inventory list after a dispense action. Repeats the dispense
    #cycle by running disMoveToIndex if there are more items to dispense
    def disRNext(s, treeview):
        if len(s.dispense) == 0:
            s.state = "none"
            s.messageInsert("Dispense: Done")
        else:
            s.disRMoveToIndex(treeview)

    def resetDisR(s):
        s.dispense = []
        s.state = "none"

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
             
            messagesToPass = ["IC dispenser ready", "done homing selector", "done homing dispenser", "dispenser already homed", "dispenser not homed! dispensing now", "error: dispenser went too far!"]
            if serialLine in messagesToPass:
                s.messageInsert(serialLine)
            elif serialLine == "start sel home":
                s.messageInsert("homing selector")

            if serialLine == "done moving to index" and s.state == "moveToIndex":
                s.disRDispense()
            elif serialLine == "dispenser homing" and s.state == "dispense":
                s.disRUpdate(s.disTree, s.dontUpdateInv.get())
                s.updateInvTree(s.invTree)
            elif serialLine == "done homing dispenser" and s.state == "dispense":
                s.disRNext(s.disTree)
            elif serialLine == "IC dispenser ready":
                s.askHomeOnStartup()

        root.after(50, s.processSerialRead)

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
