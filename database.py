import sqlite3
import hashlib
import uuid


class Database:
    def __init__(self):
        self.id = None
        self.project_db = "database/project.db"
        self.login_db = "database/sign_in_user_data.db"
        self.all_users_db = "database/all_users.db"

    def create_connection(self, name) -> sqlite3.Connection:
        # Erstellen einer Datenbankverbindung zu einer SQLite-Datenbank
        conn = None
        try:
            conn = sqlite3.connect(name)
            return conn
        except sqlite3.Error as e:
            print(e)
        return conn

    def hash_password(self, password) -> str:
        # Hashen eines Passworts
        # passwort wird mit encode() als Byte-Sequenz angegeben und dann gehasht
        has_object = hashlib.sha256(password.encode())
        return has_object.hexdigest()

    def generate_user_id(self) -> str:
        # Generiere zufällige user_id
        id = "d" + str(uuid.uuid4()).replace("-", "")
        return id

    def get_id(self) -> str:
        return self.id

    def set_id(self, new_id) -> None:
        self.id = new_id

    def create_table(self, conn, sqlcode) -> bool:
        try:
            cursor = conn.cursor()
            cursor.execute(sqlcode)
            conn.commit()
            print("Created table")
            return True

        except sqlite3.Error as e:
            print(e)
            return False

    def register_user(self, conn, username, mail, password) -> bool:
        # Hinzufügen eines neuen Benutzers zur Tabelle "user_data" -> login_db
        password_hash = self.hash_password(password)
        user_id = self.generate_user_id()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_data (user_id, username, mail, passwort_hash) VALUES (?, ?, ?, ?)",
                (user_id, username, mail, password_hash),
            )
            conn.commit()

            # user zu all_user_db hinzufügen
            self.add_user_to_all_users(username, user_id)
            print(f"User added successfully with ID {user_id}.")
            return True

        except sqlite3.IntegrityError:
            return False

        except sqlite3.Error as e:
            print(e)
            return False

    def add_user_to_all_users(self, username, user_id) -> None:
        conn = self.create_connection(self.all_users_db)

        user_id = str(user_id)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO all_users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        conn.commit()

        print(f"User {username} was added")

    def get_id_from_name(self, username) -> str:
        conn = self.create_connection(self.all_users_db)

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM all_users WHERE username = ?",
                (username,),
            )

            # fetcone -> geht auf die erste Zeile (einzige Zeile)
            row = cursor.fetchone()
            if row != None:
                # Tupel entpacken
                db_user_id = row[0]
                return db_user_id
            else:
                print("User not found.")
                return "0"

        except sqlite3.Error as e:
            print(e)
            return "0"

    def login_user(self, conn, username, password) -> bool:
        # Einloggen eines Benutzers
        password_hash = self.hash_password(password)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, passwort_hash FROM user_data WHERE username = ?",
                (username,),
            )
            # fetcone -> geht auf die erste Zeile (einzige Zeile)
            row = cursor.fetchone()
            if row is not None:
                # Tupel entpacken
                db_user_id, db_password_hash = row
                if db_password_hash == password_hash:
                    # Setze self.id auf die ID des eingeloggten Benutzers
                    self.id = db_user_id[0]
                    print("Login successful.")
                    return True

                else:
                    print("Incorrect password.")
                    return False

            else:
                print("User not found.")
                return False

        except sqlite3.Error as e:
            print(e)
            return False

    def add_project(self, conn, tupel) -> int:
        # Values werden in die Projekt Tabelle eingefügt
        try:
            sql = f""" INSERT INTO PROJECT(PID, NAME, DESCRIPTION, ADMIN, FUNDER, MEMBERS, STATUS, CREATED_DATE)
                    VALUES(?,?,?,?,?,?,?,?) """
            cur = conn.cursor()
            cur.execute(sql, tupel)
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(e)
            return 0

    def add_values_to_member(self, conn, id, tupel) -> int:
        # Values werden in die Tabelle eines anderen Users eingefügt
        try:
            sql = f""" INSERT INTO {id}(PID, ROLE)
                    VALUES(?,?) """
            cur = conn.cursor()
            cur.execute(sql, tupel)
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(e)
            return 0


    def search_user(self, name, email) -> bool:
        conn = self.create_connection(self.login_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM user_data",
        )

        conn.commit()
        row = cursor.fetchall()
        # Die Name werden hier im Lowercase verglichen, damit keine ähnlichen Namen vorkommen also es kann keine zwei Benutzer geben mit Namen Max und max
        for n in row:
            if n[0].lower() == name.lower():
                return False

            else:
                cursor.execute(
                    "SELECT user_id FROM user_data WHERE mail = ?",
                    (email,),
                )
                conn.commit()
                row = cursor.fetchone()
                if row is not None:
                    return False
        return True

    def print_table(self, conn, table_name) -> None:
        try:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            print(f"Data from {table_name}:")
            for row in rows:
                print(row)
        except sqlite3.Error as e:
            print(f"Error reading from table {table_name}: {e}")

    def get_name_from_id(self, id) -> str:
        conn = self.create_connection(self.all_users_db)

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username FROM all_users WHERE user_id = ?",
                (id,),
            )

            # fetcone -> geht auf die erste Zeile (einzige Zeile)
            row = cursor.fetchone()
            if row != None:

                # Tupel entpacken
                db_user_name = row[0]
                return db_user_name
            else:
                print("User not found.")
                return "0"

        except sqlite3.Error as e:
            print(e)
            return "0"

    def user_exists(self, username) -> bool:
    
        conn = self.create_connection(self.all_users_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM all_users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row == None:
            return False
        return True
    
