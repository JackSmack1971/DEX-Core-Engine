from risk_manager import RiskManager


def test_inventory_management():
    rm = RiskManager()
    rm.add_inventory("tok", 10)
    rm.remove_inventory("tok", 5)
    assert rm.get_inventory("tok") == 5


def test_impermanent_loss():
    rm = RiskManager()
    loss = rm.impermanent_loss(1.0, 2.0, 1.0, 1.0)
    assert loss > 0
