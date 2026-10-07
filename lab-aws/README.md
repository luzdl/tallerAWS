# Lab AWS: gestión de productos

Aplicación de dos servicios independientes: un frontend nginx y un backend Flask. PostgreSQL se usa solo para las pruebas locales; en AWS el backend puede conectarse a RDS mediante las mismas variables de entorno.

## Estructura

```text
lab-aws/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── index.html
│   ├── default.conf.template
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .env.example
└── README.md
```

## Ejecutar localmente

Desde `lab-aws/`, copia `.env.example` a `.env` y ajusta los valores si es necesario:

```bash
cp .env.example .env
docker compose up --build
```

Abre <http://localhost:8080>. El backend no publica ningún puerto al host; nginx enruta las peticiones `/api/` al servicio `backend`.

Para detener los servicios conservando los datos:

```bash
docker compose down
docker compose up
```

Para borrar también el volumen de PostgreSQL:

```bash
docker compose down -v
```

## Variables de entorno

| Variable | Uso | Ejemplo |
|---|---|---|
| `DB_HOST` | Host de PostgreSQL | `db` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `DB_NAME` | Nombre de la base | `productos` |
| `DB_USER` | Usuario de la base | `productos_user` |
| `DB_PASSWORD` | Contraseña de la base | `productos_password` |
| `BACKEND_HOST` | Nombre DNS del backend para nginx | `backend` |
| `BACKEND_PORT` | Puerto del backend para nginx | `5000` |

El backend lee la configuración de PostgreSQL exclusivamente desde `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`. `DB_PORT` usa `5432` por defecto. La tabla `productos` se crea automáticamente en la primera operación que usa la base.

## API

- `GET /api/health` devuelve `{"status":"ok"}` sin consultar la base de datos.
- `POST /api/productos` recibe `{"nombre":"Teclado","categoria":"Periféricos","precio":29.90}` y devuelve `201` con `{"id":1}`.
- `GET /api/productos` devuelve todos los registros ordenados por `id` descendente.

Pruebas con curl:

```bash
curl http://localhost:8080/api/health

curl -X POST http://localhost:8080/api/productos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Teclado","categoria":"Periféricos","precio":29.90}'

curl http://localhost:8080/api/productos
```
