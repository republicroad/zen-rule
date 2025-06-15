from typing import Union
from fastapi import FastAPI, Request
from pydantic import BaseModel
import psycopg

# https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
# https://www.psycopg.org/psycopg3/docs/api/conninfo.html
# https://www.psycopg.org/psycopg3/docs/basic/usage.html
# psql -U u1 -h 41e1af074877.c.methodot.com -p 30290 -d chinook ​1234qwer
# conn = psycopg.connect("dbname=test user=postgres")
conn = psycopg.connect(
                    host="41e1af074877.c.methodot.com",
                    port=30290,
                    dbname="chinook",
                    user="u1",
                    password="1234qwer")


app = FastAPI()

class Customer(BaseModel):
    # 定义客户模型用于插入数据和修改数据.
    customer_id: int
    first_name: str
    last_name: str
    company: str
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    phone: str
    fax:str
    email: str


@app.get("/customer/{item_id}", tags=["customer"])
def get_customer(item_id: int):
    cur = conn.cursor()
    cur.execute("select * from customer where customer_id=%s;", [item_id])
    res = cur.fetchone()
    cur.close()
    return {"Hello": "World", "customer": res}


@app.patch("/customer/{item_id}", tags=["customer"])
def patch_customer(item_id: int):
    cur = conn.cursor()
    cur.execute("update customer set item_id=%s", [item_id])
    res = cur.fetchone()
    cur.close()
    return {"Hello": "World", "customer": res}


@app.post("/customer", tags=["customer"])
def post_customer(customer: Customer):
    cur = conn.cursor()
    ## 下次讲 数据库的插入和修改. 大家可以提前预习.
    cur.close()
    return {"Hello": "World"}

