# Scientific Project Management Tool: ScienceHUB
---
**This is a simple project management application based on Flask. It enables users to create, edit, and manage projects, as well as handle project members and funders. Users can customize projects, update member roles, and save project data.
Additionally, the tool is designed for managing scientific projects, including resource and collaboration management. It features a local web interface built with HTML and CSS, with a SQL-based database implemented to store user registrations and project data. Agile methodologies such as Scrum and Kanban were employed for project management, while Docker was used for containerization, and SonarQube was integrated for code quality analysis.**


## Anforderungen
---
* Python 3.x
* Flask 
* SQLite


## Docker Installation
---
### Image erstellen
* docker build -t website  . 

### Docker-Container starten
* docker run -d -p 8000:8000 --name container-fuer-website website

### Extra Docker Befehle
* Alle laufende Container anzeigen: docker ps
* Container stoppen: docker stop sciencehub-container
* Container löschen: docker rm sciencehub-container



## Verwendung
---
### Über Docker
* Nachdem der Container gestartet wurde läuft die Anwendung unter http://localhost:8000

### Über Python
* Führe den folgenden Befehl aus: python scienhub.py
Die Anwendung läuft dann auch unter http://localhost:8000



## Autoren
---
- **Imad Azizi**
- **Torge Rau**
- **Rafik Farhane**
- **Lukas Baumeister**

## Mentoren
---
- **Prof Stephan Jonas**
- **Marko Jovanović**
- **Leon Nissen**
- **Lara Marie Reimer**
