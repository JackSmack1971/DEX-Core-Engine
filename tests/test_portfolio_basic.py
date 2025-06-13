from portfolio import Asset, Portfolio


def test_asset_and_portfolio_value():
    asset = Asset("A", 2, 3.0)
    p = Portfolio({"A": asset})
    assert asset.value == 6.0
    assert p.total_value() == 6.0
