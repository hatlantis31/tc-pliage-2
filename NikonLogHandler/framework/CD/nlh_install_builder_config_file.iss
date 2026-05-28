; Nikon Log Handler Installation Script
; This script handles the installation of Nikon Log Handler, including:
; - Automatic uninstallation of previous versions
; - Process termination of running instances
; - Installation to the correct directory structure
; - Creation of shortcuts
; - Multi-language support (English and Japanese)

[Setup]
; Basic Application Information
#define AppName "Nikon Log Handler"
#define AppVersion "4.0.0.15"
#define AppPublisher "Nikon"
#define AppURL "https://nikonglobaleu.sharepoint.com/sites/NPE-ESHardware/SitePages/Nikon-Log-Handler.aspx"
#define AppExeName "NikonLogHandler.exe"

; Application Details
AppId={{B1E42F85-0B9A-4F66-B63E-43E47E3636BE}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Additional metadata for security verification
AppContact=es-hardware@nikon.com
AppCopyright=© 2023 Nikon Corporation
VersionInfoCompany=Nikon Corporation
VersionInfoCopyright=© 2023 Nikon Corporation
VersionInfoDescription="Installation package for Nikon Log Handler utility"
VersionInfoProductName="Nikon Log Handler"
VersionInfoProductVersion={#AppVersion}
VersionInfoProductTextVersion={#AppVersion}
VersionInfoOriginalFileName=NikonLogHandler_2.1.0.26.release.exe
AppReadmeFile=https://nikonglobaleu.sharepoint.com/sites/NPE-ESHardware/SitePages/Nikon-Log-Handler.aspx
AppComments="Official Nikon utility for log file handling and analysis"

; Installation Directory Settings
DefaultDirName=C:\nikon_Tools\NikonLogHandler
DefaultGroupName={#AppName}

; Output Settings
OutputDir=.\Output
OutputBaseFilename=NikonLogHandler_4.0.0.15.testing

; Compression Settings
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4

; System Requirements
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; UI and Behavior Settings
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no
DisableFinishedPage=no
WizardStyle=modern
WizardSizePercent=120
UninstallDisplayIcon={app}\{#AppExeName}

; Administrative Settings
PrivilegesRequired=admin
AllowNoIcons=yes

; Uninstaller Settings
UninstallFilesDir={app}
UninstallDisplayName={#AppName}
CreateUninstallRegKey=yes
UninstallLogMode=append

[Languages]
; Supported Languages
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Messages]
; Custom Messages
english.WelcomeLabel1=Welcome to the [name] Setup Wizard
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nIt is recommended that you close all other applications before continuing.
japanese.WelcomeLabel1=[name] セットアップウィザードへようこそ
japanese.WelcomeLabel2=このウィザードは、[name/ver] をインストールします。%n%n続行する前に、他のアプリケーションをすべて終了することをお勧めします。

[Files]
; Main Application Files
Source: ".\dist\NikonLogHandler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Desktop and Start Menu Shortcuts
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Registry]
; Registry Entries
Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey

[Code]
var
  ResultCode: Integer;

// Function to check if a process is running
function IsProcessRunning(const ProcessName: string): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  if Exec(ExpandConstant('{sys}\tasklist.exe'), '/NH /FI "IMAGENAME eq ' + ProcessName + '"',
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := (ResultCode = 0);
  end;
end;

// Function to kill a process
procedure KillProcess(const ProcessName: string);
var
  ResultCode: Integer;
begin
  if IsProcessRunning(ProcessName) then
  begin
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "' + ProcessName + '"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    // Add a small delay to ensure the process is fully terminated
    Sleep(1000);
  end;
end;

// Function to get uninstall string from registry
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

// Function to uninstall the previous version
function UninstallPrevious(): Boolean;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := True;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then
  begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES',
            '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
    begin
      Result := True;
      // Add a small delay to ensure uninstallation is complete
      Sleep(2000);
    end
    else
      Result := False;
  end;
end;

// Function to delete a file if it exists
procedure DeleteFileIfExists(const FilePath: string);
begin
  if FileExists(FilePath) then
    DeleteFile(FilePath);
end;

// Function to delete a directory and its contents
procedure DelTree(const Path: string);
var
  FindRec: TFindRec;
  FilePath: string;
begin
  if DirExists(Path) then
  begin
    if FindFirst(Path + '\*', FindRec) then
    begin
      try
        repeat
          FilePath := Path + '\' + FindRec.Name;
          if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
          begin
            if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then
              DeleteFile(FilePath)
            else
              DelTree(FilePath);
          end;
        until not FindNext(FindRec);
      finally
        FindClose(FindRec);
      end;
    end;
    RemoveDir(Path);
  end;
end;

// Before installation starts
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// During installation steps
procedure CurStepChanged(CurStep: TSetupStep);
var
  BasePath: string;
begin
  if CurStep = ssInstall then
  begin
    // Kill any running instances
    KillProcess('{#AppExeName}');

    // Uninstall previous version
    if not UninstallPrevious() then
    begin
      MsgBox('Failed to uninstall the previous version. Installation will continue, but you may want to uninstall the old version manually.',
             mbInformation, MB_OK);
    end;

    // Set base path
    BasePath := 'C:\nikon_Tools';

    // Delete folders if they exist
    DelTree(BasePath + '\NikonLogHandler');
    DelTree(BasePath + '\_internal');
    DelTree(BasePath + '\image_files');

    // Delete files if they exist
    DeleteFileIfExists(BasePath + '\data.info');
    DeleteFileIfExists(BasePath + '\NikonLogHandler.exe');
    DeleteFileIfExists(BasePath + '\NikonLogHandler.XML');
    DeleteFileIfExists(BasePath + '\NikonLogHandlerError.log');
    DeleteFileIfExists(BasePath + '\unins000.dat');
    DeleteFileIfExists(BasePath + '\unins000.exe');
    DeleteFileIfExists(BasePath + '\Uninstall.dat');
    DeleteFileIfExists(BasePath + '\Uninstall.exe');
    DeleteFileIfExists(BasePath + '\Uninstall_lang.ifl');

    // Add a small delay to ensure all deletions are complete
    Sleep(1000);
  end;
end;

// During uninstallation steps
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // Kill any running instances before uninstall
    KillProcess('{#AppExeName}');
  end;
end;