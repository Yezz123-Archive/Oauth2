from fastapi import FastAPI
from core import Oauth2
from model import models
from database.database import engine

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title='Oauth2',
    version='0.0.1',
    description='PlayGround with JWTs used as OAuth 2.0 Bearer Tokens to encode all relevant parts of an access token into the access token itself instead of storing them in a database.',
)

app.include_router(Oauth2.router)


@app.get("/")
def index():
    return {"PlayGround": "Oauth2"}
