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
    async def close(cls):
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


@app.post("/comments/create", status_code=201, response_model=output.CensoredComment, responses={404: {"model": output.Error}, 500: {"model": output.Error}, 400: {"model": output.Error}})
async def create_comment(comment: input.CreateComment):
    # check if customer has stayed (only customers that stayed are allowed to comment)
    async with HttpClient.get_client().post("http://appointments:5000/stayed", json={"groomerName": comment.groomerName, "userName": comment.userName}) as resp:
        if not resp.ok:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    # censor and post the comment
    async with HttpClient.get_client().post("http://comments:5000/", json=vars(comment)) as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/checkout", status_code=200, response_model=output.Checkout, responses={404: {"model": output.Error}, 500: {"model": output.Error}, 400: {"model": output.Error}})
async def checkout(checkout: input.Checkout):
    # check if groomer accepts the pets specified by the customer and return pricing info of the groomer
    async with HttpClient.get_client().post(f"http://groomer:5000/accepts/{checkout.groomerName}", json={"petTypes": list(map(lambda x: x.petType, checkout.pets))}) as resp:
        json = await resp.json()
        if resp.ok:
            price_tiers = json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    # check and add capacity
    async with HttpClient.get_client().post("http://appointments:5000/checkadd", json={"groomerName": checkout.groomerName, "startTime": checkout.startTime, "endTime": checkout.endDate, "quantity": len(checkout.pets)}) as resp:
        json = await resp.json()
        if resp.ok:
            number_of_days = json["dayLength"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    # create appointment entry
    async with HttpClient.get_client().post("http://appointments:5000/create", json={"groomerName": checkout.groomerName, "userName": checkout.userName, "petInfo": checkout.pets}) as resp:
        json = await resp.json()
        if resp.ok:
            appointment_id = json["id"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    pricing = price_tiers[checkout.priceTier]
    # get stripe payment URL
    async with HttpClient.get_client().post("http://stripe:5000/create-checkout-session", json={"packages": [{"price_id": pricing, "quantity": number_of_days}]}) as resp:
        json = await resp.json()
        if resp.ok:
            checkout_url = json["checkout_url"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail="internal server error")
    return {"checkoutUrl": checkout_url, "appointmentId": appointment_id}
