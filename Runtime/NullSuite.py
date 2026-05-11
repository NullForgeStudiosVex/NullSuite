#!/usr/bin/env python3
import tkinter as tk
from tkinter import (ttk,filedialog,messagebox)
import subprocess
import threading
import setproctitle
import json
import os
import time
import webbrowser
import sys
import re
import shutil
import getpass
import queue
from queue import Queue
import select
import mido
import uinput

os.environ["PULSE_PROP_application.name"] = "NullMidiSounds"

import pygame

# ==========================================================================================
# Startup :)
# ==========================================================================================
SystemLoading = True
StartUpDelay = 100 #if you're looking at this thinking "wtf why a delay?" because tkinter runs on 1 thread...trying to make it load everything, and generate UI, and fill the UI all in 1ms is....bad. so. delay. you wont notice it.
Root = tk.Tk()
Root.title("NullSuite")
Root.geometry("1600x900")
Main = tk.Frame(Root)
Main.pack(fill="both", expand=True, padx=10, pady=10)
style = ttk.Style()
style.map("TNotebook.Tab",foreground=[("disabled", "#666666"),("selected", "#000000"),("!disabled", "#000000")])


LoadPopup = tk.Toplevel(Root)
LoadPopup.title("Loading NullSuite Data")
Width = 800
Height = 450
Root.update_idletasks()
RootX = Root.winfo_x()
RootY = Root.winfo_y()
RootWidth = Root.winfo_width()
RootHeight = Root.winfo_height()
X = RootX + ((RootWidth // 2) - (Width // 2))
Y = RootY + ((RootHeight // 2) - (Height // 2))
LoadPopup.geometry(f"{Width}x{Height}+{X}+{Y}")
LoadPopup.resizable(False, False)
LoadPopup.transient(Root)
LoadPopup.grab_set()
LoadPopup.attributes("-topmost", True)
LoadFrame = tk.Frame(LoadPopup)
LoadFrame.pack(fill="both", expand=True)
tk.Label(LoadFrame,text="This might take a bit if you have a lot of things going.\n If you're really lucky, you won't even be able to read this message.\n\n haha. look at you with the fast computer. NERD",font=("Arial", 12)).pack(expand=True)
LoadPopup.update()

def BlockClose():
    pass

LoadPopup.protocol("WM_DELETE_WINDOW", BlockClose)

# ————————————————————————————————————————————————————————————
# Directories, Dicts, Lists, Other
# ————————————————————————————————————————————————————————————
BaseDir = os.path.dirname(os.path.abspath(__file__))
IconPath = os.path.join(BaseDir,"NullSuite.png")
ConfigPath = os.path.join(BaseDir,"NullSuite.json")
Python = os.path.join(BaseDir, "venv", "bin", "python3")
NWPath = os.path.join(BaseDir, "NW.sh") 
IconImage = tk.PhotoImage(file=IconPath)
Root.iconphoto(True, IconImage)
LoadTimes = {}
LoadCompleted = 0
ProgramCount = 0
StartUpTimeString = tk.StringVar(value="")
# ------------------------------
# NullProton
# ------------------------------
ProtonDrive = os.path.join(BaseDir, "ProtonDrive")
ProtonVars = {
    "Default": tk.StringVar(value="[ not set ]"),
    "A": tk.StringVar(value="[ not set ]"),
    "B": tk.StringVar(value="[ not set ]")
}
ProtonGames = []
ProtonGameRows = []
LogQueue = queue.Queue()
# ------------------------------
# NullRip
# ------------------------------
Titles = []
SelectedChapters = []
SelectedAudio = []
SelectedSubs = []
SelectedTitle = None
CurrentProcess = None
# ------------------------------
# NullMidi
# ------------------------------
MidiRows = []
SaveRows = []
MidiDeviceListeners = {}
UInputDevice = None
ActiveCapture = {
    "Type": None,
    "Cancel": False
}
SoundQueue = Queue()
pygame.mixer.init(buffer=256)
pygame.mixer.set_num_channels(128)
OverflowChannel = 33
# ------------------------------
# NullWire
# ------------------------------
Sinks = {}
Devices = {
    "A": {f"A{i}": None for i in range(1, 21)},
    "M": {f"M{i}": None for i in range(1, 21)}
}
OutputDevices = []
OutputDeviceSelection = []
InputDevices = []
InputDeviceSelection = []
AudioSources = []
IgnoreSources = [
    "speech-dispatcher",
    "speech-dispatcher-dummy",
]
# ------------------------------
# NullCursor
# ------------------------------
Overlays = None
OverlayWindows = []
HideJob = None
ScanForMouse = False
XdotoolPath = shutil.which("xdotool") or "xdotool"
XrandrPath = shutil.which("xrandr") or "xrandr"
StartDetection = 0.01
EdgeBuffer = 3
ScanTime = 0.10
BaseDir = os.path.dirname(os.path.abspath(__file__))
RootDir = os.path.dirname(BaseDir)
Profiles = {}
ProfileWidgets = {}
ActiveProfile = None
LastMousePos = None
LastMoveTime = 0
LastWarpTime = 0
WarpCooldown = 0.01
Offset = 10
if not XdotoolPath or not XrandrPath:
    raise RuntimeError("xdotool or xrandr not found")

# ------------------------------
# NullGit
# ------------------------------
Repos = {}
RepoBoxes = []
CurrentManagedRepo = None
CurrentDownloadProcess = None
# ————————————————————————————————————————————————————————————
# Required Startup Methods
# ————————————————————————————————————————————————————————————

setproctitle.setproctitle("NullSuite")
UpdatePromptShown = False

def GetRepoRoot():
    return os.path.dirname(BaseDir)

def IsGitInstall():
    return os.path.isdir(os.path.join(GetRepoRoot(), ".git"))

def UpdateAvailable():
    RepoRoot = GetRepoRoot()

    try:
        subprocess.run(
            ["git", "-C", RepoRoot, "fetch"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )

        local = subprocess.check_output(
            ["git", "-C", RepoRoot, "rev-parse", "HEAD"]
        ).strip()

        remote = subprocess.check_output(
            ["git", "-C", RepoRoot, "rev-parse", "origin/main"]
        ).strip()

        return local != remote
    except:
        return False

def StartTray():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("AppIndicator3", "0.1")

    from gi.repository import Gtk, AppIndicator3

    indicator = AppIndicator3.Indicator.new(
        "nullsuite",
        IconPath,
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )

    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()


    def Toggle(_):
        def DoToggle():
            if Root.state() == "withdrawn":
                Root.deiconify()
                Root.lift()
                Root.focus_force()
            else:
                Root.withdraw()

        Root.after(0, DoToggle)

    def OpenFileLocation(_):
        subprocess.Popen(["xdg-open", BaseDir])
    
    def Quit(_):
        if SystemLoading:
            return
        
        subprocess.run([NWPath, "ClearSinks"])
        subprocess.run(
                    ["pkill", "-x", "NSLauncher.sh"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        Root.after(0, Root.destroy)
        Gtk.main_quit()

    # ==============================
    # Menu Items
    # ==============================
    toggle = Gtk.MenuItem(label="Show / Hide")
    toggle.connect("activate", Toggle)
    menu.append(toggle)

    filelocation = Gtk.MenuItem(label="Open File Location")
    filelocation.connect("activate", OpenFileLocation)
    menu.append(filelocation)

    spacer = Gtk.MenuItem(label="———")
    spacer.set_sensitive(False)
    menu.append(spacer)

    quitbtn = Gtk.MenuItem(label="Quit")
    quitbtn.connect("activate", Quit)
    menu.append(quitbtn)

    menu.show_all()
    indicator.set_menu(menu)

    Gtk.main()

def GetSavableMidiRows():
    global SaveRows
    SaveRows = []
    for Row in MidiRows:
        SaveRow = {}
        for Key, Value in Row.items():
            if Key in [
                "VirtualPort",
                "Frame",
                "Button",
                "Widgets"
            ]:
                continue
            SaveRow[Key] = Value
        SaveRows.append(SaveRow)
    return SaveRows

def LoadConfig():
    global StartUpDelay, ProgramCount # to control delay
    global Profiles, ActiveProfile, ScanForMouse #NullWire
    global Devices, Sinks #NullWire
    global ProtonGames #NullProton
    global MidiRows #NullMidi
    global Repos #NullGit
    

    if not os.path.isfile(ConfigPath):
        return False

    try:
        with open(ConfigPath, "r") as f:
            data = json.load(f)

        print("Loading States")
        # ==============================
        # LoadStatesFirst
        # ==============================
        proton = data.get("NullProton", {})
        wire = data.get("NullWire", {})
        cursor = data.get("NullCursor", {})
        midi = data.get("NullMidi", {})
        repos = data.get("NullGit", {})

        ProgramCount = 5
        
        # ==============================
        # NullWire
        # ==============================
        print("Loading NullWire")

        def LoadNullWire():
            global Sinks, Devices, LoadCompleted
            Sinks.clear()
            Sinks.update(wire.get("Sinks", {}))

            Devices["A"].update(wire.get("DevicesA", {}))
            Devices["M"].update(wire.get("DevicesM", {}))

            subprocess.run([NWPath, "ClearSinks"])

            for name, sink in Sinks.items():
                subprocess.run([NWPath, "CreateSink", name])
                for d, enabled in sink["Outputs"].items():
                    device = Devices["A"].get(d)
                    if not device or not enabled:
                        continue
                    subprocess.run([NWPath,"ConnectSinkToAux",name,device["ID"],str(int(sink["Mono"]))])
                for d, enabled in sink["Inputs"].items():
                    device = Devices["M"].get(d)
                    if not device or not enabled:
                        continue
                    subprocess.run([NWPath,"ConnectMicToSink",device["ID"],name])
                for src in sink["Sources"]:
                    subprocess.run([NWPath,"ConnectSourceToSink",src,name])
                
            NullWireRebuildUI()
            RefreshRoutingUI()

            LoadCompleted += 1

        Root.after(StartUpDelay, LoadNullWire)


        
        # ==============================
        # NullCursor
        # ==============================
        print("Loading NullCursor")

        def LoadNullCursor():
            global ActiveProfile, ScanForMouse,LoadCompleted
            Profiles.clear()
            Profiles.update(cursor.get("Profiles", {}))
            ActiveProfile = cursor.get("ActiveProfile")
            ScanForMouse = cursor.get("ScanForMouse", False)
            if len(Profiles) == 0:
                Profiles["Default"] = {
                    "Layout": CaptureLayout(),
                    "Warps": {}
                }
                ActiveProfile = "Default"
                SaveConfig()
            BuildUIFromProfiles()
            NullCursorEnabledVar.set(ScanForMouse)
            ToggleNullCursor()
            LoadCompleted += 1

        Root.after(StartUpDelay + 10, LoadNullCursor)


        # ==============================
        # NullMidi
        # ==============================
        print("Loading NullMidi")

        def LoadNullMidi():
            global LoadCompleted
            for row in midi.get("MidiRows", []):
                AddMidiRow(row, True)
            LoadCompleted+=1

        Root.after(StartUpDelay + 20, LoadNullMidi)

        # ==============================
        # NullGit
        # ==============================
        print("Loading NullGit")

        def LoadNullGit():
            global Repos, LoadCompleted
            Repos = repos.get("Repos", {})
            BuildRepoList()
            LoadCompleted +=1

        Root.after(StartUpDelay + 30, LoadNullGit)

        # ==============================
        # NullProton
        # ==============================
        print("Loading NullProton")


        def LoadNullProton():
            global LoadCompleted
            ProtonVars["Default"].set(proton.get("Default", "[ not set ]"))
            ProtonVars["A"].set(proton.get("A", "[ not set ]"))
            ProtonVars["B"].set(proton.get("B", "[ not set ]"))

            ProtonGames.clear()
            ProtonGames.extend(proton.get("Games", []))

            for Game in ProtonGames.copy():
                AddGameRow(Game, True)
            LoadCompleted+=1

        Root.after(StartUpDelay + 40, LoadNullProton)
        return True

    except Exception as e:
        print("LoadConfig failed:", e)
        return False

def SaveConfig():
    if LoadCompleted != ProgramCount:
        print("Attempted to save while loading")
        return
    
    print("Saved")
    
    
    data = {
        # ==============================
        # NullProton
        # ==============================
        "NullProton": {
            "Default": ProtonVars["Default"].get(),
            "A": ProtonVars["A"].get(),
            "B": ProtonVars["B"].get(),
            "Games": ProtonGames
        },

        # ==============================
        # NullWire
        # ==============================
        "NullWire": {
            "Sinks": Sinks,
            "DevicesA": Devices["A"],
            "DevicesM": Devices["M"]
        },

        # ==============================
        # NullCursor
        # ==============================
        "NullCursor": {
            "Profiles": Profiles,
            "ActiveProfile": ActiveProfile,
            "ScanForMouse": ScanForMouse
        },

        # ==============================
        # NullMidi
        # ==============================
        "NullMidi": {
            "MidiRows": GetSavableMidiRows()
        },

        # ==============================
        # NullGit
        # ==============================
        "NullGit": {"Repos":Repos}
    }

    try:
        with open(ConfigPath, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print("SaveConfig failed:", e)

def GetCurrentUpdateBranch():
    RepoRoot = GetRepoRoot()

    try:
        return subprocess.check_output(
            ["git", "-C", RepoRoot, "branch", "--show-current"],
            text=True
        ).strip()
    except:
        return None

def RunUpdateCheck():
    global UpdatePromptShown

    if UpdatePromptShown:
        return
    
    if not IsGitInstall():
        return
    
    if GetCurrentUpdateBranch() != "main":
        return

    if not UpdateAvailable():
        return

    def Prompt():
        from tkinter import messagebox

        if messagebox.askyesno("NullSuite Update", "An update is available. Install now?"):
            UpdaterPath = os.path.join(BaseDir, "Updater.sh")

            subprocess.Popen([UpdaterPath])
            os._exit(0)

    Root.after(0, Prompt)

def BringToFront():
    Root.deiconify()
    Root.lift()
    Root.focus_force()

    Root.attributes("-topmost", True)
    Root.after(50, lambda: Root.attributes("-topmost", False))

def WatchShowSignal():
    ShowPath = os.path.join(BaseDir, "Tools", "NullSuite.show")

    while True:
        if os.path.exists(ShowPath):
            os.remove(ShowPath)

            Root.after(0, BringToFront)

        time.sleep(0.5)

def BindMouseWheel(self, widget):

    try:
        widget.bind("<Button-4>", self.OnMouseWheel)
        widget.bind("<Button-5>", self.OnMouseWheel)
    except:
        pass

    for child in widget.winfo_children():
        self.BindMouseWheel(child)

#Not gonna lie, i tried fucking with this for months, MONTHS.... i asked GPT. I have no shame. Turns out. It wasn't even this method causing the problem. god. damnit :)
class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.Canvas = tk.Canvas(self, highlightthickness=0)

        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.Canvas.yview)

        self.Inner = tk.Frame(self.Canvas)

        self.Window = self.Canvas.create_window((0, 0), window=self.Inner, anchor="nw")

        self.Inner.bind("<Configure>", lambda e: self.Canvas.configure(scrollregion=self.Canvas.bbox("all")))

        self.Canvas.bind("<Configure>", lambda e: self.Canvas.itemconfig(self.Window, width=e.width))

        self.Canvas.configure(yscrollcommand=scrollbar.set)

        self.Canvas.pack(side="left", fill="both", expand=True)

        scrollbar.pack(side="right", fill="y")

        self.BindMouseWheel(self)
        self.BindMouseWheel(self.Canvas)
        self.BindMouseWheel(self.Inner)

    def BindMouseWheel(self, widget):

        widget.bind("<Button-4>", self.OnMouseWheel)
        widget.bind("<Button-5>", self.OnMouseWheel)

        for child in widget.winfo_children():
            self.BindMouseWheel(child)

    def OnMouseWheel(self, event):

        if isinstance(event.widget, (tk.Scale, ttk.Scale)):
            return

        if event.num == 4:
            self.Canvas.yview_scroll(-1, "units")

        elif event.num == 5:
            self.Canvas.yview_scroll(1, "units")

# ==========================================================================================
# System Methods
# ==========================================================================================
# ————————————————————————————————————————————————————————————
# NullSuite
# ————————————————————————————————————————————————————————————



# ————————————————————————————————————————————————————————————
# NullWire
# ————————————————————————————————————————————————————————————
def RefreshOutputDevices():
    global OutputDevices

    try:
        out = subprocess.check_output(["pactl", "list", "sinks"]).decode()
    except:
        OutputDevices = []
        return

    devices = []
    current = {}

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("Name:"):
            current["SystemID"] = line.split(":", 1)[1].strip()

        elif line.startswith("Description:"):
            current["UIName"] = line.split(":", 1)[1].strip()

            if "SystemID" in current:
                devices.append(current)
                current = {}

    OutputDevices = devices

def BuildOutputSelectionList():
    global OutputDeviceSelection
    RefreshOutputDevices()
    used_ids = set()

    for slot in Devices["A"].values():
        if slot and "ID" in slot:
            used_ids.add(slot["ID"])

    OutputDeviceSelection = []

    for device in OutputDevices:
        if device["SystemID"] not in used_ids:
            OutputDeviceSelection.append(device)

    return OutputDeviceSelection

def RefreshInputDevices():
    global InputDevices

    try:
        out = subprocess.check_output(["pactl", "list", "sources"]).decode()
    except:
        InputDevices = []
        return

    devices = []
    current = {}

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("Name:"):
            current["SystemID"] = line.split(":", 1)[1].strip()

        elif line.startswith("Description:"):
            current["UIName"] = line.split(":", 1)[1].strip()

            if "SystemID" in current:
                if ".monitor" not in current["SystemID"]:
                    devices.append(current)
                current = {}

    InputDevices = devices

def BuildInputSelectionList():
    global InputDeviceSelection
    RefreshInputDevices()
    used_ids = set()

    for slot in Devices["M"].values():
        if slot and "ID" in slot:
            used_ids.add(slot["ID"])

    InputDeviceSelection = []

    for device in InputDevices:
        if device["SystemID"] not in used_ids:
            InputDeviceSelection.append(device)

    return InputDeviceSelection

def GetAudioSources():
    global AudioSources
    try:
        out = subprocess.check_output(["pactl", "list", "sink-inputs"]).decode()
    except:
        return []

    sources = []

    for line in out.splitlines():
        line = line.strip()

        if "application.name" in line:
            name = line.split("=", 1)[1].strip().strip('"')

            if any(ignore in name for ignore in IgnoreSources):
                continue

            if name not in sources:
                sources.append(name)

    AudioSources = sources
    return sources

def GetAudioDeviceSystemVolume(DeviceID):
    try:
        out = subprocess.check_output(
            ["pactl", "get-sink-volume", DeviceID]
        ).decode()

        for part in out.split():
            if "%" in part:
                return int(part.replace("%", ""))
    except:
        pass

    return 0

def GetMicrophoneSystemVolume(source):
    try:
        out = subprocess.check_output(
            ["pactl", "get-source-volume", source]
        ).decode()

        for part in out.split():
            if "%" in part:
                return int(part.replace("%", ""))
    except:
        pass

    return 0

def ResolveSinkID(name):
    for d in OutputDevices:
        if d["UIName"] == name:
            return d["SystemID"]
    return None

def ResolveSourceID(target_name):
    out = subprocess.check_output(["pactl", "list", "short", "sources"]).decode()
    for line in out.splitlines():
        parts = line.split()
        idx = parts[0]
        name = parts[1]
        if target_name in name:
            return idx

    return None

def IsOutputEnabled(Sink, key):
    return Sink["Outputs"].get(key, False)

def IsInputEnabled(Sink, key):
    return Sink["Inputs"].get(key, False)

def AddRoutingObject():
    global Sinks
    name = NullWireRoutingEntry.get().strip()
    if not name:
        name = f"Sink {len(Sinks)}"

    name = name + "_NullWire"
    new = {"Mono": False, "Mute":False, "Outputs": {f"A{i}": False for i in range(1, 21)},"Inputs":  {f"M{i}": False for i in range(1, 21)},"Sources": [],"Volume": 100,}
    Sinks[name] = new
    subprocess.run([NWPath,"CreateSink",name])
    SaveConfig()
    RefreshRoutingUI()
    NullWireRoutingEntry.delete(0, tk.END)

def AddRoutingBlock(name, Sink):
    Frame = tk.Frame(NullWireRoutingObjects, bd=2, relief="solid")
    Frame.pack(fill="x", padx=5, pady=5)
    Frame.columnconfigure(0, weight=1)
    Frame.rowconfigure(0, weight=1)
    Frame.rowconfigure(1, weight=1)
    Frame.rowconfigure(2, weight=1)
    Frame.rowconfigure(3, weight=1) 
    Frame.rowconfigure(4, weight=1)
    Frame.rowconfigure(5, weight=1)
    tk.Frame(Frame, height=5)\
    .grid(row=5, column=0, columnspan=3)

    
    # ==============================
    # TOP ROW (DELETE + NAME)
    # ==============================
    def Delete():
        del Sinks[name]
        subprocess.run([NWPath,"DeleteSink",name,])
        SaveConfig() #
        RefreshRoutingUI()

    Column0 = tk.Frame(Frame)
    Column0.grid(row=0, column=0, sticky="ew", padx=5)
    Column0.columnconfigure(0, weight=0)  
    Column0.columnconfigure(1, weight=0)  
    Column0.columnconfigure(2, weight=0)  
    Column0.columnconfigure(3, weight=2) 
    Column0.columnconfigure(3, weight=1) 

    tk.Button(Column0, text="Delete", command=Delete)\
        .grid(row=0, column=0, padx=5, pady=5, sticky="w")
    

    # this is just here cause i added it in 4.0, and sinks created wont have the data sooooo suck it. 
    if "Mute" not in Sink:
        Sink["Mute"] = False

    MonoVar = tk.BooleanVar(value=Sink.get("Mono", False))
    MuteVar = tk.BooleanVar(value=Sink.get("Mute", False))
    InnerFrame = tk.Frame(Column0, bd=2, relief="solid")
    InnerFrame.grid(row=0, column=3, sticky="ew", padx=2)
    InnerFrame.columnconfigure(0, weight=1)
    display_name = name.replace("_NullWire", "")
    tk.Label(InnerFrame, text=display_name, anchor="w")\
    .grid(row=0, column=0, sticky="ew")
    volume_frame = tk.Frame(Column0)
    volume_frame.grid(row=0, column=4, sticky="ew", padx=5)
    volume_frame.columnconfigure(0, weight=1)
    start_vol = Sink.get("Volume", 100)
    vol_var = tk.StringVar(value=str(start_vol))
    after_id = None

    def ApplyVolume():
        volumenumber = scale.get()
        Sink["Volume"] = volumenumber
        SaveConfig()
        subprocess.run([NWPath,"SetSinkVolume",name,str(volumenumber)])

    def ScheduleApply():
        nonlocal after_id
        if after_id:
            Root.after_cancel(after_id)
        after_id = Root.after(150, ApplyVolume)

    def OnVolumeChange(val):
        vol_var.set(str(int(float(val))))

    # ==============================
    # THICK DIVIDER
    # ==============================
    tk.Frame(Frame, height=3, bg="#555")\
        .grid(row=1, column=0, columnspan=3, sticky="ew", pady=3)
    
    # ==============================
    # AUDIO DEVICES ROW
    # ==============================
    RowA = tk.Frame(Frame)
    RowA.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=0)
    RowA.columnconfigure(0, weight=1)
    AllDevices = [f"A{i}" for i in range(1, 21)]
    for i, device in enumerate(AllDevices):
        RowA.columnconfigure(i, weight=1)
        enabled = IsOutputEnabled(Sink, device)
        var = tk.BooleanVar(value=enabled)
        is_active = IsOutputEnabled(Sink, device)
        exists = Devices["A"].get(device) is not None
        def Toggle(d=device, v=var):
            DeviceData = Devices["A"].get(d)
            DeviceID = DeviceData["ID"]
            if v.get():
                subprocess.run([NWPath,"ConnectSinkToAux",name,DeviceID,str(int(Sink["Mono"]))])
                Sink["Outputs"][d] = True
            else:
                subprocess.run([NWPath,"RemoveSinkFromAux",name,DeviceID])
                Sink["Outputs"][d] = False
            SaveConfig()
        cb = tk.Checkbutton(RowA,text=device,variable=var,width=3,command=Toggle,anchor="w")
        cb.grid(row=0, column=i, sticky="ew", padx=2, pady=0)

        if not exists:
            cb.config(state="disabled")

    # ==============================
    # MIC DEVICES ROW
    # ==============================
    RowM = tk.Frame(Frame)
    RowM.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5)
    RowM.columnconfigure(0, weight=1)

    # ------------------------------
    # BUILD TOGGLES
    # ------------------------------
    AllMics = [f"M{i}" for i in range(1, 21)]

    for i, device in enumerate(AllMics):
        RowM.columnconfigure(i, weight=1)
        is_active = IsInputEnabled(Sink, device)
        var = tk.BooleanVar(value=is_active)
        DeviceData = Devices["M"].get(device)
        exists = DeviceData is not None

        def Toggle(d=device, v=var):
            DeviceID = Devices["M"][d]["ID"]
            if v.get():
                subprocess.run([NWPath,"ConnectMicToSink",DeviceID,name])
                Sink["Inputs"][d] = True
            else:
                subprocess.run([NWPath,"RemoveMicFromSink",DeviceID,name])
                Sink["Inputs"][d] = False
            SaveConfig()

        cb = tk.Checkbutton(RowM,text=device,variable=var,width=3,command=Toggle,anchor="w")
        cb.grid(row=0, column=i, sticky="ew", padx=2, pady=0)

        if not exists:
            cb.config(state="disabled")

    # ==============================
    # SOURCES ROW
    # ==============================
    SRow = tk.Frame(Frame)
    SRow.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)
    SRow.columnconfigure(2, weight=1)
    tk.Button(SRow, text="Attach", width=6, command=lambda: OpenAddSourcePopup(name, Sink))\
    .grid(row=0, column=0, sticky="ew")
    tk.Button(SRow, text="Remove", width=6, command=lambda: OpenRemoveSourcePopup(Sink))\
    .grid(row=0, column=1, padx=(5,0), sticky="ew")
    InnerFrameS = tk.Frame(SRow, bd=1, relief="solid")
    InnerFrameS.grid(row=0, column=2, sticky="nsew", padx=5)
    InnerFrameS.columnconfigure(0, weight=1)
    InnerFrameS.rowconfigure(0, weight=1)
    tk.Label(InnerFrameS,text = ", ".join(Sink["Sources"]) if Sink["Sources"] else "",anchor="nw",justify="left").grid(row=0, column=0, sticky="nsew")

    # ==============================
    # Mono cause why not
    # ==============================

    def ToggleMono():
        Sink["Mono"] = MonoVar.get()
        for d, enabled in Sink["Outputs"].items():
            if not enabled:
                continue

            DeviceData = Devices["A"].get(d)
            if not DeviceData:
                continue

            DeviceID = DeviceData["ID"]
            subprocess.run([NWPath,"RemoveSinkFromAux",name,DeviceID])
            subprocess.run([NWPath,"ConnectSinkToAux",name,DeviceID,str(int(Sink["Mono"]))])
        SaveConfig()

    tk.Checkbutton(Column0,text="Mono?",variable=MonoVar,command=ToggleMono)\
        .grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # ==============================
    # Mute is cool ig
    # ==============================
    
    def ToggleMute():
        Sink["Mute"] = MuteVar.get()
        if Sink['Mute']:
            subprocess.run([NWPath,"SetSinkVolume",name,str(0)])
        else:
            ApplyVolume()
        SaveConfig()

    tk.Checkbutton(Column0,text="Mute",variable=MuteVar,command=ToggleMute)\
        .grid(row=0, column=2, padx=5, pady=5, sticky="w")

    NullWireScrollArea.BindMouseWheel(Frame)

    # - putting scale at the end so the feckin mouse scroll still works on it. the FUCK tkinter??? Still love you windows 1995 lookin ass bitch.

    scale = tk.Scale(volume_frame,from_=0,to=150,orient="horizontal",showvalue=0,command=OnVolumeChange)
    scale.grid(row=0, column=0, sticky="ew")
    scale.bind("<ButtonRelease-1>", lambda e: ApplyVolume())
    scale.bind("<Button-4>", lambda e: (scale.set(min(150, scale.get()+5)), ScheduleApply()))
    scale.bind("<Button-5>", lambda e: (scale.set(max(0, scale.get()-5)), ScheduleApply()))
    scale.set(start_vol)
    tk.Label(volume_frame, textvariable=vol_var, width=3)\
    .grid(row=0, column=1, padx=5)


def OpenAddSourcePopup(name, Sink):
    sources = GetAudioSources()

    if len(sources) == 0:
        return

    Popup = tk.Toplevel(Root)
    Popup.title("Attach Source")
    Popup.geometry("300x400")
    Popup.grab_set()

    for src in sources:
        found = False
        owner = None
        for n, s in Sinks.items():
            if src in s["Sources"]:
                owner = n
                break
        
        bg = "#555555" if owner else None
        fg = "#aaaaaa" if owner else None
        label = src if not owner else f"{src} [FROM: {owner}]"

        tk.Button(Popup,text=label,command=lambda s=src: SelectSource(name, Sink, s, Popup)).pack(fill="x")

def SelectSource(name, Sink, source, Popup):
    for s in Sinks.values():
        if source in s["Sources"]:
            s["Sources"].remove(source)

    Sink["Sources"].append(source)

    subprocess.run([NWPath,"ConnectSourceToSink",source,name])

    SaveConfig()
    RefreshRoutingUI()
    Popup.destroy()

def OpenRemoveSourcePopup(Sink):
    if len(Sink["Sources"]) == 0:
        return

    Popup = tk.Toplevel(Root)
    Popup.title("Remove Source")
    Popup.geometry("300x400")
    Popup.grab_set()

    for src in Sink["Sources"]:
        tk.Button(Popup,text=src,command=lambda s=src: RemoveSource(Sink, s, Popup)).pack(fill="x")

def RemoveSource(Sink, source, Popup):
    if source in Sink["Sources"]:
        Sink["Sources"].remove(source)
    subprocess.run([NWPath,"RemoveSourceFromSink",source])
    SaveConfig()
    RefreshRoutingUI()
    Popup.destroy()

def SourceConnection(name,  source):
    subprocess.run([NWPath,"ConnectSourceToSink",source,name])

def RefreshRoutingUI():
    for w in NullWireRoutingObjects.winfo_children():
        w.destroy()

    for name, sink in Sinks.items():
        AddRoutingBlock(name, sink)

def CreateABlock(i):
    frame = tk.Frame(LeftColumn, bd=1, relief="solid")
    frame.pack(fill="x", pady=2)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.columnconfigure(2, weight=0)
    AKey = f"A{i}"
    data = Devices["A"][AKey]
    name = data["Name"] if data else "-"
    container = tk.Frame(frame)
    container.grid(row=0, column=0, sticky="nsew", padx=5)
    container.columnconfigure(0, weight=1)
    container.grid_propagate(False)

    tk.Label(container, text=f"{AKey}: {name}", anchor="w")\
        .grid(row=0, column=0, sticky="w")
    volume = tk.Frame(frame)
    volume.grid(row=0, column=1, sticky="e", padx=5)
    volume_controls = tk.Frame(volume)
    volume_controls.grid(row=0, column=0)
    device_id = data["ID"] if data else None
    start_vol = data.get("Volume") if data else None

    if start_vol is None:
        start_vol = GetAudioDeviceSystemVolume(device_id) if device_id else 100

    vol_var = tk.StringVar(value=str(start_vol))
    after_id = None

    def ApplyVolume():
        if not data:
            return

        volumenumber = data.get("Volume", 100)
        device_id = data.get("ID")

        if not device_id:
            device_id = ResolveSinkID(data["Name"])

        if not device_id:
            return

        data["ID"] = device_id

        try:
            subprocess.run(["pactl","set-sink-volume",device_id,f"{volumenumber}%"
            ], check=True)

        except subprocess.CalledProcessError:
            new_id = ResolveSinkID(data["Name"])

            if not new_id:
                return

            data["ID"] = new_id
            SaveConfig()

            subprocess.run(["pactl","set-sink-volume",new_id,f"{volumenumber}%"], check=True)

    def ScheduleApply():
        nonlocal after_id

        if after_id:
            Root.after_cancel(after_id)

        OnVolumeChange(scale.get())

        after_id = Root.after(100, ApplyVolume)

    def OnVolumeChange(val):
        volumenumber = int(float(val))
        vol_var.set(str(volumenumber))
        data['Volume'] = volumenumber

    scale = tk.Scale(volume_controls,from_=0,to=100,orient="horizontal",showvalue=0,length=120,sliderlength=10,command=OnVolumeChange)
    scale.grid(row=0, column=0, sticky="e", padx=5)

    def OnScrollUp(event):
        scale.set(min(150, scale.get() + 5))
        ScheduleApply()

    def OnScrollDown(event):
        scale.set(max(0, scale.get() - 5))
        ScheduleApply()

    scale.bind("<ButtonRelease-1>", lambda e: ScheduleApply())
    scale.bind("<Button-4>", OnScrollUp)
    scale.bind("<Button-5>", OnScrollDown)
    scale.set(start_vol)
    override_var = tk.BooleanVar(value=data.get("Dominant", False) if data else False)

    def ToggleOverride():
        state = override_var.get()

        data["Dominant"] = state
        SaveConfig()
        if state:
            volume_controls.grid()
        else:
            volume_controls.grid_remove()

    tk.Label(volume_controls, textvariable=vol_var, anchor="w", width= 3)\
        .grid(row=0, column=1, sticky="w")

    tk.Checkbutton(volume,text="Override System",width = 15,variable=override_var,command=ToggleOverride,anchor="w").grid(row=0, column=2, sticky="e", padx=1, pady=2)
    
    if override_var.get():
        volume_controls.grid()
    else:
        volume_controls.grid_remove()

    if data:
        if data["IsSink"]:
            volume.grid_remove()
            volume_controls.grid_remove()

    btns = tk.Frame(frame)
    btns.grid(row=0, column=2)

    tk.Button(btns, text="SET",
        command=lambda k=AKey: OpenOutputPopup(k)).pack(side="left")

    tk.Button(btns, text="CLEAR",
        command=lambda k=AKey: ClearOutput(k)).pack(side="left")
    
def CreateMBlock(i):
    frame = tk.Frame(RightColumn, bd=1, relief="solid")
    frame.pack(fill="x", pady=2)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.columnconfigure(2, weight=0)
    MKey = f"M{i}"
    data = Devices["M"][MKey]
    name = data["Name"] if data else "-"
    container = tk.Frame(frame)
    container.grid(row=0, column=0, sticky="nsew", padx=5)
    container.columnconfigure(0, weight=1)
    container.grid_propagate(False)
    tk.Label(container, text=f"{MKey}: {name}", anchor="w")\
        .grid(row=0, column=0, sticky="w")
    volume = tk.Frame(frame)
    volume.grid(row=0, column=1, sticky="e", padx=5)
    volume_controls = tk.Frame(volume)
    volume_controls.grid(row=0, column=0)
    device_id = data["ID"] if data else None
    start_vol = data.get("Volume") if data else None

    if start_vol is None:
        start_vol = GetMicrophoneSystemVolume(device_id) if device_id else 100

    vol_var = tk.StringVar(value=str(start_vol))
    after_id = None

    def ApplyVolume():
        if not data:
            return

        volumenumber = scale.get()
        data["Volume"] = volumenumber
        SaveConfig()
        device_id = data.get("ID")

        if not device_id:
            device_id = ResolveSourceID(data["Name"])
        
        if not device_id:
            return
        
        data["ID"] = device_id

        try:
            subprocess.run(["pactl","set-source-volume",device_id,f"{volumenumber}%"], check=True)

        except subprocess.CalledProcessError:
            new_id = ResolveSourceID(data["Name"])

            if not new_id:
                return

            data["ID"] = new_id
            SaveConfig()

            subprocess.run(["pactl","set-source-volume",new_id,f"{volumenumber}%"], check=True)

    def ScheduleApply():
        nonlocal after_id
        if after_id:
            Root.after_cancel(after_id)
        
        OnVolumeChange(scale.get())
        after_id = Root.after(150, ApplyVolume)

    def OnVolumeChange(val):
        volumenumber = int(float(val))
        data['Volume'] = volumenumber
        vol_var.set(str(volumenumber))

    scale = tk.Scale(volume_controls,from_=0,to=100,orient="horizontal",showvalue=0,length=120,sliderlength=10,command=OnVolumeChange)
    scale.grid(row=0, column=0, sticky="e", padx=5)

    def OnScrollUp(event):
        scale.set(min(150, scale.get() + 5))
        
        ScheduleApply()

    def OnScrollDown(event):
        scale.set(max(0, scale.get() - 5))
        ScheduleApply()

    scale.bind("<ButtonRelease-1>", lambda e: ScheduleApply())
    scale.bind("<Button-4>", OnScrollUp)
    scale.bind("<Button-5>", OnScrollDown)
    scale.set(start_vol)
    override_var = tk.BooleanVar(value=data.get("Dominant", False) if data else False)

    def ToggleOverride():
        if not data:
            return

        state = override_var.get()
        data["Dominant"] = state
        SaveConfig()

        if state:
            volume_controls.grid()
        else:
            volume_controls.grid_remove()

    tk.Label(volume_controls, textvariable=vol_var, width=3)\
        .grid(row=0, column=1, sticky="w")

    tk.Checkbutton(volume,text="Override System",width=15,variable=override_var,command=ToggleOverride,anchor="w").grid(row=0, column=2, sticky="e", padx=1, pady=2)

    if override_var.get():
        volume_controls.grid()
    else:
        volume_controls.grid_remove()

    btns = tk.Frame(frame)
    btns.grid(row=0, column=2)

    tk.Button(btns, text="SET",
        command=lambda k=MKey: OpenInputPopup(k)).pack(side="left")

    tk.Button(btns, text="CLEAR",
        command=lambda k=MKey: ClearInput(k)).pack(side="left")
    
def BuildUI():
    for i in range(1, 21):
        CreateABlock(i)
        CreateMBlock(i)

def NullWireRebuildUI():
    global LeftColumn, RightColumn, Divider
    for widget in NullWireMainRow.winfo_children():
        widget.destroy()
    LeftColumn = tk.Frame(NullWireMainRow)
    LeftColumn.grid(row=0, column=0, sticky="nsew", padx=(5, 2))
    Divider = tk.Frame(NullWireMainRow, bg="#555", width=4)
    Divider.grid(row=0, column=1, sticky="ns")
    RightColumn = tk.Frame(NullWireMainRow)
    RightColumn.grid(row=0, column=2, sticky="nsew", padx=(2, 5))
    BuildUI()

def ClearOutput(key):
    Devices["A"][key] = None
    SaveConfig()
    NullWireRebuildUI()
    RefreshRoutingUI()

def ClearInput(key):
    Devices["M"][key] = None
    SaveConfig()
    NullWireRebuildUI()
    RefreshRoutingUI()

def OpenOutputPopup(targetKey):
    BuildOutputSelectionList()
    Popup = tk.Toplevel(Root)
    Popup.title("Select Output Device")
    Popup.geometry("400x500")
    Popup.grab_set()
    
    for device in OutputDeviceSelection:
        tk.Button(Popup,text=device["UIName"],command=lambda d=device: SelectOutputDevice(d, targetKey, Popup)).pack(fill="x")

def SelectOutputDevice(device, key, Popup):
    Devices["A"][key] = {"Name": device["UIName"],"ID": device["SystemID"],"Volume": 100,"Dominant": False,"IsSink": False}
    if "_NullWire" in device["SystemID"]:
        Devices["A"][key]["IsSink"] = True
    NullWireRebuildUI()
    RefreshRoutingUI()
    SaveConfig()
    Popup.destroy()

def OpenInputPopup(targetKey):

    BuildInputSelectionList()
    Popup = tk.Toplevel(Root)
    Popup.title("Select Input Device")
    Popup.geometry("400x500")
    Popup.grab_set()
    for device in InputDeviceSelection:
        tk.Button(Popup,text=device["UIName"],command=lambda d=device: SelectInputDevice(d, targetKey, Popup)).pack(fill="x")

def SelectInputDevice(device, key, Popup):
    Devices["M"][key] = {"Name": device["UIName"],"ID": device["SystemID"],"Volume": 100,"Dominant": False}
    SaveConfig()
    NullWireRebuildUI()
    RefreshRoutingUI()
    Popup.destroy()

def ApplySources():
    active = GetAudioSources()

    for name, sink in Sinks.items():
        for src in sink["Sources"]:
            if src in active:
                SourceConnection(name, src)

def ApplyOutputs():
    for name, sink in Sinks.items():
        for d, enabled in sink["Outputs"].items():
            if not enabled:
                continue

            device = Devices["A"].get(d)
            if not device:
                print(f"Audio Device not found for {d}")
                continue

            device_id = ResolveSinkID(device["Name"])
            if not device_id:
                print(f"Audio Device ID not found for {device['Name']}")
                continue

            if device["ID"] != device_id:
                device["ID"] = device_id

            subprocess.run([NWPath,"ConnectSinkToAux",name,device_id,str(int(sink["Mono"]))])

def ApplyInputs():
    for name, sink in Sinks.items():
        for d, enabled in sink["Inputs"].items():
            if not enabled:
                continue

            device = Devices["M"].get(d)
            if not device:
                print(f"Mic Device not found for {d}")
                continue

            device_id = ResolveSourceID(device["Name"])
            if device["ID"] != device_id:
                device["ID"] = device_id

            subprocess.run([NWPath,"ConnectMicToSink",name,device_id,])

def GetSinkSystemVolume(name):
    device_id = ResolveSinkID(name)
    if not device_id:
        return None

    try:
        out = subprocess.check_output(["pactl", "get-sink-volume", device_id],stderr=subprocess.DEVNULL).decode()

        for part in out.split():
            if "%" in part:
                return int(part.replace("%", ""))
    except:
        return None

    return None

def ForceSinkVolume():
    for name, dickt in Sinks.items():
        if not dickt.get("Dominant"):
            continue
        targetvol = int(dickt.get("Volume", 1.0))

        current = GetSinkSystemVolume(name)
        if current is None:
            continue

        if abs(current - targetvol) > 2:
            subprocess.run([NWPath,"SetSinkVolume",name,str(targetvol)])

def ForceAudioDeviceVolume():
    for devicenumber in Devices["A"].values():
        if devicenumber == None:
            continue
        
        if not devicenumber.get("Dominant"):
            continue
        
        target = int(devicenumber.get("Volume", 100))

        device_id = ResolveSinkID(devicenumber["Name"])
        if not device_id:
            continue

        current = GetAudioDeviceSystemVolume(device_id)
        if current is None:
            continue

        if abs(current - target) > 2:
            subprocess.run(["pactl","set-sink-volume",device_id,f"{target}%"])

def ForceMicDeviceVolume():
    for devicenumber in Devices["M"].values():
        if devicenumber == None:
            continue

        if not devicenumber.get("Dominant"):
            continue

        target = int(devicenumber.get("Volume", 100))

        device_id = ResolveSourceID(devicenumber["Name"])
        if not device_id:
            continue

        current = GetMicrophoneSystemVolume(device_id)
        if current is None:
            continue

        if abs(current - target) > 2:
            subprocess.run(["pactl","set-source-volume",device_id,f"{target}%"])

# ————————————————————————————————————————————————————————————
# NullCursor
# ————————————————————————————————————————————————————————————
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None

        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tip,
            text=self.text,
            bg="black",
            fg="white",
            padx=5,
            pady=3
        )
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

def CaptureLayout():
    try:
        Out = subprocess.check_output([XrandrPath]).decode()
    except:
        return []

    Layout = []

    for Line in Out.splitlines():
        if " connected" in Line:
            Parts = Line.split()
            ID = Parts[0]

            Mode = None
            Pos = None
            Primary = "primary" in Parts

            for P in Parts:
                if "+" in P and "x" in P:
                    Mode, X, Y = re.split(r"[+]", P)
                    Pos = f"{X}x{Y}"
                    break

            if not Mode:
                continue

            Layout.append({
                "ID": ID,
                "Mode": Mode,
                "Pos": Pos,
                "Primary": Primary
            })

    return Layout

def GetMonitors():
    try:
        Out = subprocess.check_output([XrandrPath]).decode()
    except:
        return []

    Monitors = []

    for Line in Out.splitlines():
        if " connected" in Line:
            Parts = Line.split()
            ID = Parts[0]

            IsPrimary = " primary " in Line

            Resolution = None
            for P in Parts:
                if "+" in P and "x" in P:
                    Resolution = P.split("+")[0]
                    break

            if not Resolution:
                continue

            if IsPrimary:
                Label = f"Primary ({ID} {Resolution})"
            else:
                Label = f"{ID} ({Resolution})"

            Monitors.append({
                "ID": ID,
                "Label": Label,
                "Primary": IsPrimary
            })

    return Monitors

def GetProfiles():
    return list(Profiles.keys()) if Profiles else ["NO PROFILES. GO CREATE ONE"]

def ShowDetectionOverlay(which):
    global OverlayWindows
    if OverlayWindows:
        return


    OverlayWindows = []

    Bounds = GetMonitorBounds()

    for ID, B in Bounds.items():
        W = B["x2"] - B["x1"]
        H = B["y2"] - B["y1"]

        if which == "detection":
            Px = int(W * StartDetection)
            Py = int(H * StartDetection)
        else:
            Px = EdgeBuffer
            Py = EdgeBuffer

        # Left
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y1"], Px, H
        ))

        # Right
        OverlayWindows.append(CreateOverlay(
            B["x2"] - Px, B["y1"], Px, H
        ))

        # Top
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y1"], W, Py
        ))

        # Bottom
        OverlayWindows.append(CreateOverlay(
            B["x1"], B["y2"] - Py, W, Py
        ))
    return OverlayWindows

def CreateOverlay(x, y, w, h):
    Popup = tk.Toplevel(Root)
    Popup.overrideredirect(True)
    Popup.attributes("-topmost", True)
    Popup.attributes("-alpha", 0.25)

    Popup.geometry(f"{w}x{h}+{x}+{y}")
    Popup.configure(bg="red")

    return Popup

def HideDetectionOverlay():
    global OverlayWindows

    for W in OverlayWindows:
        try:
            W.destroy()
        except:
            pass

    OverlayWindows = []

def UpdateStartDetection(v):
    global StartDetection
    StartDetection = int(v) / 1000
    NullCursorStartValueLabel.config(text=f"{int(v)}   |") 
    SaveConfig()

def OnHoverEnter(e, which):
    global Overlays, HideJob
    if HideJob:
        Root.after_cancel(HideJob)
        HideJob = None
    HideDetectionOverlay()
    Overlays = ShowDetectionOverlay(which)

def OnHoverLeave(e):
    global HideJob
    HideJob = Root.after(50, HideDetectionOverlay)

def DelayedHide():
    Root.after(50, lambda: HideDetectionOverlay())

def UpdateEdgeBuffer(*args):
    global EdgeBuffer
    try:
        EdgeBuffer = int(NullCursorEdgeBufferVar.get())
        SaveConfig()
    except:
        pass

def UpdateScanTime(v):
    global ScanTime
    ScanTime = float(v)
    NullCursorScanValueLabel.config(text=f"{ScanTime:.3f}")
    SaveConfig()

def CenterOnRoot(Popup, width, height):
    Root.update_idletasks()

    rx = Root.winfo_rootx()
    ry = Root.winfo_rooty()
    rw = Root.winfo_width()
    rh = Root.winfo_height()

    x = rx + (rw // 2) - (width // 2)
    y = ry + (rh // 2) - (height // 2)

    Popup.geometry(f"{width}x{height}+{x}+{y}")

def SetActiveProfile(Name, Apply=True):
    global ActiveProfile

    ActiveProfile = Name

    for P, W in ProfileWidgets.items():
        W["ActiveVar"].set(P == Name)

    if Apply:
        if ActiveProfile not in Profiles:
            return
        Layout = Profiles[Name]["Layout"]

    SaveConfig()

def DeleteProfile(Name, Frame):
    global ActiveProfile
    if len(Profiles) <= 1:
        return
    Frame.destroy()
    Profiles.pop(Name, None)
    ProfileWidgets.pop(Name, None)
    if ActiveProfile == Name or len(Profiles) == 1:
        New = list(Profiles.keys())[0]
        SetActiveProfile(New)

    SaveConfig()

def OpenRemoveWarp(Name):
    print("Remove warp for", Name)

def RefreshWarpDisplay(Name):
    Warps = Profiles.get(Name, {}).get("Warps", {})

    Parts = []

    for SourceID, WarpList in Warps.items():
        for W in WarpList:
            Parts.append(
                f'{SourceID}: {W["Edge"]} → {W["Target"]}: {W["TargetEdge"]}'
            )

    Text = " , ".join(Parts) if Parts else "No warps"

    ProfileWidgets[Name]["WarpVar"].set(Text)

def SpawnMonitorPopups(OnSelect):
    Popups = {}

    Bounds = GetMonitorBounds()

    for ID, B in Bounds.items():
        Popup = tk.Toplevel(Root)
        Popup.overrideredirect(True)
        Popup.attributes("-topmost", True)

        width = 200
        height = 60

        x = B["x1"] + 20
        y = B["y1"] + 20

        Popup.geometry(f"{width}x{height}+{x}+{y}")
        Popup.config(cursor="hand2")

        Label = tk.Label(
            Popup,
            text=f"Click Here\n{ID}",
            bg="black",
            fg="white",
            font=("Arial", 12, "bold")
        )
        Label.pack(fill="both", expand=True)
        Label.bind("<Enter>", lambda e, L=Label: L.config(bg="#333"))
        Label.bind("<Leave>", lambda e, L=Label: L.config(bg="black"))

        Label.bind("<Button-1>", lambda e, mid=ID: OnSelect(mid))

        Popups[ID] = Popup

    return Popups

def CreateCenterPopup():
    Popup = tk.Toplevel(Root)
    CenterOnRoot(Popup, 400, 100)
    Popup.attributes("-topmost", True)
    

    Frame = tk.Frame(Popup)
    Frame.pack(fill="both", expand=True)

    Label = tk.Label(Frame, text="", font=("Arial", 12))
    Label.pack(expand=True)

    

    return Popup, Label

def OpenWarpConfigPopup(ProfileName, SourceID, TargetID):
    Popup = tk.Toplevel(Root)
    CenterOnRoot(Popup, 300, 200)
    Popup.title("Configure Warp")
    Popup.attributes("-topmost", True)

    Frame = tk.Frame(Popup, padx=10, pady=10)
    Frame.pack()

    tk.Label(Frame, text=f"{SourceID} → {TargetID}").pack(pady=5)

    Edges = ["TopLeft", "Top", "TopRight",
             "Right",
             "BottomRight", "Bottom", "BottomLeft",
             "Left"]

    SourceEdgeVar = tk.StringVar(value=Edges[0])
    TargetEdgeVar = tk.StringVar(value=Edges[0])

    tk.Label(Frame, text="Source Edge").pack()
    ttk.Combobox(Frame, values=Edges, textvariable=SourceEdgeVar, state="readonly").pack()

    tk.Label(Frame, text="Target Edge").pack()
    ttk.Combobox(Frame, values=Edges, textvariable=TargetEdgeVar, state="readonly").pack()

    def Confirm():
        Warp = {
            "Edge": SourceEdgeVar.get(),
            "Target": TargetID,
            "TargetEdge": TargetEdgeVar.get()
        }

        if SourceID not in Profiles[ProfileName]["Warps"]:
            Profiles[ProfileName]["Warps"][SourceID] = []

        if Warp not in Profiles[ProfileName]["Warps"][SourceID]:
            Profiles[ProfileName]["Warps"][SourceID].append(Warp)

        RefreshWarpDisplay(ProfileName)
        Popup.destroy()
        SaveConfig()

    tk.Button(Frame, text="Confirm", command=Confirm).pack(pady=5)

def StartWarpSelection(ProfileName):
    State = {"source": None}

    def Cleanup():
        for p in list(Popups.values()):
            try:
                p.destroy()
            except:
                pass
        try:
            CenterPopup.destroy()
        except:
            pass

    CenterPopup, CenterLabel = CreateCenterPopup()

    CenterPopup.protocol("WM_DELETE_WINDOW", Cleanup)
    CenterPopup.bind("<Escape>", lambda e: Cleanup())



    def UpdateText(t):
        CenterLabel.config(text=t)

    def SelectSource(ID):
        State["source"] = ID

        Popups[ID].destroy()
        del Popups[ID]

        UpdateText("Click to set warping TO monitor")
        for mid, popup in Popups.items():
            for w in popup.winfo_children():
                w.bind("<Button-1>", lambda e, m=mid: SelectTarget(m))

    def SelectTarget(ID):
        Source = State["source"]
        for p in Popups.values():
            p.destroy()

        CenterPopup.destroy()

        OpenWarpConfigPopup(ProfileName, Source, ID)

    Popups = SpawnMonitorPopups(SelectSource)

    UpdateText("Click to set warping FROM monitor")

def OpenAddWarp(Name):
    StartWarpSelection(Name)

def CreateProfileBox(Name):
    Frame = tk.LabelFrame(NullCursorProfileContainer, text=Name, padx=5, pady=5)
    Frame.pack(fill="x", pady=5)

    TopRow = tk.Frame(Frame)
    TopRow.pack(fill="x")

    ActiveVar = tk.BooleanVar()

    ActiveCheck = tk.Checkbutton(
        TopRow,
        text="Active",
        variable=ActiveVar,
        command=lambda: SetActiveProfile(Name, Apply=True)
    )
    ActiveCheck.pack(side="left")

    Spacer = tk.Frame(TopRow)
    Spacer.pack(side="left", expand=True)

    DeleteBtn = tk.Button(
        TopRow,
        text="Delete",
        command=lambda: DeleteProfile(Name, Frame)
    )
    DeleteBtn.pack(side="right")


    Spacer3 = tk.Frame(Frame, bg="black",height=2)
    Spacer3.pack(expand=True,fill="x",pady=5,)
    BtnRow = tk.Frame(Frame)
    BtnRow.pack(fill="x")

    tk.Button(BtnRow, text="Create Warp",
              command=lambda: OpenAddWarp(Name)).pack(side="left", padx=2)

    tk.Button(BtnRow, text="Delete Warp",
              command=lambda: OpenRemoveWarp(Name)).pack(side="left", padx=2)

    WarpBox = tk.Frame(Frame, padx=1, pady=1)
    WarpBox.pack(fill="x", pady=5)

    InnerWarp = tk.Frame(WarpBox)
    InnerWarp.pack(fill="x")

    WarpVar = tk.StringVar()

    WarpLabel = tk.Label(
        InnerWarp,
        textvariable=WarpVar,
        anchor="w",
        justify="left",
    )
    WarpLabel.pack(fill="x", padx=5, pady=3)

    ProfileWidgets[Name] = {
        "Frame": Frame,
        "ActiveVar": ActiveVar,
        "WarpVar": WarpVar
    }

    RefreshWarpDisplay(Name)

def CreateProfile():
    Name = NullCursorProfileNameVar.get().strip()

    if not Name:
        return

    if Name in Profiles:
        return

    Profiles[Name] = {
        "Layout": CaptureLayout(),
        "Warps": {}
    }

    CreateProfileBox(Name)
    NullCursorProfileNameVar.set("")
    SaveConfig()

def BuildUIFromProfiles():
    for w in NullCursorProfileContainer.winfo_children():
        w.destroy()

    ProfileWidgets.clear()

    for Name in Profiles:
        CreateProfileBox(Name)

    if ActiveProfile in ProfileWidgets:
        SetActiveProfile(ActiveProfile, Apply= False)

def GetMouseDirection(x, y):
    global LastMousePos

    if LastMousePos is None:
        LastMousePos = (x, y)
        return 0, 0

    lx, ly = LastMousePos
    dx = x - lx
    dy = y - ly

    LastMousePos = (x, y)

    return dx, dy

def IsEdgeBuffer(corner, x, y, B):
    left   = x <= B["x1"] + EdgeBuffer
    right  = x >= B["x2"] - EdgeBuffer
    top    = y <= B["y1"] + EdgeBuffer
    bottom = y >= B["y2"] - EdgeBuffer

    if corner == "Left":
        return left
    if corner == "Right": 
        return right
    if corner == "Top": 
        return top
    if corner == "Bottom": 
        return bottom

    if corner == "TopLeft":
        return left and top
    if corner == "TopRight":
        return right and top
    if corner == "BottomLeft":
        return left and bottom
    if corner == "BottomRight":
        return right and bottom

    return False

def ExecuteWarp(TargetID, TargetEdge, Bounds, ratio=None):
    TB = Bounds[TargetID]
    ratio = max(0, min(1, ratio))
    width  = TB["x2"] - TB["x1"]
    height = TB["y2"] - TB["y1"]

    if TargetEdge == "TopLeft":
        nx, ny = TB["x1"] + Offset, TB["y1"] + Offset

    elif TargetEdge == "TopRight":
        nx, ny = TB["x2"] - Offset, TB["y1"] + Offset

    elif TargetEdge == "BottomLeft":
        nx, ny = TB["x1"] + Offset, TB["y2"] - Offset

    elif TargetEdge == "BottomRight":
        nx, ny = TB["x2"] - Offset, TB["y2"] - Offset

    elif TargetEdge == "Left":
        nx = TB["x1"] + Offset
        ny = TB["y1"] + int(ratio * height)

    elif TargetEdge == "Right":
        nx = TB["x2"] - Offset
        ny = TB["y1"] + int(ratio * height)

    elif TargetEdge == "Top":
        nx = TB["x1"] + int(ratio * width)
        ny = TB["y1"] + Offset

    elif TargetEdge == "Bottom":
        nx = TB["x1"] + int(ratio * width)
        ny = TB["y2"] - Offset

    else:
        return


    subprocess.run([XdotoolPath, "mousemove", str(nx), str(ny)])

def GetCursorPos():
    try:
        Out = subprocess.check_output([XdotoolPath, "getmouselocation"]).decode()
        Parts = dict(p.split(":") for p in Out.strip().split())
        return int(Parts["x"]), int(Parts["y"])
    except:
        return None, None

def GetMonitorBounds():
    Bounds = {}

    Layout = Profiles[ActiveProfile]["Layout"]

    for M in Layout:
        ID = M["ID"]

        W, H = map(int, M["Mode"].split("x"))
        X, Y = map(int, M["Pos"].split("x"))

        Bounds[ID] = {
            "x1": X,
            "y1": Y,
            "x2": X + W,
            "y2": Y + H
        }

    return Bounds

def GetCurrentMonitor(x, y, Bounds):
    for ID, B in Bounds.items():
        if B["x1"] <= x <= B["x2"] and B["y1"] <= y <= B["y2"]:
            return ID
    return None

def DetectEdge(x, y, B):
    W = B["x2"] - B["x1"]
    H = B["y2"] - B["y1"]

    mx = (x - B["x1"]) / W
    my = (y - B["y1"]) / H

    left   = mx <= StartDetection
    right  = mx >= 1 - StartDetection
    top    = my <= StartDetection
    bottom = my >= 1 - StartDetection

    if top and left:
        return "TopLeft"
    if top and right:
        return "TopRight"
    if bottom and left:
        return "BottomLeft"
    if bottom and right:
        return "BottomRight"

    if top:
        return "Top"
    if bottom:
        return "Bottom"
    if left:
        return "Left"
    if right:
        return "Right"

    return None

def ToggleNullCursor():
    global ScanForMouse
    ScanForMouse = NullCursorEnabledVar.get()
    if ScanForMouse:
        NullCursorDisabledOverlay.place_forget()
    else:
        NullCursorDisabledOverlay.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )
    SaveConfig()

# ————————————————————————————————————————————————————————————
# NullProton
# ————————————————————————————————————————————————————————————
def RefreshRowUI(RowIndex):
    State = ProtonGames[RowIndex]
    Frame = ProtonGameRows[RowIndex]
    Buttons = Frame.Buttons

    for key, btn in Buttons.items():
        if key == State.get("LastProton"):
            btn.configure(bg="#a1a1a1")
        else:
            btn.configure(bg=btn.DefaultBg)

def AddGameRow(State=None, Loading=False):
    RowIndex = len(ProtonGameRows)

    Frame = tk.Frame(ProtonGameContainer)
    Frame.grid(row=RowIndex, column=0, sticky="ew", pady=(5,5), padx=(0,10))
    Frame.columnconfigure(0, weight=0)
    Frame.columnconfigure(1, weight=0)
    Frame.columnconfigure(2, weight=0)
    Frame.columnconfigure(3, weight=0)
    Frame.columnconfigure(4, weight=2)
    Frame.columnconfigure(5, weight=0)
    Frame.columnconfigure(6, weight=0)
    Frame.columnconfigure(7, weight=0)
    Frame.columnconfigure(8, weight=0)
    Frame.columnconfigure(9, weight=0)
    Frame.columnconfigure(10, weight=0)
    Frame.columnconfigure(11, weight=0)
    ProtonGameRows.append(Frame)

    if State is None:
        State = {
            "Path": "",
            "CloseNPOnExit": False,
            "MinimizeOnLaunch": False,
            "LastProton": "None"
        }

    if not Loading:
        ProtonGames.append(State)

    PathVar = tk.StringVar(value=os.path.basename(State["Path"]))

    def RemoveSelf():
        Index = ProtonGameRows.index(Frame)
        Frame.destroy()
        ProtonGameRows.pop(Index)
        ProtonGames.pop(Index)
        SaveConfig()
        for i, Row in enumerate(ProtonGameRows):
            Row.grid_configure(row=i)

    tk.Button(Frame, text="Remove", width=8, command=RemoveSelf)\
    .grid(row=0, column=0, padx=3)

    ttk.Separator(Frame, orient="vertical")\
        .grid(row=0, column=1, sticky="ns", padx=5)
    
    CloseVar = tk.BooleanVar(value=State.get("CloseToTray", False))
    MinVar = tk.BooleanVar(value=State.get("MinimizeOnLaunch", False))

    closenp = tk.Checkbutton(Frame, text="Close To Tray", variable=CloseVar)
    closenp.grid(row=0, column=2, padx=3)

    minimize = tk.Checkbutton(Frame, text="Minimize On Launch", variable=MinVar)
    minimize.grid(row=0, column=3, padx=3)

    def UpdateState():
        State["CloseToTray"] = CloseVar.get()
        State["MinimizeOnLaunch"] = MinVar.get()
        SaveConfig()

    CloseVar.trace_add("write", lambda *args: UpdateState())
    MinVar.trace_add("write", lambda *args: UpdateState())

    Entry = tk.Entry(Frame, textvariable=PathVar, state="readonly")
    Entry.grid(row=0, column=4, padx=3, sticky="ew")


    def Browse():
        Path = filedialog.askopenfilename(title="Select Game Executable")
        if Path:
            State["Path"] = Path
            PathVar.set(os.path.basename(Path))
            SaveConfig()

    tk.Button(Frame, text="Browse", width=8, command=Browse)\
        .grid(row=0, column=5, padx=3)
    
    ttk.Separator(Frame, orient="vertical")\
        .grid(row=0, column=6, sticky="ns", padx=5)

    Buttons = {}

    Buttons["Default"] = tk.Button(Frame, text="Default", width=12,
        command=lambda: LaunchGame(State, "Default", RowIndex))
    Buttons["Default"].grid(row=0, column=7, padx=2)
    Buttons["Default"].DefaultBg = Buttons["Default"].cget("bg")

    Buttons["A"] = tk.Button(Frame, text="Proton A", width=12,
        command=lambda: LaunchGame(State, "A", RowIndex))
    Buttons["A"].grid(row=0, column=8, padx=2)
    Buttons["A"].DefaultBg = Buttons["Default"].cget("bg")

    Buttons["B"] = tk.Button(Frame, text="Proton B", width=12,
        command=lambda: LaunchGame(State, "B", RowIndex))
    Buttons["B"].grid(row=0, column=9, padx=2)
    Buttons["B"].DefaultBg = Buttons["Default"].cget("bg")

    ttk.Separator(Frame, orient="vertical")\
        .grid(row=0, column=10, sticky="ns", padx=5)

    Buttons["Linux"] = tk.Button(Frame, text="Linux", width=12,
        command=lambda: LaunchGame(State, "Linux", RowIndex))
    Buttons["Linux"].grid(row=0, column=11, padx=2)
    Buttons["Linux"].DefaultBg = Buttons["Default"].cget("bg")

    Frame.Buttons = Buttons
    RefreshRowUI(len(ProtonGameRows) - 1)

    if not Loading:
        SaveConfig()

def UpdateOverlay():
    while not LogQueue.empty():
        Line = LogQueue.get()
        OverlayLabel.config(text=OverlayLabel.cget("text") + Line + "\n")
    Root.after(100, UpdateOverlay)

def ShowOverlay():
    OverlayLabel.config(text="")
    ProtonOverlay.lift()

def HideOverlay():
    ProtonOverlay.lower()

def LaunchGame(State, Mode, RowIndex):
    def Run():
        Path = State["Path"]

        if not os.path.isfile(Path):
            LogQueue.put("❌ Invalid path")
            return
        
        if Mode == "Linux":
            State["LastProton"] = Mode
            SaveConfig()
            Root.after(0, lambda: RefreshRowUI(RowIndex))
            Root.after(0, ShowOverlay)
            LogQueue.put("🐧 Launching (Linux)...")
            try:
                subprocess.Popen([Path])
                LogQueue.put("✅ Game launched")
                time.sleep(1)
                Root.after(0, ProtonOverlay.lower)
            except Exception as e:
                LogQueue.put(f"❌ Failed: {e}")

            if State.get("MinimizeOnLaunch"):
                Root.after(0, Root.iconify)

            if State.get("CloseNPOnExit"):
                Root.after(0, Root.destroy)

            return

        ProtonPath = ProtonVars[Mode].get()

        if not os.path.isfile(ProtonPath):
            LogQueue.put(f"❌ Proton '{Mode}' not set")
            return

        BaseDir = os.path.dirname(os.path.abspath(__file__))
        Prefix = os.path.join(BaseDir, ProtonDrive, "Default")
        os.makedirs(Prefix, exist_ok=True)

        Env = os.environ.copy()
        Env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = os.path.expanduser("~/.steam/steam/")
        Env["STEAM_COMPAT_DATA_PATH"] = Prefix

        Root.after(0, ShowOverlay)

        LogQueue.put("🚀 Launching...")
        LogQueue.put("Please wait...\n")

        Proc = subprocess.Popen(
            [ProtonPath, "run", Path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=Env
        )
        
        StartTime = time.time()
        LAUNCH_TIMEOUT = 10
        LastOutput = time.time()

        while True:
            if time.time() - LastOutput > 3:
                break

            if time.time() - StartTime > LAUNCH_TIMEOUT:
                break

            rlist, _, _ = select.select([Proc.stdout], [], [], 0.1)

            if rlist:
                line = Proc.stdout.readline()
                if line:
                    LogQueue.put(line.strip())
                    LastOutput = time.time()

        LogQueue.put("\n✅ Game launched")

        State["LastProton"] = Mode
        SaveConfig()
        Root.after(0, lambda: RefreshRowUI(RowIndex))
        if State.get("MinimizeOnLaunch"):
                Root.after(0, Root.iconify)

        if State.get("CloseNPOnExit"):
            Root.after(0, Root.withdraw)

        time.sleep(1)

        Root.after(0, ProtonOverlay.lower)

    threading.Thread(target=Run, daemon=True).start()

UpdateOverlay()
# ————————————————————————————————————————————————————————————
# NullRip
# ————————————————————————————————————————————————————————————
def ToggleChapters():
    all_checked = all(var.get() for _, var in SelectedChapters)

    for _, var in SelectedChapters:
        var.set(not all_checked)

def ScanDisc(path):
    result = subprocess.run(
        ["HandBrakeCLI", "-i", path, "--scan"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return result.stdout

def ParseScan(output):
    titles = []
    current = None

    audio_mode = False
    sub_mode = False

    for line in output.splitlines():

        t = re.search(r"\+ title (\d+):", line)
        if t:
            if current:
                titles.append(current)

            current = {
                "index": int(t.group(1)),
                "duration": "",
                "chapters": [],
                "audio": [],
                "subtitles": []
            }

            audio_mode = False
            sub_mode = False
            continue

        if "+ audio tracks:" in line:
            audio_mode = True
            sub_mode = False
            continue

        if "+ subtitle tracks:" in line:
            sub_mode = True
            audio_mode = False
            continue

        if audio_mode:
            m = re.search(r"\+ (\d+), (.+)", line)
            if m and current:
                raw = m.group(2)

                name = re.match(r"([^(]+)", raw)
                clean = name.group(1).strip() if name else raw

                current["audio"].append({
                    "id": int(m.group(1)),
                    "name": clean
                })
            continue

        if sub_mode:
            m = re.search(r"\+ (\d+), (.+)", line)
            if m and current:
                raw = m.group(2)

                name = re.match(r"([^(]+)", raw)
                clean = name.group(1).strip() if name else raw

                current["subtitles"].append({
                    "id": int(m.group(1)),
                    "name": clean
                })
            continue

        d = re.search(r"\+ duration: (\d+:\d+:\d+)", line)
        if d and current:
            current["duration"] = d.group(1)
            continue

        c = re.search(r"\+ (\d+): duration (\d+:\d+:\d+)", line)
        if c and current:
            current["chapters"].append({
                "num": int(c.group(1)),
                "time": c.group(2)
            })
            continue

    if current:
        titles.append(current)

    return titles

def LoadTitles(data):
    global Titles
    Titles = data

    for w in NullRipTitlesBox.Inner.winfo_children():
        w.destroy()

    for w in NullRipChaptersBox.Inner.winfo_children():
        w.destroy()

    for w in NullRipOptionsBoxSplit.Inner.winfo_children():
        w.destroy()

    for title in data:
        button = tk.Button(
            NullRipTitlesBox.Inner,
            text=f"Title {title['index']} ({title['duration']})",
            anchor="w",
            command=lambda t=title: OnTitleSelected(t)
        )

        button.pack(fill="x", padx=5, pady=2)

def OnTitleSelected(title):
    global SelectedTitle
    SelectedTitle = title

    LoadChapters(title)
    LoadOptions(title)

def GetVLCCommand():
    if shutil.which("vlc"):
        return ["vlc"]

    if shutil.which("flatpak"):
        result = subprocess.run(
            ["flatpak", "list"],
            stdout=subprocess.PIPE,
            text=True
        )

        if "org.videolan.VLC" in result.stdout:
            return ["flatpak", "run", "org.videolan.VLC"]

    return None

def PreviewChapter(title_index, chapter_num):
    cmd = GetVLCCommand()

    if not cmd:
        messagebox.showerror(
            "VLC Required",
            "Install VLC (apt or flatpak) to preview chapters."
        )
        return

    try:
        subprocess.Popen(
            cmd + [f"dvd://{NullRipInputPath.get()}#{title_index}:{chapter_num}"])
    except Exception as e:
        print("VLC launch failed:", e)

def LoadChapters(title):
    global SelectedChapters
    SelectedChapters.clear()

    for w in NullRipChaptersBox.Inner.winfo_children():
        w.destroy()

    for chap in title["chapters"]:
        var = tk.BooleanVar(value=False)
        SelectedChapters.append((chap, var))

        row = tk.Frame(NullRipChaptersBox.Inner)
        row.pack(fill="x", padx=5, pady=2)

        tk.Checkbutton(
            row,
            text=f"Chapter {chap['num']} ({chap['time']})",
            variable=var,
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            row,
            text="▶",
            width=3,
            command=lambda t=title['index'], c=chap['num']: PreviewChapter(t, c)
        ).pack(side="right")

def LoadOptions(title):
    global SelectedAudio, SelectedSubs

    SelectedAudio.clear()
    SelectedSubs.clear()

    frame = NullRipOptionsBoxSplit.Inner

    for w in frame.winfo_children():
        w.destroy()

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.columnconfigure(2, weight=1)

    tk.Label(frame, text="Audio").grid(row=0, column=0, sticky="ew")
    tk.Label(frame, text="Subtitles").grid(row=0, column=2, sticky="ew")

    max_rows = max(len(title["audio"]), len(title["subtitles"]))

    divider = tk.Frame(frame, width=2, bg="black")
    divider.grid(row=0, column=1, rowspan=max_rows+1, sticky="ns", padx=5)

    

    for i in range(max_rows):

        if i < len(title["audio"]):
            track = title["audio"][i]
            var = tk.BooleanVar(value=True)

            SelectedAudio.append((track, var))

            tk.Checkbutton(
                frame,
                text=track["name"],
                variable=var
            ).grid(row=i+1, column=0, sticky="w", padx=(5,10))

        if i < len(title["subtitles"]):
            track = title["subtitles"][i]
            var = tk.BooleanVar(value=True)

            SelectedSubs.append((track, var))

            tk.Checkbutton(
                frame,
                text=track["name"],
                variable=var
            ).grid(row=i+1, column=2, sticky="w", padx=(10,5))

def StartScan():
    popup, progress = ShowScanPopup()

    threading.Thread(
        target=lambda: ScanThread(popup, progress),
        daemon=True
    ).start()

def ScanThread(popup, progress):
    path = NullRipInputPath.get()

    if not path:
        Root.after(0, popup.destroy)
        return

    raw = ScanDisc(path)
    titles = ParseScan(raw)

    Root.after(0, lambda: FinishScan(popup, progress, titles))

def FinishScan(popup, progress, titles):
    progress.stop()
    popup.destroy()

    LoadTitles(titles)
    NullRipStartButton.config(state="normal")

def GetSelectedTracks():
    audio = [t["id"] for t, v in SelectedAudio if v.get()]
    subs  = [t["id"] for t, v in SelectedSubs if v.get()]
    return audio, subs

def GetVideosDir():
    home = os.path.expanduser("~")
    config = os.path.join(home, ".config", "user-dirs.dirs")

    if os.path.exists(config):
        with open(config, "r") as f:
            for line in f:
                if line.startswith("XDG_VIDEOS_DIR"):
                    path = line.split("=")[1].strip().strip('"')
                    path = path.replace("$HOME", home)
                    return path

    return os.path.join(home, "Videos")

def BrowseInput():
    import os

    user = getpass.getuser()

    media_path = f"/media/{user}"
    run_media_path = f"/run/media/{user}"

    start_dir = None

    if os.path.exists(media_path):
        start_dir = media_path
    elif os.path.exists(run_media_path):
        start_dir = run_media_path
    else:
        start_dir = "/"  # fallback

    path = filedialog.askdirectory(initialdir=start_dir)

    if path:
        NullRipInputPath.set(path)

def BrowseOutput():
    start_dir = GetVideosDir()

    if not os.path.exists(start_dir):
        start_dir = os.path.expanduser("~")

    path = filedialog.askdirectory(initialdir=start_dir)

    if path:
        NullRipOutputPath.set(path)

def ShowScanPopup():
    popup = tk.Toplevel(Root)
    popup.title("Scanning")
    popup.geometry("300x100")
    popup.resizable(False, False)

    tk.Label(popup, text="Scanning disc...").pack(pady=10)

    progress = ttk.Progressbar(popup, mode="indeterminate")
    progress.pack(fill="x", padx=10, pady=5)
    progress.start(10)

    popup.grab_set()
    popup.transient(Root)

    CenterWindow(popup)

    return popup, progress

def CenterWindow(win):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
    y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

def GetSelections():
    if not SelectedTitle:
        return None

    title_index = SelectedTitle["index"]

    chapters = [c["num"] for c, v in SelectedChapters if v.get()]
    audio    = [t["id"] for t, v in SelectedAudio if v.get()]
    subs     = [t["id"] for t, v in SelectedSubs if v.get()]

    return title_index, chapters, audio, subs

def ConfirmNoAudio():
    return messagebox.askyesno(
        "No Audio Selected",
        "No audio selected.\nAre you sure you want to begin the rip?"
    )

def FormatChapters(chapters):
    if not chapters:
        return None

    chapters = sorted(chapters)

    ranges = []
    start = prev = chapters[0]

    for num in chapters[1:]:
        if num == prev + 1:
            prev = num
        else:
            ranges.append((start, prev))
            start = prev = num

    ranges.append((start, prev))

    parts = []
    for s, e in ranges:
        if s == e:
            parts.append(str(s))
        else:
            parts.append(f"{s}-{e}")

    return ",".join(parts)

def BuildCommand(title, chapters, audio, subs):
    filename = NullRipFileName.get().strip()

    if not filename:
        filename = f"Title_{title}"

    if not filename.lower().endswith(".mkv"):
        filename += ".mkv"

    output_file = os.path.join(NullRipOutputPath.get(), filename)
    if os.path.exists(output_file):
        if not messagebox.askyesno("Overwrite?", f"{filename} already exists.\nOverwrite?"):
            return None

    cmd = [
        "HandBrakeCLI",
        "-i", NullRipInputPath.get(),
        "-o", output_file,
        "--title", str(title),
        "-q", "20",
    ]

    if chapters:
        formatted = FormatChapters(chapters)
        cmd += ["--chapters", formatted]

    if audio:
        cmd += ["--audio", ",".join(map(str, audio))]

    if subs:
        cmd += ["--subtitle", ",".join(map(str, subs))]

    return cmd

def ShowRipOverlay():
    NullRipOverlay.place(
        relx=0,
        rely=0,
        relwidth=1,
        relheight=1
    )
    NullRipOverlay.lift()

def HideRipOverlay():
    NullRipOverlay.place_forget()

def UpdateRipOverlay(percent=0, eta="--"):
    NullRipOverlayLabel.config(
        text=(
            "Ripping Video...\n\n"
            f"Progress: {percent:.1f}%\n"
            f"ETA: {eta}\n\n"
            "Please wait..."
        )
    )

def CancelRip():
    global CurrentProcess

    if CurrentProcess:
        try:
            CurrentProcess.terminate()
        except:
            pass

    HideRipOverlay()

def StartRip():
    data = GetSelections()

    if not data:
        messagebox.showerror("Error", "No title selected.")
        return

    title, chapters, audio, subs = data

    if not chapters:
        messagebox.showerror("Error", "No chapters selected.")
        return

    if not audio:
        if not ConfirmNoAudio():
            return

    if not NullRipInputPath.get():
        messagebox.showerror("Error", "No input selected.")
        return

    if not NullRipOutputPath.get():
        messagebox.showerror("Error", "No output folder selected.")
        return

    filename = NullRipFileName.get().strip()

    if not filename:
        messagebox.showerror("Error", "No filename set.")
        return

    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    NullRipFileName.set(filename)

    cmd = BuildCommand(title, chapters, audio, subs)

    if not cmd:
        return

    ShowRipOverlay()
    UpdateRipOverlay(0, "--")

    threading.Thread(
        target=RipThread,
        args=(cmd,),
        daemon=True
    ).start()

def RipThread(cmd):
    global CurrentProcess

    try:
        CurrentProcess = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        percent = 0
        eta = "--"

        for line in CurrentProcess.stdout:
            line = line.strip()
            print(line)

            percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
            eta_match = re.search(r"ETA\s+([0-9hms:]+)", line)

            if percent_match:
                percent = float(percent_match.group(1))

            if eta_match:
                eta = eta_match.group(1)

            Root.after(0, UpdateRipOverlay, percent, eta)

        CurrentProcess.wait()

        if CurrentProcess.returncode != 0:
            Root.after(
                0,
                lambda: messagebox.showerror(
                    "Error",
                    "Rip failed or cancelled."
                )
            )
            Root.after(0, HideRipOverlay)
            return

        Root.after(0, FinishRip)

    finally:
        CurrentProcess = None

def FinishRip():
    HideRipOverlay()

    messagebox.showinfo("Done", "Rip complete.")

    if NullRipOpenFolder.get():
        try:
            subprocess.Popen(["xdg-open", NullRipOutputPath.get()])
        except Exception as e:
            print("Failed to open folder:", e)

# ————————————————————————————————————————————————————————————
# NullMidi
# ————————————————————————————————————————————————————————————
# ------------------------------ 
# Key Handling 
# ------------------------------
def BuildDevice(Target, Field):
    global UInputDevice
    Keys = set()
    for Key in Target.get(Field) or []:
        Candidate = f"KEY_{Key.upper()}"
        if hasattr(uinput, Candidate):
            Keys.add(getattr(uinput, Candidate))

    if Keys:
        if UInputDevice:
            UInputDevice.destroy()
        UInputDevice = uinput.Device(list(Keys))

def PressKeyCombo(Keys):
    if not UInputDevice:
        BuildDevice()

    Mapped = []
    for Key in Keys:
        Candidate = f"KEY_{Key.upper()}"
        if hasattr(uinput, Candidate):
            Mapped.append(getattr(uinput, Candidate))

    if not Mapped:
        return

    for Key in Mapped[:-1]:
        UInputDevice.emit(Key, 1)

    UInputDevice.emit_click(Mapped[-1])

    for Key in Mapped[:-1]:
        UInputDevice.emit(Key, 0)

    UInputDevice.syn()

def NormalizeKey(Key):
    Key = Key.upper()
    if "SHIFT" in Key: return "LEFTSHIFT"
    if "CONTROL" in Key: return "LEFTCTRL"
    if "ALT" in Key: return "LEFTALT"
    return Key

def SortKeys(Keys):
    Priority = {
        "LEFTSHIFT": 0,
        "RIGHTSHIFT": 0,
        "LEFTCTRL": 1,
        "RIGHTCTRL": 1,
        "LEFTALT": 2,
        "RIGHTALT": 2
    }
    return sorted(Keys, key=lambda K: (Priority.get(K, 99), K))

def FormatKeyName(Key):
    if "SHIFT" in Key: return "Shift"
    if "CTRL" in Key: return "Ctrl"
    if "ALT" in Key: return "Alt"
    return Key

def IsOnlyModifiers(Keys):
    for K in Keys:
        if not ("SHIFT" in K or "CTRL" in K or "ALT" in K):
            return False
    return True

def CancelActiveCapture():
    ActiveCapture["Cancel"] = True

def DetectKey(Button, Target, Field, Timeout=5):

    CancelActiveCapture()
    ActiveCapture["Cancel"] = False

    Button.config(text=f"Waiting... {Timeout}\n Hold ESC to clear")

    HeldKeys = set()

    LastInputTime = [0]

    EscapeHeld = [False]

    EndTime = time.time() + Timeout

    def Cleanup():

        Root.unbind("<KeyPress>")
        Root.unbind("<KeyRelease>")


    def ClearBinding():

        if not EscapeHeld[0]:
            return

        Target[Field] = []

        Button.config(text="Set Key")

        BuildDevice()
        SaveConfig()
        Cleanup()


    def OnPress(Event):

        if ActiveCapture["Cancel"]:
            Cleanup()
            return

        Key = NormalizeKey(Event.keysym)

        if Key == "ESCAPE":

            if not EscapeHeld[0]:

                EscapeHeld[0] = True

                Root.after(1000, ClearBinding)

            return

        HeldKeys.add(Key)

        LastInputTime[0] = time.time()

        Button.config(
            text="+".join(
                FormatKeyName(K)
                for K in SortKeys(HeldKeys)
            )
        )

    def OnRelease(Event):

        Key = NormalizeKey(Event.keysym)

        if Key == "ESCAPE":

            EscapeHeld[0] = False


    def Tick():

        if ActiveCapture["Cancel"]:
            Cleanup()
            return

        if not HeldKeys:

            Remaining = int(EndTime - time.time())

            if Remaining <= 0:

                Button.config(text="Set Key")

                Cleanup()

                return

            Button.config(text=f"Waiting... {Remaining}")

            Root.after(1000, Tick)

            return

        if IsOnlyModifiers(HeldKeys):

            Remaining = int(EndTime - time.time())

            if Remaining <= 0:

                Target[Field] = SortKeys(HeldKeys)

                Button.config(
                    text="+".join(
                        FormatKeyName(K)
                        for K in Target[Field]
                    )
                )

                BuildDevice(Target,Field)

                SaveConfig()

                Cleanup()

                return

            Button.config(
                text=f"{FormatKeyName(list(HeldKeys)[0])}... {Remaining}"
            )

            Root.after(1000, Tick)

            return

        if time.time() - LastInputTime[0] > 0.5:

            Target[Field] = SortKeys(HeldKeys)

            Button.config(
                text="+".join(
                    FormatKeyName(K)
                    for K in Target[Field]
                )
            )

            BuildDevice(Target,Field)

            SaveConfig()

            Cleanup()

            return

        Root.after(100, Tick)

    Root.bind("<KeyPress>", OnPress)

    Root.bind("<KeyRelease>", OnRelease)

    Tick()

# ------------------------------ 
# Midi Handling
# ------------------------------
def StartMidiListener(Device):

    if Device in MidiDeviceListeners:
        return

    Running = True

    def MidiListener():

        try:
            Port = mido.open_input(Device)

        except Exception as E:
            print(f"❌ Failed To Open MIDI Device: {Device}")
            print(E)
            return

        MidiDeviceListeners[Device]["Port"] = Port

        print(f"🎹 Started MIDI Listener: {Device}")

        while MidiDeviceListeners[Device]["Running"]:

            try:
                for Message in Port.iter_pending():

                    HandleMidiMessage(Device, Message)

                time.sleep(0.001)

            except Exception as E:
                print(f"❌ MIDI Runtime Error ({Device})")
                print(E)
                break

        try:
            Port.close()
        except:
            pass

        print(f"🛑 Closed MIDI Listener: {Device}")

    Thread = threading.Thread(target=MidiListener, daemon=True)

    MidiDeviceListeners[Device] = {
        "Thread": Thread,
        "Port": None,
        "Running": Running
    }

    Thread.start()

def StopMidiListener(Device):

    if Device not in MidiDeviceListeners:
        return

    MidiDeviceListeners[Device]["Running"] = False

    Port = MidiDeviceListeners[Device].get("Port")

    if Port:
        try:
            Port.close()
        except:
            pass

    del MidiDeviceListeners[Device]

    print(f"🛑 Stopped MIDI Listener: {Device}")

def HandleMidiMessage(Device, Message):

    for Row in MidiRows:

        if not Row.get("Active"):
            continue

        if Row.get("Device") != Device:
            continue

        print(Device, Message)

def GetPorts():
    try:
        RawPorts = mido.get_input_names()
    except Exception:
        return []
    IgnoreKeywords = ("Virtual","LoopMIDI","Through","Midi Through","Monitor")
    ValidPorts = []

    for Port in RawPorts:
        if any(K in Port for K in IgnoreKeywords):
            continue
        if Port not in ValidPorts:
            ValidPorts.append(Port)

    return ValidPorts

def DetectNote(Button, Device, Target, Field, Timeout=5):
    CancelActiveCapture()
    ActiveCapture["Cancel"] = False
    Button.config(text=f"Waiting... {Timeout}\n Hold ESC to clear")
    EscapeHeld = [False]


    def Cleanup():
        Root.unbind("<KeyPress>")
        Root.unbind("<KeyRelease>")

    def ClearBinding():
        if not EscapeHeld[0]:
            return

        Target[Field] = None
        Button.config(text="Set Midi")
        SaveConfig()
        Cleanup()

    def OnPress(Event):
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            if not EscapeHeld[0]:
                EscapeHeld[0] = True
                Root.after(1000, ClearBinding)


    def OnRelease(Event):
        Key = NormalizeKey(Event.keysym)
        if Key == "ESCAPE":
            EscapeHeld[0] = False

    def Worker():
        EndTime = time.time() + Timeout
        try:
            with mido.open_input(Device) as Port:
                while time.time() < EndTime:
                    if ActiveCapture["Cancel"]:
                        Cleanup()
                        return
                    for Msg in Port.iter_pending():
                        if Msg.type == "note_on":
                            Target[Field] = Msg.note
                            Button.config(text=str(Msg.note))
                            SaveConfig()
                            Cleanup()
                            return
                    time.sleep(0.01)
            Button.config(text="Set Midi")
            Cleanup()

        except:
            Button.config(text="Error")
            Cleanup()

    Root.bind("<KeyPress>", OnPress)
    Root.bind("<KeyRelease>", OnRelease)
    threading.Thread(target=Worker, daemon=True).start()

def MidiListener(Row):
    global LastPedalValue
    Device = Row["Device"]
    while True:
        if not Row["Active"]:
            continue

        if Row['Device'] != Device:
            continue

        try:
            with mido.open_input(Device) as Port:
                for msg in Port:
                    
                    if msg.type == "control_change":
                        if Row['Drums']:
                            if msg.control == 4:
                                LastPedalValue = msg.value
                            continue
                        elif Row['Keyboard']:
                            continue
                        else:
                            continue
                        continue

                    if msg.type == "polytouch":
                        if Row['Drums']:
                            for i in range(pygame.mixer.get_num_channels()):
                                pygame.mixer.Channel(i).stop()
                            continue
                        elif Row['Keyboard']:
                            continue
                        else:
                            continue
                        continue

                    if msg.type == "note_on" and msg.velocity >= Row['Input']['VelocityRequirement']:
                        if Row['Drums']:
                            continue
                        elif Row['Keyboard']:
                            continue
                        else:
                            continue
                    
                    if not Row['PressKeys']:
                        Mapping = Row["Mappings"].get(msg.note)
                        if not Mapping:
                            continue
                        else:
                            PressKeyCombo(Mapping["Keys"])

                    
        except Exception as E:
            print("Listener Error:", E)
            time.sleep(1)

def CreateVirtualPort(Row):
    Name = f"NullMidiVirtualPort{len(MidiRows)+1:02d}"
    try:
        Port = mido.open_output(Name, virtual=True)
        Row["VirtualPortName"] = Name
        Row["VirtualPort"] = Port
    except Exception as E:
        print(f"❌ Failed To Create Virtual Port: {E}")
        Row["VirtualPortName"] = None
        Row["VirtualPort"] = None

# ------------------------------ 
# UI Stuff
# ------------------------------

def SearchForSoundFile(Drum, var):
        path = filedialog.askopenfilename(
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if not path:
            return
        
        Drum['CenterSoundFilePath'] = path
        var.set(path)

        SaveConfig()

def AddMidiRow(Row=None, Loading=False):
    global MidiRows
    Frame = tk.Frame(MidiContainer, bd=2, relief="solid")
    Frame.pack(fill="both", expand=True, padx=5, pady=5)
    Frame.columnconfigure(0, weight=1)
    Frame.rowconfigure(0, weight=1)

    if Row is None:
        Row = {}
        Row['Index'] = len(MidiRows) -1
        Row['Device'] = None
        Row['Controller'] = False
        Row['Drums'] = False
        Row['Keyboard'] = False
        Row['Active'] = True
        Row['Sounds'] = False
        Row['DrumList'] = []
        Row['KeyboardList'] = []
        Row['ControllerList'] = []

    CreateVirtualPort(Row)

    TogglesRow = tk.Frame(Frame)
    TogglesRow.pack(fill="x", padx=5, pady=5)
    TogglesRow.columnconfigure(0, weight=1)
    TogglesRow.columnconfigure(1, weight=1)
    TogglesRow.columnconfigure(2, weight=1)
    TogglesRow.columnconfigure(3, weight=1)
    TogglesRow.columnconfigure(4, weight=1)

    MainControllerVar = tk.BooleanVar(value=Row.get("Controller", False))
    MainDrumVar = tk.BooleanVar(value=Row.get("Drums", False))
    MainKeyboardVar = tk.BooleanVar(value=Row.get("Keyboard", False))

    BasicTopRow = tk.Frame(Frame)
    BasicTopRow.pack(fill="x", padx=5, pady=5)
    BasicTopRow.columnconfigure(0, weight=0)
    BasicTopRow.columnconfigure(1, weight=0)
    BasicTopRow.columnconfigure(2, weight=0)
    BasicTopRow.columnconfigure(3, weight=0)
    BasicTopRow.columnconfigure(4, weight=2)
    BasicTopRow.columnconfigure(5, weight=0)
    BasicTopRow.rowconfigure(0, weight=0)
    
    ControllerRow = tk.Frame(Frame)
    ControllerRow.pack(fill="x", padx=5, pady=5)
    ControllerRow.pack_forget()

    DrumRow = tk.Frame(Frame)
    DrumRow.pack(fill="both", expand=True, padx=5, pady=5)
    DrumRow.columnconfigure(0, weight=1)
    DrumRow.rowconfigure(0,weight=0)
    DrumRow.rowconfigure(1,weight=1, minsize=700)
    DrumRow.pack_forget()

    KeyboardRow = tk.Frame(Frame)
    KeyboardRow.pack(fill="x", padx=5, pady=5)
    KeyboardRow.pack_forget()


    BasicControllerVar = tk.BooleanVar(value=True)
    BasicDrumVar = tk.BooleanVar(value=True)
    BasicKeyboardVar = tk.BooleanVar(value=True)

    ActiveMidiDevice = tk.BooleanVar(value=Row.get("Active", False))
    MuteMidiDevice = tk.BooleanVar(value=Row.get("Mute", False))
    
    def HideBasictopRow():
        BasicControllerVar.set(True)
        BasicDrumVar.set(True)
        BasicKeyboardVar.set(True)
        Row['Controller'] = False
        Row['Drums'] = False
        Row['Keyboard'] = False
        BasicTopRow.pack_forget()
        ControllerRow.pack_forget()
        DrumRow.pack_forget()
        KeyboardRow.pack_forget()
        TogglesRow.pack(fill="x", padx=5, pady=5)

    def UpdateActiveState():
        Row["Active"] = ActiveMidiDevice.get()
        SaveConfig()

    def UpdateActiveState():
        Row["Mute"] = MuteMidiDevice.get()
        SaveConfig()


    BasicTopRowControllerToggle = tk.Checkbutton(BasicTopRow,variable=BasicControllerVar,text="Controller", command=lambda:HideBasictopRow())
    BasicTopRowControllerToggle.grid(row=0, column=0, sticky="ew", padx=2)
    BasicTopRowControllerToggle.grid_remove()
    BasicTopRowDrumToggle = tk.Checkbutton(BasicTopRow,variable=BasicDrumVar,text="Drums", command=lambda:HideBasictopRow())
    BasicTopRowDrumToggle.grid(row=0, column=0, sticky="ew", padx=2)
    BasicTopRowDrumToggle.grid_remove()
    BasicTopRowKeyboardToggle = tk.Checkbutton(BasicTopRow,variable=BasicKeyboardVar,text="Keyboard", command=lambda:HideBasictopRow())
    BasicTopRowKeyboardToggle.grid(row=0, column=0, sticky="ew", padx=2)
    BasicTopRowKeyboardToggle.grid_remove()

    Divider = tk.Frame(BasicTopRow,width=2,bg="#555")
    Divider.grid(row=0,column=1,sticky="news",padx=5)

    BasicTopRowActiveMidi = tk.Checkbutton(BasicTopRow,variable=ActiveMidiDevice, text="Active?", command=lambda: UpdateActiveState())
    BasicTopRowActiveMidi.grid(row=0, column=2, sticky="ew", padx=2)

    BasicTopRowMuteMidi = tk.Checkbutton(BasicTopRow,variable=MuteMidiDevice, text="Mute", command=lambda: UpdateActiveState())
    BasicTopRowMuteMidi.grid(row=0, column=3, sticky="ew", padx=2)

    def UpdateMidiDevice(Event=None):
        Row["Device"] = MidiDeviceVar.get()
        SaveConfig()

    MidiDeviceVar = tk.StringVar(value=Row.get("MidiDevice", ""))
    BasicTopRowMidiDeviceDropDown = ttk.Combobox(BasicTopRow, textvariable=MidiDeviceVar, state="readonly",values=GetPorts())
    BasicTopRowMidiDeviceDropDown.grid(row=0, column=4, sticky="ew", padx=2)
    BasicTopRowMidiDeviceDropDown.bind("<<ComboboxSelected>>",UpdateMidiDevice)

    BasicTopRowDelete = tk.Button(BasicTopRow, text="Delete Row", command=lambda:RemoveMidiRow(Frame, Row), width = 15)
    BasicTopRowDelete.grid(row=0, column=5, sticky="ew", padx=2)

    BasicTopRow.pack_forget()

    def HideToggleRowShowOtherRow(Which):
        TogglesRow.pack_forget()
        ControllerRow.pack_forget()
        DrumRow.pack_forget()
        KeyboardRow.pack_forget()
        BasicTopRow.pack(fill="x", padx=5, pady=5)
        Row['Controller'] = False
        Row['Drums'] = False
        Row['Keyboard'] = False
        Row['Advanced'] = False
        MainControllerVar.set(False)
        MainDrumVar.set(False)
        MainKeyboardVar.set(False)

        if Which == "Controller":
            Row['Controller'] = True
            ControllerRow.pack(fill="x", padx=5, pady=5)
            BasicTopRowControllerToggle.grid()
        elif Which == "Drums":
            Row['Drums'] = True
            DrumRow.pack(fill="both", expand=True, padx=5, pady=5)
            BasicTopRowDrumToggle.grid()
        elif Which == "Keyboard":
            Row['Keyboard'] = True
            KeyboardRow.pack(fill="x", padx=5, pady=5)
            BasicTopRowKeyboardToggle.grid()
        SaveConfig()
    
    ControllerToggle = tk.Checkbutton(TogglesRow, text="Controller", variable=MainControllerVar, command=lambda: HideToggleRowShowOtherRow("Controller"))
    ControllerToggle.grid(row=0, column=0, sticky="ew", padx=2)
    DrumsToggle = tk.Checkbutton(TogglesRow, text="Drums", variable=MainDrumVar, command=lambda: HideToggleRowShowOtherRow("Drums"))
    DrumsToggle.grid(row=0, column=1, sticky="ew", padx=2)
    KeyboardToggle = tk.Checkbutton(TogglesRow, text="Keyboard", variable=MainKeyboardVar, command=lambda: HideToggleRowShowOtherRow("Keyboard"))
    KeyboardToggle.grid(row=0, column=2, sticky="ew", padx=2)
    ToggleRowDelete = tk.Button(TogglesRow, text="Delete Row", command=lambda:RemoveMidiRow(Frame, Row))
    ToggleRowDelete.grid(row=0, column=4, sticky="ew", padx=2)

    # --------------- Drums
    

    DrumList = ScrollableFrame(DrumRow)

    DrumList.grid(row=1, column=0, sticky="ewns", padx=2)
    DrumList.columnconfigure(0,weight=1)
    DrumList.rowconfigure(1,weight=1)

    def AddDrumToList(Drum=None, Loading=False):
        MainDrumFrame = tk.Frame(DrumList.Inner, bd=2, relief="solid")
        MainDrumFrame.pack(fill="both", expand=True, padx=5, pady=5)

        MainDrumFrame.columnconfigure(0, weight=1)
        MainDrumFrame.rowconfigure(0, weight=1)
        

        if Drum is None:
            Drum = {}
            Drum['Drum'] = False
            Drum['Cymbal'] = False
            Drum['Kick'] = False
            Drum['Hihat'] = False

            Drum['Channel1'] = 0
            Drum['Channel2'] = 0
            Drum['Channel3'] = 0

            Drum['CenterGhostNoteThreshold'] = 0
            Drum['CenterSlamNoteThreshold'] = 0

            Drum['RimGhostNoteThreshold'] = 0
            Drum['RimSlamNoteThreshold'] = 0

            Drum['BellGhostNoteThreshold'] = 0
            Drum['BellSlamNoteThreshold'] = 0

            Drum['CenterVolume'] = 0
            Drum['RimVolume'] = 0
            Drum['BellVolume'] = 0

            Drum['CenterMidiInput'] = None
            Drum['RimMidInput'] = None
            Drum['BellMidInput'] = None

            Drum['CenterKeyOutput'] = []
            Drum['RimKeyOutput'] = []
            Drum['BellKeyOutput'] = []
            
            Drum['CenterSoundFilePath'] = None
            Drum['RimSoundFilePath'] = None
            Drum['BellSoundFilePath'] = None

            Drum['KickDrumMinimumVelocity'] = None

            Drum['HiHatClosedThreshold'] = 0
            Drum['HiHatHalfThreshold'] = 0
            Drum['HiHatOpenThreshold'] = 0
            Drum['HiHatClosedPath'] = None
            Drum['HiHatHalfPath'] = None
            Drum['HiHatOpenPath'] = None
            Drum['HiHatStompPath'] = None
            Drum['HiHatBellOpenPath'] = None
            Drum['HiHatBellClosedPath'] = None
            Drum['HiHatClosedVolume'] = 0
            Drum['HiHatHalfVolume'] = 0
            Drum['HiHatOpenVolume'] = 0
            Drum['HiHatStompVolume'] = 0
            Drum['HiHatBellOpenVolume'] = 0
            Drum['HiHatBellCloseVolume'] = 0
            Row['DrumList'].append(Drum)


        DrumRowDrumVar = tk.BooleanVar(value=Drum.get("Drum", False))
        DrumRowCymbalVar = tk.BooleanVar(value=Drum.get("Cymbal", False))
        DrumRowKickVar = tk.BooleanVar(value=Drum.get("Kick", False))
        DrumRowHihatVar = tk.BooleanVar(value=Drum.get("Hihat", False))

        MainDrumRowToggles = tk.Frame(MainDrumFrame)
        MainDrumRowToggles.grid(row=0, column=0, sticky="ew", padx=2)
        MainDrumRowToggles.columnconfigure(0, weight=1)
        MainDrumRowToggles.columnconfigure(1, weight=1)
        MainDrumRowToggles.columnconfigure(2, weight=1)
        MainDrumRowToggles.columnconfigure(3, weight=1)
        MainDrumRowToggles.columnconfigure(4, weight=1)
        MainDrumRowToggles.rowconfigure(0, weight=1)

        DrumRowDrumRow = tk.Frame(MainDrumFrame)
        DrumRowDrumRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowDrumRow.grid_forget()

        DrumRowCymbalRow = tk.Frame(MainDrumFrame)
        DrumRowCymbalRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowCymbalRow.grid_forget()

        DrumRowKickRow = tk.Frame(MainDrumFrame)
        DrumRowKickRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowKickRow.grid_forget()

        DrumRowHihatRow = tk.Frame(MainDrumFrame)
        DrumRowHihatRow.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowHihatRow.grid_forget()

        DrumRowCymbalRowVar = tk.BooleanVar(value=True)
        DrumRowKickRowVar = tk.BooleanVar(value=True)
        DrumRowHiHatRowVar = tk.BooleanVar(value=True)
        DrumRowDrumRowVar = tk.BooleanVar(value=True)

        def RemoveDrum(Drum):
            Row["DrumList"].remove(Drum)
            MainDrumFrame.destroy()
            SaveConfig()

        def SwitchDrumType(Which):
            MainDrumRowToggles.grid_forget()
            DrumRowDrumRow.grid_forget()
            DrumRowCymbalRow.grid_forget()
            DrumRowKickRow.grid_forget()
            DrumRowHihatRow.grid_forget()
            Drum['Drum'] = False
            Drum['Cymbal'] = False
            Drum['Kick'] = False
            Drum['Hihat'] = False
            DrumRowDrumVar.set(False)
            DrumRowCymbalVar.set(False)
            DrumRowKickVar.set(False)
            DrumRowHihatVar.set(False)

            if Which == "Pad":
                DrumRowDrumRow.grid(row=0, column=0, sticky="ew", padx=2)
                DrumRowDrumRow.columnconfigure(0, weight=1)
                DrumRowDrumRow.rowconfigure(0, weight=1)
                DrumRowDrumRow.rowconfigure(1, weight=0)
                DrumRowDrumRow.rowconfigure(2, weight=0)
                Drum['Drum'] = True
            elif Which == "Cymbal":
                DrumRowCymbalRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Cymbal'] = True
            elif Which == "Kick":
                DrumRowKickRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Kick'] = True
            elif Which == "Hihat":
                DrumRowHihatRow.grid(row=0, column=0, sticky="ew", padx=2)
                Drum['Hihat'] = True
            elif Which == "Main":
                MainDrumRowToggles.grid(row=0, column=0, sticky="ew", padx=2)

            channels = []
            for i in range(128):
                channels.append(i)

            def UpdateChannel(*args):
                Drum['Channel1'] = Channel1.get()
                Drum['Channel2'] = Channel2.get()
                Drum['Channel3'] = Channel3.get()
                SaveConfig()

            Channel1 = tk.IntVar(value=Drum['Channel1'])
            Channel2 = tk.IntVar(value=Drum['Channel2'])
            Channel3 = tk.IntVar(value=Drum['Channel3'])

            Channel1.trace_add("write", UpdateChannel)
            Channel2.trace_add("write", UpdateChannel)
            Channel3.trace_add("write", UpdateChannel)

            #--- Drums. Basic Drum Row
            #------ TopRow
            DrumRowTopRow = tk.Frame(DrumRowDrumRow)
            DrumRowTopRow.grid(row=0, column=0, sticky="ew", padx=2)

            DrumRowTopRow.columnconfigure(0, weight=0 )
            DrumRowTopRow.columnconfigure(1, weight=0 )
            DrumRowTopRow.columnconfigure(2, weight=0 )
            DrumRowTopRow.columnconfigure(3, weight=0 )
            DrumRowTopRow.columnconfigure(4, weight=0 )
            DrumRowTopRow.columnconfigure(5, weight=0 )
            DrumRowTopRow.columnconfigure(6, weight=0 )
            DrumRowTopRow.rowconfigure(0, weight=0 )

            DrumRowDrumToMainToggle = tk.Checkbutton(DrumRowTopRow, text="Pad?", variable=DrumRowDrumRowVar, command=lambda:SwitchDrumType("Main"))
            DrumRowDrumToMainToggle.grid(row=0, column=0, sticky="ew", padx=2)

            Divider = tk.Frame(DrumRowTopRow,width=2,bg="#555")
            Divider.grid(row=0,column=1,sticky="ns",padx=5)

            DrumRowChannelsLabel= tk.Label(DrumRowTopRow, text="Channels:")
            DrumRowChannelsLabel.grid(row=0, column=2, sticky="ew", padx=2)

            DrumRowDrumChannel1 = ttk.Combobox(DrumRowTopRow, textvariable=Channel1, state="readonly",values=channels)
            DrumRowDrumChannel1.grid(row=0, column=3, padx=2)
            DrumRowDrumChannel2 = ttk.Combobox(DrumRowTopRow, textvariable=Channel2, state="readonly",values=channels)
            DrumRowDrumChannel2.grid(row=0, column=4, padx=2)
            DrumRowDrumChannel3 = ttk.Combobox(DrumRowTopRow, textvariable=Channel3, state="readonly",values=channels)
            DrumRowDrumChannel3.grid(row=0, column=5, padx=2)

            RemoveDrumObjectFromList= tk.Button(DrumRowTopRow, text="Remove Pad?", command=lambda:RemoveDrum(Drum))
            RemoveDrumObjectFromList.grid(row=0, column=6, sticky="ew", padx=2)
            #------------ CenterRow
            DrumRowCenterPad = tk.Frame(DrumRowDrumRow, bd=2, relief="solid")
            DrumRowCenterPad.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
            DrumRowCenterPad.rowconfigure(0, minsize=8)
            DrumRowCenterPad.rowconfigure(1, weight=0)
            DrumRowCenterPad.rowconfigure(2, weight=0)
            DrumRowCenterPad.rowconfigure(2, weight=0)

            DrumRowCenterPad.columnconfigure(0, weight=0)
            DrumRowCenterPad.columnconfigure(1, weight=0)
            DrumRowCenterPad.columnconfigure(2, weight=0)
            DrumRowCenterPad.columnconfigure(3, weight=0)
            DrumRowCenterPad.columnconfigure(4, weight=0)

            DrumRowCenterSoundLocationVar = tk.StringVar(value= Drum.get("CenterSoundFilePath", ""))
            CenterVolumeVar = tk.IntVar(value=Drum.get("CenterVolume", 100))
            CenterGhostNote = tk.IntVar(value=Drum.get("CenterGhostNoteThreshold", 100))
            CenterSlam= tk.IntVar(value=Drum.get("CenterSlamNoteThreshold", 100))

            DrumRowCenterLabel = tk.Label(DrumRowCenterPad, text= "Center Pad", width= 8)
            DrumRowCenterLabel.grid(row=0, column=0, sticky="ew")

            DrumRowCenterSoundLabel = tk.Label(DrumRowCenterPad, text= "Sound:", width= 8)
            DrumRowCenterSoundLabel.grid(row=1, column=0, sticky="ew")
            DrumRowCenterBrowseButton = tk.Button(DrumRowCenterPad, command=lambda: SearchForSoundFile(Drum ,DrumRowCenterSoundLocationVar ), text="Browse", width=22)
            DrumRowCenterBrowseButton.grid(row=1, column=1)
            DrumRowCenterSoundLocationIF = tk.Entry(DrumRowCenterPad, textvariable=DrumRowCenterSoundLocationVar, state="readonly", width=44)
            DrumRowCenterSoundLocationIF.grid(row=1, column=2, sticky="ew")

            Divider = tk.Frame(DrumRowCenterPad,width=2,bg="#555")
            Divider.grid(row=1,column=3 ,padx=5)

            
            DrumRowCenterVolumeSlider = tk.Scale(DrumRowCenterPad,from_=0,to=100,orient="horizontal",variable=CenterVolumeVar,showvalue=False, length=300,)
            DrumRowCenterVolumeSlider.grid(row=1, column=4)
            DrumRowCenterVolumeShowLabel = tk.Label(DrumRowCenterPad,textvariable=CenterVolumeVar, width= 4)
            DrumRowCenterVolumeShowLabel.grid(row=1, column=5, sticky="e")
            DrumRowCenterVolumeLabel = tk.Label(DrumRowCenterPad, text= "Volume", width = 12, height=2)
            DrumRowCenterVolumeLabel.grid(row=1, column=6, sticky="ew")

            DrumRowCenterInputsLabel = tk.Label(DrumRowCenterPad, text= "Inputs:", width =8 )
            DrumRowCenterInputsLabel.grid(row=2, column=0)

            DrumRowCenterMidiInputButton = tk.Button(DrumRowCenterPad,text=("Set Midi"if Drum.get("CenterMidiInput") is None else str(Drum.get("CenterMidiInput"))),command=lambda: DetectNote(DrumRowCenterMidiInputButton,Row["Device"],Drum, "CenterMidiInput"), width =22)
            DrumRowCenterMidiInputButton.grid(row=2, column=1)

            DrumRowcenterKeyOutputButton = tk.Button(DrumRowCenterPad,text="+".join(Drum.get("CenterKeyOutput")) or "Set Key",command=lambda: DetectKey(DrumRowcenterKeyOutputButton,Drum, "CenterKeyOutput"), width=22)
            DrumRowcenterKeyOutputButton.grid(row=2, column=2, sticky="ew")

            def UpdateCenterVolume(*args):
                Drum["CenterVolume"] = CenterVolumeVar.get()
                SaveConfig()

            CenterVolumeVar.trace_add("write",UpdateCenterVolume)

            def UpdateCenterGhost(*args):
                Drum["CenterGhostNoteThreshold"] = CenterGhostNote.get()
                SaveConfig()

            CenterGhostNote.trace_add("write",UpdateCenterGhost)

            def UpdateCenterSlam(*args):
                Drum["CenterSlamNoteThreshold"] = CenterSlam.get()
                SaveConfig()

            CenterSlam.trace_add("write",UpdateCenterSlam)

            DrumRowCenterSliders = tk.Frame(DrumRowCenterPad)
            DrumRowCenterSliders.grid(row=3, column=0, sticky="ew", padx=(0,2), pady=2,columnspan=7,)
            DrumRowCenterSliders.columnconfigure(0, weight=0)
            DrumRowCenterSliders.columnconfigure(1, weight=0)
            DrumRowCenterSliders.columnconfigure(2, weight=0)
            DrumRowCenterSliders.columnconfigure(3, weight=0)
            DrumRowCenterSliders.columnconfigure(4, weight=0)
            DrumRowCenterSliders.columnconfigure(5, weight=0)
            DrumRowCenterSliders.columnconfigure(6, weight=0)
            DrumRowCenterSliders.columnconfigure(7, weight=0)
            DrumRowCenterSliders.rowconfigure(0, weight=0)

            DrumRowCenterVelocityLabel = tk.Label(DrumRowCenterSliders, text= "Velocities:", width = 12, height=2)
            DrumRowCenterVelocityLabel.grid(row=0, column=0, sticky="w")

            DrumRowCenterGhostSlider = tk.Scale(DrumRowCenterSliders,from_=1,to=127,orient="horizontal",variable=CenterGhostNote,showvalue=False, length=300,)
            DrumRowCenterGhostSlider.grid(row=0, column=1, sticky="ew")
            
            DrumRowCenterGhostShowLabel = tk.Label(DrumRowCenterSliders,textvariable=CenterGhostNote)
            DrumRowCenterGhostShowLabel.grid(row=0, column=2, sticky="e")

            DrumRowCenterGhostLabel = tk.Label(DrumRowCenterSliders, text= "Ghost Note", width = 12, height=2)
            DrumRowCenterGhostLabel.grid(row=0, column=3, sticky="e")

            Divider = tk.Frame(DrumRowCenterSliders,width=2,bg="#555")
            Divider.grid(row=0,column=4,sticky="ns",padx=5)

            DrumRowCenterSlamSlider = tk.Scale(DrumRowCenterSliders,from_=1,to=127,orient="horizontal",variable=CenterSlam,showvalue=False, length=300,)
            DrumRowCenterSlamSlider.grid(row=0, column=5, sticky="ew")

            DrumRowCenterSlamShowLabel = tk.Label(DrumRowCenterSliders,textvariable=CenterSlam, width= 4)
            DrumRowCenterSlamShowLabel.grid(row=0, column=6, sticky="e")

            DrumRowCenterSlamLabel = tk.Label(DrumRowCenterSliders, text= "Slam Note", width = 12, height=2)
            DrumRowCenterSlamLabel.grid(row=0, column=7, sticky="e")
            
        
            


            #------------ RimRow
            DrumRowRimPad = tk.Frame(DrumRowDrumRow, bd=2, relief="solid")
            DrumRowRimPad.grid(row=2, column=0, sticky="ew", padx=2,)

            DrumRowRimPad.rowconfigure(0, weight=0)
            DrumRowRimPad.rowconfigure(1, weight=0)
            DrumRowRimPad.rowconfigure(2, weight=0)

            DrumRowRimPad.columnconfigure(0, weight=0)
            DrumRowRimPad.columnconfigure(1, weight=0)
            DrumRowRimPad.columnconfigure(2, weight=1)
            DrumRowRimPad.columnconfigure(3, weight=1)
            DrumRowRimPad.columnconfigure(4, weight=0)
            DrumRowRimPad.columnconfigure(5, weight=0)
            DrumRowRimPad.columnconfigure(6, weight=0)
            DrumRowRimPad.columnconfigure(7, weight=0)

            DrumRowRimSoundLocationVar = tk.StringVar(value=Drum.get("RimSoundFilePath", ""))
            RimVolumeVar = tk.IntVar(value=Drum.get("RimVolume", 100))
            RimGhostNote = tk.IntVar(value=Drum.get("RimGhostNoteThreshold", 100))
            RimSlam = tk.IntVar(value=Drum.get("RimSlamNoteThreshold", 100))
            DrumRowRimLabel = tk.Label(DrumRowRimPad,text="Rim:", width= 8)
            DrumRowRimLabel.grid(row=0,column=0,sticky="ew")
            DrumRowRimBrowseButton = tk.Button(DrumRowRimPad,command=lambda: SearchForSoundFile(Drum,DrumRowRimSoundLocationVar),text="Browse",width=8)
            DrumRowRimBrowseButton.grid(row=0,column=1,sticky="ew")
            DrumRowRimSoundLocationIF = tk.Entry(DrumRowRimPad,textvariable=DrumRowRimSoundLocationVar,state="readonly")
            DrumRowRimSoundLocationIF.grid(row=0,column=2,sticky="ew")
            DrumRowRimVolumeSlider = tk.Scale(DrumRowRimPad,from_=0,to=100,orient="horizontal",variable=RimVolumeVar,showvalue=False)
            DrumRowRimVolumeSlider.grid(row=0,column=3,sticky="ew")
            DrumRowRimVolumeLabel = tk.Label(DrumRowRimPad,text="Volume:")
            DrumRowRimVolumeLabel.grid(row=0,column=4,sticky="ew")
            DrumRowRimVolumeShowLabel = tk.Label(DrumRowRimPad,textvariable=RimVolumeVar)
            DrumRowRimVolumeShowLabel.grid(row=0,column=5,sticky="w")
            DrumRowRimMidiInputButton = tk.Button(DrumRowRimPad,text=str(Drum.get("RimMidiInput", "Set Midi")),command=lambda: DetectNote(DrumRowRimMidiInputButton,Row["Device"],Drum,"RimMidiInput"))
            DrumRowRimMidiInputButton.grid(row=0,column=6,sticky="ew")
            DrumRowRimKeyOutputButton = tk.Button(DrumRowRimPad,text="+".join(Drum.get("RimKeyOutput")) or [],command=lambda: DetectKey(DrumRowRimKeyOutputButton,Drum,"RimKeyOutput"))
            DrumRowRimKeyOutputButton.grid(row=0,column=7,sticky="ew")

            def UpdateRimVolume(*args):
                Drum["RimVolume"] = RimVolumeVar.get()
                SaveConfig()

            RimVolumeVar.trace_add("write",UpdateRimVolume)

            def UpdateRimGhost(*args):
                Drum["RimGhostNoteThreshold"] = RimGhostNote.get()
                SaveConfig()

            RimGhostNote.trace_add("write",UpdateRimGhost)

            def UpdateRimSlam(*args):
                Drum["RimSlamNoteThreshold"] = RimSlam.get()
                SaveConfig()

            RimSlam.trace_add("write",UpdateRimSlam)
            DrumRowRimGhostSlider = tk.Scale(DrumRowRimPad,from_=1,to=127,orient="horizontal",variable=RimGhostNote,showvalue=False)
            DrumRowRimGhostSlider.grid(row=1,column=3,sticky="ew")
            DrumRowRimGhostLabel = tk.Label(DrumRowRimPad,text="Ghost Note Velocity:")
            DrumRowRimGhostLabel.grid(row=1,column=4,sticky="ew")
            DrumRowRimGhostShowLabel = tk.Label(DrumRowRimPad,textvariable=RimGhostNote)
            DrumRowRimGhostShowLabel.grid(row=1,column=5,sticky="w")
            DrumRowRimSlamSlider = tk.Scale(DrumRowRimPad,from_=1,to=127,orient="horizontal",variable=RimSlam,showvalue=False)
            DrumRowRimSlamSlider.grid(row=2,column=3,sticky="ew")
            DrumRowRimSlamLabel = tk.Label(DrumRowRimPad,text="Slam Note Velocity:")
            DrumRowRimSlamLabel.grid(row=2,column=4,sticky="ew")
            DrumRowRimSlamShowLabel = tk.Label(DrumRowRimPad,textvariable=RimSlam)
            DrumRowRimSlamShowLabel.grid(row=2,column=5,sticky="w")
            
            #--- Drums, Cymbal Row
            

            DrumRowCymbalToMainToggle = tk.Checkbutton(DrumRowCymbalRow, text="Cymbal?", variable=DrumRowCymbalRowVar, command=lambda:SwitchDrumType("Main"))
            DrumRowCymbalToMainToggle.grid(row=0, column=0, sticky="ew", padx=2)

            #--- Drums, Kick Row
            

            DrumRowKickToMainToggle = tk.Checkbutton(DrumRowKickRow, text="Kick?", variable=DrumRowKickRowVar, command=lambda:SwitchDrumType("Main"))
            DrumRowKickToMainToggle.grid(row=0, column=0, sticky="ew", padx=2)

            #--- Drums, HiHat Row
            

            DrumRowHihatToMainToggle = tk.Checkbutton(DrumRowHihatRow, text="Hihat?", variable=DrumRowHiHatRowVar, command=lambda:SwitchDrumType("Main"))
            DrumRowHihatToMainToggle.grid(row=0, column=0, sticky="ew", padx=2)

            SaveConfig()

        DrumRowDrumToggle = tk.Checkbutton(MainDrumRowToggles, text="Pad?", variable=DrumRowDrumVar, command=lambda:SwitchDrumType("Pad"))
        DrumRowDrumToggle.grid(row=0, column=0, sticky="ew", padx=2)
        DrumRowCymbalToggle = tk.Checkbutton(MainDrumRowToggles, text="Cymbal?", variable=DrumRowCymbalVar, command=lambda: SwitchDrumType("Cymbal"))
        DrumRowCymbalToggle.grid(row=0, column=1, sticky="ew", padx=2)
        DrumRowKickToggle = tk.Checkbutton(MainDrumRowToggles, text="Kick?", variable=DrumRowKickVar, command=lambda: SwitchDrumType("Kick"))
        DrumRowKickToggle.grid(row=0, column=2, sticky="ew", padx=2)
        DrumRowHihatToggle = tk.Checkbutton(MainDrumRowToggles, text="Hihat?", variable=DrumRowHihatVar, command=lambda: SwitchDrumType("Hihat"))
        DrumRowHihatToggle.grid(row=0, column=3, sticky="ew", padx=2)
        RemoveDrumObjectFromListMainDrum = tk.Button(MainDrumRowToggles, text="Remove Drum", command=lambda:RemoveDrum(Drum))
        RemoveDrumObjectFromListMainDrum.grid(row=0, column=4, sticky="ew", padx=2)

        SaveConfig()
    
    AddDrumObjectToList = tk.Button(DrumRow, text="Add Drum", command=lambda:AddDrumToList())
    AddDrumObjectToList.grid(row=0, column=0, sticky="ew", padx=2)

    


    MidiRows.append(Row)

    if not Loading:
        SaveConfig()
    else:



        if Row['Drums']:
            HideToggleRowShowOtherRow("Drums")
            for drum in Row['DrumList']:
                AddDrumToList(drum, True)
        elif Row['Keyboard']:
            HideToggleRowShowOtherRow("Keyboard")
        elif Row['Controller']:
            HideToggleRowShowOtherRow("Controller")
        elif Row['Advanced']:
            HideToggleRowShowOtherRow("Advanced")
        

def RemoveMidiRow(Frame, Row):
    Frame.destroy()
    MidiRows.remove(Row)
    SaveConfig()

# ————————————————————————————————————————————————————————————
# NullGit
# ————————————————————————————————————————————————————————————
def BrowseForRepo():
    Path = filedialog.askdirectory()
    if not Path:
        return
    GitPath = os.path.join(Path, ".git")
    if os.path.isdir(GitPath):
        NullGitInputPath.set(Path)
    else:
        messagebox.showerror(
            "Invalid Repo",
            "Selected folder is not a Git repository."
        )

def CreateRepo():

    Path = NullGitCreateRepoPath.get().strip()

    if not Path:
        return

    try:

        # ------------------------------
        # Initialize Repo
        # ------------------------------

        subprocess.run(
            ["git", "init"],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        # ------------------------------
        # Check Existing Files
        # ------------------------------

        Files = [
            File
            for File in os.listdir(Path)
            if File != ".git"
        ]

        # ------------------------------
        # Empty Repo Fix
        # ------------------------------

        if not Files:

            ReadMePath = os.path.join(
                Path,
                "README.md"
            )

            with open(ReadMePath, "w") as File:

                File.write(
                    "Required file for Repo"
                )

        # ------------------------------
        # Initial Commit
        # ------------------------------

        subprocess.run(
            ["git", "add", "."],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "first"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        # ------------------------------
        # Remote Setup
        # ------------------------------

        Remote = NullGitCreateRepoLink.get().strip()

        if Remote.startswith("git remote add origin"):
            Remote = Remote.replace("git remote add origin","").strip()

        if Remote:

            subprocess.run(
                [
                    "git",
                    "remote",
                    "add",
                    "origin",
                    Remote
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

            subprocess.run(
                [
                    "git",
                    "push",
                    "-u",
                    "origin",
                    "main"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        # ------------------------------
        # Add To NullGit
        # ------------------------------
        messagebox.showinfo(
            "Repo Created",
            "Repository initialized successfully."
        )

        AddRepo(Path)


    except subprocess.CalledProcessError as e:

        messagebox.showerror(
        "Create Repo Failed",
        f"{e}\n\n{e.stderr}"
    )

    except Exception as e:

        messagebox.showerror(
            "Create Repo Failed",
            str(e)
        )

def SetCloneLocation():
    Path = filedialog.askdirectory()
    if not Path:
        return
    NullGitClonePath.set(Path)

def CloneRepo():
    Path = NullGitClonePath.get().strip()
    Link = NullGitCloneLink.get().strip()
    if not Path or not Link:
        return
    try:
        subprocess.run(
            [
                "git",
                "clone",
                Link
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        RepoName = os.path.basename(Link)
        if RepoName.endswith(".git"):
            RepoName = RepoName[:-4]
        RepoPath = os.path.join(
            Path,
            RepoName
        )
        AddRepo(RepoPath)
        messagebox.showinfo(
            "Clone Complete",
            f"Repository cloned successfully.\n\n{RepoPath}"
        )
    except subprocess.CalledProcessError as e:

        messagebox.showerror(
            "Clone Repo Failed",
            e.stderr
        )
    except Exception as e:
        messagebox.showerror(
            "Clone Repo Failed",
            str(e)
        )

def SetRepoCreationLocation():
    Path = filedialog.askdirectory()
    if not Path:
        return
    NullGitCreateRepoPath.set(Path)

def GetBranches(Path):
    try:
        Result = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        Branches = Result.stdout.strip().split("\n")
        return Branches
    except:
        return []
    
def GetCurrentBranch(Path):
    try:
        Result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        return Result.stdout.strip()

    except:
        return ""

def ChangeBranch(Repo, Branch, StatusVar):
    StatusVar.set("🔄 Checking...")
    try:
        subprocess.run(
            ["git", "checkout", Branch],
            cwd=Repo['Path'],
            check=True,
            capture_output=True,
            text=True
        )

        StatusVar.set(GetRepoStatus(Repo))
    except Exception as e:
        messagebox.showerror(
            "Branch Change Failed",
            str(e)
        )

def GetRepoStatus(Repo):
    Path = Repo["Path"]
    Selected = Repo.get(
        "CurrentBranch",
        ""
    )
    if "[Release]" in Selected:
        try:
            RepoName = GetGitHubRepo(Path)
            if not RepoName:
                return "⚪ No GitHub Repo"
            Result = subprocess.run(
                [
                    "curl",
                    "-s",
                    f"https://api.github.com/repos/{RepoName}/releases/latest"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            Data = json.loads(Result.stdout)
            LatestTag = Data.get(
                "tag_name",
                ""
            )
            InstalledTag = Repo.get(
                "InstalledReleaseTag",
                ""
            )
            if not InstalledTag:
                return "⚪ No Release Installed"

            if InstalledTag == LatestTag:
                return "🟢 Up To Date"

            return "🔴 Needs Updated"

        except:
            return "⚪ Release Unknown"

    try:
        subprocess.run(
            ["git", "fetch"],
            cwd=Path,
            capture_output=True,
            text=True
        )
        Result = subprocess.run(
            ["git", "status", "-sb"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        Status = Result.stdout.lower()
        if "behind" in Status:
            return "🔴 Needs Updated"
        if "ahead" in Status:
            return "🟡 Ahead"
        return "🟢 Up To Date"
    except:
        return "⚪ Unknown"

def ShowDownloadOverlay():
    DownloadOverlay.place(
        relx=0,
        rely=0,
        relwidth=1,
        relheight=1
    )

    DownloadOverlay.lift()

def HideDownloadOverlay():
    DownloadOverlay.place_forget()

def UpdateDownloadOverlay(percent=0, eta="--", file=""):
    DownloadOverlayLabel.config(
        text=(
            f"Downloading Release...\n\n"
            f"{file}\n\n"
            f"Progress: {percent:.1f}%\n"
            f"ETA: {eta}\n\n"
            "Please wait..."
        )
    )

def CancelDownload():
    global CurrentDownloadProcess
    if CurrentDownloadProcess:
        try:
            CurrentDownloadProcess.terminate()
        except:
            pass
    HideDownloadOverlay()

def PushGit(Repo, CommitMessage, Status):
    Path = Repo["Path"]
    Message = CommitMessage.get().strip()
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        if Message:
            subprocess.run(
                ["git", "commit", "-m", Message],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            subprocess.run(
                ["git", "commit", "-m", "Quick Commit"],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        PushCommand = ["git", "push"]

        subprocess.run(
            PushCommand,
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        Status.set(GetRepoStatus(Repo))
        CommitMessage.set("")

    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Push Failed",
            e.stderr
        )

    except Exception as e:
        messagebox.showerror(
            "Push Failed",
            str(e)
        )

def PullRepo(Repo, StatusVar):
    Selected = Repo.get(
        "CurrentBranch",
        ""
    )

    if "[Branch]" in Selected:
        Branch = Selected.replace(
            " [Branch]",
            ""
        )
        Path = Repo["Path"]
        StatusVar.set("🔄 Pulling...")
        try:
            subprocess.run(
                [
                    "git",
                    "pull",
                    "origin",
                    Branch
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
            StatusVar.set(
                GetRepoStatus(Repo)
            )
        except subprocess.CalledProcessError as e:
            StatusVar.set(
                "🔴 Pull Failed"
            )
            messagebox.showerror(
                "Pull Failed",
                e.stderr
            )
        except Exception as e:
            StatusVar.set(
                "🔴 Pull Failed"
            )
            messagebox.showerror(
                "Pull Failed",
                str(e)
            )
        return

    if "[Release]" in Selected:
        PullRelease(
            Repo,
            StatusVar
        )
        return
    StatusVar.set(
        "⚪ Unknown"
    )

def PushOnlyCommited():

    if not CurrentManagedRepo:
        return

    Path = CurrentManagedRepo["Path"]

    Message = OnlyCommitMessage.get().strip()

    try:
        if Message:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    Message
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        else:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "Quick Commit"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )

        subprocess.run(
            [
                "git",
                "push"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        CommittedVar.set(
            Result.stdout.strip()
        )

        OnlyCommitMessage.set("")

        messagebox.showinfo(
            "Push Complete",
            "Staged files committed and pushed."
        )
    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Push Failed",
            f"{e}\n\n{e.stderr}"
        )
    except Exception as e:
        messagebox.showerror(
            "Push Failed",
            str(e)
        )

def ForcePushCommit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    Message = OnlyCommitMessage.get().strip()
    Confirm = messagebox.askyesno(
        "Force Push",
        "Force push to remote?\n\nThis can overwrite remote history."
    )
    if not Confirm:
        return

    try:
        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        StagedFiles = Result.stdout.strip()
        if not StagedFiles:

            subprocess.run(
                [
                    "git",
                    "add",
                    "."
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        if Message:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    Message
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "I wasn't asking. I said COMMIT"
                ],
                cwd=Path,
                check=True,
                capture_output=True,
                text=True
            )
        subprocess.run(
            [
                "git",
                "push",
                "--force"
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )
        OnlyCommitMessage.set("")

        messagebox.showinfo(
            "Force Push Complete",
            "Repo force pushed successfully."
        )

    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Force Push Failed",
            f"{e}\n\n{e.stderr}"
        )
    except Exception as e:

        messagebox.showerror(
            "Force Push Failed",
            str(e)
        )

def OnNotebookChanged(event):
    CurrentTab = NullGitNotebook.select()
    if str(CurrentTab) == str(NullGitMainPage):
        NullGitNotebook.tab(
            NullGitManagePage,
            state="disabled"
        )
        global CurrentManagedRepo
        CurrentManagedRepo = None

def MergeBranch():
    
    global CurrentManagedRepo
    Path = CurrentManagedRepo["Path"]
    Branch = CurrentMergeBranch.get()
    if not Branch:
        return

    try:
        subprocess.run(
            ["git", "merge", Branch],
            cwd=Path,
            check=True
        )
        print(f"Successfully merged {Branch} with {CurrentManagedRepo['CurrentBranch']} ")
    except Exception as e:
        print(f"Merge failed: {e}")

def ManageRepo(Repo):
    global CurrentManagedRepo
    Path = Repo["Path"]

    CurrentManagedRepo = Repo

    ManageRepoPath.set(Path)
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        ManageRemoteURL.set(
            Result.stdout.strip()
        )
    except:
        ManageRemoteURL.set("")

    ManageBranchName.set(
        Repo.get("CurrentBranch", "")
    )
    GitIgnorePath = os.path.join(
        Path,
        ".gitignore"
    )
    if os.path.exists(GitIgnorePath):
        CreateGitIgnoreButton.grid_remove()
        EditGitIgnoreButton.grid()
        with open(GitIgnorePath, "r") as File:

            GitIgnoredVar.set(
                File.read()
            )

        GitList.grid()

    else:
        EditGitIgnoreButton.grid_remove()
        CreateGitIgnoreButton.grid()
        GitIgnoredVar.set("")
        GitList.grid_remove()

    try:
        Result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        Files = Result.stdout.strip()
        CommittedVar.set(Files)

    except:
        CommittedVar.set("")

    try:
        Result = subprocess.run(
            ["git", "branch"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )

        Branches = []

        for B in Result.stdout.splitlines():

            Clean = B.replace ("*", "").strip()
            if Clean != CurrentManagedRepo["CurrentBranch"].replace(" [Branch]", ""):
                Branches.append(Clean)

        MergeBranchBox["values"] = Branches

    except Exception as e:
        print(e)

    NullGitNotebook.tab(NullGitManagePage,state="normal")
    NullGitNotebook.select(NullGitManagePage)
    return

def DownloadReleaseThread(Repo, StatusVar, SelectedAssets, Tag, Path, OpenOnFinish):

    global CurrentDownloadProcess

    try:

        TotalAssets = len(SelectedAssets)

        CurrentAsset = 0

        for Asset in SelectedAssets:

            CurrentAsset += 1

            DownloadURL = Asset.get("browser_download_url", "")
            FileName = Asset.get("name", "UnknownFile")

            NameLower = FileName.lower()

            if "linux" in NameLower:
                Platform = "Linux"

            elif "windows" in NameLower:
                Platform = "Windows"

            elif "mac" in NameLower:
                Platform = "Mac"

            else:
                Platform = "Unknown"

            ReleasePath = os.path.join(Path, "Releases", Platform)

            os.makedirs(ReleasePath, exist_ok=True)

            DownloadPath = os.path.join(ReleasePath, FileName)

            Root.after(
                0,
                UpdateDownloadOverlay,
                0,
                "--",
                f"{FileName}\n({CurrentAsset}/{TotalAssets})"
            )

            StatusVar.set(f"🟣 Downloading...")

            CurrentDownloadProcess = subprocess.Popen(
                [
                    "wget",
                    "--progress=bar:force",
                    "-O",
                    DownloadPath,
                    DownloadURL
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )

            Percent = 0
            ETA = "--"

            for Line in CurrentDownloadProcess.stdout:

                Line = Line.strip()

                print(Line)

                PercentMatch = re.search(r"(\d+)\%", Line)

                ETAMatch = re.search(
                    r"ETA\s+([0-9hms:]+)",
                    Line,
                    re.IGNORECASE
                )

                if PercentMatch:
                    Percent = float(PercentMatch.group(1))

                if ETAMatch:
                    ETA = ETAMatch.group(1)

                Root.after(
                    0,
                    UpdateDownloadOverlay,
                    Percent,
                    ETA,
                    f"{FileName}\n({CurrentAsset}/{TotalAssets})"
                )

            CurrentDownloadProcess.wait()

            if CurrentDownloadProcess.returncode != 0:

                Root.after(
                    0,
                    HideDownloadOverlay
                )

                Root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Download Failed",
                        f"Failed downloading:\n{FileName}"
                    )
                )

                return

            if FileName.endswith(".zip"):

                subprocess.run(
                    ["unzip", "-o", DownloadPath, "-d", ReleasePath],
                    check=True
                )

                os.remove(DownloadPath)

            elif FileName.endswith(".7z"):

                subprocess.run(
                    ["7z", "x", "-y", DownloadPath, f"-o{ReleasePath}"],
                    check=True
                )

                os.remove(DownloadPath)

        Repo["InstalledReleaseTag"] = Tag

        SaveConfig()

        Root.after(
            0,
            HideDownloadOverlay
        )

        Root.after(
            0,
            lambda: StatusVar.set(
                "🟢 Up To Date"
            )
        )
        if OpenOnFinish:

            subprocess.Popen(
                ["xdg-open", ReleasePath]
            )

        Root.after(
            0,
            lambda: messagebox.showinfo(
                "Download Complete",
                f"Release Installed:\n{Tag}"
            )
        )

    except Exception as e:

        Root.after(
            0,
            HideDownloadOverlay
        )

        Root.after(
            0,
            lambda: StatusVar.set(
                "🔴 Failed"
            )
        )

        Root.after(
            0,
            lambda: messagebox.showerror(
                "Release Pull Failed",
                str(e)
            )
        )
    finally:
        CurrentDownloadProcess = None

def PullRelease(Repo, StatusVar):

    Path = Repo["Path"]

    RepoName = GetGitHubRepo(Path)

    if not RepoName:
        StatusVar.set("🔴 No Repo")
        return

    StatusVar.set("🟣 Checking...")

    try:

        Result = subprocess.run(["curl", "-s", f"https://api.github.com/repos/{RepoName}/releases/latest"], capture_output=True, text=True, check=True)

        Data = json.loads(Result.stdout)

        Assets = Data.get("assets", [])

        if not Assets:
            StatusVar.set("🔴 No Assets")
            messagebox.showerror("No Assets Found", "Latest release contains no downloadable assets.")
            return

        # ==================================================
        # Asset Selection Popup
        # ==================================================

        Popup = tk.Toplevel(Root)

        Popup.title("Select Release Assets")
        Popup.geometry("500x450")
        Popup.transient(Root)
        Popup.grab_set()

        tk.Label(Popup, text="Select Release Assets").pack(pady=5)

        Scroll = ScrollableFrame(Popup)

        Scroll.pack(fill="both", expand=True, padx=10, pady=10)

        AssetVars = []

        for Asset in Assets:

            Name = Asset.get("name", "Unknown")
            Size = round(Asset.get("size", 0) / 1024 / 1024, 2)

            Var = tk.BooleanVar()

            tk.Checkbutton(Scroll.Inner, text=f"{Name} ({Size} MB)", variable=Var).pack(anchor="w", padx=5, pady=2)

            AssetVars.append({
                "Var": Var,
                "Asset": Asset
            })

        OpenOnFinish = tk.BooleanVar(value=False)

        tk.Checkbutton(Popup, text="Open Folder After Download", variable=OpenOnFinish).pack(pady=5)

        SelectedAssets = []

        def DownloadSelected():

            for Item in AssetVars:

                if Item["Var"].get():
                    SelectedAssets.append(Item["Asset"])

            Popup.destroy()

        tk.Button(Popup, text="Download Selected", command=DownloadSelected).pack(pady=5)

        Popup.wait_window()

        # ==================================================
        # Cancelled
        # ==================================================

        if not SelectedAssets:
            StatusVar.set("⚪ Cancelled")
            return

        Tag = Data.get("tag_name", "UnknownRelease")

        # ==================================================
        # Start Download Thread
        # ==================================================

        ShowDownloadOverlay()

        UpdateDownloadOverlay(
            0,
            "--",
            "Preparing Download..."
        )

        threading.Thread(
            target=DownloadReleaseThread,
            args=(
                Repo,
                StatusVar,
                SelectedAssets,
                Tag,
                Path,
                OpenOnFinish.get()
            ),
            daemon=True
        ).start()

    except Exception as e:

        StatusVar.set("🔴 Failed")

        messagebox.showerror(
            "Release Pull Failed",
            str(e)
        )

def GetGitHubRepo(Path):
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        URL = Result.stdout.strip()
        URL = URL.replace("git@github.com:", "")
        URL = URL.replace("https://github.com/", "")
        URL = URL.replace(".git", "")
        return URL

    except:
        return None

#This is probably what you're looking for vex.
#lmfao it was.
def AddRepoObject(Repo):
    global RepoBoxes
    Frame = tk.LabelFrame(NullGitcontainer, text=Repo["Name"], bd=2, relief="solid")
    Frame.pack(fill="x", padx=5, pady=5)
    Frame.columnconfigure(0, weight=0)
    Frame.columnconfigure(1, weight=2)
    Frame.columnconfigure(2, weight=0)
    for i in range(9):
        Frame.rowconfigure(i, weight=0)

    StatusVar = tk.StringVar()
    Branches = GetBranches(Repo["Path"])
    RepoOptions = []

    for Branch in Branches:
        RepoOptions.append({"Label": f"{Branch} [Branch]", "Type": "Branch", "Value": Branch})

    try:
        RepoName = GetGitHubRepo(Repo["Path"])
        if RepoName:
            Result = subprocess.run(["curl", "-s", f"https://api.github.com/repos/{RepoName}/releases/latest"], capture_output=True, text=True, check=True)
            Data = json.loads(Result.stdout)
            if (Data.get("tag_name") and isinstance(Data.get("assets"), list)and len(Data.get("assets")) > 0):
                RepoOptions.append({"Label": "Latest [Release]", "Type": "Release", "Value": "latest"})
    except:
        pass
    DisplayValues = [x["Label"] for x in RepoOptions]
    SavedBranch = Repo.get("CurrentBranch", f"{GetCurrentBranch(Repo['Path'])} [Branch]")
    CurrentBranch = tk.StringVar(value=SavedBranch)
    Repo["CurrentBranch"] = SavedBranch
    def OnRepoOptionChanged():
        Selected = CurrentBranch.get()
        Match = next((x for x in RepoOptions if x["Label"] == Selected), None)
        if not Match:
            return
        Repo["CurrentBranch"] = Match["Label"]
        if Match["Type"] == "Branch":
            ChangeBranch(Repo, Match["Value"], StatusVar)
        StatusVar.set(GetRepoStatus(Repo))
        SaveConfig()
        Frame.focus_set()

    BranchBox = ttk.Combobox(Frame, values=DisplayValues, textvariable=CurrentBranch, state="readonly")
    BranchBox.grid(row=0, column=1, sticky="ew")
    BranchBox.bind("<<ComboboxSelected>>", lambda e: OnRepoOptionChanged())
    tk.Button(Frame, text="Pull Repo", width=10, command=lambda: PullRepo(Repo, StatusVar)).grid(row=0, column=2, columnspan=3)
    ttk.Separator(Frame, orient="horizontal").grid(row=1, column=0, sticky="ew", columnspan=3, pady=6)
    StatusVar.set(GetRepoStatus(Repo))
    StatusLabel = tk.Label(Frame, textvariable=StatusVar, width=15, padx=5)
    StatusLabel.grid(row=0, column=0, sticky="ew")
    InnerFrame = tk.Frame(Frame)
    InnerFrame.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
    InnerFrame.columnconfigure(0, weight=1)
    InnerFrame.columnconfigure(1, weight=1)
    tk.Button(InnerFrame, text="Open Repo In Browser", command=lambda: OpenRepo(Repo, False)).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
    tk.Button(InnerFrame, text="Open Repo Location", command=lambda: OpenRepo(Repo, True)).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    ttk.Separator(Frame, orient="horizontal").grid(row=5, column=0, sticky="ew", columnspan=3, pady=6)
    if Repo["Owner"]:
        tk.Button(Frame, text="Manage Repo", command=lambda: ManageRepo(Repo)).grid(row=6, column=0, columnspan=3, sticky="ew", padx=5)
        #don't know why you'd need this for a repo you're not the owner of... lmfao. I was tired.
        CommitMessage = tk.StringVar()
        CommitMessageShow = tk.Label(Frame, text="Commit Message:", width=15, padx=5)
        CommitMessageShow.grid(row=2, column=0, sticky="ew")
        CommitEntry = tk.Entry(Frame, width=30, textvariable=CommitMessage)
        CommitEntry.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Separator(Frame, orient="horizontal").grid(row=3, column=0, sticky="ew", columnspan=3, pady=6)
        tk.Button(Frame, text="Push Repo", width=10, command=lambda: PushGit(Repo, CommitMessage, StatusVar)).grid(row=2, column=2, padx=5)
    else:
        tk.Button(Frame, text="Delete Repo From NullGit", command=lambda: DeleteRepoInNull(Repo)).grid(row=6, column=0, sticky="ew", padx=5, pady=2, columnspan=3)

    RepoBoxes.append(Frame)
    
def BuildRepoList():
    global RepoBoxes

    for Box in RepoBoxes:
        Box.destroy()

    RepoBoxes.clear()

    for repo in Repos.values():
        AddRepoObject(repo)
        
    return

def GetLoggedInGitHubUser():
    try:
        Result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True
        )
        return Result.stdout.strip().lower()
    except:
        return None

def GetRepoOwner(Path):
    try:
        Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path,
            capture_output=True,
            text=True,
            check=True
        )
        URL = Result.stdout.strip().lower()
        URL = URL.replace("git@github.com:", "")
        URL = URL.replace("https://github.com/", "")
        URL = URL.replace(".git", "")
        Owner = URL.split("/")[0]
        return Owner
    except:
        return None

def IsOwner(Path):
    User = GetLoggedInGitHubUser()
    if not User:
        return False
    Owner = GetRepoOwner(Path)
    if not Owner:
        return False
    return User == Owner

def AddRepo(Path):

    Name = os.path.basename(Path)

    if Path in Repos:
        return
    
    Repos[Path] = {
        "Name": Name,
        "Path": Path,
        "Owner": IsOwner(Path),
    }

    SaveConfig()
    BuildRepoList()

def OpenRepo(Repo, LocalOrNet=True):
    try:
        if LocalOrNet:
            subprocess.Popen(
                ["xdg-open", Repo["Path"]]
            )
        else:
            Result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Repo["Path"],
            capture_output=True,
            text=True,
            check=True
        )
            URL = Result.stdout.strip()

            if URL.startswith("git@github.com:"):
                URL = URL.replace(
                    "git@github.com:",
                    "https://github.com/"
                )
            if URL.endswith(".git"):
                URL = URL[:-4]
            subprocess.Popen(
                ["xdg-open", URL]
            )
    except Exception as e:
        messagebox.showerror(
            "Open Repo Failed",
            str(e)
        )


def DeleteRepoInNull(Repo):
    
    Path = Repo["Path"]

    Confirm = messagebox.askyesno(
        "Remove Repo",
        "Remove this repo from NullGit?"
    )
    if not Confirm:
        return
    Repos.pop(Path, None)
    SaveConfig()
    BuildRepoList()
    NullGitNotebook.select(NullGitMainPage)

def CreateBranchOnGit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    Branch = ManageBranchName.get().strip()
    if not Branch:
        return
    try:
        subprocess.run(
            ["git", "checkout", "-b", Branch],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        messagebox.showinfo(
            "Branch Created",
            f"Created branch:\n{Branch}"
        )

        subprocess.run(
        ["git", "push", "--set-upstream", "origin", Branch],
        cwd=Path,
        check=True,
        capture_output=True,
        text=True
        )
        SaveConfig()
        BuildRepoList()
    except Exception as e:
        messagebox.showerror(
            "Create Branch Failed",
            str(e)
        )

def RenameBranchOnGit():
    if not CurrentManagedRepo:
        return
    Path = CurrentManagedRepo["Path"]
    OldBranch = CurrentManagedRepo["CurrentBranch"].replace(" [Branch]","")
    NewBranch = ManageBranchName.get().strip()
    if not NewBranch:
        return
    try:
        subprocess.run(
            [
                "git",
                "branch",
                "-m",
                OldBranch,
                NewBranch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        CurrentManagedRepo["CurrentBranch"] = f"{NewBranch} [Branch]"
        SaveConfig()
        BuildRepoList()
        messagebox.showinfo(
            "Branch Renamed",
            f"{OldBranch} → {NewBranch}"
        )
    except Exception as e:
        messagebox.showerror(
            "Rename Branch Failed",
            str(e)
        )

def DeleteBranchOnGit():

    if not CurrentManagedRepo:
        return

    Path = CurrentManagedRepo["Path"]

    Branch = CurrentManagedRepo["CurrentBranch"].replace(" [Branch]","")

    Branches = GetBranches(Path)

    if len(Branches) <= 1:

        messagebox.showerror(
            "Delete Branch Failed",
            "You cannot delete the only branch."
        )

        return

    Confirm = messagebox.askyesno(
        "Delete Branch",
        f"Delete branch:\n{Branch}?"
    )

    if not Confirm:
        return

    try:
        OtherBranch = next(
            B for B in Branches
            if B != Branch
        )
        subprocess.run(
            [
                "git",
                "checkout",
                OtherBranch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "git",
                "branch",
                "-D",
                Branch
            ],
            cwd=Path,
            check=True,
            capture_output=True,
            text=True
        )
        SaveConfig()
        BuildRepoList()
        NullGitNotebook.select(
            NullGitMainPage
        )
        messagebox.showinfo(
            "Branch Deleted",
            f"Deleted branch:\n{Branch}"
        )
    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Delete Branch Failed",
            f"{e}\n\n{e.stderr}"
        )
    except Exception as e:
        messagebox.showerror(
            "Delete Branch Failed",
            str(e)
        )

def CreateGitIgnoreFile():
    if not CurrentManagedRepo:
        print("no current manage repo")
        return
    Path = CurrentManagedRepo["Path"]
    GitIgnorePath = os.path.join(
        Path,
        ".gitignore"
    )
    try:
        open(GitIgnorePath, "w").close()
        CreateGitIgnoreButton.grid_remove()
        EditGitIgnoreButton.grid()
        GitList.grid()
        GitIgnoredVar.set("")

    except Exception as e:
        messagebox.showerror(
            "Create .gitignore Failed",
            str(e)
        )

def EditGitIgnoreFile():

    Popup = tk.Toplevel(Root)
    Popup.title("Edit .gitignore")
    Popup.resizable(False, False)

    Popup.transient(Root)
    Popup.grab_set()

    Frame = tk.Frame(Popup)
    Frame.pack(padx=10, pady=10)

    tk.Label(
        Frame,
        text="What do you want to ignore?"
    ).pack(fill="x", pady=(0, 10))

    tk.Button(
        Frame,
        text="Select File",
        command=lambda: SelectGitIgnore(
            "file",
            Popup
        )
    ).pack(fill="x", pady=3)

    tk.Button(
        Frame,
        text="Select Folder",
        command=lambda: SelectGitIgnore(
            "folder",
            Popup
        )
    ).pack(fill="x", pady=3)

def SelectGitIgnore(Type, Popup):

    Popup.destroy()

    if not CurrentManagedRepo:
        return

    RepoPath = CurrentManagedRepo["Path"]

    if Type == "file":

        SelectedPath = filedialog.askopenfilename(
            initialdir=RepoPath
        )

    else:

        SelectedPath = filedialog.askdirectory(
            initialdir=RepoPath
        )

    if not SelectedPath:
        return

    try:

        GitIgnorePath = os.path.join(
            RepoPath,
            ".gitignore"
        )

        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )

        RelativePath = "/" + RelativePath.replace("\\", "/")

        if os.path.isdir(SelectedPath):
            RelativePath += "/"

        Lines = []

        if os.path.exists(GitIgnorePath):

            with open(GitIgnorePath, "r") as File:

                Lines = [
                    Line.strip()
                    for Line in File.readlines()
                    if Line.strip()
                ]

        if RelativePath in Lines:

            # ------------------------------
            # Remove ignore
            # ------------------------------
            Lines.remove(RelativePath)

            subprocess.run(
                [
                    "git",
                    "add",
                    RelativePath.strip("/")
                ],
                cwd=RepoPath,
                capture_output=True,
                text=True
            )

        else:

            # ------------------------------
            # Add ignore
            # ------------------------------
            Lines.append(RelativePath)

            subprocess.run(
                [
                    "git",
                    "rm",
                    "--cached",
                    "-r",
                    RelativePath.strip("/")
                ],
                cwd=RepoPath,
                capture_output=True,
                text=True
            )

        Lines = sorted(set(Lines))

        with open(GitIgnorePath, "w") as File:

            File.write(
                "\n".join(Lines)
            )

        GitIgnoredVar.set(
            "\n".join(Lines)
        )

        if Lines:
            GitList.grid()
        else:
            GitList.grid_remove()

    except Exception as e:

        messagebox.showerror(
            "Edit .gitignore Failed",
            str(e)
        )

def AddFileToCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    SelectedPath = filedialog.askopenfilename(
        initialdir=RepoPath
    )
    if not SelectedPath:
        return
    try:
        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )
        RelativePath = RelativePath.replace(
            "\\",
            "/"
        )
        subprocess.run(
            [
                "git",
                "add",
                RelativePath
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )

    except Exception as e:
        messagebox.showerror(
            "Add File Failed",
            str(e)
        )

def RemoveFileFromCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    SelectedPath = filedialog.askopenfilename(
        initialdir=RepoPath
    )
    if not SelectedPath:
        return

    try:
        RelativePath = os.path.relpath(
            SelectedPath,
            RepoPath
        )
        RelativePath = RelativePath.replace(
            "\\",
            "/"
        )
        subprocess.run(
            [
                "git",
                "reset",
                "HEAD",
                RelativePath
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )

        Result = subprocess.run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set(
            Result.stdout.strip()
        )
    except Exception as e:
        messagebox.showerror(
            "Remove File Failed",
            str(e)
        )

def ClearCurrentCommit():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    Confirm = messagebox.askyesno(
        "Clear Commit",
        "Remove all files from the current staged commit?"
    )
    if not Confirm:
        return
    try:
        subprocess.run(
            [
                "git",
                "reset",
                "HEAD"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        CommittedVar.set("")
        messagebox.showinfo(
            "Commit Cleared",
            "All staged files removed."
        )
    except Exception as e:
        messagebox.showerror(
            "Clear Commit Failed",
            str(e)
        )

def StashAndPull():
    if not CurrentManagedRepo:
        return
    RepoPath = CurrentManagedRepo["Path"]
    Confirm = messagebox.askyesno(
        "Stash all local changes and pull latest from remote?\n\nThis will overwrite your current workflow state."
    )
    if not Confirm:
        return

    try:
        subprocess.run(
            [
                "git",
                "stash"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        subprocess.run(
            [
                "git",
                "pull"
            ],
            cwd=RepoPath,
            capture_output=True,
            text=True,
            check=True
        )
        messagebox.showinfo(
            "Repo Updated",
            "Local changes stashed.\nLatest repo pulled."
        )

        BuildRepoList()
        SaveConfig()

    except Exception as e:
        messagebox.showerror(
            "Stash And Pull Failed",
            str(e)
        )

# ==========================================================================================
# UI
# ==========================================================================================

# ————————————————————————————————————————————————————————————
# Setup UI
# ————————————————————————————————————————————————————————————
Notebook = ttk.Notebook(Main)
Notebook.pack(fill="both", expand=True)
NullSuite = tk.Frame(Notebook)
NullWire = tk.Frame(Notebook)
NullCursor = tk.Frame(Notebook)
NullMidi = tk.Frame(Notebook)
NullProton = tk.Frame(Notebook)
NullRip = tk.Frame(Notebook)
NullGit = tk.Frame(Notebook)
#Leave a gap incase i add more
Notebook.add(NullSuite, text="NullSuite")
Notebook.add(NullWire, text="NullWire")
Notebook.add(NullCursor, text="NullCursor")
#Notebook.add(NullMidi, text = "NullMidi")
Notebook.add(NullProton, text = "NullProton")
Notebook.add(NullRip, text = "NullRip")
Notebook.add(NullGit, text = "NullGit")
#Leave a gap incase i add more

# ------------------------------
# Null Suite UI
# ------------------------------
NullSuiteFrame = tk.Frame(NullSuite)
NullSuiteFrame.pack(side="bottom", fill="x")
AboutNullWire = tk.Label(
    NullSuiteFrame,
    text="Hey there demons, it's me ya boi.\nIDK what to even put here tbh.\n I like to make things. I have problems, and I code my way out of them. \n Enjoy the efforts of my labor 👍 \n IF you want to support more programs or just donate...theres our ko-fi. "
)
AboutNullWire.pack(fill="x")

link = tk.Label(
    NullSuiteFrame,
    text="Our Ko-fi",
    fg="blue",
    cursor="hand2"
)
link.pack()

link.bind("<Button-1>", lambda e: webbrowser.open_new("https://ko-fi.com/nullforgestudios"))

ttk.Separator(NullSuiteFrame, orient="horizontal").pack(fill="both", pady=5)
tk.Label(NullSuiteFrame, textvariable=StartUpTimeString).pack(fill="both", pady=5)

# ------------------------------
# Null Proton UI
# ------------------------------
ProtonMain = tk.Frame(NullProton)
ProtonMain.pack(fill="both", expand=True, padx=10, pady=10)
ProtonTop = tk.Frame(ProtonMain)
ProtonTop.pack(fill="x")
ProtonTop.rowconfigure(0, weight=1)
ProtonTop.rowconfigure(1, weight=1)
ProtonTop.rowconfigure(2, weight=1)
ProtonTop.columnconfigure(0, weight=0)
ProtonTop.columnconfigure(1, weight=2)
ProtonTop.columnconfigure(2, weight=1)

def MakeProtonRow(row, key, label):
    tk.Label(ProtonTop, text=label, anchor="w").grid(row=row, column=0, padx=3, pady=5, sticky="w")

    entry = tk.Entry(ProtonTop, textvariable=ProtonVars[key], state="readonly")
    entry.grid(row=row, column=1, padx=3, pady=5, sticky="ew")

    def Pick():
        Home = os.path.expanduser("~")

        Paths = [
            os.path.join(Home, ".steam/root/compatibilitytools.d"),
            os.path.join(Home, ".local/share/Steam/compatibilitytools.d")
        ]

        StartDir = next((p for p in Paths if os.path.isdir(p)), Home)

        path = filedialog.askopenfilename(
        title=f"Select Proton ({label})",
        initialdir=StartDir,
        filetypes=[("Proton Executable", "proton*"),("All Files", "*")])

        if path:
            ProtonVars[key].set(path)
            SaveConfig()

    tk.Button(ProtonTop, text="Browse", command=Pick).grid(row=row, column=2, sticky="ew")

MakeProtonRow(0, "Default", "Default Proton:")
MakeProtonRow(1, "A", "Proton A:")
MakeProtonRow(2, "B", "Proton B:")
ProtonScroll = ScrollableFrame(ProtonMain)
ProtonScroll.pack(fill="both", expand=True)
ProtonGameContainer = ProtonScroll.Inner
ProtonGameContainer.columnconfigure(0, weight=1)
AddGameBar = tk.Frame(ProtonTop)
AddGameBar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5, 10))
AddGameBar.columnconfigure(0, weight=1)
tk.Button(AddGameBar, text="Add Game", command=AddGameRow)\
    .grid(row=0, column=0, sticky="ew")
ProtonOverlay = tk.Frame(ProtonScroll, bg="#000000")
ProtonOverlay.place(relx=0, rely=0, relwidth=1, relheight=1)
ProtonOverlay.lower()
OverlayLabel = tk.Label(
    ProtonOverlay,
    text="",
    fg="white",
    bg="#000000",
    justify="left",
    anchor="nw"
)
OverlayLabel.pack(fill="both", expand=True, padx=10, pady=10)

# ------------------------------
# Null Midi UI
# ------------------------------
TopBar = tk.Frame(NullMidi)
TopBar.pack(fill="x", padx=5, pady=5)
MidiScrollBox = ScrollableFrame(NullMidi)
MidiScrollBox.pack(fill="both", expand=True)
MidiContainer = MidiScrollBox.Inner
tk.Button(TopBar, text="Add New Input", command=lambda: AddMidiRow(None)).pack(fill="x")
ttk.Separator(NullMidi, orient="horizontal").pack(fill="both", pady=5)
# ------------------------------
# Null Rip UI
# ------------------------------
NullRiptop = tk.Frame(NullRip)
NullRiptop.pack(fill="x", padx=10, pady=(10, 0))
NullRiptop.columnconfigure(0,weight=0)
NullRiptop.columnconfigure(1,weight=1)
NullRiptop.columnconfigure(2,weight=0)
NullRiptop.rowconfigure(0, weight=1)
NullRiptop.rowconfigure(1, weight=1)
NullRiptop.rowconfigure(2, weight=1)
NullRipScan = tk.Frame(NullRip)
NullRipScan.pack(fill="x", padx=10)
NullRipScan.columnconfigure(0,weight=1)
NullRipScan.rowconfigure(0, weight=1)
NullRipInputPath = tk.StringVar()
NullRipOutputPath = tk.StringVar()
NullRipOutputPath.set(GetVideosDir())
NullRipFileName = tk.StringVar()
NullRipOpenFolder = tk.BooleanVar()
tk.Label(NullRiptop, text="Input:").grid(row=0, column=0, sticky="ew")
tk.Button(NullRiptop, text="Browse", width =8,command=BrowseInput).grid(row=0, column=2, sticky="e")
tk.Entry(NullRiptop,width=30,textvariable=NullRipInputPath,state="readonly",readonlybackground="#e7e7e7").grid(row=0, column=1, sticky="ew")
tk.Label(NullRiptop, text="Output:").grid(row=1, column=0, sticky="ew")
tk.Entry(NullRiptop, width=30, textvariable=NullRipOutputPath, state="readonly", readonlybackground="#e7e7e7").grid(row=1, column=1, sticky="ew")
tk.Button(NullRiptop, text="Browse", width =8,command=BrowseOutput).grid(row=1, column=2, sticky="e")
tk.Label(NullRiptop, text="Name It:").grid(row=2, column=0, sticky="ew")
tk.Entry(NullRiptop, width=30, textvariable=NullRipFileName,).grid(row=2, column=1, sticky="ew")
tk.Button(NullRipScan,text="Scan",command=lambda: StartScan()).grid(row=3, column=0, pady=5, sticky="ew")
divider = tk.Frame(NullRip, height=2, bg="gray")
divider.pack(fill="x", padx=10, pady=5)
NullRipbottom = tk.Frame(NullRip)
NullRipbottom.pack(fill="both", expand=True)
NullRipbottom.rowconfigure(0,weight=0)
NullRipbottom.rowconfigure(1,weight=1)
NullRipbottom.columnconfigure(0,weight=1)
NullRipbottom.columnconfigure(1,weight=1)
NullRipbottom.columnconfigure(2,weight=1)
NullRipTitlesLabel = tk.Label(NullRipbottom, text="Titles")
NullRipTitlesLabel.grid(row=0, column=0, sticky="ew", padx=(10,5), pady=0)
NullRipTitlesBoxContainer = tk.Frame(NullRipbottom, bd=2, relief="solid")
NullRipTitlesBoxContainer.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=(5,10))
NullRipTitlesBox = ScrollableFrame(NullRipTitlesBoxContainer)
NullRipTitlesBox.pack(fill="both", expand=True)
NullRipChaptersLabel = tk.Label(NullRipbottom, text="Chapters")
NullRipChaptersLabel.grid(row=0, column=1, sticky="ew", padx=(10,5), pady=0)
NullRipChaptersBoxContainer = tk.Frame(NullRipbottom, bd=2, relief="solid")
NullRipChaptersBoxContainer.grid(row=1, column=1, sticky="nsew", padx=(10,5), pady=(5,10))
NullRipChaptersBox = ScrollableFrame(NullRipChaptersBoxContainer)
NullRipChaptersBox.pack(fill="both", expand=True)
NullRipOptionsText = tk.Label(NullRipbottom, text="Options")
NullRipOptionsText.grid(row=0, column=2, sticky="ew", padx=(10,5), pady=0)
NullRipOptionsBox = tk.Frame(NullRipbottom, bd=2, relief="solid")
NullRipOptionsBox.grid(row=1, column=2, sticky="nsew", padx=(5,10), pady=(5,10))
NullRipOptionsBox.rowconfigure(0, weight=1)
NullRipOptionsBox.rowconfigure(1, weight=0)
NullRipOptionsBox.columnconfigure(0, weight=1)
NullRipOptionsBoxGrid = tk.Frame(NullRipOptionsBox)
NullRipOptionsBoxGrid.grid(row=0, column=0, sticky="nsew")
NullRipOptionsBoxGrid.rowconfigure(0, weight=1)
NullRipOptionsBoxGrid.rowconfigure(1, weight=0)
NullRipOptionsBoxGrid.rowconfigure(2, weight=0)
NullRipOptionsBoxGrid.rowconfigure(3, weight=0)
NullRipOptionsBoxGrid.columnconfigure(0, weight=1)
NullRipOptionsBoxGrid.columnconfigure(1, weight=0)
NullRipOptionsBoxSplit = ScrollableFrame(NullRipOptionsBoxGrid)
NullRipOptionsBoxSplit.grid(row=0, column=0, sticky="nsew", padx=(5,5), pady=(5,10))
NullRipOpenAfterRip = tk.Checkbutton(NullRipOptionsBoxGrid, text="Open Output After Rip?", variable=NullRipOpenFolder)
NullRipOpenAfterRip.grid(row=1, column=0, sticky="swe", padx=(5,5))
NullRipToggleAllChapters = tk.Button(NullRipOptionsBoxGrid, text="Toggle All Chapters")
NullRipToggleAllChapters.grid(row=2, column=0, sticky="swe", padx=(5,5))
NullRipToggleAllChapters.config(command=ToggleChapters)
NullRipStartButton = tk.Button(NullRipOptionsBoxGrid, text="Start")
NullRipStartButton.grid(row=3, column=0, sticky="swe", padx=(5,5), pady=(0,5))
NullRipStartButton.config(state="disabled")
NullRipStartButton.config(command=StartRip)
NullRipprogress = ttk.Progressbar(NullRipScan, mode="indeterminate")
NullRipprogress.grid(row=4, column=0, sticky="ew", pady=5)
NullRipprogress.grid_remove()
NullRipOverlay = tk.Frame(NullRip, bg="#000000")
NullRipOverlayContent = tk.Frame(
    NullRipOverlay,
    bg="#000000"
)
NullRipOverlayContent.place(
    relx=0.5,
    rely=0.5,
    anchor="center"
)
NullRipOverlayLabel = tk.Label(
    NullRipOverlayContent,
    text="",
    fg="white",
    bg="#000000",
    justify="center",
    anchor="center",
    font=("Arial", 12)
)
NullRipOverlayLabel.pack(padx=20, pady=(20,10))
NullRipCancelButton = tk.Button(
    NullRipOverlayContent,
    text="Cancel Rip",
    command=CancelRip
)
NullRipCancelButton.pack(pady=(0,20))
NullRipOverlay.lower()
# ------------------------------
# Null Cursor UI
# ------------------------------
NullCursorNotebook = ttk.Notebook(NullCursor)
NullCursorNotebook.pack(fill="both", expand=True)
NullCursorPage = tk.Frame(NullCursorNotebook)
NullCursorHowToPage = tk.Frame(NullCursorNotebook)
NullCursorNotebook.add(NullCursorPage, text="Main")
NullCursorNotebook.add(NullCursorHowToPage, text="HowTo")
# --------------- NullCursor Main Page
NullCursorCheck = tk.Frame(NullCursorPage)
NullCursorCheck.pack(fill="x", padx=5, pady=5)
NullCursorTopBar = tk.Frame(NullCursorPage)
NullCursorTopBar.pack(fill="x", padx=5, pady=5)
NullCursorTopBar.columnconfigure(0, weight=2)
NullCursorTopBar.columnconfigure(1, weight=1)
NullCursorTopBar.rowconfigure(0, weight=0)
NullCursorTopBar.rowconfigure(1, weight=0)
NullCursorProfileBox = tk.Frame(NullCursorPage)
NullCursorProfileBox.pack(fill="x", padx=5, pady=5)
NullCursorProfileBox.columnconfigure(0, weight=2)
NullCursorProfileBox.columnconfigure(1, weight=1)
NullCursorProfileBox.rowconfigure(0, weight=0)
NullCursorProfileNameVar = tk.StringVar()
NullCursorProfileEntry = tk.Entry(NullCursorProfileBox, textvariable=NullCursorProfileNameVar)
NullCursorProfileEntry.grid(row=0, column=0, sticky="ew", padx=(0,5))
NullCursorCreateBtn = tk.Button(NullCursorProfileBox, text="Create Profile", command=CreateProfile)
NullCursorCreateBtn.grid(row=0, column=1, sticky="ew")
NullCursorEditables = tk.Frame(NullCursorTopBar)
NullCursorEditables.grid(row=1, column=0, sticky="ew", padx=(0,5))
NullCursorStartDetectionVar = tk.IntVar(value=int(StartDetection * 1000))
NullCursorRow = tk.Frame(NullCursorEditables)
NullCursorRow.pack(fill="x", pady=2)
NullCursordetectionlabel = tk.Label(NullCursorRow, text="Detection:", width=11)
NullCursordetectionlabel.grid(row=0, column=0, padx=(0,0), sticky="w")
NullCursorStartValueLabel = tk.Label(NullCursorRow, text=f"{int(StartDetection * 1000)}   |", width=6)
NullCursorStartValueLabel.grid(row=0, column=2, padx=(0,0))
NullCursorScanValueLabel = tk.Label(NullCursorRow, text=f"{ScanTime:.2f}", width=4)
NullCursorScanValueLabel.grid(row=0, column=7, padx=(0,0))
NullCursorSlider1 = tk.Scale(
    NullCursorRow,
    from_=1,
    to=50,
    resolution=1,
    orient="horizontal",
    variable=NullCursorStartDetectionVar,
    command=lambda v: UpdateStartDetection(v),
    showvalue=0
)
NullCursorSlider1.grid(row=0, column=1, sticky="ew", padx=(0,0))
ToolTip(NullCursordetectionlabel, "When your mouse enters this area, edge detection begins, Lower values may help performance, but detection might suffer. Recommended is 15")
NullCursorSlider1.bind("<Enter>", lambda e: OnHoverEnter(e, "detection"))
NullCursorSlider1.bind("<Leave>", lambda e: DelayedHide())
NullCursoredge = tk.Label(NullCursorRow, text="Buffer:", width= 7)
NullCursoredge.grid(row=0, column=3, padx=(0,0), sticky="w")
NullCursorEdgeBufferVar = tk.IntVar(value=EdgeBuffer)
NullCursorEntry = tk.Entry(NullCursorRow, textvariable=NullCursorEdgeBufferVar, width=5)
NullCursorEntry.grid(row=0, column=4, padx=(0,0))
NullCursorEntry.bind("<Enter>", lambda e: OnHoverEnter(e, "edge"))
NullCursorEntry.bind("<Leave>", lambda e: DelayedHide())
NullCursorEdgeBufferVar.trace_add("write", UpdateEdgeBuffer)
ToolTip(NullCursoredge, "How many pixels past the edge triggers a warp")
NullCursorScan = tk.Label(NullCursorRow, text="|   ScanTime", width=12)
NullCursorScan.grid(row=0, column=5, padx=(0,0), sticky="w")
NullCursorScanTimeVar = tk.DoubleVar(value=ScanTime)
NullCursorSlider2 = tk.Scale(
    NullCursorRow,
    from_=0.010,
    to=0.20,
    resolution=0.005,
    orient="horizontal",
    variable=NullCursorScanTimeVar,
    command=lambda v: UpdateScanTime(v),
    showvalue=0
)
NullCursorSlider2.grid(row=0, column=6, sticky="ew")
NullCursorSlider2.bind("<Button-4>", lambda e: (NullCursorSlider2.set(min(150, NullCursorSlider2.get()+0.005)), UpdateScanTime()))
NullCursorSlider2.bind("<Button-5>", lambda e: (NullCursorSlider2.set(max(0, NullCursorSlider2.get()-0.005)), UpdateScanTime()))
ToolTip(NullCursorScan, "How often the cursor is scanned (higher = less CPU, more delay). Recommended is 0.05 or lower.")
NullCursorScroll = ScrollableFrame(NullCursorPage)
NullCursorScroll.pack(fill="both", expand=True, padx=5, pady=5)
NullCursorProfileContainer = NullCursorScroll.Inner
NullCursorProfileContainer.pack(padx=(0,10),fill="x")
NullCursorEnabledVar = tk.BooleanVar(value=ScanForMouse)
NullCursorDisabledOverlay = tk.Frame(NullCursorTopBar,bg="#000000")
NullCursorDisabledOverlay.place(relx=0,rely=0,relwidth=1,relheight=1)
NullCursorOverlayText = tk.Label(NullCursorDisabledOverlay,text="NullCursor is currently disabled. When disabled, no cursor scanning occurs, and no background resources are used. Enable 'Scan For Mouse' to activate NullCursor.",bg="#000000",fg="white")
NullCursorOverlayText.pack(anchor="center")
NullCursorToggle = tk.Checkbutton(NullCursorCheck,text="Scan For Mouse",variable=NullCursorEnabledVar,command=ToggleNullCursor)
NullCursorToggle.grid(row=0,column=1,columnspan=2,pady=(5,0))
# --------------- NullCursor HowTo Page
NullCursorMainRowHT = tk.Frame(NullCursorHowToPage)
NullCursorMainRowHT.pack(fill="both",pady=20)
NullCursorHowToUse = tk.Label(NullCursorMainRowHT, 
text = 
"Step 1. When you first launch NullCursor, a default profile is created for you automatically. This profile uses your current monitor layout.\n\n"

"Step 2. If you want multiple setups, type a name into the box at the top and click \"Create Profile\". Otherwise, you can just use the default profile.\n\n"

"Step 3. Make sure a profile is active. Only one profile should be active at a time. When active, your warps will function.\n\n"

"Step 4. Click \"Create Warp\". You will be prompted to click a monitor to warp FROM, then a monitor to warp TO.\n\n"

"Step 5. After selecting both monitors, choose the edge or corner where your cursor leaves, and where it should appear.\n\n"

"Step 6. Once created, moving your mouse to that edge will teleport it to the target monitor.\n\n"

"Step 7. If you want to remove a warp, click \"Delete Warp\" and select the one you no longer want.\n\n"

"Step 8. Use the settings at the top to adjust behavior:\n"
"Detection: How early the program detects you're near an edge.\n"
"EdgeBuffer: How many pixels past the edge are required before warping.\n"
"ScanTime: How often your cursor position is checked.\n\n"

"Step 9. Hover over the Detection and Edge settings to preview their effect visually on your monitors.\n\n"

"Bonus: Lower ScanTime makes warps feel faster, but uses more CPU. Higher values are lighter, but may feel slightly delayed."
)
NullCursorHowToUse.pack(fill="both")
# ------------------------------
# Null Wire UI
# ------------------------------
NullWireNotebook = ttk.Notebook(NullWire)
NullWireNotebook.pack(fill="both", expand=True)
NullWireRoutingPage = tk.Frame(NullWireNotebook)
NullWireDevicesPage = tk.Frame(NullWireNotebook)
NullWireHowTo = tk.Frame(NullWireNotebook)
NullWireNotebook.add(NullWireRoutingPage, text="Wires")
NullWireNotebook.add(NullWireDevicesPage, text="Devices")
NullWireNotebook.add(NullWireHowTo, text = "How To")
# --------------- Routing Page
NullWireRoutingTop = tk.Frame(NullWireRoutingPage)
NullWireRoutingTop.pack(fill="x")
NullWireRoutingEntry = tk.Entry(NullWireRoutingTop)
NullWireRoutingEntry.pack(side="left", fill="x", expand=True)
NullWireAddButton = tk.Button(NullWireRoutingTop, text="Add")
NullWireAddButton.pack(side="left", fill="x", expand=True)
NullWireScrollArea = ScrollableFrame(NullWireRoutingPage)
NullWireScrollArea.pack(fill="both", expand=True)
NullWireRoutingObjects = NullWireScrollArea.Inner
NullWireAddButton.config(command=AddRoutingObject)
# --------------- Devices Page
NullWireMainRow = tk.Frame(NullWireDevicesPage)
NullWireMainRow.pack(fill="both", expand=True)
NullWireMainRow.columnconfigure(0, weight=49, uniform="group")
NullWireMainRow.columnconfigure(1, weight=2,  uniform="group")
NullWireMainRow.columnconfigure(2, weight=49, uniform="group")
NullWireLeftColumn = tk.Frame(NullWireMainRow)
NullWireLeftColumn.grid(row=0, column=0, sticky="nsew", padx=(5, 2))
NullWireDivider = tk.Frame(NullWireMainRow, bg="#555", width=4)
NullWireDivider.grid(row=0, column=1, sticky="ns")
NullWireRightColumn = tk.Frame(NullWireMainRow)
NullWireRightColumn.grid(row=0, column=2, sticky="nsew", padx=(2, 5))
# --------------- How To Page
NullWireMainRowHT = tk.Frame(NullWireHowTo)
NullWireMainRowHT.pack(fill="both",pady=20)
NullWireHowToUse = tk.Label(NullWireMainRowHT, 
text = "Step 1. In the Devices Page. Go to A1. Click \"Set\", and Select your Audio Output Device. It does not have to be your default device.\n\n" \
"Step 2. Now in Wires Page. In the white long box. Type a name, and then click \"Add\".\n\n"\
"Step 3. You now have a routing wire. Click on the A1 toggle inside the box. This allows audio to go from the Wire, into your Audio Device.\n\n"\
"Step 4. Within your wire, there is \"Attach\" and \"Remove\" boxes. Have audio be playing (e.g. spotify, or a youtube video or something). Click attach, and then select that Audio Source.\n\n"\
"Step 5. Now that your Audio source is connected. It will go into your wire, and then pass through to your Audio Device.\n\n"\
"Step 6? If you're using NullWire for streaming. Wires will show up as an Audio Output. So you may now attach your wire into OBS, and if you don't wish to also hear it? Uncheck the A1 box.\n\n"\
"Bonus: Feel free to mess around with settings and such. However, for equalization, and other special effects. I recommend EasyEffects"
    )
NullWireHowToUse.pack(fill="both")
# ------------------------------
# Null Git UI
# ------------------------------
NullGitNotebook = ttk.Notebook(NullGit)
NullGitNotebook.pack(fill="both", expand=True)
NullGitMainPage = tk.Frame(NullGitNotebook)
NullGitManagePage = tk.Frame(NullGitNotebook)
NullGitNotebook.add(NullGitMainPage, text="Repos")
NullGitNotebook.add(NullGitManagePage, text="Manage")
NullGitNotebook.tab(NullGitManagePage,state="disabled")
NullGitNotebook.bind("<<NotebookTabChanged>>",OnNotebookChanged)
# -------------- Main Page
NullGitMainPage.rowconfigure(0, weight=0)
NullGitMainPage.rowconfigure(1, weight=0)
NullGitMainPage.rowconfigure(2, weight=0)
NullGitMainPage.rowconfigure(3, weight=0)
NullGitMainPage.rowconfigure(4, weight=0)
NullGitMainPage.rowconfigure(5, weight=0)
NullGitMainPage.rowconfigure(6, weight=0)
NullGitMainPage.rowconfigure(7, weight=1)
NullGitMainPage.columnconfigure(0, weight=0)
NullGitMainPage.columnconfigure(1, weight=2)
NullGitMainPage.columnconfigure(2, weight=0)
NullGitInputPath = tk.StringVar()
NullGitCreateRepoPath = tk.StringVar()
NullGitCreateRepoLink = tk.StringVar()
NullGitClonePath = tk.StringVar()
NullGitCloneLink =tk.StringVar()
tk.Button(NullGitMainPage, text="Browse For Repo", width =16,command=lambda: BrowseForRepo()).grid(row=0, column=0, sticky="e", padx=5)
tk.Entry(NullGitMainPage,width=30,textvariable=NullGitInputPath,state="readonly",readonlybackground="#e7e7e7").grid(row=0, column=1, sticky="ew")
tk.Button(NullGitMainPage, text="Add Repo", width =16,command=lambda: AddRepo(NullGitInputPath.get())).grid(row=0, column=2, sticky="e", padx=5)
ttk.Separator(NullGitMainPage, orient="horizontal").grid(row=1, column=0, sticky="ew",columnspan=2, pady=6)
tk.Button(NullGitMainPage, text="Creation Location", width =16,command=lambda: SetRepoCreationLocation()).grid(row=2, column=0, sticky="w", padx=5)
NullGitEntryContainer = tk.Frame(NullGitMainPage)
NullGitEntryContainer.grid(row=2, column=1, sticky="ew")
NullGitEntryContainer.columnconfigure(0, weight=1)
NullGitEntryContainer.columnconfigure(1, weight=1)
tk.Entry(NullGitEntryContainer,width=30,textvariable=NullGitCreateRepoPath,state="readonly",).grid(row=0, column=0, sticky="ew")
tk.Entry(NullGitEntryContainer,width=30,textvariable=NullGitCreateRepoLink,).grid(row=0, column=1, sticky="ew")
tk.Button(NullGitMainPage, text="Create Repo", width =16,command=lambda:CreateRepo()).grid(row=2, column=2, sticky="w", padx=5)
ttk.Separator(NullGitMainPage, orient="horizontal").grid(row=3, column=0, sticky="ew",columnspan=2, pady=6)
tk.Button(NullGitMainPage, text="Set Clone Location", width =16,command=lambda:SetCloneLocation()).grid(row=4, column=0, sticky="e", padx=5)
tk.Entry(NullGitMainPage,width=30,textvariable=NullGitClonePath,state="readonly",readonlybackground="#e7e7e7").grid(row=4, column=1, sticky="ew")
tk.Button(NullGitMainPage, text="Clone Repo", width =16,command=lambda:CloneRepo()).grid(row=5, column=0, sticky="w", padx=5)
tk.Entry(NullGitMainPage,width=30,textvariable=NullGitCloneLink,readonlybackground="#e7e7e7").grid(row=5, column=1, sticky="ew")
tk.Label(NullGitMainPage, width=18, text="<-- Paste Repo Link").grid(row=5, column=2, sticky="ew")
ttk.Separator(NullGitMainPage, orient="horizontal").grid(row=6, column=0, sticky="ew",columnspan=2, pady=2)
NullGitReposList = ScrollableFrame(NullGitMainPage)
NullGitReposList.grid(row=7, column=0, sticky="nsew", padx=5, columnspan=3)
NullGitcontainer = NullGitReposList.Inner
DownloadOverlay = tk.Frame(NullGit,bg="#000000")
DownloadOverlayLabel = tk.Label(DownloadOverlay,text="Downloading...",font=("Arial", 12),justify="center")
DownloadOverlayLabel.pack(expand=True)
tk.Button(DownloadOverlay,text="Cancel",command=CancelDownload).pack(pady=10)
# --------------- manage
ManageRemoteURL = tk.StringVar()
ManageRepoPath = tk.StringVar()
ManageBranchName = tk.StringVar()
GitIgnoredVar = tk.StringVar()
CommittedVar = tk.StringVar()

NullGitManagePage.columnconfigure(0, weight=1)
NullGitManagePage.rowconfigure(0, weight=0)
NullGitManagePage.rowconfigure(1, weight=0)
NullGitManagePage.rowconfigure(2, weight=1)
NullGitManagePage.rowconfigure(3, weight=1)
NullGitManagePage.rowconfigure(4, weight=0)



RepoFrame = tk.LabelFrame(NullGitManagePage,text="Repo Management",bd=3,relief="solid")
RepoFrame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
RepoFrame.columnconfigure(0, weight=0)
RepoFrame.columnconfigure(1, weight=1)
RepoFrame.columnconfigure(2, weight=0)
RepoFrame.rowconfigure(0, weight=1)
BranchFrame = tk.LabelFrame(NullGitManagePage,text="Branch Management",bd=3,relief="solid")
BranchFrame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
BranchFrame.columnconfigure(0, weight=0)
BranchFrame.columnconfigure(1, weight=1)
BranchFrame.columnconfigure(2, weight=0)
BranchFrame.rowconfigure(0, weight=1)
IgnoreFrame = tk.LabelFrame(NullGitManagePage,text="GitIgnore Management",bd=3,relief="solid")
IgnoreFrame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
IgnoreFrame.columnconfigure(0, weight=1)
IgnoreFrame.rowconfigure(0, weight=0)
IgnoreFrame.rowconfigure(1, weight=1)
CommitFrame = tk.LabelFrame(NullGitManagePage,text="Commit Management",bd=3,relief="solid")
CommitFrame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
CommitFrame.columnconfigure(0, weight=1)
CommitFrame.columnconfigure(1, weight=1)
CommitFrame.rowconfigure(0, weight=0)
CommitFrame.rowconfigure(1, weight=0)
CommitFrame.rowconfigure(2, weight=0)
CommitFrame.rowconfigure(3, weight=1)

NuclearFrame = tk.LabelFrame(NullGitManagePage,text="Nuclear Commands",bd=3,relief="solid")
NuclearFrame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
NuclearFrame.columnconfigure(0, weight=1)
NuclearFrame.columnconfigure(1, weight=1)
NuclearFrame.rowconfigure(0, weight=0)
NuclearFrame.rowconfigure(1, weight=0)
NuclearFrame.rowconfigure(2, weight=1)
tk.Button(RepoFrame, text="Delete Repo From NullGit", command=lambda:DeleteRepoInNull(CurrentManagedRepo)).grid(row=0, column=0, sticky="ew", padx=5, pady=2, columnspan=3)


tk.Button(BranchFrame, text="Create Branch", width= 11, command=lambda:CreateBranchOnGit()).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
tk.Entry(BranchFrame, textvariable=ManageBranchName).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
tk.Button(BranchFrame, text="Rename Branch", width= 11, command=lambda:RenameBranchOnGit()).grid(row=0, column=2, sticky="ew", padx=5, pady=2)
tk.Button(BranchFrame, text="Delete Branch", command=lambda:DeleteBranchOnGit()).grid(row=1, column=0, sticky="ew", padx=5, pady=2, columnspan=3)

CurrentMergeBranch = tk.StringVar()
MergeBranches = tk.Label(BranchFrame,text="Merge this branch into current:",font=("Arial", 12),justify="center")
MergeBranches.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
MergeBranchBox = ttk.Combobox(BranchFrame, values=[], textvariable=CurrentMergeBranch, state="readonly")
MergeBranchBox.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
MergeButton = tk.Button(BranchFrame,text="Merge", command=lambda:MergeBranch())
MergeButton.grid(row=2,column=2,sticky="ew",padx=5,pady=2)

CreateGitIgnoreButton = tk.Button(IgnoreFrame,text="Create .gitignore", command=lambda:CreateGitIgnoreFile())
CreateGitIgnoreButton.grid(row=0,column=0,sticky="ew",padx=5,pady=2)
EditGitIgnoreButton = tk.Button(IgnoreFrame,text="Edit .gitignore", command=lambda:EditGitIgnoreFile())
EditGitIgnoreButton.grid(row=0,column=0,sticky="ew",padx=5,pady=2)
ToolTip(EditGitIgnoreButton, "Adding a file to the .gitignore also removes it from the repo, to remove something from the .gitignore, add a file/folder already in the .gitignore")
GitList = ScrollableFrame(IgnoreFrame)
GitList.grid(row=1, column=0, sticky="nsew", padx=5, columnspan=3)
GitListContainer = GitList.Inner
GitListContainer.configure(bg="white")
CreateGitIgnoreButton.grid_remove()
EditGitIgnoreButton.grid_remove()
GitList.grid_remove()
GitIgnoredLabel = tk.Label(GitListContainer,textvariable=GitIgnoredVar, justify="left",anchor="nw",bg="white",fg="black")
GitIgnoredLabel.pack(fill="both",expand=True,padx=5,pady=5)
tk.Button(CommitFrame, text="Add File To Commit", command=lambda:AddFileToCommit()).grid(row=0, column=0, sticky="ew", padx=5, pady=2)
tk.Button(CommitFrame, text="Remove File From Commit", command=lambda:RemoveFileFromCommit()).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
tk.Button(CommitFrame, text="Clear Current Commit", command=lambda:ClearCurrentCommit()).grid(row=1, column=0, sticky="ew", padx=5, pady=2, columnspan=2)
OnlyCommitMessage = tk.StringVar()
tk.Entry(CommitFrame,width=30,textvariable=OnlyCommitMessage).grid(row=2, column=0, sticky="ew", padx=5)
tk.Button(CommitFrame, text="Push Commit List", command=lambda:PushOnlyCommited()).grid(row=2, column=1, sticky="ew", padx=5, pady=2, columnspan=2)



CommitList = ScrollableFrame(CommitFrame)
CommitList.grid(row=3, column=0, sticky="nsew", padx=5, columnspan=2)
CommitListContainer = CommitList.Inner
CommitListContainer.configure(bg="white")
CommittedLabel = tk.Label(CommitListContainer,textvariable=CommittedVar,justify="left",anchor="nw",bg="white",fg="black")
CommittedLabel.pack(fill="both",expand=True,padx=5,pady=5) 



Stash = tk.Button(NuclearFrame,text="Stash & Pull", command=lambda:StashAndPull())
Stash.grid(row=0,column=0,sticky="ew",padx=5,pady=2,)
ForcePush = tk.Button(NuclearFrame,text="Force Push", command=lambda:ForcePushCommit())
ForcePush.grid(row=0,column=1,sticky="ew",padx=5,pady=2, columnspan=2)

# ==========================================================================================
# Initializing
# ==========================================================================================


def NullCursorLoop():
    global LastWarpTime, LastOutputs, LastInputs, LastSources, LoadTimes

    Start = time.time()

    FirstLoop = True
    
    while True:
        if ScanForMouse:
            x, y = GetCursorPos()
            if x is None:
                time.sleep(0.1)
                continue

            Bounds = GetMonitorBounds()
            CurrentID = GetCurrentMonitor(x, y, Bounds)

            if not CurrentID:
                continue

            B = Bounds[CurrentID]
            Corner = DetectEdge(x, y, B)

            if Corner not in ["TopLeft", "TopRight", "BottomLeft", "BottomRight", "Left", "Right", "Top", "Bottom"]:
                continue

            if not IsEdgeBuffer(Corner, x, y, B):
                continue

            if ActiveProfile not in Profiles:
                time.sleep(0.05)
                continue

            Warps = Profiles[ActiveProfile]["Warps"]

            if CurrentID not in Warps:
                continue

            for W in Warps[CurrentID]:
                if W["Edge"] != Corner:
                    continue

                TargetID = W["Target"]
                TargetEdge = W["TargetEdge"]

                if TargetID not in Bounds:
                    print("target not in bounds")
                    continue

                SourceB = B

                ratio = 0.5

                if Corner in ["Left", "Right"]:
                    ratio = (y - SourceB["y1"]) / (SourceB["y2"] - SourceB["y1"])
                elif Corner in ["Top", "Bottom"]:
                    ratio = (x - SourceB["x1"]) / (SourceB["x2"] - SourceB["x1"])

                now = time.time()
                if now - LastWarpTime < WarpCooldown:
                    continue

                LastWarpTime = now
                ExecuteWarp(TargetID, TargetEdge, Bounds, ratio)
                break

        if FirstLoop:
            FirstLoop = False
            LoadTimes['NullCursor'] = (time.time() - Start)

        time.sleep(max(ScanTime, WarpCooldown))

def NullWireLoop():
    global LastOutputs, LastInputs, LastSources, SystemLoading, LoadTimes
    LastOutputs = set()
    LastInputs = set()
    LastSources = set()
    tick = 0

    Start = time.time()

    FirstLoop = True

    while True:
        if tick == 0:
            RefreshOutputDevices()
            if OutputDevices != LastOutputs:
                print("Outputs changed")
                ApplyOutputs() 
                LastOutputs = OutputDevices.copy()
            ForceAudioDeviceVolume()

        elif tick == 1:
            RefreshInputDevices()
            if InputDevices != LastInputs:
                print("Inputs changed")
                ApplyInputs()
                LastInputs = InputDevices.copy()
            ForceMicDeviceVolume()
        elif tick == 2:
            GetAudioSources()
            if AudioSources != LastSources:
                print("Sources changed")
                ApplySources()
                LastSources = AudioSources.copy()
            ForceSinkVolume()

        tick = (tick + 1) % 3

        if FirstLoop:
            if tick == 0:
                FirstLoop = False
                SystemLoading = False
                LoadTimes["NullWire"] = (time.time() - Start)
        else:
            time.sleep(1)

def NullMidiLoop():
    global LoadTimes

    Start = time.time()
    FirstLoop = True

    while True:
        Ports = mido.get_input_names()
        NeededDevices = set()

        for Row in MidiRows:
            if not Row.get("Active"):
                continue

            Device = Row.get("Device")

            if not Device:
                continue

            if Device not in Ports:
                continue

            NeededDevices.add(Device)

        for Device in NeededDevices:
            if Device not in MidiDeviceListeners:
                StartMidiListener(Device)

        for Device in list(MidiDeviceListeners.keys()):
            if Device not in NeededDevices:
                StopMidiListener(Device)

        if FirstLoop:
            FirstLoop = False
            LoadTimes['NullMidi'] = (time.time() - Start)

        time.sleep(1)

def HideToTray():
    if SystemLoading:
        return
    Root.withdraw()

Root.protocol("WM_DELETE_WINDOW", HideToTray)

def Startup():
    global StartUpDelay, SystemLoading, StartUpTime, SystemLoading, LoadTimes
    StartUpTime = time.time()
    SystemLoading = True
    LoadConfig()
    LoadTimes['UI&Data'] = (time.time() - StartUpTime)
    LoadPopup.destroy()

    threading.Thread(target=StartTray, daemon=True).start()
    threading.Thread(target=WatchShowSignal, daemon=True).start()
    
    
    def StartBackgroundThreads():
        global StartUpTime, WaitTime, StartUpTimeString
        def UpdateStartUpTimeString():
            StartUpTimeString.set(f"Total Start Time:{LoadTimes.get("All"):.2f} seconds. \n Generating UI/Loading Your Data:{LoadTimes.get("UI&Data"):.2f}\n NullWire Scanning Your Audio:{LoadTimes.get("NullWire"):.2f}\n NullCursor Scanning Your Monitors/Mouse:{LoadTimes.get("NullCursor"):.2f}\n NullMidi Scanning Your Midi Devices:{LoadTimes.get("NullMidi"):.2f}")

        threading.Thread(target=NullCursorLoop, daemon=True).start()
        threading.Thread(target=NullMidiLoop, daemon=True).start()
        threading.Thread(target=RunUpdateCheck, daemon=True).start()
        threading.Thread(target=NullWireLoop, daemon=True).start()

        while SystemLoading:
            time.sleep(0.01)
            continue

        LoadTimes['All'] = (time.time() - StartUpTime)

        UpdateStartUpTimeString()

    Root.after(1,StartBackgroundThreads)

Root.after(1, Startup)
Root.mainloop()