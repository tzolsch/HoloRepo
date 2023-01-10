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