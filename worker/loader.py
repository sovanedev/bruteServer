from fastapi import FastAPI
from worker.database import Storage

app = FastAPI()
storage = Storage()