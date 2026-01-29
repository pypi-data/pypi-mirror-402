from blazing_astro.server import calculate_natal_chart, calculate_transits, save_subject
import os

def test_package():
    print("Testing Package Structure...")
    # Clean up old persistence file if it exists in package dir? 
    # Actually storage.py uses __file__ relative path, so it should be fine.
    
    # Save check
    res = save_subject("PkgTest", 2000, 1, 1, 12, 0, "Paris", "FR")
    print(res)
    
    # Chart check
    chart = calculate_natal_chart(saved_subject_name="PkgTest")
    assert "Natal Chart for PkgTest" in chart
    
    print("Package Test Passed!")

if __name__ == "__main__":
    test_package()
