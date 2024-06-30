from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
import os
import shutil
import secrets
import json

validProMicroPins = ["D3","D2","D1","D0","D4","C6","D7","E6","B4","B5","D5","B0","F4","F5","F6","F7","B1","B3","B2","B6"]

def makeDirectory(directoryPath):
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, rf'{directoryPath}')
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

def copyDirectory(fromDirectoryPath, toDirectoryPath):
    current_directory = os.getcwd()
    finalFromDirectory = os.path.join(current_directory, rf'{fromDirectoryPath}')
    finalToDirectory = os.path.join(current_directory, rf'{toDirectoryPath}')

    # fetch all files
    for file_name in os.listdir(finalFromDirectory):
        # construct full file path
        source = os.path.join(finalFromDirectory, rf'{file_name}')
        destination = os.path.join(finalToDirectory, rf'{file_name}')
        # copy only files
        if os.path.isfile(source):
            shutil.copy(source, destination)
            print('copied', file_name)
    
def writeFileNewLine(file, toWrite):
    with open(file, "a") as f:
        f.write(f'{toWrite}\n')

def writeFile(file, toWrite):
    with open(file, "a") as f:
        f.write(f'{toWrite}')

def replaceLine(fileName, lineNum, text):
    lines = open(fileName, 'r').readlines()
    lines[lineNum-1] = text
    out = open(fileName, 'w')
    out.writelines(lines)
    out.close()

def main():
    absoluteDirectory = os.path.dirname(os.path.abspath(__file__))

    # Ask user information --------------
    MCU = prompt("MCU (Atmega32u4 or RP2040): ", completer=WordCompleter(['Atmega32u4', 'RP2040']))
    keyboardName = prompt("Firmware File Name: ", history=FileHistory("History/.keyboard-name-history-file")).lower()
    keyboardPRODUCT = prompt("Firmware PRODUCT Name: ", history=FileHistory("History/.keyboard-PRODUCT-Name-history-file"))
    keyboardProductID = prompt("Firmware ProductID: ", history=FileHistory("History/.keyboard-PRODUCT-ID-history-file"))
    inputRows = prompt("Rows: ", history=FileHistory("History/.keyboard-rows-history-file"))
    inputColumns = prompt("Columns: ", history=FileHistory("History/.keyboard-cols-history-file"))
    for row in inputRows.split(","):
        if row in inputColumns.split(","):
            print(f"Duplicate Pin used for Row/Column: {row}")
            return
    encoderNumber = prompt("Number of Encoders: ")
    if keyboardName == "" or inputColumns == "" or inputRows == "" or keyboardPRODUCT =="" or keyboardProductID == "" or encoderNumber == "":
        print("Exiting")
        return
    encoderPinAArray = []
    encoderPinBArray = []
    if int(encoderNumber) != 0:
        for i in range(int(encoderNumber)):
            Apin = prompt(f"Encoder{i} A pin: ")
            Bpin = prompt(f"Encoder{i} B pin: ")
            encoderPinAArray.append(Apin)
            encoderPinBArray.append(Bpin)

    rows = inputRows.split(',')
    cols = inputColumns.split(',')

    # end ask user information ----------------------
    
    print(keyboardName)
    # move template into new folder
    makeDirectory(f"{absoluteDirectory}/Generated/")
    makeDirectory(f"{absoluteDirectory}/Generated/{keyboardName}")
    makeDirectory(f"{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial")
    print(2)
    copyDirectory(f'{absoluteDirectory}/Template',f"{absoluteDirectory}/Generated/{keyboardName}")
    print(3)
    copyDirectory(f'{absoluteDirectory}/Template/keymaps/vial',f"{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial")
    print(4)
    
    #update keymaps/vial/config.h file
    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/config.h',18,"#define VIAL_KEYBOARD_UID {{{}}}\n".format(", ".join(["0x{:02X}".format(x) for x in secrets.token_bytes(8)])))


    #rules.mk
    if MCU == "RP2040":
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/rules.mk',2,f"MCU = RP2040\n")
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/rules.mk',5,f"BOOTLOADER = rp2040\n")

    
    #info.json
    info = {}
    info["keyboard_name"] = keyboardName
    if MCU == "RP2040":
        info["processor"] = "RP2040"
        info["bootloader"] = "rp2040"
    info["usb"] = {}
    info["usb"]["pid"] = keyboardProductID
    info["usb"]["vid"] = "0x5049"
    info["usb"]["device_version"] = "0.0.1"
    info["url"] = "http://www.pikatea.com"
    info["maintainer"] = "Jack Kester"
    info["manufacturer"] = "Jack Kester"
    info["dynamic_keymap"] = {}
    info["dynamic_keymap"]["layout_count"] = 4
    # info["matrix_size"] = {}
    # info["matrix_size"]["cols"] = len(cols)
    # info["matrix_size"]['rows'] = len(rows)
    info["diode_direction"] = "COL2ROW"
    info["features"] = {"bootmagic": True,"command": False,"console": False,"mousekey": False,"extrakey": True,"nkro": False}
    if int(encoderNumber) != 0:
        info["features"]["encoder"] = True
    info["matrix_pins"] = {"cols":cols,"rows": rows}
    if int(encoderNumber) != 0:
        info["encoder"] = {"enable": True, "rotary": []}
        for i in range(int(encoderNumber)):
            info["encoder"]["rotary"].append({"pin_a": encoderPinAArray[i], "pin_b": encoderPinBArray[i]})
    info["layouts"] = {"LAYOUT": {"layout": []}}
    for r in range(len(rows)):
        for c in range(len(cols)):
            info["layouts"]["LAYOUT"]["layout"].append({"label":f"k{r}{c}","x":r,"y":c,"matrix":[r, c]})
    
    

    with open(f"{absoluteDirectory}/Generated/{keyboardName}/info.json", "w") as fp:
        json.dump(info, fp)


    #keymap.c
    if int(encoderNumber) != 0:
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/keymap.c',33,'#if defined(ENCODER_MAP_ENABLE)\nconst uint16_t PROGMEM encoder_map[][NUM_ENCODERS][2] = {')
        encoderKeymapSubstring = ""
        for i in range(int(encoderNumber)):
            encoderKeymapSubstring += "ENCODER_CCW_CW(KC_VOLD, KC_VOLU)"
            if i != int(encoderNumber)-1:
                encoderKeymapSubstring += ","
        for i in range(4):
            replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/keymap.c',35+i,"    ["+str(i)+"] =   { "+encoderKeymapSubstring+"  },\n")
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/keymap.c',39,"};\n#endif\n")
    keymapString = ""
    for row in range(len(rows)):
        for col in range(len(cols)):
            if col == len(cols)-1 and row == len(rows)-1:
                keymapString += "_______ "
            else:
                keymapString += "_______, "
        keymapString += "\n"
    
    for lineNumber in [29,26,23,20]:
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/keymap.c',lineNumber,keymapString)
    
    

    #vial.json
    encoderNumberTemp = int(encoderNumber)
    encoderCount = 0
    jsonString = ""
    if len(rows) < encoderNumberTemp:
        print('\033[91m' + 'Not enough rows for all encoders in Vial.json' + '\033[0m')
    for row in range(len(rows)):
        jsonString += "[\n"
        for col in range(len(cols)):
            if col == len(cols)-1:
                jsonString += f'"{row},{col}"\n'
                if (encoderNumberTemp) > 0:
                    encoderNumberTemp -= 1
                    jsonString += f',"{encoderCount},0\\n\\n\\n\\n\\n\\n\\n\\n\\ne","{encoderCount},1\\n\\n\\n\\n\\n\\n\\n\\n\\ne"'
                    encoderCount += 1
            else:
                jsonString += f'"{row},{col}",\n'
        if row == len(rows)-1:
            jsonString += "]\n"
        else:
            jsonString += "],\n"

    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/vial.json',12,jsonString)
    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/vial.json',4,f'  "productId": "{keyboardProductID}",\n')
    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/vial.json',2,f'  "name": "{keyboardName}",\n')
    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/vial.json',7,f'    "rows": {len(rows)},\n')
    replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/vial.json',8,f'    "cols": {len(cols)}\n')


    #rules.mk in vial folder
    if int(encoderNumber) != 0:
        replaceLine(f'{absoluteDirectory}/Generated/{keyboardName}/keymaps/vial/rules.mk',5,"ENCODER_ENABLE = yes\nENCODER_MAP_ENABLE = yes\n")


if __name__ == '__main__':
    main()