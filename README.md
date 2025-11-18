# API de Reconocimiento Facial

Esta es una API de backend construida con FastAPI para realizar registro y autenticación de usuarios mediante
reconocimiento facial.

## Características

- **Registro de Usuarios**: Registra nuevos usuarios subiendo una imagen de su rostro.
- **Autenticación de Usuarios**: Auténtica a los usuarios existentes mediante una imagen de su rostro.
- **Prevención de Duplicados**: Evita que un mismo rostro sea registrado múltiples veces.
- **Base de Datos Segura**: Utiliza Firebase Firestore para almacenar las codificaciones faciales (no las imágenes).
- **Manejo de Errores**: Incluye un manejo detallado de errores para diferentes escenarios (ej. no se detecta rostro,
  múltiples rostros, etc.).
- **Documentación de la API**: Documentación autogenerada por FastAPI (Swagger UI y ReDoc).

## Estructura del Proyecto

```
facial_recognition_backend/
├── app/
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Carga de configuraciones desde variables de entorno.
│   ├── models/
│   │   ├── __init__.py
│   │   └── api_models.py         # Modelos Pydantic para las respuestas de la API.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py           # Lógica para interactuar con Firebase.
│   │   └── facial_recognition.py # Lógica para el procesamiento de imágenes y reconocimiento facial.
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py                   # Archivo principal de la aplicación FastAPI con los endpoints.
├── .env                          # Archivo para las variables de entorno.
└── requirements.txt              # Dependencias del proyecto.
```

## Configuración y Puesta en Marcha

### 1. Prerrequisitos

- Python 3.11+
- Una cuenta de Firebase con Firestore habilitado.
- `dlib` y sus dependencias (`cmake`, `boost`).
    - **macOS**: `brew install cmake boost`
    - **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install build-essential cmake`

### 2. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd facial_recognition_backend
```

### 3. Crear un Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables:

```
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=app/api/faacil-facial-recognition-firebase-adminsdk.json
FIREBASE_PROJECT_ID=faacil-facial-recognition
CONFIDENCE_THRESHOLD=0.6
```

- `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`: La ruta al archivo JSON de credenciales de Firebase.
- `FIREBASE_PROJECT_ID`: El ID del proyecto de Firebase (puedes encontrarlo en la configuración de proyecto).
- `CONFIDENCE_THRESHOLD`: (Opcional) El umbral de similitud para considerar dos rostros como una coincidencia. El valor
  por defecto es `0.6`. Un valor más bajo es más estricto.

### 6. Ejecutar la Aplicación

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.

### 7. Endpoints de la API

### `POST /register`

- **Descripción**: Registra un nuevo usuario.
- **Cuerpo de la Solicitud**: `multipart/form-data` con un campo `file` que contiene la imagen del rostro.
- **Respuesta Exitosa (201)**:
  ```json
  {
    "user_id": "some-unique-user-id",
    "message": "Usuario registrado exitosamente."
  }
  ```
- **Respuestas de Error**:
    - `400 Bad Request`: Si no se detecta un rostro, se detectan múltiples rostros o el formato de la imagen no es
      válido.
    - `409 Conflict`: Si el rostro ya está registrado en la base de datos.
    - `500 Internal Server Error`: Para errores inesperados del servidor.

### `POST /login`

- **Descripción**: Autentica a un usuario existente.
- **Cuerpo de la Solicitud**: `multipart/form-data` con un campo `file` que contiene la imagen del rostro.
- **Respuesta Exitosa (200)**:
  ```json
  {
    "user_id": "some-unique-user-id",
    "message": "Login exitoso."
  }
  ```
- **Respuestas de Error**:
    - `401 Unauthorized`: Si el rostro no coincide con ningún usuario registrado.
    - `400 Bad Request`: Si no se detecta un rostro o se detectan múltiples rostros.
    - `500 Internal Server Error`: Para errores inesperados del servidor.

### `GET /health`

- **Descripción**: Endpoint de verificación de estado para confirmar que la API está funcionando.
- **Respuesta Exitosa (200)**:
  ```json
  {
    "status": "ok"
  }
  ```

## Documentación de la API

Una vez que la aplicación esté en funcionamiento, se puede acceder a la documentación interactiva de la API a traves de
los siguientes enlaces:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

Desde la interfaz de Swagger, se pueden probar los endpoints directamente desde el navegador.

## Pruebas con cURL

cURL para probar cada endpoint de la API desde la terminal o desde herramientas como Postman:

### Health Check - Verificar estado de la API

```bash
curl -X GET "http://localhost:8000/health" \
     -H "accept: application/json"
```

**Respuesta esperada:**

```json
{
  "status": "ok"
}
```

### Registro de Usuario

```bash
curl -X POST "http://localhost:8000/register" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/ruta/a/tu/imagen.jpg"
```

**Ejemplo con imagen específica:**

```bash
curl -X POST "http://localhost:8000/register" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@./test_images/usuario1.jpg"
```

**Respuesta exitosa (201):**

```json
{
  "user_id": "abc123def456",
  "message": "Usuario registrado exitosamente."
}
```

**Respuesta de error - No se detectó rostro (400):**

```json
{
  "error": "No se pudo extraer la codificación facial de la imagen."
}
```

**Respuesta de error - Usuario ya existe (409):**

```json
{
  "error": "Este rostro ya ha sido registrado."
}
```

### Login de Usuario

```bash
curl -X POST "http://localhost:8000/login" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/ruta/a/tu/imagen.jpg"
```

**Respuesta exitosa (200):**

```json
{
  "user_id": "abc123def456",
  "message": "Login exitoso."
}
```

**Respuesta de error - Rostro no reconocido (401):**

```json
{
  "error": "Autenticación fallida. Rostro no reconocido."
}
```

## Notas Importantes

### Formatos de Imagen Soportados

- La API acepta formatos comunes de imagen: JPG, PNG, JPEG, etc.
- Asegúrate de que la imagen contenga un rostro claramente visible
- La imagen no debe contener múltiples rostros

### Configuración de Firebase

- El archivo de credenciales debe estar ubicado en `app/api/faacil-facial-recognition-firebase-adminsdk.json`
- Para Firestore, no es necesario configurar `DATABASE_URL`
- Asegúrate de que Firestore esté habilitado en tu proyecto de Firebase

### Seguridad

- Las imágenes no se almacenan en la base de datos
- Solo se guardan las codificaciones faciales (vectores numéricos)
- Las credenciales de Firebase deben mantenerse seguras y no exponerse públicamente

### Resolución de Problemas Comunes

1. **Error "No face detected"**: Asegúrate de que la imagen contenga un rostro visible
2. **Error "Multiple faces detected"**: Usa una imagen con un solo rostro
3. **Error "Invalid image format"**: Verifica que el archivo sea una imagen válida
4. **Error de conexión a Firebase**: Revisa las credenciales y la configuración del proyecto
