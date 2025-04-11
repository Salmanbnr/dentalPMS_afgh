; -- MyAppInstaller.iss --

[Setup]
AppName=DentalClinic
AppVersion=1.0
DefaultDirName={pf}\MyApp
DefaultGroupName=DentalClinic
DisableProgramGroupPage=yes
OutputBaseFilename=DentalClinic_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=logo.ico

[Files]
; include every file from the PyInstaller dist folder
Source: "dist\DentalClinic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start‑menu shortcut
Name: "{group}\MyApp"; Filename: "{app}\DentalClinic.exe"; WorkingDir: "{app}"
; Desktop shortcut
Name: "{userdesktop}\DentalClinic"; Filename: "{app}\DentalClinic.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
