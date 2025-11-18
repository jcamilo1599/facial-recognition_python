import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any
import numpy as np
from app.core.config import settings
import uuid

db = None


def initialize_firebase():
    """
    Inicializa la conexión con Firebase Firestore.
    Utiliza la clave de la cuenta de servicio especificada en la configuración.
    """

    global db

    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.get_firebase_key_path())

            # Para Firestore, solo necesitamos las credenciales
            firebase_admin.initialize_app(cred)
            db = firestore.client()

            print("Firebase Firestore initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise


def save_user(face_encodings: List[np.ndarray]) -> str:
    """
    Guarda un nuevo usuario en la base de datos con sus codificaciones faciales.

    Args:
        face_encodings (List[np.ndarray]): Una lista de codificaciones faciales para el nuevo usuario.

    Returns:
        str: El ID del usuario recién creado.

    Raises:
        ConnectionError: Si Firebase no está inicializado.
        ValueError: Si no se proporcionan codificaciones faciales.
    """

    if db is None:
        raise ConnectionError(
            "Firebase not initialized. Call initialize_firebase() first."
        )

    if not face_encodings:
        raise ValueError("No face encodings provided")

    user_id = str(uuid.uuid4())

    # Tomar el primer encoding y convertirlo a formato compatible con Firestore
    first_encoding = face_encodings[0]

    if isinstance(first_encoding, np.ndarray):
        encoding_list = [float(x) for x in first_encoding.tolist()]
    else:
        encoding_list = [float(x) for x in first_encoding]

    user_data = {
        "user_id": user_id,
        "encoding": encoding_list
    }

    try:
        user_ref = db.collection("users").document(user_id)
        user_ref.set(user_data)
        return user_id
    except Exception as e:
        print(f"Error saving user to Firestore: {str(e)}")
        raise


def get_all_users() -> List[Dict[str, Any]]:
    """
    Obtiene todos los usuarios registrados y sus codificaciones faciales de la base de datos.

    Returns:
        List[Dict[str, Any]]: Una lista de diccionarios, donde cada diccionario representa a un usuario
                              y contiene su ID y sus codificaciones faciales.
    """

    if db is None:
        raise ConnectionError(
            "Firebase not initialized. Call initialize_firebase() first."
        )

    users_ref = db.collection("users")
    docs = users_ref.stream()

    users = []
    for doc in docs:
        user_data = doc.to_dict()

        # Adaptar tanto la estructura antigua como la nueva
        if "encoding" in user_data:
            # Nueva estructura: un solo encoding
            user_data["face_encodings"] = [np.array(user_data["encoding"])]
        elif "face_encodings" in user_data:
            # Estructura antigua: múltiples encodings
            user_data["face_encodings"] = [
                np.array(encoding) for encoding in user_data.get("face_encodings", [])
            ]
        else:
            # Datos corruptos, saltar
            continue

        users.append(user_data)

    return users
