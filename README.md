# API de Reconocimiento Facial (Python + FastAPI + TensorFlow Lite)

Backend de alto rendimiento diseñado para la gestión de identidades biométricas. Proporciona servicios RESTful para el
registro y autenticación de usuarios mediante análisis facial, utilizando modelos de aprendizaje profundo optimizados
para entornos de producción en la nube.

## Características Principales

- **Motor de Inferencia Híbrido:** Combina `dlib` (HOG/CNN) para una detección de rostros robusta y `TensorFlow Lite` (
  FaceNet 512) para la generación de embeddings de alta precisión.
- **Compatibilidad Multiplataforma:** Genera vectores biométricos (embeddings) compatibles matemáticamente con la
  aplicación móvil Android, permitiendo autenticación offline.
- **Almacenamiento Seguro:** Los vectores faciales se almacenan en Firebase Firestore. No se almacenan imágenes de
  rostros, garantizando la privacidad.
- **Arquitectura Serverless:** Contenerizado con Docker y optimizado para despliegue en Google Cloud Run.
- **Documentación Automática:** Especificación OpenAPI (Swagger) disponible en `/docs`.

## Stack Tecnológico

- **Framework Web:** FastAPI (Python 3.10+)
- **ML & Visión:** TensorFlow Lite, OpenCV, face_recognition (dlib)
- **Base de Datos:** Google Firebase Firestore
- **Infraestructura:** Docker, Google Cloud Build, Google Cloud Run

## Estructura del Proyecto

```
facial_recognition_python/
├── app/
│   ├── api/                      # Credenciales y recursos estáticos
│   ├── core/                     # Configuración (Variables de entorno)
│   ├── models/                   # Modelos Pydantic (Request/Response)
│   ├── services/                 # Lógica de negocio
│   │   ├── database.py           # Capa de acceso a datos (Firestore)
│   │   └── facial_recognition.py # Pipeline de ML (Detección -> Recorte -> Embedding)
│   └── main.py                   # Entrypoint de la aplicación
├── Dockerfile                    # Definición del contenedor para Cloud Run
├── cloudbuild.yaml               # Pipeline de CI/CD para Google Cloud
├── requirements.txt              # Dependencias de Python
└── .env                          # Variables de entorno locales
```

## Configuración y Ejecución Local

### 1. Prerrequisitos

- Python 3.10 o superior.
- CMake y otras instalaciones necesarias para compilar `dlib`.
    - macOS: `brew install cmake libpng libjpeg boost`
    - Linux: `sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev`
- Credenciales de Firebase (`serviceAccountKey.json`) ubicadas en `app/api/`.

### 2. Instalación de Dependencias

Se recomienda utilizar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Variables de Entorno

Crear un archivo `.env` en la raíz con la siguiente configuración:

```ini
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = app/api/faacil-facial-recognition-firebase-adminsdk.json
FIREBASE_PROJECT_ID = faacil-facial-recognition

# Umbral para distancia Euclidiana (L2 Norm). 
# 1.0 es el valor estándar para FaceNet 512 cuantizado.
CONFIDENCE_THRESHOLD = 1.0
```

### 4. Ejecución del Servidor local

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Endpoints Principales

`POST /register`: Recibe una imagen (multipart/form-data), extrae el vector facial y lo almacena en Firestore si no
existe un duplicado.

`POST /login`: Recibe una imagen, extrae el vector y lo compara con todos los usuarios registrados usando distancia
Euclidiana. Retorna el ID del usuario y su embedding actualizado si hay coincidencia.

La API estará disponible en `http://127.0.0.1:8000`.

## Despliegue en Google Cloud Run

El proyecto está configurado para desplegarse como un contenedor en Cloud Run.

### 1. Construcción de la Imagen (Cloud Build)

Para una compilación sin problemas por dependencias nativas (dlib, OpenCV), se recomienda desplegar en Cloud Run usando
el Dockerfile incluido.
El archivo de configuración `app/api/faacil-facial-recognition-firebase-adminsdk.json` debe estar para no tener fallas.
Estos pasos construyen la imagen con Docker (Cloud Build) y despliegan en Cloud Run usando ese JSON mediante variables
de entorno.

1) Autenticación y proyecto

```bash
gcloud auth login
gcloud config set project faacil
```

2) Habilitar APIs necesarias (si aún no están habilitadas)

```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com
```

3) Construir la imagen con Cloud Build

```bash
gcloud builds submit --tag gcr.io/faacil/facial-recognition-api
```

4) Desplegar en Cloud Run incluyendo las variables de entorno y la ruta al JSON de Firebase

```bash
gcloud run deploy facial-recognition-api \
  --image gcr.io/faacil/facial-recognition-api \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --port 8080 \
  --memory 1Gi \
  --set-env-vars \
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=app/api/faacil-facial-recognition-firebase-adminsdk.json,\
FIREBASE_PROJECT_ID=faacil-facial-recognition,\
CONFIDENCE_THRESHOLD=0.6
```

5) Abrir en el navegador

```bash
gcloud run services describe facial-recognition-api --region <REGION> --format 'value(status.url)'
```

### 2. Ejecutar localmente con Docker

```bash
docker build -t facial-recognition-api .
docker run --rm -p 8080:8080 \
  -e FIREBASE_SERVICE_ACCOUNT_KEY_PATH=app/api/faacil-facial-recognition-firebase-adminsdk.json \
  -e FIREBASE_PROJECT_ID=faacil-facial-recognition \
  -e CONFIDENCE_THRESHOLD=0.6 \
  facial-recognition-api
```

La API estará en http://localhost:8080

### 3. Endpoints de la API

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
    "message": "Login exitoso.",
    "embedding": []
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

## Detalles del Pipeline de ML

Para garantizar la consistencia entre el backend y el cliente móvil, se sigue estrictamente el siguiente proceso:

1. **Preprocesamiento:**
    - Detección de rostro y obtención de landmarks.
    - Recorte (Cropping) del área facial.
    - Redimensionamiento a 160x160 píxeles.
    - Estandarización (Whitening): `(x - mean) / std`.
2. **Inferencia:**
    - Modelo: `facenet_512.tflite` (Inception ResNet v1).
    - Salida: Vector de 512 flotantes.
3. **Post-procesamiento:**
    - Normalización L2 del vector resultante.

## Documentación de la API

Una vez que la aplicación esté en funcionamiento, se puede acceder a la documentación interactiva de la API a traves de
los siguientes enlaces:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

Desde la interfaz de Swagger, se pueden probar los endpoints directamente desde el navegador.

### Opción alternativa: usar cloudbuild.yaml (build y deploy en un solo comando)

Este repositorio incluye un archivo `cloudbuild.yaml` que automatiza el build y deploy a Cloud Run.

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_SERVICE=facial-recognition-api \
  .
```

- Por defecto, el pipeline despliega con las variables de entorno:
    - `FIREBASE_SERVICE_ACCOUNT_KEY_PATH=app/api/faacil-facial-recognition-firebase-adminsdk.json`
    - `FIREBASE_PROJECT_ID=faacil-facial-recognition`
    - `CONFIDENCE_THRESHOLD=0.6`
- Se pueden cambiar editando `cloudbuild.yaml` o sobreescribiendo `_ENV_VARS` en substitutions.

Notas importantes:

- Cloud Run ejecuta el contenedor escuchando en el puerto 8080, que ya está configurado en el Dockerfile.
- Si es necesario mantener el JSON de credenciales fuera de la imagen, se puede usar Secret Manager y montar el secreto
  como variable o archivo; ajusta `--set-env-vars` o usa `--set-secrets` en `gcloud run deploy`.

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
