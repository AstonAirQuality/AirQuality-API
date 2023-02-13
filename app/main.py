from math import fabs
from os import environ as env

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routers.bgtasks import backgroundTasksRouter
from routers.firebaseAuth import authRouter
from routers.logs import logsRouter

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter
from routers.users import usersRouter

load_dotenv()

description = """
Aston Air Quality API helps you do awesome stuff. 🚀

## Sensors
You can:
* **Create sensors**.
* **Read sensors**.
* **Update sensors**.
* **Delete sensors**.

## Sensor Summaries
You can:
* **read sensor summaries**.

## Sensor Types
You can:
* **Create sensor types**.
* **Read sensor types**.
* **Update sensor types**.
* **Delete sensor types**.

## Users.
You can:
* **read users**.
* **create users**.

## Logs.
You can:
* **read logs**.
* **delete logs**.

## Auth
You can:
* **signin**.
* **signup**.
* **firebase login**.
* **firebase register**.
* **delete account**.
"""

tags_metadata = [
    {
        "name": "auth",
        "description": "Firebase authentication.",
    },
    {
        "name": "sensor",
        "description": "Operations with sensors.",
    },
    {
        "name": "sensor-type",
        "description": "Operations with sensor types.",
    },
    {
        "name": "sensor-summary",
        "description": "Operations with sensor summaries.",
    },
    {
        "name": "api-task",
        "description": "Operations with background tasks.",
    },
    {
        "name": "user",
        "description": "Operations with users.",
    },
    {
        "name": "data-ingestion-logs",
        "description": "Operations with logs.",
    },
]

stage = env.get("AWS_STAGE_NAME", None)
openapi_prefix = f"/{stage}" if stage else "/"

app = FastAPI(title="Aston Air Quality API", openapi_tags=tags_metadata, description=description, root_path=openapi_prefix)

app.include_router(authRouter, prefix="/auth", tags=["auth"])
app.include_router(sensorsRouter, prefix="/sensor", tags=["sensor"])
app.include_router(sensorsTypesRouter, prefix="/sensor-type", tags=["sensor-type"])
app.include_router(sensorSummariesRouter, prefix="/sensor-summary", tags=["sensor-summary"])
app.include_router(backgroundTasksRouter, prefix="/api-task", tags=["api-task"])
app.include_router(usersRouter, prefix="/user", tags=["user"])
app.include_router(logsRouter, prefix="/data-ingestion-logs", tags=["data-ingestion-logs"])


# TODO change this to a more secure origin
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# setting up sentry
if env["PRODUCTION_MODE"] == "TRUE":
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=env["FASTAPI_SENTRY_DSN"],
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=env["FASTAPI_SENTRY_SAMPLE_RATE"],
    )

handler = Mangum(app=app)
# this is for testing purposes only
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
