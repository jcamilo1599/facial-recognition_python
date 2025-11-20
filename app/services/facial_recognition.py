from typing import List

import cv2
import face_recognition
import numpy as np
import tensorflow as tf
from fastapi import UploadFile, HTTPException, status

# Configuración del modelo TFLite
# Se utiliza la versión 512-D (Inception ResNet) para máxima precisión
MODEL_PATH = "app/models/facenet_512.tflite"
interpreter = None

try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"Modelo TFLite cargado desde {MODEL_PATH}")
except Exception as e:
    print(f"Error cargando modelo TFLite: {e}")


async def image_to_np_array(image_file: UploadFile) -> np.ndarray:
    """
    Convierte un archivo de imagen cargado en un array de NumPy.
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


def preprocess_for_facenet(face_image: np.ndarray) -> np.ndarray:
    """
    Preprocesa el recorte del rostro para el modelo FaceNet TFLite.
    Replica la lógica de Android: Cambiar tamaño a 160x160 + Standardization.
    """

    # Cambiar tamaño
    img = cv2.resize(face_image, (160, 160))

    # Convertir a float32
    img = img.astype(np.float32)

    # Estandarización (Whitening)
    mean = np.mean(img)
    std = np.std(img)
    std = max(std, 1.0 / np.sqrt(img.size))
    img = (img - mean) / std

    # Expandir dimensiones (Batch size = 1)
    img = np.expand_dims(img, axis=0)
    return img


def get_face_encodings(image: np.ndarray) -> List[np.ndarray]:
    """
    Extrae las codificaciones faciales usando FaceNet TFLite.
    Usa face_recognition solo para detectar y recortar el rostro.
    """
    # Convertir a RGB para detección
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detectar rostros
    face_locations = face_recognition.face_locations(rgb_image)

    if not face_locations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the image.",
        )

    if len(face_locations) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple faces detected. Please upload an image with a single face.",
        )

    # Tomar el primer rostro
    top, right, bottom, left = face_locations[0]

    # Recortar el rostro (usando la imagen RGB)
    face_image = rgb_image[top:bottom, left:right]

    # Generar embedding con TFLite
    if interpreter is None:
        raise HTTPException(status_code=500, detail="Model not initialized")

    input_data = preprocess_for_facenet(face_image)

    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()
    embedding = interpreter.get_tensor(output_details[0]["index"])[0]

    # Normalización L2 (Euclidiana)
    # Crucial para que la distancia tenga sentido y el umbral sea estable (0.0 a 2.0)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return [embedding]


def compare_faces(
    known_encodings: List[np.ndarray],
    face_encoding_to_check: np.ndarray,
    tolerance: float = 1.0,  # Umbral estándar para vectores normalizados (0.8 - 1.2)
) -> bool:
    """
    Compara embeddings usando distancia euclidiana.
    """
    for known_encoding in known_encodings:
        # Calcular distancia euclidiana
        distance = np.linalg.norm(known_encoding - face_encoding_to_check)
        print(f"Distancia calculada: {distance}")

        if distance <= tolerance:
            return True

    return False
