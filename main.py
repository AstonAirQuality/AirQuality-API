# sentry dependancies
from os import environ as env

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status  # TODO remove body

from routers.bgtasks import backgroundTasksRouter

# routers
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter

load_dotenv()

app = FastAPI()

app.include_router(sensorsRouter)
app.include_router(sensorsTypesRouter)
app.include_router(sensorSummariesRouter)
app.include_router(backgroundTasksRouter)


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


# this is for testing purposes only
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
