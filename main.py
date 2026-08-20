from fastapi import FastAPI,HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import crear_tabla, get_connection
from models import Hurto, Tipo_hurto, UsuarioRegistro, Token
from auth import hashear_password, verificar_password, crear_token, verificar_token, obtener_usuario_actual
import psycopg

app = FastAPI()

crear_tabla()

@app.get("/")
def start():
    return {"Mensaje" : " Bienvenido a la API de hurtos"}

@app.post("/hurto")
def create_hurto(hurto: Hurto, usuario_actual: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tipo_hurto WHERE id = %s",
                (hurto.tipo_hurto,))
    tipo_hurto_id = cur.fetchone()
    if not tipo_hurto_id:
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")
    cur.execute("INSERT INTO "\
        "hurto (IdTipoHurto, denunciante, direccion, fecha_hurto) VALUES (%s, %s, %s, %s) "\
            "RETURNING id",
            (hurto.tipo_hurto, hurto.denunciante, hurto.direccion, hurto.fecha_hurto,))
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"Mensaje" : "registro de hurto creado exitosamente", "id": new_id}

@app.get("/hurto")
def get_hurtos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hurto")
    hurtos = cur.fetchall()
    cur.close()
    conn.close()
    return {"Hurtos" : hurtos}

@app.get("/hurto/{id}")
def get_hurto(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hurto WHERE id = %s", (id,))
    hurto = cur.fetchone()
    cur.close()
    conn.close()
    if not hurto:
        raise HTTPException(status_code=404, detail="Registro de hurto no encontrado")
    return {"Hurto" : hurto}

@app.put("/hurto/{id}")
def update_hurto(id: int, hurto: Hurto):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM hurto WHERE id = %s", (id,))
    existing_hurto = cur.fetchone()
    if not existing_hurto:
        raise HTTPException(status_code=404, detail="Registro de hurto no encontrado")
    cur.execute("UPDATE hurto SET IdTipoHurto = %s, denunciante = %s, direccion = %s, fecha_hurto = %s WHERE id = %s", (hurto.tipo_hurto, hurto.denunciante, hurto.direccion, hurto.fecha_hurto, id))
    conn.commit()
    cur.close()
    conn.close()
    return {"Mensaje" : "Registro de hurto actualizado exitosamente"}

@app.delete("/hurto/{id}")
def delete_hurto(id: int, usuario_actual: dict = Depends(obtener_usuario_actual)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM hurto WHERE id = %s", (id,))
    existing_hurto = cur.fetchone()
    if not existing_hurto:
        raise HTTPException(status_code=404, detail="Registro de hurto no encontrado")
    cur.execute("DELETE FROM hurto WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"Mensaje" : "Registro de hurto eliminado exitosamente"}

@app.post("/tipo_hurto")
def create_tipo_hurto(tipo_hurto: Tipo_hurto):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tipo_hurto (nombre) VALUES (%s) RETURNING id", (tipo_hurto.nombre,))
        new_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El tipo de hurto ya existe")
    finally:
        if not cur.closed:
            cur.close()
        if not conn.closed:
            conn.close()

    return {"Mensaje" : "Tipo de hurto creado exitosamente", "id" : new_id}

@app.get("/tipo_hurto")
def get_tipo_hurtos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tipo_hurto")
    tipo_hurtos = cur.fetchall()
    cur.close()
    conn.close()
    return {"Tipo de hurtos" : tipo_hurtos}

@app.get("/tipo_hurto/{id}")
def get_tipo_hurto(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tipo_hurto WHERE id = %s", (id,))
    tipo_hurto = cur.fetchone()
    cur.close()
    conn.close()
    if not tipo_hurto:
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")
    return {"Tipo de hurto" : tipo_hurto}

@app.put("/tipo_hurto/{id}")
def update_tipo_hurto(id: int, tipo_hurto: Tipo_hurto):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tipo_hurto WHERE id = %s", (id,))
    existing_tipo_hurto = cur.fetchone()
    if not existing_tipo_hurto:
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")
    cur.execute("UPDATE tipo_hurto SET nombre = %s WHERE id = %s", (tipo_hurto.nombre, id))
    conn.commit()
    cur.close()
    conn.close()
    return {"Mensaje" : "Tipo de hurto actualizado exitosamente"}

@app.delete("/tipo_hurto/{id}")
def delete_tipo_hurto(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tipo_hurto WHERE id = %s", (id,))
    existing_tipo_hurto = cur.fetchone()
    if not existing_tipo_hurto:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")

    cur.execute("SELECT id FROM hurto WHERE IdTipoHurto = %s LIMIT 1", (id,))
    associated_hurto = cur.fetchone()
    if associated_hurto:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El tipo de hurto tiene hurtos asociados y no se puede eliminar")

    cur.execute("DELETE FROM tipo_hurto WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"Mensaje": "Tipo de hurto eliminado exitosamente", "ID": id}

@app.post("/registro")
def registrar_usuario(usuario: UsuarioRegistro):
    conn = get_connection()
    cur = conn.cursor()

    password_hash = hashear_password(usuario.password)

    try:
        cur.execute(
            "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s) RETURNING id",
            (usuario.username, password_hash)
        )
        nuevo_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Ese nombre de usuario ya existe")

    cur.close()
    conn.close()
    return {"mensaje": "Usuario registrado", "id": nuevo_id}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash FROM usuarios WHERE username = %s",
        (form_data.username,)
    )
    usuario = cur.fetchone()
    cur.close()
    conn.close()
    
    if not usuario or not verificar_password(form_data.password, usuario ["password_hash"]):
        raise HTTPException(status_code=401, detail= "Usuario o contraseña incorrectos")
    
    token = crear_token({"sub": usuario["username"], "id": usuario["id"]})
    return {"access_token": token, "token_type": "bearer"}
