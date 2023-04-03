from fastapi import FastAPI, HTTPException
import input
import output
from aiographql.client import GraphQLClient
from aiohttp import ClientSession, ClientTimeout
from typing import Optional
from contextlib import asynccontextmanager
import pika
import time
from starlette.responses import RedirectResponse

time.sleep(9)

# Making an API gateway-like microservice is not our initial intention, but it is our goal to provide user-friendly API docs in a single place
# Hence, the advantages of using an actual API gateway like Kong quickly becomes more murky

hostname = "esd-rabbit"
port = 5672

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port,
                              heartbeat=3600, blocked_connection_timeout=3600)
)

channel = connection.channel()
exchange_name = "main"
exchange_type = "topic"
channel.exchange_declare(exchange=exchange_name,
                         exchange_type=exchange_type, durable=True)

queue_name = "sms"
channel.queue_declare(queue=queue_name, durable=True)

channel.queue_bind(exchange=exchange_name,
                   queue=queue_name, routing_key="sms.*")

channel.basic_publish(exchange=exchange_name, routing_key="sms.user",
                      body="+6581650034", properties=pika.BasicProperties(delivery_mode=2))


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

app = FastAPI(lifespan=lifespan, root_path="/backend")


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
    else:
        channel.basic_publish(exchange=exchange_name, routing_key="sms.user",
                              body=user.contactNo, properties=pika.BasicProperties(delivery_mode=2))


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


@app.post("/user/update/{name}", status_code=200, responses={404: {"model": output.Error}}, description="None of the JSON fields are optional, you must send all the information together with the updated field to update an entry.")
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
        if resp.ok:
            channel.basic_publish(exchange=exchange_name, routing_key="sms.groomer",
                                  body=groomer.contactNo, properties=pika.BasicProperties(delivery_mode=2))
        else:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/groomer/search/keyword/{keyword}", status_code=200, response_model=list[output.Groomer], responses={404: {"model": output.Error}, 400: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def search_groomer_by_keyword(keyword: str):
    async with HttpClient.get_client().get(f"http://groomer:5000/search/keyword/{keyword}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/groomer/search/name/{name}", status_code=200, response_model=output.Groomer, responses={404: {"model": output.Error}, 400: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_groomer_by_name(name: str):
    async with HttpClient.get_client().get(f"http://groomer:5000/search/name/{name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/groomer/delete/{name}", status_code=200, responses={400: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def delete_groomer(name: str):
    async with HttpClient.get_client().get(f"http://groomer:5000/delete/{name}") as resp:
        if not resp.ok:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/groomer/update/{name}", status_code=200, responses={400: {"model": output.Error}}, description="All of the input fields are optional. If you want to search a keyword or name with a space, replace the space with %20")
async def update_groomer(name: str, updated: input.UpdateGroomer):
    async with HttpClient.get_client().post(f"http://groomer:5000/update/{name}", json=vars(updated)) as resp:
        if resp.ok:
            return
        else:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/groomer/read", status_code=200, response_model=output.GroomerRead, responses={400: {"model": output.Error}}, summary="Filter groomers by accepted pet type or get every single groomer", description="All of the input fields are optional. Send an empty JSON: `{}`, to get every single groomer.")
async def read_groomer(filters: input.ReadGroomer):
    async with HttpClient.get_client().post("http://groomer:5000/read", json=vars(filters)) as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/comments/read/{groomer_name}", status_code=200, response_model=list[output.Comment], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_comments(groomer_name: str):
    async with HttpClient.get_client().get(f"http://comments:5000/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/user/{user_name}", status_code=200, response_model=list[output.Appointment], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_appointments_of_user(user_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/user/{user_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/signin/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_arriving_customers(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/signin/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/staying/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_staying_customers(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/staying/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.get("/appointments/groomer/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_all_groomer_appointments(groomer_name: str):
    async with HttpClient.get_client().get(f"http://appointments:5000/groomer/{groomer_name}") as resp:
        json = await resp.json()
        if resp.ok:
            return json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/appointments/get/{groomer_name}", status_code=200, response_model=list[output.CustomerAppointments], responses={500: {"model": output.Error}, 404: {"model": output.Error}}, description="If you want to search a keyword or name with a space, replace the space with %20")
async def get_appointments_by_month(groomer_name: str, time: input.MonthYear):
    async with HttpClient.get_client().post(f"http://appointments:5000/get/{groomer_name}", json=vars(time)) as resp:
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


@app.post("/appointments/update/{groomer_name}", status_code=200, responses={404: {"model": output.Error}, 500: {"model": output.Error}, 400: {"model": output.Error}}, description="To send the time in Javascript, call `date.toISOString()` on a `Date` object. If you want to search a keyword or name with a space, replace the space with %20")
async def update_appointment_date(groomer_name: str, dates: input.AppointmentUpdate):
    async with HttpClient.get_client().post(f"http://appointments:5000/update/{groomer_name}", json=vars(dates)) as resp:
        if resp.ok:
            return
        else:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])


@app.post("/checkout", responses={404: {"model": output.Error}, 500: {"model": output.Error}, 400: {"model": output.Error}}, description="To send the time in Javascript, call `date.toISOString()` on a `Date` object.")
async def checkout(checkout: input.Checkout):
    # check if groomer accepts the pets specified by the customer and return pricing info of the groomer
    async with HttpClient.get_client().post(f"http://groomer:5000/accepts/{checkout.groomerName}", json={"petTypes": list(map(lambda x: x.petType, checkout.pets))}) as resp:
        json = await resp.json()
        if resp.ok:
            price_tiers = json
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    # get number of days
    async with HttpClient.get_client().post("http://appointments:5000/quantity", json={"startTime": checkout.startTime, "endTime": checkout.endTime}) as resp:
        json = await resp.json()
        if resp.ok:
            number_of_days = json["dayLength"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    pricing = price_tiers[checkout.priceTier]
    # get stripe payment URL (you may realise that we did not check whether the user has paid for the service, this is a limitation of our microservices being locally hosted, resulting in the Stripe servers not being able to contact this microservice)
    async with HttpClient.get_client().post("http://stripe:5000/create-checkout-session", json={"cust_checkout": [{"price_id": pricing, "quantity": number_of_days}]}) as resp:
        if resp.ok:
            json = await resp.json()
            checkout_url = json["checkout_url"]
            transaction_id = json["id"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail="internal server error")
    # create appointment entry
    async with HttpClient.get_client().post("http://appointments:5000/create", json={"groomerName": checkout.groomerName, "userName": checkout.userName, "petInfo": [vars(pet) for pet in checkout.pets], "priceTier": checkout.priceTier, "totalPrice": pricing * number_of_days, "startTime": checkout.startTime, "endTime": checkout.endTime, "transactionId": transaction_id}) as resp:
        if not resp.ok:
            json = await resp.json()
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    response = RedirectResponse(url=checkout_url)
    return response


@app.post("/refund", status_code=200, responses={404: {"model": output.Error}, 500: {"model": output.Error}, 400: {"model": output.Error}})
async def refund(appointment_id: str):
    # get the transaction id from the appointment id
    async with HttpClient.get_client().get(f"http://appointments:5000/transaction/{appointment_id}") as resp:
        json = await resp.json()
        if resp.ok:
            transaction_id = json["transactionId"]
        else:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
    # refund the customer
    async with HttpClient.get_client().post("http://stripe:5000/make-refund", json={"id": transaction_id}) as resp:
        if not resp.ok:
            raise HTTPException(status_code=resp.status,
                                detail="internal server error")
    # delete the appointment
    async with HttpClient.get_client().delete(f"http://appointments:5000/delete/{appointment_id}") as resp:
        if not resp.ok:
            raise HTTPException(status_code=resp.status,
                                detail=json["message"])
