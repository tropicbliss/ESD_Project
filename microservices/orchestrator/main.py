from fastapi import FastAPI, HTTPException
import input
import output
from aiographql.client import GraphQLClient
from aiohttp import ClientSession, ClientTimeout
from typing import Optional
from contextlib import asynccontextmanager


graphql_client = GraphQLClient(
    endpoint="http://user:5000/"
)


class HttpClient:
    aiohttp_client: Optional[ClientSession] = None

    @classmethod
    def get_client(cls) -> ClientSession:
        if cls.aiohttp_client is None:
            cls.aiohttp_client = ClientSession(timeout=ClientTimeout(total=9))
        return cls.aiohttp_client

    @classmethod
    async def close(cls) -> ClientSession:
        if cls.aiohttp_client is not None:
            await cls.aiohttp_client.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await HttpClient.close()

app = FastAPI(lifespan=lifespan)


@app.post("/user/create", status_code=201, responses={400: {"model": output.Error}})
async def create_user(user: input.CreateUser):
    query = """
    mutation {{
        createUser(name: "{name}", contactNo: "{contact_no}", email: "{email}")
    }}
    """.format(name=user.name, contact_no=user.contactNo, email=user.email)
    res = await graphql_client.query(query)
    is_error = "errors" in res.json
    if is_error:
        return HTTPException(
            status_code=400, detail=res.json["errors"][0]["message"])


@app.get("/user/read/{name}", status_code=200, response_model=output.ReadUser, responses={404: {"model": output.Error}})
async def get_user(name: str):
    query = """
    query {{
        getUser(name: "{name}") {{
            name,
            contactNo,
            email
        }}
    }}
    """.format(name=name)
    res = await graphql_client.query(query)
    res = res.json["data"]["getUser"]
    if res == None:
        raise HTTPException(
            status_code=404, detail="user not found")
    else:
        return res


@app.post("/user/update/{name}", status_code=200, responses={404: {"model": output.Error}})
async def update_user(name: str, info: input.UpdateUser):
    if info.contactNo != None:
        info.contactNo = f"\"{info.contactNo}\""
    else:
        info.contactNo = "null"
    if info.email != None:
        info.email = f"\"{info.email}\""
    else:
        info.email = "null"
    query = """
    mutation {{
        updateUser(name: "{name}", contactNo: {contact_no}, email: {email})
    }}
    """.format(name=name, contact_no=info.contactNo, email=info.email)
    res = await graphql_client.query(query)
    res = res.json
    if res["data"] == None:
        raise HTTPException(
            status_code=404, detail=res["errors"][0]["message"])


@app.post("/groomer/create", status_code=201, responses={400: {"model": output.Error}})
async def create_groomer(groomer: input.CreateGroomer):
    async with HttpClient.get_client().post("http://groomer:5000/create", json=vars(groomer)) as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/groomer/search/keyword/{keyword}", status_code=200, response_model=list[output.Groomer], responses={404: {"model": output.Error}, 400: {"model": output.Error}})
async def search_groomer_by_keyword(keyword: str):
    async with HttpClient.get_client().get(f"http://groomer:5000/search/keyword/{keyword}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/groomer/search/name/{name}", status_code=200, response_model=output.Groomer, responses={404: {"model": output.Error}, 400: {"model": output.Error}})
async def get_groomer_by_name(name: str):
    async with HttpClient.get_client().get(f"http://groomer:5000/search/name/{name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/groomer/update/{name}", status_code=200, responses={400: {"model": output.Error}})
async def update_groomer(name: str, updated: input.UpdateGroomer):
    async with HttpClient.get_client().post(f"http://groomer:5000/update/{name}", json=vars(updated)) as resp:
        if resp.ok:
            return
        else:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/groomer/read", status_code=200, response_model=output.Groomer, responses={400: {"model": output.Error}})
async def read_groomer(filters: input.ReadGroomer):
    async with HttpClient.get_client().post("http://groomer:5000/read", json=vars(filters)) as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/capacity/check/{groomer_name}", status_code=200, response_model=list[output.FutureCapacity], responses={500: {"model": output.Error}, 404: {"model": output.Error}})
async def get_future_capacities(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/check/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/comments/read/{groomer_name}", status_code=200, response_model=list[output.Comment], responses={500: {"model": output.Error}, 404: {"model": output.Error}})
async def get_comments(groomer_name: str):
    async with HttpClient.get_client().get(f"http://comments:5000/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/user/{user_name}", status_code=200, response_model=list[output.Appointment], responses={500: {"model": output.Error}, 404: {"model": output.Error}})
async def get_appointments_of_user(user_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/user/{user_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/signin/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}})
async def get_arriving_customers(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/signin/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/staying/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}})
async def get_staying_customers(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/staying/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/appointments/status/{appointment_id}", status_code=200, responses={400: {"model": output.Error}, 500: {"model": output.Error}, 404: {"model": output.Error}})
async def change_appointment_status(appointment_id: str, status: input.Status):
    async with HttpClient.get_client().post(f"http://appointments:5000/status/{appointment_id}", json=vars(status)) as resp:
        if resp.ok:
            return
        else:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
