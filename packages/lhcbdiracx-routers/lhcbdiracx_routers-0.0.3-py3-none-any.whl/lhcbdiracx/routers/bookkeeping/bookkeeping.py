from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Any

from diracx.routers.fastapi_classes import DiracxRouter
from fastapi import Body, Depends, Response
from fastapi.responses import StreamingResponse

from lhcbdiracx.core.models import BKSearchParams, BKSummaryParams
from lhcbdiracx.db.sql import BookkeepingDB as _BookkeepingDB
from lhcbdiracx.logic.bookkeeping.bookkeeping import dump_bk_paths
from lhcbdiracx.logic.bookkeeping.bookkeeping import hello_world as hello_world_bl
from lhcbdiracx.logic.bookkeeping.bookkeeping import (
    search_datasets as search_datasets_bl,
)
from lhcbdiracx.logic.bookkeeping.bookkeeping import (
    search_files as search_files_bl,
)
from lhcbdiracx.logic.bookkeeping.bookkeeping import (
    summary_datasets as summary_datasets_bl,
)
from lhcbdiracx.logic.bookkeeping.bookkeeping import (
    summary_files as summary_files_bl,
)

from .access_policy import ActionType, CheckBookkeepingPolicyCallable

router = DiracxRouter()

# Define the dependency at the top, so you don't have to
# be so verbose in your routes
BookkeepingDB = Annotated[_BookkeepingDB, Depends(_BookkeepingDB.transaction)]


@router.get("/")
async def hello_world(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
):
    await check_permission(action=ActionType.HELLO)
    return await hello_world_bl(bookkeeping_db)


@router.get(
    "/dump-paths",
    response_class=StreamingResponse,
    response_description="A text dump of all possible bookkeeping paths with one path per line.",
)
async def dump_paths(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
):
    await check_permission(action=ActionType.READ)
    return StreamingResponse(dump_bk_paths(bookkeeping_db), media_type="text/plain")


EXAMPLE_SEARCHES = {
    "Get bookkeeping paths": {
        "summary": "Get all paths for 2016 data and MC",
        "description": "Get Bookkeeping Paths for 2016 data and MC, ordered alphabetically (asc) by BkPath",
        "value": {
            "parameters": ["BkPath"],
            "search": [
                {"parameter": "ConfigName", "operator": "in", "values": ["LHCb", "MC"]},
                {
                    "parameter": "ConfigVersion",
                    "operator": "in",
                    "values": ["Collision16", "2016"],
                },
            ],
            "sort": [{"parameter": "BkPath", "direction": "asc"}],
        },
    },
}

EXAMPLE_FILE_SEARCHES = {
    "Get bookkeeping files under a path": {
        "summary": "Get all files under a specific bookkeeping path",
        "description": "Get all files under a specific bookkeeping path, ordered alphabetically (asc) by FileName",
        "value": {
            "parameters": ["FileName"],
            "search": [
                {"parameter": "ConfigName", "operator": "eq", "value": "LHCb"},
                {
                    "parameter": "ConfigVersion",
                    "operator": "eq",
                    "value": "Collision16",
                },
                {
                    "parameter": "ConditionsDescription",
                    "operator": "eq",
                    "value": "Beam6500GeV-VeloClosed-MagDown",
                },
                {
                    "parameter": "ProcPath",
                    "operator": "eq",
                    "value": "Real Data/Turbo03a",
                },
                {"parameter": "EventType", "operator": "eq", "value": "94000000"},
                {
                    "parameter": "FileType",
                    "operator": "eq",
                    "value": "CHARMMULTIBODY.DST",
                },
            ],
            "sort": [{"parameter": "FileName", "direction": "asc"}],
        },
    },
}


@router.post("/datasets/search")
async def search_datasets(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    response: Response,
    page: int = 1,
    per_page: int = 100,
    body: Annotated[
        BKSearchParams | None, Body(openapi_examples=EXAMPLE_FILE_SEARCHES)
    ] = None,
) -> list[dict[str, Any]]:
    """Retrieve information about bookkeeping datasets.

    The body of the request should contain the search parameters.
    You can also use the `sort` parameter to specify the sorting order.
    """
    await check_permission(action=ActionType.READ)

    total, datasets = await search_datasets_bl(
        bookkeeping_db=bookkeeping_db,
        page=page,
        per_page=per_page,
        body=body,
    )

    # Set the Content-Range header if needed
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4

    # No datasets found but there are datasets for the requested search
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4.4
    if len(datasets) == 0 and total > 0:
        response.headers["Content-Range"] = f"datasets */{total}"
        response.status_code = HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    # The total number of datasets is greater than the number of datasets returned
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4.2
    elif len(datasets) < total:
        first_idx = per_page * (page - 1)
        last_idx = min(first_idx + len(datasets), total) - 1 if total > 0 else 0
        response.headers["Content-Range"] = f"datasets {first_idx}-{last_idx}/{total}"
        response.status_code = HTTPStatus.PARTIAL_CONTENT
    return datasets


EXAMPLE_SUMMARY = {
    "Group with one column": {
        "value": {"grouping": "ConfigName"},
    },
    "Group with multiple columns": {
        "value": {"grouping": ["ConfigName", "ConfigVersion"]},
    },
    "Group with multiple columns and filter": {
        "value": {
            "grouping": ["ConfigName", "ConfigVersion"],
            "search": [{"parameter": "ConfigName", "operator": "eq", "value": "LHCb"}],
        },
    },
}


@router.post("/datasets/summary")
async def summary_datasets(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    body: Annotated[BKSummaryParams, Body(openapi_examples=EXAMPLE_SUMMARY)],
):
    """Show information suitable for plotting.
    Grouping and filtering information about datasets.
    """
    await check_permission(action=ActionType.READ, bookkeeping_db=bookkeeping_db)

    return await summary_datasets_bl(
        bookkeeping_db=bookkeeping_db,
        body=body,
    )


@router.post("/datasets/files/search")
async def search_files(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    response: Response,
    page: int = 1,
    per_page: int = 100,
    body: Annotated[
        BKSearchParams | None, Body(openapi_examples=EXAMPLE_SEARCHES)
    ] = None,
) -> list[dict[str, Any]]:
    """Retrieve information about files under bookkeeping datasets.

    The body of the request should contain the search parameters.
    You can also use the `sort` parameter to specify the sorting order.
    """
    await check_permission(action=ActionType.READ)

    total, files = await search_files_bl(
        bookkeeping_db=bookkeeping_db,
        page=page,
        per_page=per_page,
        body=body,
    )

    # Set the Content-Range header if needed
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4

    # No files found but there are files for the requested search
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4.4
    if len(files) == 0 and total > 0:
        response.headers["Content-Range"] = f"files */{total}"
        response.status_code = HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    # The total number of files is greater than the number of files returned
    # https://datatracker.ietf.org/doc/html/rfc7233#section-4.2
    elif len(files) < total:
        first_idx = per_page * (page - 1)
        last_idx = min(first_idx + len(files), total) - 1 if total > 0 else 0
        response.headers["Content-Range"] = f"files {first_idx}-{last_idx}/{total}"
        response.status_code = HTTPStatus.PARTIAL_CONTENT
    return files


@router.post("/datasets/files/summary")
async def summary_files(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    body: Annotated[BKSummaryParams, Body(openapi_examples=EXAMPLE_SUMMARY)],
):
    """Show information suitable for plotting.
    Grouping and filtering information about files.
    """
    await check_permission(action=ActionType.READ, bookkeeping_db=bookkeeping_db)

    return await summary_files_bl(
        bookkeeping_db=bookkeeping_db,
        body=body,
    )


@router.post("/datasets/files/ancestors")
async def files_ancestors(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    response: Response,
    page: int = 1,
    per_page: int = 100,
    body: Annotated[
        BKSearchParams | None, Body(openapi_examples=EXAMPLE_SEARCHES)
    ] = None,
) -> dict[str, list[str]] | None:
    """TODO. Get file ancestors.

    Returns a mapping of LFN -> list[LFN]
    """
    await check_permission(action=ActionType.READ, bookkeeping_db=bookkeeping_db)

    return {}


@router.post("/datasets/files/jobinfo")
async def job_info(
    bookkeeping_db: BookkeepingDB,
    check_permission: CheckBookkeepingPolicyCallable,
    response: Response,
    body: Annotated[
        BKSearchParams | None, Body(openapi_examples=EXAMPLE_SEARCHES)
    ] = None,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """TODO. Get job info.

    Returns dict[str, Any] or list[dict[str, Any]]
    """
    await check_permission(action=ActionType.READ, bookkeeping_db=bookkeeping_db)

    return {}
