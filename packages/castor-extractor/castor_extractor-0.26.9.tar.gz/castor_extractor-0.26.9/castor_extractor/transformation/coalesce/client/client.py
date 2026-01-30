import logging
import time
from collections.abc import Callable
from functools import partial
from http import HTTPStatus

from requests.exceptions import ConnectTimeout, ReadTimeout

from ....exceptions import TestConnectionException
from ....utils import (
    APIClient,
    BearerAuth,
    RequestSafeMode,
    SerializedAsset,
    fetch_all_pages,
)
from ....utils.client.api.smart_pagination import SmartPagination
from ..assets import CoalesceAsset, CoalesceQualityAsset
from .credentials import CoalesceCredentials
from .endpoint import (
    CoalesceEndpointFactory,
)
from .pagination import CoalescePagination

logger = logging.getLogger(__name__)

# increase pagination when extraction is too slow
# reduce pagination when hitting timeouts
COALESCE_PAGE_SIZE = 200
COALESCE_PAGE_SIZE_RUN_RESULTS = 1_000
COALESCE_MIN_PAGE_SIZE = 1

# raising this value might end up in remote server disconnection
COALESCE_TIMEOUT_SECONDS = 4 * 60  # 4 minutes

_MAX_ERRORS = 200

COALESCE_SAFE_MODE = RequestSafeMode(
    status_codes=(HTTPStatus.INTERNAL_SERVER_ERROR,),
    max_errors=_MAX_ERRORS,
)

RETRY_COUNT = 1
RETRY_BASE_MS = 5 * 60 * 1000  # 5 minutes
RETRY_EXCEPTIONS = (ConnectTimeout, ReadTimeout)

RETRY_EXCEPTION_MSG = """CoalesceClient raised exception '{exception}' while fetching env {environment_id},
with {{"startingFrom": {starting_from}}} and page_size of {page_size}
retrying in {retry}secs"""


def _run_result_payload(
    environment_id: str,
    result: dict,
    query_result: dict,
) -> dict:
    return {
        "environment_id": environment_id,
        "node_id": result["nodeID"],
        "node_name": result["name"],
        "test_name": query_result["name"],
        "start_time": query_result["startTime"],
        "end_time": query_result["endTime"],
        "status": query_result["status"],
        "success": query_result["success"],
        "isRunning": query_result["isRunning"],
    }


class CoalesceBearerAuth(BearerAuth):
    """Bearer Authentication for Coalesce"""

    def fetch_token(self) -> str | None:
        pass

    def __init__(self, token: str):
        self._token = token


class CoalesceClient(APIClient):
    """REST API client to extract data from Coalesce"""

    def test_connection(self) -> None:
        endpoint = CoalesceEndpointFactory.environments()
        request = self._get_paginated(endpoint=endpoint)
        try:
            next(fetch_all_pages(request, CoalescePagination))
        except Exception as e:
            raise TestConnectionException(e)

    def __init__(
        self,
        credentials: CoalesceCredentials,
    ):
        auth = CoalesceBearerAuth(token=credentials.token)
        super().__init__(
            host=credentials.host,
            auth=auth,
            safe_mode=COALESCE_SAFE_MODE,
            timeout=COALESCE_TIMEOUT_SECONDS,
        )

    def _get_paginated(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> Callable:
        return partial(
            self._get,
            retry_on_timeout=False,
            endpoint=endpoint,
            params={
                **(params or dict()),
            },
        )

    def _fetch_environments(self) -> SerializedAsset:
        endpoint = CoalesceEndpointFactory.environments()
        request = self._get_paginated(endpoint=endpoint)
        result = fetch_all_pages(request, CoalescePagination)
        return list(result)

    def _fetch_env_node_page(
        self, endpoint: str, page_size: int, starting_from: str | int | None
    ) -> tuple[dict | None, int | None]:
        response = self._call(
            method="GET",
            endpoint=endpoint,
            params={
                "detail": "false",
                "limit": page_size,
                "startingFrom": starting_from,
            },
            retry_on_timeout=False,
        ).json()
        return response.get("data"), response.get("next")

    def _fetch_env_nodes(self, environment_id: int) -> SerializedAsset:
        endpoint = CoalesceEndpointFactory.nodes(environment_id=environment_id)
        starting_from: None | str | int = None
        pagination = SmartPagination(COALESCE_PAGE_SIZE)
        result: list[dict] = []
        while True:
            try:
                data, next_page = self._fetch_env_node_page(
                    endpoint, pagination.page_size, starting_from
                )
                if data is not None:
                    result.extend(data)
                pagination.next()
                if next_page is None:
                    break
                starting_from = next_page
            except RETRY_EXCEPTIONS as e:
                if pagination.page_size <= COALESCE_MIN_PAGE_SIZE:
                    raise e
                logging.info(
                    RETRY_EXCEPTION_MSG.format(
                        exception=e,
                        starting_from=starting_from,
                        page_size=pagination.page_size,
                        environment_id=environment_id,
                        retry=RETRY_BASE_MS // 1000,
                    )
                )
                pagination.reduce_page_size()
                time.sleep(RETRY_BASE_MS // 1000)

        return [
            {
                **node,
                "environment_id": environment_id,
            }
            for node in result
        ]

    def _fetch_all_nodes(self) -> SerializedAsset:
        environments = self._fetch_environments()
        total = len(environments)
        nodes: list[dict] = []

        for index, env in enumerate(environments):
            env_id = env["id"]
            logger.info(f"Fetching nodes for env #{env_id} - {index}/{total}")
            nodes.extend(self._fetch_env_nodes(env_id))
            logger.info(f"{len(nodes)} nodes extracted so far")
        return nodes

    def _fetch_runs(self, starting_from: str | None) -> SerializedAsset:
        endpoint = CoalesceEndpointFactory.runs()
        params = {
            "orderBy": "runEndTime",
            "orderByDirection": "asc",
            "startingFrom": starting_from,
        }
        request = self._get_paginated(
            endpoint=endpoint,
            params=params,
        )
        return list(fetch_all_pages(request, CoalescePagination))

    def _fetch_run_results(self, run_id: str) -> SerializedAsset:
        endpoint = CoalesceEndpointFactory.run_results(run_id)
        result = self._get(endpoint=endpoint)
        return result["data"]

    def _run_results_by_run(
        self,
        environment_id: str,
        run_id: str,
    ) -> SerializedAsset:
        run_results: list[dict] = []
        for result in self._fetch_run_results(run_id):
            for query_result in result["queryResults"]:
                if query_result["type"] != "sqlTest":
                    continue
                run_result = _run_result_payload(
                    environment_id,
                    result,
                    query_result,
                )
                run_results.append(run_result)
        return run_results

    def _fetch_all_run_results(
        self,
        starting_from: str | None,
    ) -> SerializedAsset:
        run_results: list[dict] = []

        runs = self._fetch_runs(starting_from)
        total = len(runs)

        for index, run in enumerate(runs):
            logger.info(f"Extracting run results ({index}/{total})")
            run_id = run["id"]
            environment_id = run["environmentID"]
            current_results = self._run_results_by_run(environment_id, run_id)
            run_results.extend(current_results)
        return run_results

    def fetch(
        self,
        asset: CoalesceAsset | CoalesceQualityAsset,
        starting_from: str | None = None,
    ) -> SerializedAsset:
        """Extract the given Coalesce Asset"""
        if asset in (CoalesceAsset.NODES, CoalesceQualityAsset.NODES):
            return self._fetch_all_nodes()
        elif asset == CoalesceQualityAsset.RUN_RESULTS:
            return self._fetch_all_run_results(starting_from=starting_from)
        raise AssertionError(
            f"Asset {asset} is not supported by CoalesceClient"
        )
