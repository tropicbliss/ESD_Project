from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import input
import output
from aiographql.client import GraphQLClient

app = FastAPI()


# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None


# @app.get("/")
# async def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}

graphql_client = GraphQLClient(
    endpoint="http://127.0.0.1:3000/"
)


@app.post("/user/create", status_code=201)
async def create_user(user: input.CreateUser):
    query = """
    mutation {{
        createUser(name: "{name}", contactNo: "{contact_no}", email: "{email}")
    }}
    """.format(name=user.name, contact_no=user.contactNo, email=user.email)
    res = await graphql_client.query(query)
    is_error = "errors" in res.json
    if is_error:
        raise HTTPException(
            status_code=400, detail=res.json["errors"][0]["message"])
