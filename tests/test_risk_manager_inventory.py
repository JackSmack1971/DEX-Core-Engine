import math

from risk_manager import RiskManager


def test_inventory_management():
    rm = RiskManager()
    rm.add_inventory("tok", 10)
    rm.set_price("tok", 2.0)
    rm.remove_inventory("tok", 5)
    assert rm.get_inventory("tok") == 5
    assert rm.inventory_value() == 10.0


def test_rebalance_and_hedge():
    rm = RiskManager()
    rm.add_inventory("a", 10)
    rm.add_inventory("b", 5)
    rm.set_price("a", 2.0)
    rm.set_price("b", 1.0)
    rm.rebalance_inventory("a", "b", 1.0)
    assert math.isclose(
        rm.inventory["a"].value, rm.inventory["b"].value, rel_tol=1e-2
    )

    loss = rm.hedge_impermanent_loss("a", "b", 1.0, 2.0)
    assert loss > 0
    assert math.isclose(
        rm.inventory["a"].value, rm.inventory["b"].value, rel_tol=1e-2
    )
