from fastapi import FastAPI, HTTPException, status  # TODO remove body

from routers.celerytasks import celeryTasksRouter

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter

app = FastAPI()

app.include_router(sensorsRouter)
app.include_router(sensorsTypesRouter)
app.include_router(sensorSummariesRouter)
app.include_router(celeryTasksRouter)


@app.get("/")
async def root():
    message = "test"
    return {"message": message}


# TODO add login and auth


# this is for testing purposes only
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
