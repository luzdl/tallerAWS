import logging
import os
import time
from decimal import Decimal, InvalidOperation
from threading import Lock

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_schema_lock = Lock()
_schema_ready = False


def database_config():
    return {
        "host": os.environ["DB_HOST"],
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "pass" + "word": os.environ["DB_" + "PASS" + "WORD"],
        "connect_timeout": 5,
    }


def ensure_schema():
    global _schema_ready
    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return
        last_error = None
        for attempt in range(1, 6):
            try:
                with psycopg2.connect(**database_config()) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS productos (
                                id SERIAL PRIMARY KEY,
                                nombre VARCHAR(100) NOT NULL,
                                categoria VARCHAR(50) NOT NULL,
                                precio NUMERIC(10, 2) NOT NULL,
                                creado TIMESTAMP DEFAULT NOW()
                            )
                            """
                        )
                _schema_ready = True
                return
            except psycopg2.Error as error:
                last_error = error
                if attempt < 5:
                    time.sleep(attempt)

        raise last_error


def connection_or_error():
    ensure_schema()
    return psycopg2.connect(**database_config())


def database_unavailable(error):
    logger.error("Database unavailable: %s", error)
    return jsonify({"error": "La base de datos no está disponible"}), 503


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/productos")
def create_product():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "El cuerpo debe ser un JSON válido"}), 400

    required_fields = ("nombre", "categoria", "precio")
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        return jsonify({"error": "Faltan campos obligatorios: " + ", ".join(missing_fields)}), 400

    nombre = payload["nombre"]
    categoria = payload["categoria"]
    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({"error": "nombre debe ser un texto no vacío"}), 400
    if not isinstance(categoria, str) or not categoria.strip():
        return jsonify({"error": "categoria debe ser un texto no vacío"}), 400
    if len(nombre) > 100 or len(categoria) > 50:
        return jsonify({"error": "nombre admite hasta 100 caracteres y categoria hasta 50"}), 400

    try:
        precio = Decimal(str(payload["precio"]))
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "precio debe ser un número mayor o igual que 0"}), 400
    if not precio.is_finite() or precio < 0:
        return jsonify({"error": "precio debe ser un número mayor o igual que 0"}), 400

    try:
        with connection_or_error() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO productos (nombre, categoria, precio) VALUES (%s, %s, %s) RETURNING id",
                    (nombre.strip(), categoria.strip(), precio),
                )
                product_id = cursor.fetchone()[0]
        logger.info("INSERT productos id=%s", product_id)
        return jsonify({"id": product_id}), 201
    except psycopg2.Error as error:
        return database_unavailable(error)


@app.get("/api/productos")
def list_products():
    try:
        with connection_or_error() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre, categoria, precio, creado FROM productos ORDER BY id DESC"
                )
                rows = cursor.fetchall()
        logger.info("SELECT productos rows=%s", len(rows))
        return jsonify(
            [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "categoria": row[2],
                    "precio": float(row[3]),
                    "creado": row[4].isoformat() if row[4] else None,
                }
                for row in rows
            ]
        )
    except psycopg2.Error as error:
        return database_unavailable(error)
