import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from temporalio.client import Client, WorkflowExecution
from temporalio.common import SearchAttributeKey

from antgent.config import config
from antgent.temporal.client import tclient

router = APIRouter(prefix="/api", tags=["Workflows"])
logger = logging.getLogger(__name__)


def get_workflow_types_from_config() -> list[str]:
    """Get workflow type names from config, ensuring defaults are included."""
    workflow_types = set()

    # 1. Get from loaded configuration which might override the defaults.
    worker_configs = config().workers
    for worker_config in worker_configs:
        for workflow in worker_config.workflows:
            workflow_types.add(workflow.split(":")[-1])

    # 2. Get from default schema to ensure base workflows are always present.
    from antgent.config import ConfigSchema

    temporal_config_field = ConfigSchema.model_fields["temporalio"]
    default_temporal_config = temporal_config_field.get_default()
    if default_temporal_config and default_temporal_config.workers:
        for worker_config in default_temporal_config.workers:
            for workflow in worker_config.workflows:
                workflow_types.add(workflow.split(":")[-1])

    return sorted(list(workflow_types))


@router.get("/workflows/types", response_model=list[str], summary="List all discoverable workflow types.")
async def list_workflow_types():
    """Lists all unique workflow type names found in the configuration."""
    return get_workflow_types_from_config()


def _build_list_workflows_query(
    workflow_type: str | None,
    case_id: str | None,
    status: str | None,
    original_workflow_id: str | None,
) -> str:
    query_parts = []

    def _get_processed_values(param: str | None) -> list[str]:
        if not param:
            return []
        return [v.strip() for v in param.split(",") if v.strip()]

    processed_types = _get_processed_values(workflow_type)
    if processed_types:
        valid_types = get_workflow_types_from_config()
        for wt in processed_types:
            if wt not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid workflow type '{wt}'. Valid types are: {', '.join(valid_types)}",
                )
        types_str = "', '".join(processed_types)
        query_parts.append(f"WorkflowType IN ('{types_str}')")

    processed_case_ids = _get_processed_values(case_id)
    if processed_case_ids:
        case_ids_str = "', '".join(processed_case_ids)
        query_parts.append(f"CaseId IN ('{case_ids_str}')")

    processed_original_ids = _get_processed_values(original_workflow_id)
    if processed_original_ids:
        original_ids_str = "', '".join(processed_original_ids)
        query_parts.append(f"OriginalWorkflowId IN ('{original_ids_str}')")

    processed_statuses = _get_processed_values(status)
    if processed_statuses:
        # Values for ExecutionStatus are capitalized: Running, Completed, etc.
        statuses = [s.capitalize() for s in processed_statuses]
        statuses_str = "', '".join(statuses)
        query_parts.append(f"ExecutionStatus IN ('{statuses_str}')")

    return " AND ".join(query_parts)


def _process_workflow_execution(w: WorkflowExecution) -> dict:
    duration = None
    if w.close_time and w.start_time:
        delta = w.close_time - w.start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration = f"{hours:02}:{minutes:02}:{seconds:02}"

    search_attributes = {}
    if w.search_attributes:
        for key_str in w.search_attributes:
            try:
                # Use untyped key to get value, letting the SDK handle decoding
                value = w.typed_search_attributes.get(SearchAttributeKey.for_untyped(key_str))
                search_attributes[key_str] = value
            except Exception:
                search_attributes[key_str] = "Error decoding search attribute"

    return {
        "workflow_id": w.id,
        "run_id": w.run_id,
        "workflow_type": w.workflow_type,
        "status": w.status.name,
        "start_time": w.start_time,
        "end_time": w.close_time,
        "duration": duration,
        "search_attributes": search_attributes,
    }


@router.get("/workflows", response_model=list[dict], summary="List workflow executions.")
async def list_workflows(
    workflow_type: Annotated[
        str | None,
        Query(alias="type", description="Filter by one or more workflow type names (comma-separated)."),
    ] = None,
    status: Annotated[
        str,
        Query(description="Filter by one or more workflow statuses (comma-separated)."),
    ] = "RUNNING,COMPLETED,FAILED",
    case_id: Annotated[
        str | None,
        Query(description="Filter by one or more CaseId search attributes (comma-separated)."),
    ] = None,
    original_workflow_id: Annotated[
        str | None,
        Query(alias="OriginalWorkflowId", description="Filter by OriginalWorkflowId search attribute."),
    ] = None,
):
    """Lists workflow executions, with optional filters for type, status, and case ID."""
    client: Client = await tclient()
    query = _build_list_workflows_query(workflow_type, case_id, status, original_workflow_id)

    workflows = []
    logger.info(f"Listing workflows with query: '{query}'")
    try:
        async for w in client.list_workflows(query=query):
            workflows.append(_process_workflow_execution(w))
    except Exception as e:
        logger.error(f"Error listing workflows from Temporal with query '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list workflows from Temporal.") from e

    return workflows
