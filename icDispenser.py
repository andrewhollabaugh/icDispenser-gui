from tkinter import *
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

    inventoryFilePath = "/home/andrew/icDispenser-gui/inventory.csv"
    itemListFormat = "{:<12} #InTube {:<6} i{:<}"
    inventory = []
    formattedInventory = []
    selectedItems = []
    formattedSelectedItems = []
    dispense = []

    port = "/dev/ttyUSB0"
    baud = 9600
    ser = None

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

    state = "none" #Possible states: none, moveToPos, dispense, homing
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
        #controlFrame
        #   -advancedFrame
        #       -debug/test buttons
        #       -serialFrame
        #           -portEntry/connectButton
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

        #itemSelectFrame stuff
        s.itemSelectFrame = Frame(s.commonFrame)
        s.itemListBoxScroll = Scrollbar(s.itemSelectFrame, orient=VERTICAL)
        s.itemListBox = Listbox(s.itemSelectFrame, width=30, height = 25, font=s.monoFont, yscrollcommand=s.itemListBoxScroll.set)
        s.itemListBoxScroll.config(command=s.itemListBox.yview)
        s.updateItemListBox("index")
        s.itemListBox.pack(side=LEFT)
        s.itemListBoxScroll.pack(side=RIGHT, fill=Y)
        #end itemSelectFrame stuff

        s.selectLabel = Label(s.commonFrame, text="Select Items to Dispense", font=s.monoFont)

        #itemSelectFrame2 stuff
        s.itemSelectFrame2 = Frame(s.commonFrame)
        s.itemListBox2Scroll = Scrollbar(s.itemSelectFrame2, orient=VERTICAL)
        s.itemListBox2 = Listbox(s.itemSelectFrame2, width=30, height = 25, font=s.monoFont, yscrollcommand=s.itemListBox2Scroll.set)
        s.itemListBox2Scroll.config(command=s.itemListBox2.yview)
        s.itemListBox2.pack(side=LEFT)
        s.itemListBox2Scroll.pack(side=RIGHT, fill=Y)
        #end itemSelectFrame2 stuff)

        s.selectLabel2 = Label(s.commonFrame, text="Items To Dispense", font=s.monoFont)

        s.sortFrame = Frame(s.commonFrame)

        #sortFrame stuff
        s.sortOptionMenuList = ["Index", "Name"]
        s.sortOptionMenuVar = StringVar(root)
        s.sortOptionMenuVar.trace("w", s.sortOptionMenuChange)
        s.sortOptionMenuVar.set(s.sortOptionMenuList[0])
        s.sortOptionMenu = OptionMenu(s.sortFrame, s.sortOptionMenuVar, *s.sortOptionMenuList)

        s.sortLabel = Label(s.sortFrame, text="Sort By:", font=s.monoFont)

        s.sortLabel.pack(side=LEFT)
        s.sortOptionMenu.pack(side=RIGHT)
        #end sortFrame stuff

        s.addArrowButton = Button(s.commonFrame, text="---->", font=s.monoFont, command=s.addItemToSelected)

        s.deleteArrowButton = Button(s.commonFrame, text="<----", font=s.monoFont, command=s.removeItemFromSelected)

        s.dispenseButton = Button(s.commonFrame, text="Dispense", font=s.monoFont, bg="lime", command=s.initDispenseRoutine)

        #commonframe grid
        s.selectLabel.grid(row=0, column=0)
        s.itemSelectFrame.grid(row=1, column=0, rowspan=2)
        s.sortFrame.grid(row=3, column=0)
        s.addArrowButton.grid(row=1, column=1)
        s.deleteArrowButton.grid(row=2, column=1)
        s.selectLabel2.grid(row=0, column=2)
        s.itemSelectFrame2.grid(row=1, column=2, rowspan=2)
        s.dispenseButton.grid(row=3, column=2, sticky=W)

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

        s.dispenseMMEntry = Entry(s.advancedFrame, width=5)
        s.dispenseMMEntry.insert(0, "0")

        s.dispenseMMButton = Button(s.advancedFrame, text="Dispense by mm", font=s.monoFont, command=s.dispenseByMM)

        s.testDispenseMMButton = Button(s.advancedFrame, text="Test Dispense by mm", font=s.monoFont, command=s.testDispenseByMM)

        s.serialFrame = LabelFrame(s.advancedFrame, text="Serial", font=s.monoFont, relief=RIDGE, borderwidth=5)

        #serialFrame stuff
        s.portLabel = Label(s.serialFrame, text="Port", font=s.monoFont)
        s.portEntry = Entry(s.serialFrame, width=8)
        s.connectButton = Button(s.serialFrame, text="Connect", font=s.monoFont)

        s.portLabel.grid(row=0, column=0, sticky=E)
        s.portEntry.grid(row=0, column=1)
        s.connectButton.grid(row=1, column=0, columnspan=2)
        #end serialFrame stuff

        s.enableSMButton.grid(row=0, column=0, sticky=W)
        s.enableDMButton.grid(row=2, column=0, sticky=W)
        s.disableSMButton.grid(row=1, column=0, sticky=W)
        s.disableDMButton.grid(row=3, column=0, sticky=W)
        s.homeSelectorButton.grid(row=4, column=0, sticky=W)
        s.homeDispenserButton.grid(row=5, column=0, sticky=W)
        s.moveOneButton.grid(row=6, column=0, sticky=W)
        s.moveToSelectedItemButton.grid(row=7, column=0, sticky=W)
        s.dispenseMMButton.grid(row=0, column=1)
        s.testDispenseMMButton.grid(row=1, column=1)
        s.dispenseMMEntry.grid(row=2, column=1)
        s.serialFrame.grid(row=3, column=1, rowspan=3)
        #end advancedFrame stuff

        s.disableButton = Button(s.controlFrame, text="Disable", font=s.monoFont, bg="red", fg="white", width=10, height=4, command=s.disableAll)

        
        s.changeItemsButton = Button(s.controlFrame, text="Change Item Locations", font=s.monoFont)

        #controlFrame grid
        s.advancedFrame.grid(row=0, column=0, rowspan=3)
        s.changeItemsButton.grid(row=1, column=1)
        s.disableButton.grid(row=2, column=1)

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
        s.updateInventoryFromFile()
        s.updateItemListBox("index")
        s.openSerial()
        s.messageInsert("IC Dispenser Started")

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

    #Reads inventory list and updates item list box to display the list contents sorted by index or name
    #sortType - string containing either "index" or "name" for sorting type
    def updateItemListBox(s, sortType):
        s.itemListBox.delete(0, END)
        if sortType == "index":
            for item in s.formattedInventory:
                s.itemListBox.insert(END, item)
        elif sortType == "name":
            for item in numpy.sort(s.formattedInventory): #sorts inventory by name
                s.itemListBox.insert(END, item)

    #Run whenever sortOptionMenu changes. Runs updateItemListBox to redisplay list contents after sorting type changes
    def sortOptionMenuChange(s, *args):
        if s.sortOptionMenuVar.get() == "Index":
            s.updateItemListBox("index")
        elif s.sortOptionMenuVar.get() == "Name":
            s.updateItemListBox("name")

    #Enable selector motor
    def enableSM(s):
        s.sendSerial(s.enableSelCommand)
        s.messageInsert("enabling selector motor")

    #Enable dispenser motor
    def enableDM(s):
        s.sendSerial(s.enableDisCommand)
        s.messageInsert("enabling dispenser motor")

    #Disable selector motor
    def disableSM(s):
        s.sendSerial(s.disableSelCommand)
        s.messageInsert("disabling selector motor")

    #Disable dispenser motor
    def disableDM(s):
        s.sendSerial(s.disableDisCommand)
        s.messageInsert("disabling dispenser motor")

    #Disable both motors
    def disableAll(s):
        s.sendSerial(s.disableSelCommand)
        s.sendSerial(s.disableDisCommand)
        s.messageInsert("disabling all")

    #Home selector motor
    def homeSM(s):
        s.sendSerial(s.homeSelCommand)
        s.messageInsert("homing selector")

    #Move selector to next tube (for testing)
    def moveOne(s):
        s.sendSerial(s.moveSelNextCommand)
        s.messageInsert("moving to next item")

    #Home dispenser motor
    def homeDM(s):
        s.sendSerial(s.homeDisCommand)
        s.messageInsert("homing dispenser")

    #Update inventory list from inventory.csv file
    #First reads the file and puts contents in inventory list (sorted by index)
    #Creates a formattedInventory array, formatted for use in the itemListBox, using contents from inventory list
    def updateInventoryFromFile(s):
        s.inventory = []
        with open(s.inventoryFilePath, 'r') as inventoryFile:
            itemData = csv.reader(inventoryFile, delimiter=',')
            for item in itemData:
                s.inventory.append(item)

        print("inventory after reading: " + str(s.inventory))

        s.formattedInventory = []
        for item in s.inventory:
            index = s.inventory.index(item)
            name = item[0];
            amount = item[1];
            itemInfoList = [name, amount, index]
            s.formattedInventory.append(s.itemListFormat.format(name, amount, index))

    #Functionality for overwriting a single value to the inventory.csv file.
    #indexStr - string containing index of item to modify
    #valueType - string specifying the parameter to modify. Options are  "name", "qtyInTube", "icLength", or "tubeLength" 
    #value - new value to write
    def writeInventoryFile(s, indexStr, valueType, value):
        itemData = []
        
        #Read the inventory.csv file first and put into list
        with open(s.inventoryFilePath, 'r') as inventoryFile:
            itemFile = csv.reader(inventoryFile, delimiter=',')
            for item in itemFile:
                itemData.append(item)

        print("itemData when writing1: " + str(itemData))

        index = int(indexStr)

        #Get row that will be modified
        itemRow = itemData[index]

        if valueType == "name":
            itemData[index] = [value, itemRow[1], itemRow[2], itemRow[3]]
        elif valueType == "qtyInTube":
            itemData[index] = [itemRow[0], value, itemRow[2], itemRow[3]]
        elif valueType == "icLength":
            itemData[index] = [itemRow[0], itemRow[1], value, itemRow[3]]
        elif valueType == "tubeLength":
            itemData[index] = [itemRow[0], itemRow[1], itemRow[2], value]

        print("itemData when writing2: " + str(itemData))

        #Write back the entire inventory to the file
        with open(s.inventoryFilePath, 'w') as inventoryFile:
            writer = csv.writer(inventoryFile, delimiter=',')
            for item in itemData:
                writer.writerow(item)

        s.updateInventoryFromFile()
        s.sortOptionMenuChange()

    #Open serial communications with microcontroller
    def openSerial(s):
        try:
            s.ser = serial.Serial(s.port, s.baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
            print("serial connected")
        except:
            print("error: failed to open serial")

    #Send data over serial with added carriage return
    def sendSerial(s, data):
        print("serialT: " + data)
        data = data + "\n"
        try:
            s.ser.write(data.encode('utf-8'))
        except:
            print("error: serial is disconnected")

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

    #Dispense a number of millimeters based on an Entry widget, mainly for debug
    def dispenseByMM(s):
        mm = s.dispenseMMEntry.get()
        s.sendCommandWithArgument(s.dispenseCommand, mm)
        s.messageInsert("Dispenseing " + mm + " mm")

    def testDispenseByMM(s):
        mm = s.dispenseMMEntry.get()
        s.sendCommandWithArgument(s.dispenseNoHomeCommand, mm)
        s.messageInsert("Testing Dispense " + mm + " mm")

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

    #Add item to list of selected items (itemListBox2), occurs when right arrow button is pressed
    #If no item is selected, it adds the first item (index 0)
    def addItemToSelected(s):
        #if there is at least one item selected
        if len(s.itemListBox.curselection()) > 0:
            itemToAddIndex = s.itemListBox.curselection()[0]
        else:
            itemToAddIndex = 0

        #check if the number of ICs in tube > 0
        if int(s.inventory[itemToAddIndex][1]) > 0:
            itemToAddName = s.itemListBox.get(itemToAddIndex)
            s.itemListBox2.insert(END, itemToAddName)
            s.messageInsert("Added item: " + itemToAddName)
        else:
            s.messageInsert("error: no ICs left in tube")

    #Remove item from list of selected items (itemListBox2), occurs when left arrow button is pressed
    def removeItemFromSelected(s):
        #if there is at least one item selected
        if len(s.itemListBox2.curselection()) > 0:
            itemToRemoveIndex = s.itemListBox2.curselection()[0]
        else:
            itemToRemoveIndex = 0
        itemToRemoveName = s.itemListBox2.get(itemToRemoveIndex)
        s.itemListBox2.delete(itemToRemoveIndex)
        s.messageInsert("Removed item: " + itemToRemoveName)

    #Initiialze the dispense routine. How the dispense routine works:
    #This method is run whenever the dispense button is pressed. It adds the items in the selected items list
    #(listbox2) to the dispense list. The dispense list is a 2D list that contains the hardware index and
    #number of items to dispense in each row. When items are read from the selected items list, either a new
    #row in the dispense list is created (if that item's index not already in the dispense list) or add 1 to
    #the dispense amount in an existing row (if the item's index is already in the dispense list).
    #
    #disMoveToPos() is called, then waits for a serial signal from the microcontroller to say it is done moving
    #to position. disDispense() is called, and it waits for another signal to say it is done dispensing.
    #disNext() is called, which updates stuff and either ends the dispense routine, or calls disMoveToPos() again
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
            
            s.disRMoveToPos()

        else:
            s.messageInsert("error: no items to dispense")

    #Sends a moveToPos command during the dispense routine based on the first index in the dispense list
    def disRMoveToPos(s):
        index = s.dispense[0][0]
        s.sendCommandWithArgument(s.moveSelCommand, index)
        s.state = "moveToPos"
        s.messageInsert("Dispense: Moving to index " + index)

    #Sends a dispense command during the dispense routine based on the dispense and inventory lists.
    #Calculates number of millimeters to dispense
    def disRDispense(s):
        index = int(s.dispense[0][0])
        qtyToDispense = int(s.dispense[0][1])
        qtyInTube = int(s.inventory[index][1])
        icLength = float(s.inventory[index][2])
        tubeLength = float(s.inventory[index][3])
        mm = float((tubeLength - (qtyInTube * icLength)) + (qtyToDispense * icLength))
        mmR = int(round(mm))
        s.sendCommandWithArgument(s.dispenseCommand, mmR)
        s.state = "dispense"
        s.messageInsert("Dispense: Dispensing " + str(qtyToDispense) + " items; moving " + str(mmR) + " mm")

    #Updates inventory.csv file, dispense list, inventory list after a dispense action. Repeats the dispense
    #cycle by running disMoveToPos if there are more items to dispense
    def disRNext(s):
        index = int(s.dispense[0][0])
        qtyDispensed = int(s.dispense[0][1])
        qtyInTube = int(s.inventory[index][1])

        #update inventory.csv file 
        s.writeInventoryFile(s.dispense[0][0], "qtyInTube", str(qtyInTube - qtyDispensed))

        del s.dispense[0]

        print("dispenseList: " + str(s.dispense))

        if len(s.dispense) == 0:
            s.itemListBox2.delete(0, END)
            s.state = "none"
            s.messageInsert("Dispense: Done")
        else:
            s.disRMoveToPos()

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
             
            if serialLine == "done moving to pos" and s.state == "moveToPos":
                    s.disRDispense()
            elif serialLine == "done homing dispenser":
                if s.state == "dispense":
                    s.disRNext()
                elif s.state == "homing":
                    s.homeSM()
            elif serialLine == "homing...":
                s.messageInsert("Homing selector")
            elif serialLine == "done homing selector" and s.state == "homing":
                s.state = "none"

        root.after(100, s.processSerialRead)

#Reads serial port in a separate thread
class SerialThread(threading.Thread):

    def __init__(s, serial):
        threading.Thread.__init__(s)
        s.ser = serial

    def run(s):
        global hasExited
        global serialQueue
        while not hasExited:
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
