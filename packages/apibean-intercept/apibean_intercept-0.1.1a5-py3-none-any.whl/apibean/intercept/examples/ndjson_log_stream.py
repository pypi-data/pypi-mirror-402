from fastapi import FastAPI

from apibean.intercept.brokers.builder import InterceptBuilder
from apibean.intercept.recipes.dispatchers import NDJSONLogStreamDispatcher
from apibean.intercept.recipes.interceptors import NDJSONEnrichmentInterceptor

builder = InterceptBuilder(upstream_base="http://example.com")

def random_log(log):
    index = log.pop("index")
    log.update(
        level = "DEBUG",
        message = f"log message #{ index }",
    )
    return log

builder.broker.dispatchers.append(
    NDJSONLogStreamDispatcher(transform_log=random_log)
)

def enrich(data, ctx, response):
    data["node"] = "notebook-1"
    data["debug"] = True

builder.broker.interceptors.append(
    NDJSONEnrichmentInterceptor(enrich)
)

app = FastAPI()
app.include_router(builder.router)

# uv run uvicorn apibean.intercept.examples.ndjson_log_stream:app --port=9090
