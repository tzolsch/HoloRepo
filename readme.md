* requirements_basic.txt 
  * reicht um alles zum laufen zu kriegen (pip requirements file), bis auf lokale Sprachmodelle (aber das nicht so wichtig)
* requirements.txt 
  * installiert auch EasyMNT für lokale sprachmodelle - ist aber tricky weil es bestimmte Python version braucht für PyTorch und automatische abhängigkeits auflösung höchst wahrscheinlich nicht funktioniert
* OSCSpawn:
  * Ist Bibliothek für funktionalitäten (wie "auf messungen warten", "Micro anmachen",...) und script zum spawnen für den udp-client zu gleich (bisschen crowded)
* DMMRead
  * Enthält einfach das decodierungs funktionalität für das auslesen des elektrometers über serial-port
* MeasData
  * Enthält Beispielmessreihen für messdaten
* TDdata
  * enthält touchdesigner scripte und snippets: 
    * "HoloTD.toe" ist der aktuelle stand and quasi die öh front seite um mit dem udp proczess zu kommunizieren der in OSCSpawn.py gespawnt wird

Also um alles zu testen/an zu stoßen einfach OSCspawn.py ausführen dann kann man über touchdesigner oder von wo anders OSC/udp nachrichten an den clienten (oder server - bringe das immer durcheinander) schicken und die entsprechendn threads werden dann gespawned und messungen oder MICRO mitschnitte oder was so anfällt senden die threads dann auch über diesen clienten. Die Adresse von dem clienten ist einfach:

ip = "127.0.0.1"
sendPort = 7000
inPort = 8000

Aber das kann man im OSCSpawn leicht ändern (da in dem main block ist das gut sichtbar)
Auch welche OSC tags auf welche funktionalität gemapt wird kann man da in dem main block ganz gut sehen. Ich hab alles versuch ein bisschen zu dokumentieren

LG
