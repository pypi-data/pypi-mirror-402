from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from datetime import datetime
import pytz

def test_logic():
    print("Testing Natal Chart Logic...")
    # NOTE: Kerykeion v5 tries to fetch data online. 
    # For CI/test without network or api keys, it might fail if we don't handle it.
    # But usually it just works for major cities.
    s1 = AstrologicalSubjectFactory.from_birth_data("Test1", 1990, 1, 1, 12, 0, "New York", "US")
    data1 = ChartDataFactory.create_natal_chart_data(s1)
    
    sun = data1.subject.sun
    print(f"Sun in {sun.sign}")
    assert sun.sign in ["Cap", "Capricorn"]
    
    print("\nTesting Synastry Logic...")
    s2 = AstrologicalSubjectFactory.from_birth_data("Test2", 1992, 2, 2, 12, 0, "London", "GB")
    syn_data = ChartDataFactory.create_synastry_chart_data(s1, s2)
    print(f"Score: {syn_data.relationship_score.score_value}")
    
    print("\nTesting Current Skies Logic...")
    # Helper for current skies
    s_now = AstrologicalSubjectFactory.from_current_time(city="Paris", nation="FR")
    c_now = ChartDataFactory.create_natal_chart_data(s_now)
    print(f"Current Sun in {c_now.subject.sun.sign}")

if __name__ == "__main__":
    test_logic()
