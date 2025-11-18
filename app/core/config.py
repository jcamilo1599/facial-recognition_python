from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Configuraciones de la aplicación, cargadas desde variables de entorno.
    """

    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = "app/api/faacil-facial-recognition-firebase-adminsdk.json"
    FIREBASE_PROJECT_ID: str = "faacil-facial-recognition"

    # El umbral de similitud para considerar dos rostros como una coincidencia.
    CONFIDENCE_THRESHOLD: float = 0.6

    class Config:
        env_file = ".env"

    def get_firebase_key_path(self) -> str:
        """
        Devuelve la ruta absoluta del archivo de credenciales de Firebase.
        """

        project_root = Path(__file__).parent.parent.parent
        return str(project_root / self.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)


settings = Settings()
