#define MyAppName "NEPOS"
#define MyAppVersion "0.1.0-piloto"
#define MyAppPublisher "NEPOS"
#define MyAppExeName "NEPOS.exe"

[Setup]
AppId={{38CB0B67-123B-49E5-AE0B-6E458F31B37B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NEPOS
DefaultGroupName=NEPOS
DisableProgramGroupPage=yes
LicenseFile=..\licencia.txt
OutputDir=..\dist\instalador
OutputBaseFilename=NEPOS_Setup_0.1.0-piloto
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\dist\NEPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\Configurar_NEPOS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\NEPOS"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Configurar instalacion de NEPOS"; Filename: "{app}\Configurar_NEPOS.exe"
Name: "{autodesktop}\NEPOS"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar NEPOS"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    WizardForm.StatusLabel.Caption :=
      'Configurando NEPOS y aplicando actualizaciones...';

    if not Exec(
      ExpandConstant('{app}\Configurar_NEPOS.exe'),
      '',
      ExpandConstant('{app}'),
      SW_SHOWNORMAL,
      ewWaitUntilTerminated,
      ResultCode
    ) then
      RaiseException(
        'No se pudo iniciar el asistente de configuracion de NEPOS.'
      );

    if ResultCode <> 0 then
      RaiseException(
        'La configuracion de NEPOS no finalizo correctamente. ' +
        'El codigo de salida fue ' + IntToStr(ResultCode) + '.'
      );
  end;
end;
