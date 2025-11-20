from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.services.database import initialize_firebase, save_user, get_all_users
from app.core.config import settings
from app.entities.api_models import UserResponse, ErrorResponse
from app.services.facial_recognition import image_to_np_array, get_face_encodings, compare_faces


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja los eventos del ciclo de vida de la aplicación.
    """

    # Startup: se ejecuta cuando la aplicación se inicia
    initialize_firebase()
    print("Application startup complete")
    yield

    # Shutdown: se ejecuta cuando la aplicación se cierra (si es necesario)
    print("Application shutdown")


# Crear una instancia de la aplicación FastAPI
app = FastAPI(
    title="API de Reconocimiento Facial",
    description="Una API para registrar y autenticar usuarios mediante reconocimiento facial.",
    version="1.0.0",
    lifespan=lifespan,
)


# Endpoint de registro de usuario
@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Sube una imagen de un rostro para registrar un nuevo usuario. El sistema verificará si el rostro ya está registrado para evitar duplicados.",
    responses={
        201: {"description": "Usuario registrado exitosamente."},
        400: {
            "model": ErrorResponse,
            "description": "Error en la solicitud (ej. no se detectó rostro, múltiples rostros, formato de imagen inválido).",
        },
        409: {"model": ErrorResponse, "description": "El usuario ya está registrado."},
    },
)
async def register(file: UploadFile = File(...)):
    """
    Maneja el registro de un nuevo usuario.

    - **file**: Archivo de imagen que contiene el rostro del usuario.

    El proceso implica:
    1. Convertir la imagen a un formato utilizable.
    2. Extraer la codificación facial de la imagen.
    3. Comparar la codificación con las existentes en la base de datos para evitar duplicados.
    4. Si el usuario es nuevo, se guarda en la base de datos.
    """

    try:
        image = await image_to_np_array(file)
        new_face_encodings = get_face_encodings(image)

        if not new_face_encodings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo extraer la codificación facial de la imagen.",
            )

        new_face_encoding = new_face_encodings[0]

        all_users = get_all_users()
        for user in all_users:
            if compare_faces(
                    user["face_encodings"], new_face_encoding, settings.CONFIDENCE_THRESHOLD
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este rostro ya ha sido registrado.",
                )

        user_id = save_user([new_face_encoding])

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"user_id": user_id, "message": "Usuario registrado exitosamente."},
        )

    except PermissionError as e:
        # Errores de permisos en Firestore: 403
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"error": str(e)}
        )
    except ConnectionError as e:
        # Firebase no inicializado u otros problemas de conexión: 503
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"error": str(e)}
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Ocurrió un error inesperado: {str(e)}"},
        )


# Endpoint de login de usuario
@app.post(
    "/login",
    response_model=UserResponse,
    summary="Autenticar un usuario",
    description="Sube una imagen de un rostro para autenticar a un usuario. El sistema buscará una coincidencia en la base de datos.",
    responses={
        200: {"description": "Usuario autenticado exitosamente."},
        400: {
            "model": ErrorResponse,
            "description": "Error en la solicitud (ej. no se detectó rostro, múltiples rostros).",
        },
        401: {
            "model": ErrorResponse,
            "description": "Autenticación fallida. Rostro no reconocido.",
        },
    },
)
async def login(file: UploadFile = File(...)):
    """
    Maneja la autenticación de un usuario.

    - **file**: Archivo de imagen que contiene el rostro del usuario para el login.

    El proceso implica:
    1. Extraer la codificación facial de la imagen proporcionada.
    2. Comparar esta codificación con todas las codificaciones de usuarios registrados.
    3. Si se encuentra una coincidencia con suficiente confianza, se autentica al usuario.
    """
    try:
        image = await image_to_np_array(file)
        login_face_encodings = get_face_encodings(image)

        if not login_face_encodings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo extraer la codificación facial de la imagen.",
            )

        login_face_encoding = login_face_encodings[0]

        all_users = get_all_users()
        for user in all_users:
            known_encodings = user["face_encodings"]

            if compare_faces(known_encodings, login_face_encoding, settings.CONFIDENCE_THRESHOLD):
                embedding_list = known_encodings[0].tolist()
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "user_id": user["user_id"],
                        "message": "Login exitoso.",
                        "embedding": embedding_list,
                    },
                )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación fallida. Rostro no reconocido.",
        )

    except PermissionError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"error": str(e)}
        )
    except ConnectionError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"error": str(e)}
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Ocurrió un error inesperado: {str(e)}"},
        )


# Endpoint de health check
@app.get(
    "/health",
    summary="Verificar el estado de la API",
    description="Un endpoint simple para verificar si la API está en funcionamiento.",
    responses={200: {"description": "La API está funcionando correctamente."}},
)
def health_check():
    """
    Endpoint de verificación de estado.
    """
    return {"status": "👌"}
