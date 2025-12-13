# **Stadterkennung durch OCR**

## **Requirements**
* Python Version 3.13 https://www.python.org/downloads/ (Kann auch sein das es mit älteren Versionen auch geht)
* Installiere Requirements (Entweder über ein venv oder direkt für die Python Version)
    
  Wenn du die Python Version die du benutzen willst in deiner IDE als Interpreter hast kannst du einfach auf die grünen Pfeile drücken.
  Wenn nicht selbst die gleichen Befehle im Terminal eingeben.
    ````bash
  pip install opencv-python~=4.11.0.86
  pip install numpy~=2.2.5
  pip install easyocr~=1.7.2
  pip install RapidFuzz~=3.13.0
  pip install geopy~=2.4.1
  pip install aiohttp~=3.11.18
  pip install requests==2.32.*
  ````
* Vor dem Starten müssen noch die Straßen namen für den Wort abgleich der OCR-Postprocessing heruntergeladene werden führe dafür die [download_streets_from_osm.py](setups/download_streets_from_osm.py) aus:
  ````bash 
  cd setups
  ````
  ````bash
  python.exe download_streets_from_osm.py 
  ````

## **Run**
````bash
python.exe run.py 
````

## Tests
* Führe die aus[_test_one_city.py](tests/_test_one_city.py) oder [_test_all_16_citys.py](tests/_test_all_16_citys.py) aus. 


## **Configurations**
* In der test Datei den input_file festlegen, um die OCR-Pipeline für ein anderes bild laufen zu lassen.
* Man kann auch neue bilder verwenden einfach in den "input" folder legen und auswählen 
* Falls eine neue Stadt verwendet wird, muss der Stadtname vorher in die [download_streets_from_osm.py](setups/download_streets_from_osm.py) eingetragen werden und das Setup-File muss erneut ausgeführt werden