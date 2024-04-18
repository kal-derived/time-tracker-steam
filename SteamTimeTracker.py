import winreg
import datetime
import time
import os
from ast import literal_eval

checkDelay = 8 # Limits the program to 1 check every 'x' seconds - Affects timing accuracy & performance
dirty = False # Determines whether the records should be updated or not

folder = winreg.HKEY_CURRENT_USER
pathString = "SOFTWARE\\Valve\\Steam\\Apps\\"

filePath = os.path.expanduser('~') + "\\Documents\\"
outputName = "gameRecords.txt"

gameAndDateRecords = [] # The array of game info that will be read from/written to file
listOfRunningGames = []

# Find the Steam "folder" (key) in the registry
def GetFolder(pathTo):

    keys = []
    keyCount = 0
    while 1:
        try:
            key = winreg.EnumKey(pathTo, keyCount)
            #print(key)
            keys.append(key)
            keyCount += 1

        except WindowsError as e:
            break

    return keys

# Obtain the game info (value) in the registry folder (key)
def GetValuesInFolder(pathTo, pathStr, folderIndex):

    localRegKeys = GetFolder(pathTo)
    newFolder = winreg.OpenKeyEx(folder, pathString + localRegKeys[folderIndex])
    localCount = 0
    values = []

    while 1:
        try:
            
            values.append(winreg.EnumValue(newFolder, localCount))
            #print(values)

            localCount = localCount + 1

        except WindowsError as subError:
            #print(subError)
            winreg.CloseKey(newFolder)
            break

    winreg.CloseKey(newFolder)
    return values

# Write out the game info to file
def OverwriteRecords(data):
    
    with open(filePath + outputName, 'w') as file:
        for entry in data:
            file.write(str(entry))
        file.close()

# Read in the game records (if they exist)
def ReadFile():  
    
    with open(filePath + outputName, 'r') as file:
        data = file.readlines()
        #file.close() Not needed when using 'with'
    for i in range(0, len(data)):
        data[i] = literal_eval(data[i])
        
    return data
    
# Scan the steam-related registry keys for valid games
def ReadRegKeys():
    #Obtain the register keys related to game info
    path = winreg.OpenKeyEx(folder, pathString)
    regkeys = GetFolder(path)
    count = 0
    finalValues = []
    for k in regkeys:
        finalValues.append(GetValuesInFolder(path, pathString, count))
        count += 1
    winreg.CloseKey(path)

    #Obtain the values from the keys, swap value places if needed, and append to the game list
    gameLibrary = []
    changed = False
    for value in finalValues:
        currentGame = {"Name": None, "Running": ""}
        for property in value:
            if property[0] == "Name":
                currentGame["Name"] = property[1]
                #print(currentGame["Name"])
                changed = True
            if property[0] == "Running":
                currentGame["Running"] = property[1]
                changed = True
        if changed == True:
            gameLibrary.append(currentGame)

    # Woulda used a for-in loop, but it auto moves to the next item (which skips current index if we remove an item, which may also be an empty to remove)
    i = 0
    while i < len(gameLibrary):
        try:
            print(gameLibrary[i]["Name"][0]) #checks if the entry has a printable name
            i = i + 1
        except:
            gameLibrary.pop(i) 
    return gameLibrary

# Check if the search term 'item' is in the dataset 'data'
def FindGameInRecords(item, data):
    i = 0
    for entry in data:
        if item["Name"] == entry["Name"]:
            return i
        i = i + 1
    return -1
            
#Check the if any games have began running recently
def CheckRunningGames():
    global gameAndDateRecords

    gameRegInfo = ReadRegKeys()
    gameAndDateRecords = ReadFile()

    for game in gameRegInfo:
        gameDateEntry = {"Name": "", "StartDate": 0, "TotalTime": 0, "SessionStart": 0, "SessionEnd":0}
    
        #Track game if it's currently running
        if game["Running"] == True and game not in listOfRunningGames:
            print("THERES A GAME RUNNING")
            #check if running game is in records already 
            recordIndex = FindGameInRecords(game, gameAndDateRecords)
            if recordIndex != -1:
                gameDateEntry = gameAndDateRecords[recordIndex]
            else:
                gameDateEntry["Name"] = game["Name"]
                gameDateEntry["StartDate"] = datetime.datetime.timestamp(datetime.datetime.now())

            gameDateEntry["SessionStart"] = datetime.datetime.timestamp(datetime.datetime.now())
            listOfRunningGames.append(gameDateEntry)

#Check if any games have stopped running and tally their running time if so
def CalculateRunningTime():
    global dirty
    gameRegInfo = ReadRegKeys() #Need the register values to know what's stoppped runnning
    
    for activeGame in listOfRunningGames:
        i = 0
        for gameReg in gameRegInfo:
            #Check if game is still running
            if activeGame["Name"] == gameReg["Name"] and gameReg["Running"] == False:
                dirty = True
                #Calculate the time spent running & remove it from the list
                activeGame["SessionEnd"] = datetime.datetime.timestamp(datetime.datetime.now())
                activeGame["TotalTime"] += (activeGame["SessionEnd"] - activeGame["SessionStart"])
                print("New total time: " + str(activeGame["TotalTime"]))
                #Update the game info records, or add it to the records if its not there
                if UpdateGameInfo(activeGame) == False:
                    print("Adding new entry " + str(activeGame))
                    gameAndDateRecords.append(activeGame)
                listOfRunningGames.pop(i)
                print("Records: " + str(gameAndDateRecords))
        i += 1
    if dirty == True:
        OverwriteRecords(gameAndDateRecords)

#Loop through the list of game records and update the one in question 
def UpdateGameInfo(gameToUpdate):
    global gameAndDateRecords
    print("Help 0")
    for i in range(0, len(gameAndDateRecords)):
        if gameAndDateRecords[i]["Name"] == gameToUpdate["Name"]:
            print("Game in records: " + gameAndDateRecords[i]["Name"] + " | " + str(gameAndDateRecords[i]["TotalTime"]))
            print("Game to update: " + gameToUpdate["Name"] + " | " + str(gameToUpdate["TotalTime"]))
            gameAndDateRecords[i] = gameToUpdate
            print("Updated game: "+ gameAndDateRecords[i]["Name"] + " | " + str(gameAndDateRecords[i]["TotalTime"]))
            return True
    print("Game info couldn't be updated since it wasn't found in the records")
    return False

# Main loop - runs forever in console until closed manually
while True:
    CheckRunningGames()
    print(listOfRunningGames)
    CalculateRunningTime()
    time.sleep(checkDelay)

