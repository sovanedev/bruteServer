from pydantic import BaseModel, Field

class InstallHash(BaseModel):
    id: str
    hash: str
    hash_type: int
    dest: str = Field("~/worker/hashes/")