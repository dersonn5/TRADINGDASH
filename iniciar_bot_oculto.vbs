Set WshShell = CreateObject("WScript.Shell")
' Executa o batch de inicializacao oculta (estilo de janela = 0, espera retornar = falso)
WshShell.Run "cmd.exe /c """ & WshShell.CurrentDirectory & "\iniciar_bot_silencioso.bat""", 0, False
