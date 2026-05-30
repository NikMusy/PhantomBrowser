; Phantom Browser installer (Inno Setup 6)
; Per-user install into %LOCALAPPDATA% without admin rights, like Google Chrome.

[Setup]
AppId={{8F3A2C1E-5B7D-4E96-A1F2-9C4D6E8B0A37}
AppName=Phantom Browser
AppVersion=3.0
AppVerName=Phantom Browser 3.0
AppPublisher=PhantomLabs
AppPublisherURL=https://github.com/NikMusy/PhantomBrowser
AppSupportURL=https://github.com/NikMusy/PhantomBrowser/issues
AppUpdatesURL=https://github.com/NikMusy/PhantomBrowser/releases
VersionInfoVersion=3.0.0.0
VersionInfoCompany=PhantomLabs
VersionInfoDescription=Phantom Browser — privacy-first AI browser
VersionInfoProductName=Phantom Browser
DefaultDirName={localappdata}\Programs\Phantom Browser
DisableProgramGroupPage=yes
DisableWelcomePage=no
UninstallDisplayName=Phantom Browser
UninstallDisplayIcon={app}\PhantomBrowser.exe
PrivilegesRequired=lowest
OutputDir=installer_out
OutputBaseFilename=PhantomBrowserSetup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=110
WizardImageFile=wizard_large.bmp
WizardSmallImageFile=wizard_small.bmp
WizardImageStretch=yes
SetupIconFile=app.ico
AppCopyright=© 2026 PhantomLabs

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Messages]
ru.WelcomeLabel2=Сейчас на компьютер будет установлен [name/ver].%n%nPhantom — приватный браузер с AI-ассистентом, своей поисковой системой и режимом Ghost Mode. Ставится в пользовательскую папку без прав администратора, как Chrome.
ru.FinishedHeadingLabel=👻 Phantom Browser установлен

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "setdefault"; Description: "Зарегистрировать Phantom как браузер (чтобы выбрать по умолчанию)"; Flags: unchecked

[Files]
Source: "dist\PhantomBrowser\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Phantom Browser"; Filename: "{app}\PhantomBrowser.exe"
Name: "{group}\{cm:UninstallProgram,Phantom Browser}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Phantom Browser"; Filename: "{app}\PhantomBrowser.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\PhantomHTML"; ValueType: string; ValueData: "Phantom HTML Document"; Flags: uninsdeletekey; Tasks: setdefault
Root: HKCU; Subkey: "Software\Classes\PhantomHTML\DefaultIcon"; ValueType: string; ValueData: "{app}\PhantomBrowser.exe,0"; Tasks: setdefault
Root: HKCU; Subkey: "Software\Classes\PhantomHTML\shell\open\command"; ValueType: string; ValueData: """{app}\PhantomBrowser.exe"" ""%1"""; Tasks: setdefault
Root: HKCU; Subkey: "Software\Phantom\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "Phantom Browser"; Tasks: setdefault
Root: HKCU; Subkey: "Software\Phantom\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Privacy-first AI browser"; Tasks: setdefault
Root: HKCU; Subkey: "Software\Phantom\Capabilities\URLAssociations"; ValueType: string; ValueName: "http"; ValueData: "PhantomHTML"; Tasks: setdefault
Root: HKCU; Subkey: "Software\Phantom\Capabilities\URLAssociations"; ValueType: string; ValueName: "https"; ValueData: "PhantomHTML"; Tasks: setdefault
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "Phantom"; ValueData: "Software\Phantom\Capabilities"; Flags: uninsdeletevalue; Tasks: setdefault

[Run]
Filename: "{app}\PhantomBrowser.exe"; Description: "{cm:LaunchProgram,Phantom Browser}"; Flags: nowait postinstall skipifsilent
Filename: "ms-settings:defaultapps"; Flags: shellexec postinstall skipifsilent; Tasks: setdefault
