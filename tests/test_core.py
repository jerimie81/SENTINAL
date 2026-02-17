from sentinal import core

def test_health_check():
    assert core.health_check() == True
