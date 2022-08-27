# import uvicorn
from fastapi import Body, FastAPI

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter
from tasks import add

app = FastAPI()

app.include_router(sensorsRouter)
app.include_router(sensorsTypesRouter)
app.include_router(sensorSummariesRouter)


@app.get("/")
async def root():
    message = "test"
    return {"message": message}


# {"x": 100, "y": 123}
@app.post("/ex1")
def run_task(data=Body(...)):
    x = data["x"]
    y = data["y"]
    task = add.delay(x, y)
    return {"result": task.get()}


# this is for testing purposes only
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
