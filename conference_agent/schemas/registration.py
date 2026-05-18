from pydantic import BaseModel


class RegistrationData(BaseModel):
    """Output of Prompt B (registration page)."""

    covers_accommodation: bool
