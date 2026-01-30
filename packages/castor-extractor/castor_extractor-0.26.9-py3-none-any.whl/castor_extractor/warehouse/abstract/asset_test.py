from .asset import (
    EXTERNAL_LINEAGE_ASSETS,
    AssetsMapping,
    WarehouseAsset,
    WarehouseAssetGroup,
    extractable_assets,
)

COOL_TECHNOLOGY_ASSETS: AssetsMapping = {
    WarehouseAssetGroup.CATALOG: (
        WarehouseAsset.DATABASE,
        WarehouseAsset.SCHEMA,
    ),
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}


def test_extractable_asset_groups():
    # Default behavior: all extractable groups, external lineage excluded
    all_assets = set(extractable_assets(COOL_TECHNOLOGY_ASSETS))
    assert all_assets == {
        WarehouseAsset.DATABASE,
        WarehouseAsset.SCHEMA,
        WarehouseAsset.USER,
    }

    # With skip_groups: ROLE explicitly skipped, external lineage still excluded
    all_assets = set(
        extractable_assets(
            COOL_TECHNOLOGY_ASSETS,
            skip_groups={WarehouseAssetGroup.ROLE},
        )
    )
    assert all_assets == {
        WarehouseAsset.DATABASE,
        WarehouseAsset.SCHEMA,
    }
