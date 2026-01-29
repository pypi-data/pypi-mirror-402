from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, model_validator


class BillProfile(BaseModel):
    name: str = ""
    search_subject: str = ""
    sender_email: str = ""
    file_suffix: str = ""
    encoding: str = "utf-8"
    save_subdir: Path = Path.home() / ".flow" / "data"

    @model_validator(mode="after")
    def set_dynamic_path(self):
        if self.name:
            self.save_subdir = self.save_subdir / self.name
        return self


class AuthType(Enum):
    PASS = "pass"
    TOKEN = "token"


@dataclass
class Auth(BaseModel):
    username: str = ""
    password: str = ""
    token: str = ""


class PayConfig(BaseModel):
    email: str
    download: str
    auth_type: AuthType
    auth: Auth
    profile: BillProfile
