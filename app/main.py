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
* **read sensors**.
* **create sensors**.
* **update sensors**.
* **delete sensors**.

## Sensor Summaries

You can:
* **read sensor summaries**.
* **create sensor summaries**.
* **update sensor summaries**.
* **delete sensor summaries** (_not implemented_).

## Sensor Types

You can:
* **read sensor types**.
* **create sensor types**.
* **update sensor types**.
* **delete sensor types**.

## Users.
You will be able to:

You can:
* **read users**.
* **create users**.

"""

stage = env.get("AWS_STAGE_NAME", None)
openapi_prefix = f"/{stage}" if stage else "/"

app = FastAPI(title="Aston Air Quality API", description=description, root_path=openapi_prefix)


app.include_router(sensorsRouter, prefix="/sensor", tags=["sensor"])
app.include_router(sensorsTypesRouter, prefix="/sensorType", tags=["sensorType"])
app.include_router(sensorSummariesRouter, prefix="/sensorSummary", tags=["sensorSummary"])
app.include_router(backgroundTasksRouter, prefix="/api-task", tags=["api-task"])
app.include_router(usersRouter, prefix="/user", tags=["user"])
app.include_router(logsRouter, prefix="/log", tags=["log"])
app.include_router(authRouter, prefix="/auth", tags=["auth"])


# # TODO docs issue: openapi.json is being nested in a path (e.g. /prod/prod/openapi.json)

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
