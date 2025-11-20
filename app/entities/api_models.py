from pydantic import BaseModel


class UserResponse(BaseModel):
    """
    Modelo de respuesta para operaciones de usuario exitosas.
    """

    user_id: str
    message: str
    embedding: list[float] | None = None


class ErrorResponse(BaseModel):
    """
    Modelo de respuesta para errores.
    """

    error: str
