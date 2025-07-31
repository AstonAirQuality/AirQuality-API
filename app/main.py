from os import environ as env

from docsMarkdown import description, tags_metadata
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from mangum import Mangum
from middleware.file_check import FileSizeLimitMiddleware
from routers.auth import authRouter
from routers.bgtasks import backgroundTasksRouter
from routers.logs import logsRouter
from routers.sensors import sensorsRouter
from routers.sensorSummaries import sensorSummariesRouter
from routers.sensorTypes import sensorsTypesRouter
from routers.users import usersRouter

load_dotenv()

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

origins = ["*"]
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(FileSizeLimitMiddleware)


@app.get("/")
async def root():
    return {"message": "Greetings from the Aston Air Quality API. 🚀"}


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
