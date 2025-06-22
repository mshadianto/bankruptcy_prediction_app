import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def test_import():
    """Test basic import"""
    try:
        from app.main import BankruptcyPredictor
        assert True
    except ImportError:
        assert False, "Cannot import BankruptcyPredictor"

def test_altman_calculation():
    """Test Altman calculation with sample data"""
    from app.main import BankruptcyPredictor
    
    sample_data = {
        'current_assets': 1000000,
        'current_liabilities': 500000,
        'total_assets': 2000000,
        'total_liabilities': 800000,
        'total_revenue': 1500000,
        'ebit': 200000,
        'net_income': 150000,
        'retained_earnings': 300000,
        'market_cap': 1500000
    }
    
    result = BankruptcyPredictor.altman_z_score(sample_data)
    assert 'error' not in result
    assert 'score' in result
    assert isinstance(result['score'], (int, float))
