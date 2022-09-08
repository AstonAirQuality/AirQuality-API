from os import environ as env

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status  # TODO remove body
from mangum import Mangum

from routers.bgtasks import backgroundTasksRouter

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

if env.get("PRODUCTION_MODE") == "True":
    app = FastAPI(
        title="Aston Air Quality API",
        description=description,
        openapi_prefix="/{stage_name}".format(stage_name=env["AWS_STAGE_NAME"]),
    )
else:
    app = FastAPI(
        title="Aston Air Quality API",
        description=description,
        # openapi_prefix="/{stage_name}".format(stage_name=env["AWS_STAGE_NAME"]),
        # docs_url="/{stage_name}/docs".format(stage_name=env["AWS_STAGE_NAME"]),
        # redoc_url="/{stage_name}/redoc".format(stage_name=env["AWS_STAGE_NAME"]),
        # openapi_url="/{stage_name}/openapi.json".format(stage_name=env["AWS_STAGE_NAME"]),
    )

app.include_router(sensorsRouter, prefix="/sensor", tags=["sensor"])
app.include_router(sensorsTypesRouter, prefix="/sensorType", tags=["sensorType"])
app.include_router(sensorSummariesRouter, prefix="/sensorSummary", tags=["sensorSummary"])
app.include_router(backgroundTasksRouter, prefix="/api-task", tags=["api-task"])
app.include_router(usersRouter, prefix="/user", tags=["user"])


# # TODO remove this
# @app.get("/sentry-debug")
# async def trigger_error():
#     division_by_zero = 1 / 0


@app.get("/")
async def root():
    return {"message": "Hello World"}


# TODO add login and auth


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
