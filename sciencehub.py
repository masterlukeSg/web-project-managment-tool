from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from flask import jsonify
from flask import flash
from datetime import date, datetime
import sqlite3
import hashlib
import uuid
import database

app = Flask(__name__)

# Flash key
app.secret_key = "your_secret_key"

db = database.Database()

# Dictionary which safes the information for the new project
new_project_info = dict(
    project_name="", project_description="", project_member=[], project_funder=[]
)

edit_project_info = dict(
    new_project_name="", new_project_desc="", new_member = [], new_funder = [], added_member = [], deleted_member = []
)


def create_dbs():
    # Öffne eine Verbindung zur Datenbank
    conn_user_data = db.create_connection(db.login_db)
    conn_all_users = db.create_connection(db.all_users_db)
    conn_project = db.create_connection(db.project_db)

    user_table = """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id TEXT PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                mail TEXT VARCHAR NOT NULL,
                passwort_hash TEXT NOT NULL
            )"""

    # Erstelle die Nutzertabelle mit allen Nutzern fürs login & registrieren
    db.create_table(conn_user_data, user_table)

    all_users_table = """CREATE TABLE IF NOT EXISTS all_users (
                user_id TEXT PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL
            )"""

    # Erstelle eine Nutzertabell mit allen Nutzern, um auf id & username zuzugreifen
    db.create_table(conn_all_users, all_users_table)

    project_table = """CREATE TABLE IF NOT EXISTS PROJECT (
                      PID VARCHAR(40) PRIMARY KEY,
                      NAME VARCHAR(30) NOT NULL,
                      DESCRIPTION TEXT NOT NULL,
                      ADMIN VARCHAR(40) NOT NULL,
                      FUNDER TEXT,
                      MEMBERS TEXT,
                      STATUS VARCHAR(7) NOT NULL,
                      CREATED_DATE NOT NULL
                ); """

    # Erstelle ein Projekttabelle für alle Projekte
    db.create_table(conn_project, project_table)


#Funktion um das new_project_info dict zu leeren
def empty_dict():
    new_project_info["project_name"] = ""
    new_project_info["project_description"] = ""
    new_project_info["project_funder"] = []
    new_project_info["project_member"] = []


#Funktion welche zu einem String die user zurueckgibt deren username mit diesem String beginnt
def search_for_users(query) -> dict:

    #Verbindung zur all_users databass erstellen
    conn = db.create_connection(db.all_users_db)
    cursor = conn.cursor()
    #Nutzer aus der Database abfragen, die mit dem selben String beginnen welcher eingegeben wurde 
    cursor.execute('SELECT username FROM all_users WHERE username LIKE ?', (query + '%',))
    users = cursor.fetchall()
    conn.close()
    #usernames zurueck an die html datei senden 
    user_list = [{'username': user[0]} for user in users]
    return user_list




@app.route("/")
def starting_page():
    return redirect("login")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login/check", methods=["POST"])
def check_login():
    # username vom input Field bekommen
    username = request.form["username"]

    # password vom input Field bekommen
    password = request.form["password"]

    # conection zur login Datenbank
    login_conn = db.create_connection(db.login_db)

    # wenn Passwort & Nutzername inkorrekt
    if db.login_user(login_conn, username, password) == False:
        flash("Username or password is wrong")
        return redirect(url_for("login"))

    else:
        # id des nutzer aus der DB anfragen
        cursor = login_conn.cursor()
        id = cursor.execute(
            "SELECT user_id FROM user_data WHERE username = ?",
            (username,),
        )

        # id aus der Anfrage ziehen
        row = cursor.fetchone()
        if row is not None:
            # Tupel entpacken
            id = row[0]

        # id auf den eingelogten Nutzer setzten
        db.set_id(id)

        return redirect(url_for("dashboard", username=username))


@app.route("/sign_up")
def sign_up():
    return render_template("register.html")


@app.route("/sign_up/complete_sign_up", methods=["POST"])
def complete_sign_up():
    name = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    if password != repeat_password:
        flash("The passwords are not identical!")
        return redirect(url_for("sign_up"))

    else:
        conn = db.create_connection(db.login_db)

        if db.search_user(name, email) == True:
            register = db.register_user(conn, name, email, password)

            if register == False:
                flash("ERROR something went wrong")
                return redirect(url_for("sign_up"))

            cursor = conn.cursor()
            id = cursor.execute(
                "SELECT user_id FROM user_data WHERE username = ?",
                (name,),
            )

            row = cursor.fetchone()
            if row is not None:
                id = str(row[0])

            db.set_id(id)

            user_table = f"""
            CREATE TABLE IF NOT EXISTS {id} (
                    PID VARCHAR(40) NOT NULL,
                    ROLE VARCHAR(5) NOT NULL,
                    FOREIGN KEY (PID) REFERENCES PROJECT(PID)
                );
            """
            user_conn = db.create_connection(db.project_db)
            db.create_table(user_conn, user_table)

            return redirect(url_for("dashboard", username=name))
        else:
            flash("Username or E-Mail already exists")
            return redirect(url_for("sign_up"))


@app.route("/dashboard/<username>")
def dashboard(username):

    # wenn der übergebene Nutzer nicht mit dem angemeldeten Nutzer übereinstimmt, zurück zu login
    if db.get_id() != db.get_id_from_name(username):
        return redirect(url_for("login"))
    
    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()

    # Die ID des Benutzers basierend auf dem Benutzernamen abrufen
    user_id = db.get_id_from_name(username)

    # Führen Sie die Abfrage aus, um alle Projekte des Benutzers zu erhalten
    cursor.execute(
        f"""SELECT P.NAME, P.STATUS, B.ROLE, P.ADMIN, P.MEMBERS, P.CREATED_DATE, P.PID
        FROM {user_id} AS B JOIN PROJECT AS P ON B.PID = P.PID"""
    )

    # Holt alle Ergebnisse
    results = cursor.fetchall()

    # Erstellt eine Liste von Projektdaten für alle Projekte des Nutzers
    projects = []
    if results:
        for result in results:
            project_name, status, role, creator, members, date_str, project_id = result
            try:
                # Versuche, den Datum-String in ein Datum-Objekt umzuwandeln
                date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            except ValueError:
                # Falls das Umwandeln fehlschlägt, setze date auf None oder eine Standardmeldung
                date = date.today()
                print("No date found")

            if members:
                members_count = len(members.split(','))
            else:
                members_count = 0

            values = [
                project_name,
                status,
                role,
                db.get_name_from_id(creator) + " + " + str(members_count) + " more members",
                # Datum zum dd.mm.yyyy Format umändern
                date.strftime('%d.%m.%Y') if date else "No Date",
                project_id
            ]
            projects.append(values)
    else:
        flash("No projects found for this user")

    return render_template("dashboard.html", text_for_column=projects)


#log out aus aus seinem Account
@app.route("/log_out")
def log_out():
    #id wird auf none gesetzt somit ist man abgemeldet
    db.set_id(None)
    #zurueckleiten auf start seite
    return redirect(url_for("starting_page"))


# Fuege ein neues Projekt hinzu
@app.route("/NewProject")
def new_project():
    # Die New Project page wird mit den entsprechenden Parametern gerendert
    return render_template(
        "NewProjectUI.html",
        name_value=new_project_info["project_name"],
        description_value=new_project_info["project_description"],
        user=new_project_info["project_member"],
        funder=new_project_info["project_funder"],
    )


@app.route('/NewProject/search_users', methods=['GET'])
def search_users():

    #Erhalt der Eingegeben Buchstaben aus dem Inputfeld
    query = request.args.get('q', '')
    #Rufe Funktion auf welche nach den entsprechenden usern sucht
    user_list = search_for_users(query)
    return jsonify(user_list)


#zurueck zum dashboard wenn man doch kein neues projekt erstellen will
@app.route("/NewProject/back_to_dashboard")
def back_to_dashboard():
    
    #hole die aktuelle id des nutzers
    id = db.get_id()
    #hole den dazu entsprechenden nutzername aus der datenbank
    name = db.get_name_from_id(id)
    #new_project_info dict leeren
    empty_dict()
    #leite zurueck auf die nutzer dashboard seite
    return redirect(url_for("dashboard", username = name))


# Funktion um neue Member zu einem neuen Projekt hinzuzufuegen
@app.route("/NewProject/add_user", methods=["POST"])
def add_user():
    # Request aus der Html datei wo die Request form den Namen name hat
    user = request.form["name"]
    #test ob user ueberhaupt existiert
    if db.user_exists(user) == True:
        if user not in new_project_info["project_member"]:
            id = db.get_id()
            name = db.get_name_from_id(id)

            if name != user:
                # fuege den neuen Member in die Member Liste hinzu
                new_project_info["project_member"].append(user)
            else:
                flash("You can not add yourself")
        else:
            flash("This User is already part of your project")
    else:
        flash("This User does not exist")
    # kehre zur new_project Seite zurueck
    return redirect(url_for("new_project"))


# Funktion welche Projektnamen und beschreibung sichert
@app.route("/NewProject/save_data", methods=["POST"])
def save_data():
    # Request die Json Daten welche den Projektnamen und die Projektbeschreibung enthalten
    data = request.json
    # Setze die Variablen um Projektnamen und Projektbeschreibung zu speichern
    project_name = data.get("project_name")
    project_description = data.get("project_description")

    # Wenn die Daten korrekt übertragen wurde übernehme sie in das Dictionary
    if project_name or project_description:
        new_project_info["project_name"] = project_name
        new_project_info["project_description"] = project_description
        # return successmessage
        return (
            jsonify(
                {
                    "message": "Project data saved successfully",
                    "projects": new_project_info,
                }
            ),
            200,
        )
    # Wenn die Daten nicht korrekt transferiert wurden
    else:
        # return error message
        return jsonify({"message": "Invalid data"}), 400


@app.route("/NewProject/add_funding", methods=["POST"])
def add_funding():
    # Request aus der Html Datei wo das form den Namen name hat um von dort die funder abzufragen
    funder = request.form["name"]
    # Fuege den Funder zur Funder Liste hinzu
    new_project_info["project_funder"].append(funder)
    # kehre zur new_project Seite zurueck
    return redirect(url_for("new_project"))


# Nach dem Entwurf eines Projekts werden die Daten in der Datenbank gespeichert
@app.route("/NewProject/create_project")
def create_project():

    id = db.get_id()
    conn = db.create_connection(db.project_db)

    # PID erstellen
    pid = "p" + str(uuid.uuid4())

    # Die NID des Admins vom Projekt
    user_admin = id

    # Tupel erstellen
    user_values = (pid, "admin")

    # Tupel in Tabelle einfügen
    db.add_values_to_member(conn, id, user_values)

    # die benötigten Daten aus dem Dictionary holen
    project_name = new_project_info["project_name"]
    project_description = new_project_info["project_description"]
    project_members = new_project_info["project_member"]
    project_members_str = ",".join(project_members)
    project_funder = new_project_info["project_funder"]
    project_funder_str = ",".join(project_funder)

    # Tupel erstellen
    project_values = (
        pid,
        project_name,
        project_description,
        user_admin,
        project_funder_str,
        project_members_str,
        "open",
        date.today(),
    )

    # Tupel in Projekt Tabelle einfügen
    db.add_project(conn, project_values)

    # Plan: Die PID zu den einzelnen Member Tabellen einfügen
    for member in new_project_info["project_member"]:
        member_id = db.get_id_from_name(member)
        db.add_values_to_member(conn, member_id, (pid, "read"))

    # Das Dictonary nach dem eingeben wieder leeren

    empty_dict()
    name = db.get_name_from_id(id)

    return redirect(url_for("dashboard", username=name))



@app.route("/project/<projectid>")
def project(projectid):
    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()
    print(projectid)

    cursor.execute(
        "SELECT NAME, DESCRIPTION, FUNDER, ADMIN, MEMBERS, STATUS FROM PROJECT WHERE PID = ?", (projectid,)
    )
    
    project = cursor.fetchone()

    project_name, description, funder, admin, members, status = project
    member_names = members.split(',') if members else []
    members_roles = []
    members_roles.append((db.get_name_from_id(admin), 'admin'))


    for name in member_names:
        member_id = db.get_id_from_name(name)
        user_conn = db.create_connection(db.project_db)
        user_cursor = user_conn.cursor()

        user_cursor.execute(f"SELECT ROLE FROM '{member_id}' WHERE PID = ?", (projectid,))
        role = user_cursor.fetchone()
        if role:
            members_roles.append((name, role[0]))
        else:
            members_roles.append((name, 'read'))  # Default role if not found

    user_id = db.get_id()
    new_conn = db.create_connection(db.project_db)
    new_cursor = new_conn.cursor()

    new_cursor.execute(f"SELECT ROLE FROM '{user_id}' WHERE PID = ?", (projectid,))
    role = new_cursor.fetchone()

    # Überprüfe, ob das Projekt archiviert ist
    if status == 'archived':
        # Zeige das Projekt nur dem Admin an
        if role and role[0] == 'admin':
            return render_template("project_page.html", project_name=project_name, description=description, funder=funder, members=members_roles, status=status, project_id=projectid)
        else:
            return "Access denied", 403
    else:
        # Zeige das Projekt den Mitgliedern an
        if role and (role[0] == 'admin' or role[0] == 'write'):
            return render_template("project_page.html", project_name=project_name, description=description, funder=funder, members=members_roles, status=status, project_id=projectid)
        else:
            return render_template("project_page_read.html", project_name=project_name, description=description, funder=funder, members=members_roles, status=status)
    

#Seite um ein Projekt zu bearbeiten   
@app.route("/edit_project/<projectid>")
def edit_project(projectid):
    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()

    pid = projectid

    #Wenn edit_project_info leer ist, heißt das die entsprechenden Daten müssen erst geladen werden
    if edit_project_info["new_project_name"] == "":

        #Daten des Projektes werden aus der Datenbank geladen und in das Dict eingefügt
        cursor.execute(
            "SELECT NAME, DESCRIPTION, FUNDER, MEMBERS FROM PROJECT WHERE PID = ?", (projectid,)
        )

        project = cursor.fetchone()

        project_name, project_description, project_funders, project_members = project


        edit_project_info["new_project_name"] = project_name
        edit_project_info["new_project_desc"] = project_description
        
        member_list = project_members.split(',') if project_members else []

        #Für jeden Member wird jetzt auch noch die entsprechende Rolle die der Nutzer im Projekt hat abgerufen.
        for member in member_list:
            mid = db.get_id_from_name(member)
            cursor.execute(
                f"SELECT ROLE FROM '{mid}' WHERE PID = ?", (projectid,)
            )

            result = cursor.fetchone()
            role = result[0]

            print(role)

            member_dict = {'name': member, 'role': role}

            edit_project_info["new_member"].append(member_dict)
        
        funder_list = project_funders.split(',') if project_funders else []
        for funder in funder_list:
            edit_project_info["new_funder"].append(funder)

    return render_template("edit_project.html", project_name=edit_project_info["new_project_name"], project_description=edit_project_info["new_project_desc"], project_funders=edit_project_info["new_funder"], project_members=edit_project_info["new_member"], project_id=pid)

#save_new_data speichert änderungen am Projektnamen und der Projektbeschriebung
#Funktion identisch zu der Funktion wenn man ein neues Projekt erstellt
@app.route("/edit_project/<projectid>/save_new_data", methods = ["POST"])
def save_new_data(projectid):
     # Request die Json Daten welche den Projektnamen und die Projektbeschreibung enthalten
    data = request.json
    # Setze die Variablen um Projektnamen und Projektbeschreibung zu speichern
    project_name = data.get("project_name")
    project_description = data.get("project_description")

    # Wenn die Daten korrekt übertragen wurde übernehme sie in das Dictionary
    if project_name or project_description:
        edit_project_info["new_project_name"] = project_name
        edit_project_info["new_project_desc"] = project_description
        # return successmessage
        return (
            jsonify(
                {
                    "message": "Project data saved successfully",
                    "projects": edit_project_info,
                }
            ),
            200,
        )
    # Wenn die Daten nicht korrekt transferiert wurden
    else:
        # return error message
        return jsonify({"message": "Invalid data"}), 400


#Funktion um Nutzer zu einem Projekt hinzuzufuegen
@app.route("/edit_project/<projectid>/add_user_project", methods = ["POST"])
def add_user_project(projectid):
    # Request aus der Html datei wo die Request form den Namen name hat
    user = request.form["name"]
    #test ob user ueberhaupt existiert
    if db.user_exists(user) == True:
        if user not in edit_project_info["new_member"]:
            id = db.get_id()
            name = db.get_name_from_id(id)

            if name != user:
                # fuege den neuen Member in die Member Liste hinzu
                # und in die Liste der neu hinzugefuegten Member
                user_role = {'name': user, 'role': 'read'}
                edit_project_info["new_member"].append(user_role)
                edit_project_info["added_member"].append(user)

                #Wenn der Member vorher schon einmal entfernt wurde muss er aus der deleted Member Liste geloescht werden
                if user in edit_project_info["deleted_member"]:
                    edit_project_info["deleted_member"].remove(user)
                    
            else:
                flash("You can not add yourself")
        else:
            flash("This User is already part of your project")
    else:
        flash("This User does not exist")
    # kehre zur new_project Seite zurueck
    return redirect(url_for("edit_project", projectid = projectid))


#Funktion um Funding hinzuzufuegen
@app.route("/edit_project/<projectid>/add_funding_project", methods = ["POST"])
def add_funding_project(projectid):
    # Request aus der Html Datei wo das form den Namen name hat um von dort die funder abzufragen
    funder = request.form["name"]
    # Fuege den Funder zur Funder Liste hinzu
    edit_project_info["new_funder"].append(funder)
    # kehre zur new_project Seite zurueck
    return redirect(url_for("edit_project", projectid = projectid))


#Funktion um Nutzer zu entfernen
@app.route("/edit_project/<projectid>/remove_user", methods = ["POST"])
def remove_user(projectid):
    data = request.get_json()
    user = data.get('username')
    print(f'User {user} removed')

    mid = db.get_id_from_name(user)

    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT ROLE FROM '{mid}' WHERE PID = ?", (projectid,)
        )
    
    value  = cursor.fetchone()
    role = value[0]

    user_role = {'name': user, 'role': role}

    #Nutzer wird aus new_Member Liste entfernt und die Liste der entfernten Nutzer hinzugefuegt
    edit_project_info["new_member"].remove(user_role)
    edit_project_info["deleted_member"].append(user) 

    #Wenn der Nutzer schon in der added_member Liste auftaucht muss er aus dieser geloescht werden
    if user in edit_project_info["added_member"]:
        edit_project_info["added_member"].remove(user)

    return jsonify({'message': f'User {user} has been removed'}), 200

#Funktion um funder zu loeschen
@app.route("/edit_project/<projectid>/remove_funder", methods = ["POST"])
def  remove_funder(projectid):
    data = request.get_json()
    name = data.get('fundername')
    print(f'Funder {name} removed')

    edit_project_info["new_funder"].remove(name)

    return jsonify({'message': f'Funder {name} has been removed'}), 200


#Funktion um die Rollen von Nutzern zu ändern
@app.route("/edit_project/<projectid>/change_role", methods = ["POST"])
def change_role(projectid):
    #json datei mit Rollenänderungen werden abgefragt
    data = request.json
    name = data.get('name')
    new_role = data.get('role')

    #Es wird nach dem User mit dem passenden Namen gesucht
    #Und seine Rolle geändert
    for member in edit_project_info["new_member"]:
        if member['name'] == name:
            member['role'] = new_role

    return jsonify({"status": "success"})

#Funktion um die entsprechenden änderungen zu speichern
@app.route("/edit_project/<projectid>/save_changes")
def save_changes(projectid):

    #DAten werden aus dem Dict entnommen
    #Daten die in Listen auftauchen werden zu strings gemacht
    new_name = edit_project_info["new_project_name"]
    new_description = edit_project_info["new_project_desc"]
    new_member = edit_project_info["new_member"]
    new_member_list = []
    for member in new_member:
        new_member_list.append(member['name'])
    new_members_str = ",".join(new_member_list)
    new_funder = edit_project_info["new_funder"]
    new_funder_str = ",".join(new_funder)

    #Die PROJECT Tabelle wird an der Stelle der entsprechenden PID mit den neuen Daten geupdated
    conn = db.create_connection(db.project_db)

    cursor = conn.cursor()


    cursor.execute(
        "UPDATE PROJECT SET NAME = ?, DESCRIPTION = ?, FUNDER = ?, MEMBERS = ? WHERE PID = ?",
        (new_name, new_description, new_funder_str, new_members_str, projectid,)
        )
    
    conn.commit()

    #Member die neu in das Projekt hinzugefuegt wurden erhalten einen neuen Eintrag des Projektes in ihrer Tabelle
    for member in edit_project_info["added_member"]:
        member_id = db.get_id_from_name(member)
        db.add_values_to_member(conn, member_id, (projectid, "read"))

    #Bei Member die aus dem Projekt geloescht wurden wird auch der entsprechende Tabelleneintrag geloescht
    for member in edit_project_info["deleted_member"]:
        member_id = db.get_id_from_name(member)
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM '{member_id}' WHERE PID = ?", (projectid,)
            )
        conn.commit()

    #Die Rollen der User werden geupdated
    for member in edit_project_info["new_member"]:
        name = member['name']
        role = member['role']
        print(name, role)

        mid = db.get_id_from_name(name)
        cursor = conn.cursor()

        cursor.execute(
            f"UPDATE '{mid}' SET ROLE = ? WHERE PID = ?", (role, projectid,)
        )
        conn.commit()
    
    #Das Dict wird geleert
    edit_project_info["new_project_name"] = ""
    edit_project_info["new_project_desc"] = ""
    edit_project_info["new_member"] = []
    edit_project_info["new_funder"] = []
    edit_project_info["added_member"] = []
    edit_project_info["deleted_member"] = []


    return redirect(url_for("project", projectid = projectid))


#Funktion um das editieren abzubrechen
@app.route("/edit_project/<projectid>/back_to_project")
def back_to_project(projectid):

    #Das dict wird geloescht
    edit_project_info["new_project_name"] = ""
    edit_project_info["new_project_desc"] = ""
    edit_project_info["new_member"] = []
    edit_project_info["new_funder"] = []
    edit_project_info["added_member"] = []
    edit_project_info["deleted_member"] = []

    return redirect(url_for("project", projectid = projectid))



@app.route("/delete_project/<project_id>")
def delete_project(project_id):
    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()
    
    # Lösche das Projekt aus der PROJECT-Tabelle
    cursor.execute(
        "DELETE FROM PROJECT WHERE PID = ?",
        (project_id,),
    )
    conn.commit()

    flash("Project has been deleted successfully")

    # Verbindung zur all_users Datenbank
    conn2 = db.create_connection(db.all_users_db)
    cursor2 = conn2.cursor()

    # Alle user_id's aus der all_users Tabelle holen
    cursor2.execute("SELECT user_id FROM all_users")
    users = cursor2.fetchall()

    for user in users:
        user_id = user[0]  # user ist ein Tupel, extrahiere die user_id
        cursor.execute(f"DELETE FROM '{user_id}' WHERE PID = ?", (project_id,))
        conn.commit()

    # hole die aktuelle id des Nutzers
    id = db.get_id()

    # hole den dazu entsprechenden Nutzername aus der Datenbank
    name = db.get_name_from_id(id)

    # Leitet den Nutzer zurück zum Dashboard oder einer anderen Seite
    return redirect(url_for("dashboard", username=name))



@app.route("/archive_project/<project_id>")
def archive_project(project_id):
    # Verbindung zur all_users Datenbank
    conn = db.create_connection(db.project_db)
    cursor = conn.cursor()

    conn2 = db.create_connection(db.all_users_db)
    cursor2 = conn2.cursor()

    # Alle user_id's aus der all_users Tabelle holen
    cursor2.execute("SELECT user_id FROM all_users")
    users = cursor2.fetchall()

    for user in users:
        user_id = user[0]  # user ist ein Tupel, extrahiere die user_id
        cursor.execute(f"DELETE FROM '{user_id}' WHERE PID = ? AND ROLE <> ?", (project_id, 'admin',))
        conn.commit()

    # Update the project status to "archived"
    cursor.execute("UPDATE PROJECT SET STATUS = ? WHERE PID = ?", ("archived", project_id))
    conn.commit()

    # hole die aktuelle id des Nutzers
    id = db.get_id()

    # hole den dazu entsprechenden Nutzername aus der Datenbank
    name = db.get_name_from_id(id)

    # Leitet den Nutzer zurück zum Dashboard oder einer anderen Seite
    return redirect(url_for("dashboard", username=name))


if __name__ == "__main__":
    create_dbs()
    app.run(host='0.0.0.0', port=8000, debug=True)
