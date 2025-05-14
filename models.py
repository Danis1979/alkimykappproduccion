import sqlite3
from werkzeug.security import generate_password_hash

def crear_tabla_usuarios():
    conn = sqlite3.connect('basedatos.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def crear_admin():
    conn = sqlite3.connect('basedatos.db')
    c = conn.cursor()
    password_hash = generate_password_hash('Mica1979')
    try:
        c.execute("""
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (?, ?, ?, ?)
        """, ('alkimykfood', 'alkimykfood@gmail.com', password_hash, 'admin'))
        conn.commit()
        print("✅ Usuario administrador creado correctamente.")
    except sqlite3.IntegrityError:
        print("⚠️ El usuario administrador ya existe.")
    conn.close()

if __name__ == "__main__":
    crear_tabla_usuarios()
    crear_admin()