# Scientific Project Management Tool (ScienceHUB)

Dies ist eine einfache Projektverwaltungsanwendung, die auf Flask basiert. Sie ermöglicht die Erstellung, Bearbeitung und Verwaltung von Projekten sowie die Verwaltung von Projektmitgliedern und Geldgebern (Fundern). Benutzer können Projekte anpassen, Mitgliederrollen ändern, und Projektdaten speichern.


## Anforderungen
Python 3.x
Flask 
SQLite


## Docker Installation

### Image erstellen
docker build -t sciencehub-app:latest .

### Docker-Container starten
docker run -d -p 5000:5000 --name sciencehub-container sciencehub-app:latest

### Extra Docker Befehle
Alle laufende Container anzeigen: docker ps
Container stoppen: docker stop sciencehub-container
Container löschen: docker rm sciencehub-container



## Verwendung

### Über Docker
Nachdem der Container gestartet wurde läuft die Anwendung unter http://localhost:8000

### Über Python
Führe den folgenden Befehl aus: python scienhub.py
Die Anwendung läuft dann auch unter http://localhost:8000



## Autoren
- **Imad Azizi**
- **Torge Rau**
- **Rafik Farhane**
- **Lukas Baumeister**

## Mentoren
- **Prof Stephan Jonas**
- **Marko Jovanović**
- **Leon Nissen**
- **Lara Marie Reimer**

