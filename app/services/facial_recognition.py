import face_recognition
import numpy as np
from fastapi import UploadFile, HTTPException, status
from typing import List
import cv2


async def image_to_np_array(image_file: UploadFile) -> np.ndarray:
    """
    Convierte un archivo de imagen cargado en un array de NumPy.

    Args:
        image_file (UploadFile): El archivo de imagen cargado.

    Returns:
        np.ndarray: La imagen como un array de NumPy en formato BGR.

    Raises:
        HTTPException: Si el formato de la imagen no es válido.
    """
    contents = await image_file.read()
    nparr = np.fromstring(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format.",
        )
    return img


def get_face_encodings(image: np.ndarray) -> List[np.ndarray]:
    """
    Extrae las codificaciones faciales de una imagen.

    Args:
        image (np.ndarray): La imagen como un array de NumPy.

    Returns:
        List[np.ndarray]: Una lista de codificaciones faciales (vectores).

    Raises:
        HTTPException: Si no se detectan rostros o se detectan múltiples rostros.
    """
    # Convertir la imagen de BGR (OpenCV) a RGB (face_recognition)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_image)

    if not face_locations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the image.",
        )

    if len(face_locations) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple faces detected in the image. Please upload an image with a single face.",
        )

    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    return face_encodings


def compare_faces(
        known_encodings: List[np.ndarray],
        face_encoding_to_check: np.ndarray,
        tolerance: float = 0.6,
) -> bool:
    """
    Compara una codificación facial con una lista de codificaciones conocidas.

    Args:
        known_encodings (List[np.ndarray]): Una lista de codificaciones faciales conocidas.
        face_encoding_to_check (np.ndarray): La codificación facial a verificar.
        tolerance (float, optional): La distancia para considerar una coincidencia. Por defecto es 0.6.

    Returns:
        bool: True si se encuentra una coincidencia, False en caso contrario.
    """
    matches = face_recognition.compare_faces(
        known_encodings, face_encoding_to_check, tolerance=tolerance
    )
    return any(matches)
