# import uvicorn
from fastapi import FastAPI

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter

# from fastapi_sqlalchemy import DBSessionMiddleware, db  # TODO uninstall

app = FastAPI()

# app.add_middleware(DBSessionMiddleware, db_url=env["DATABASE_URL"])
app.include_router(sensorsRouter)
app.include_router(sensorsTypesRouter)
app.include_router(sensorSummariesRouter)


@app.get("/")
async def root():
    message = "test"
    return {"message": message}


# this is for testing purposes only
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
