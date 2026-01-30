# Databricks notebook source
# MAGIC %md
# MAGIC # Validate source code for Spark Declarative Pipeline
# MAGIC
# MAGIC This notebook creates a temporary Lakeflow SDP pipeline that includes the converted SDP code and triggers a validation-only update. It is intended to be
# MAGIC invoked from orchestrator notebooks after SDP conversion has been exported to the Databricks workspace.
# MAGIC

# COMMAND ----------

# DBTITLE 1,SDP APIs
import json
from typing import Any, Dict, Optional

import requests
from pyspark.sql.functions import array, lit
from pyspark.sql.types import ArrayType, StringType

# Initialize Databricks notebook context / API config
notebook_context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
_api_token = notebook_context.apiToken().get()
_workspace_url = notebook_context.apiUrl().get()

API_BASE_URL = f"{_workspace_url}/api/2.0/pipelines"

DEFAULT_HEADERS = {
    "Authorization": f"Bearer {_api_token}",
    "Content-Type": "application/json",
}

DEBUG = False


def _check_response(response: requests.Response) -> None:
    """Raise a helpful error if the request failed, otherwise pretty-print the JSON response."""
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if response.ok:
        if DEBUG and payload is not None:
            print("Response from API:\n{}".format(json.dumps(payload, indent=2)))
        elif DEBUG:
            print("Response from API (no JSON body):\n{}".format(response.text))
        return

    # Build a meaningful error message
    message = None
    if isinstance(payload, dict):
        # Databricks APIs often use "message" or "error" keys
        message = payload.get("message") or payload.get("error")

    if not message:
        message = response.text

    raise RuntimeError(f"Request failed: status={response.status_code}, message={message}")


def _request(
    method: str,
    path: str = "",
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[str] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """
    Internal helper to send an HTTP request to the pipelines API.

    - `path` is appended to API_BASE_URL.
    - Either `data` (raw JSON string) or `json_body` (dict auto-serialized) can be used.
    """
    url = f"{API_BASE_URL}{path}"
    all_headers = {**DEFAULT_HEADERS, **(headers or {})}

    response = requests.request(
        method=method,
        url=url,
        headers=all_headers,
        params=params,
        data=data,
        json=json_body,
    )
    _check_response(response)
    return response


def create_pipeline(pipeline_definition: str) -> str:
    """
    Create a Delta Live Table / Lakeflow pipeline.

    `pipeline_definition` is expected to be a JSON string. If you have a dict,
    call `json.dumps()` before passing it here.
    """
    response = _request(
        "POST",
        "",
        data=pipeline_definition,
    )
    payload = response.json()
    pipeline_id = payload.get("pipeline_id")
    if not pipeline_id:
        raise RuntimeError("Pipeline created but 'pipeline_id' missing in response.")
    return pipeline_id


def edit_pipeline(pipeline_id: str, pipeline_definition: str) -> None:
    """
    Edit an existing pipeline definition.

    `pipeline_definition` is expected to be a JSON string.
    """
    _request(
        "PUT",
        f"/{pipeline_id}",
        data=pipeline_definition,
    )


def delete_pipeline(pipeline_id: str) -> None:
    """Delete an existing pipeline by ID."""
    _request("DELETE", f"/{pipeline_id}")


def get_pipeline(pipeline_id: str) -> Dict[str, Any]:
    """Retrieve a pipeline by ID and return its JSON payload."""
    response = _request("GET", f"/{pipeline_id}")
    return response.json()


def validate_pipeline(pipeline_id: str, validate_only: bool = True):
    """
    Trigger a validation (or update) on a pipeline.

    When `validate_only` is True, the API will validate the pipeline
    without applying an update.
    """
    body = {
        "validate_only": validate_only,
        "cause": "API_CALL",
    }
    response = _request(
        "POST",
        f"/{pipeline_id}/updates",
        json_body=body,
    )
    payload = response.json()
    return payload.get("update_id")


def stop_pipeline(pipeline_id: str) -> None:
    """Stop a running pipeline."""
    _request("POST", f"/{pipeline_id}/stop")


def get_pipeline_update(pipeline_id: str, update_id: str) -> Dict[str, Any]:
    """
    Get details about a specific pipeline update.

    Returns the JSON payload of the update.
    """
    response = _request(
        "GET",
        f"/{pipeline_id}/updates/{update_id}",
    )
    return response.json()


def list_pipeline_events(
    pipeline_id: str,
    page_token: Optional[str] = None,
    log_filter: str = "level='ERROR'",
) -> Dict[str, Any]:
    """
    List pipeline events.

    - `log_filter` is an events filter expression, e.g. "level='ERROR'".
    - `page_token` can be used for pagination.

    Returns the JSON payload including events and next_page_token (if any).
    """
    params: Dict[str, Any] = {"filter": log_filter}
    if page_token:
        params["page_token"] = page_token

    response = _request(
        "GET",
        f"/{pipeline_id}/events",
        params=params,
    )
    return response.json()


# COMMAND ----------

# DBTITLE 1,Widgets and Configuration
# Parameters passed from orchestrators
dbutils.widgets.text("output_ws_dir", "", "Output Workspace Directory")
dbutils.widgets.text("catalog", "", "Catalog")
dbutils.widgets.text("schema", "", "Schema")
dbutils.widgets.text("result_table", "", "Conversion Result Table")
dbutils.widgets.text("comment_lang", "", "Comment Language")
dbutils.widgets.text("sdp_language", "python", "The language of the source code of SDP")

output_ws_dir = dbutils.widgets.get("output_ws_dir")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
result_table = dbutils.widgets.get("result_table")
comment_lang = dbutils.widgets.get("comment_lang")
sdp_language = dbutils.widgets.get("sdp_language")

print("SDP validation configuration:")
print(f"  output_ws_dir: {output_ws_dir}")
print(f"  catalog      : {catalog}")
print(f"  schema       : {schema}")
print(f"  result_table : {result_table}")
print(f"  comment_lang : {comment_lang}")
print(f"  sdp_language : {sdp_language}")

if not output_ws_dir:
    raise ValueError("Parameter 'output_ws_dir' is required for SDP validation.")
if not result_table:
    raise ValueError("Parameter 'result_table' is required for SDP validation.")

# COMMAND ----------

# DBTITLE 1,Export the converted code to workspace.

dbutils.notebook.run(
    "../exporters/export_to_notebook",
    0,
    {
        "result_table": result_table,
        "output_dir": output_ws_dir,
        "comment_lang": comment_lang,
        "notebook_language": sdp_language,
    },
)


# COMMAND ----------

# DBTITLE 1,Create SDP Pipeline for Validation
# Normalize workspace dir and build glob include to pick up all notebooks under it
normalized_output_ws_dir = output_ws_dir.rstrip("/")
glob_include_path = f"{normalized_output_ws_dir}/**"

pipeline_spec = {
    "name": f"_Lakebridge_Switch_SDP_Conversion_Validate_{__import__('uuid').uuid4().hex}",
    "libraries": [{"glob": {"include": glob_include_path}}],
    "catalog": catalog,
    "schema": schema,
    "channel": "PREVIEW",
    "development": True,
    "serverless": True,
    "continuous": False,
}

pipeline_id = create_pipeline(json.dumps(pipeline_spec))
print("Created pipeline for validation:", pipeline_id)


# COMMAND ----------

# DBTITLE 1,Start Validation and Check Results
import time

# Start a validation-only update
update_id = validate_pipeline(pipeline_id)

TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELED"}
payload: Dict[str, Any] = {}

while True:
    raw = get_pipeline_update(pipeline_id, update_id)  # returns dict like {"update": {...}}
    update = raw.get("update", {})
    state = update.get("state")

    if DEBUG:
        print(f"Current update state: {state}")

    if state in TERMINAL_STATES:
        payload = update  # keep final state in payload for later logic
        break
    time.sleep(5)

# Collect failure events if the update failed
failure_events: list[str] = []

if payload.get("state") == "FAILED":
    page_token = None

    while True:
        events_payload = list_pipeline_events(
            pipeline_id,
            page_token=page_token,
            log_filter="level='ERROR'",
        )

        for e in events_payload.get("events", []):
            error_obj = e.get("error")
            if not error_obj:
                continue

            # Filter out table/view not found errors which are not fixable for validation
            exceptions = error_obj.get("exceptions") or []
            has_table_or_view_not_found = any(
                isinstance(ex, dict) and ex.get("error_class") == "TABLE_OR_VIEW_NOT_FOUND" for ex in exceptions
            )
            if has_table_or_view_not_found:
                print(f"Skipping table/view not found error:\n {json.dumps(error_obj, indent=2)}")
                continue

            failure_events.append(json.dumps(error_obj, indent=2))

        page_token = events_payload.get("next_page_token")
        if not page_token:
            break

if failure_events:
    print("SDP validation failed with error(s):")
else:
    print("SDP pipeline validated successfully.")

for e in failure_events:
    print(e)

# Persist SDP validation errors into result_table for downstream processing
# Similar in spirit to validate_python_notebook, but aggregated at pipeline level.
source_df = spark.table(result_table)

if failure_events:
    errors_array_col = array(*[lit(e) for e in failure_events])
    updated_df = source_df.withColumn("result_sdp_errors", errors_array_col)
else:
    updated_df = source_df.withColumn("result_sdp_errors", lit(None).cast(ArrayType(StringType())))

updated_df.write.mode("overwrite").saveAsTable(result_table)


# COMMAND ----------

# DBTITLE 1,Delete Validation Pipeline
delete_pipeline(pipeline_id)
