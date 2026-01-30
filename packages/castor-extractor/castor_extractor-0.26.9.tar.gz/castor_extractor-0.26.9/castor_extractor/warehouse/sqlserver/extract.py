import logging

from ...utils import LocalStorage, filter_items, from_env, write_summary
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    AssetsMapping,
    SQLExtractionProcessor,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
    extractable_assets,
)
from .client import MSSQLClient
from .query import MSSQLQueryBuilder

logger = logging.getLogger(__name__)


MSSQL_ASSETS: AssetsMapping = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
}


MSSQL_USER = "CASTOR_MSSQL_USER"
MSSQL_PASSWORD = "CASTOR_MSSQL_PASSWORD"  # noqa: S105
MSSQL_HOST = "CASTOR_MSSQL_HOST"
MSSQL_PORT = "CASTOR_MSSQL_PORT"
MSSQL_DEFAULT_DB = "CASTOR_MSSQL_DEFAULT_DB"


def _credentials(params: dict) -> dict:
    """extract mssql credentials"""
    return {
        "host": params.get("host") or from_env(MSSQL_HOST),
        "password": params.get("password") or from_env(MSSQL_PASSWORD),
        "port": params.get("port") or from_env(MSSQL_PORT),
        "user": params.get("user") or from_env(MSSQL_USER),
        "default_db": params.get("default_db")
        or from_env(MSSQL_DEFAULT_DB, allow_missing=True),
    }


def extract_all(**kwargs) -> None:
    """
    Extract all assets from mssql and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = MSSQLClient(credentials=_credentials(kwargs))

    databases = filter_items(
        items=client.get_databases(),
        allowed=kwargs.get("db_allowed"),
        blocked=kwargs.get("db_blocked"),
    )

    logger.info(f"Available databases: {databases}\n")

    query_builder = MSSQLQueryBuilder(databases=databases)

    storage = LocalStorage(directory=output_directory)

    extractor = SQLExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    skip_queries = kwargs.get("skip_queries") or False
    skip_groups = {WarehouseAssetGroup.QUERY} if skip_queries else None

    for asset in extractable_assets(MSSQL_ASSETS, skip_groups=skip_groups):
        logger.info(f"Extracting `{asset.value.upper()}` ...")
        location = extractor.extract(asset, skip_existing)
        logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
