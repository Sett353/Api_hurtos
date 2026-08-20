import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def crear_tabla():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS tipo_hurto(
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL UNIQUE
                );
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS hurto(
                    id SERIAL PRIMARY KEY,
                    IdTipoHurto INTEGER NOT NULL,
                    denunciante VARCHAR (100) NOT NULL,
                    direccion VARCHAR(200) NOT NULL,
                    fecha_hurto DATE NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_tipo_hurto
                        FOREIGN KEY (IdTipoHurto)
                        REFERENCES tipo_hurto(id)
                        ON DELETE RESTRICT
                    );""")
    conn.commit()
    cur.close()
    conn.close()

