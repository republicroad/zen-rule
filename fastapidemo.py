from typing import Union
from fastapi import FastAPI, Request
app = FastAPI()


@app.get("/", tags=["test"]) 
@app.put("/", tags=["test"]) 
@app.post("/", tags=["test"]) 
def mytest(request: Request):
    return {"Hello": "World", "http_method": request.method}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}







