from os import environ as env

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status  # TODO remove body
from mangum import Mangum

from routers.bgtasks import backgroundTasksRouter

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter

load_dotenv()

description = """
Aston Air Quality API helps you do awesome stuff. 🚀

## Sensors

You can **read sensors**.
You can **create sensors**.
You can **update sensors**.
You can **delete sensors**.

## Sensor Summaries

You can **read sensor summaries**.
You can **create sensor summaries**.
You can **update sensor summaries**.
* **delete sensor summaries** (_not implemented_).

## Sensor Types

You can **read sensor types**.
You can **create sensor types**.
* **update sensor types** (_not implemented_).
* **delete sensor types** (_not implemented_).

## Users (_not implemented_).

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="Aston Air Quality API",
    description=description,
)

app.include_router(sensorsRouter, prefix="/sensor", tags=["sensor"])
app.include_router(sensorsTypesRouter, prefix="/sensorType", tags=["sensorType"])
app.include_router(sensorSummariesRouter, prefix="/sensorSummary", tags=["sensorSummary"])
app.include_router(backgroundTasksRouter, prefix="/api-task", tags=["api-task"])


# # TODO remove this
# @app.get("/sentry-debug")
# async def trigger_error():
#     division_by_zero = 1 / 0


@app.get("/")
async def root():
    message = "test"
    return {"message": message}


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
