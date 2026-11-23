import os
from dotenv import load_dotenv
load_dotenv()


def require(envName:str) -> str:
    value = os.getenv(envName)
    
    if not value:
        raise ValueError(f"{envName} is missing from your .env file!")
    return value


class Settings:
    
