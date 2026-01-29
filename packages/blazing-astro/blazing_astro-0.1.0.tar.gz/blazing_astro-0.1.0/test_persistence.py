from server import save_subject, calculate_natal_chart, calculate_synastry, calculate_transits
import storage
import os

def test_persistence():
    print("Testing Persistence...")
    
    # Clean up
    if os.path.exists("subjects.json"):
        os.remove("subjects.json")
        
    # Test Save
    res = save_subject("Alice", 1990, 1, 1, 12, 0, "New York", "US")
    print(res)
    assert "saved successfully" in res
    
    res = save_subject("Bob", 1992, 2, 2, 12, 0, "London", "GB")
    print(res)
    
    # Test List
    subs = storage.list_subjects()
    print(f"Subjects: {subs}")
    assert "alice" in subs
    assert "bob" in subs
    
    # Test Natal with Saved
    print("\nTesting Natal with Saved Subject...")
    # Directly calling the tool function (not via MCP protocol but as py func)
    chart = calculate_natal_chart(saved_subject_name="Alice")
    print(chart[:50] + "...")
    assert "Natal Chart for Alice" in chart
    assert "Sun: Cap" in chart or "Sun: Capricorn" in chart
    
    # Test Synastry with Saved
    print("\nTesting Synastry with Saved Subjects...")
    syn = calculate_synastry(saved_subject_name1="Alice", saved_subject_name2="Bob")
    print(syn[:100] + "...")
    assert "Synastry Report: Alice and Bob" in syn
    
    print("\nTesting Transits...")
    transits = calculate_transits(saved_subject_name="Alice")
    print(transits[:100] + "...")
    assert "Transit Report for Alice" in transits
    assert "Transit" in transits and "Natal" in transits

    print("\nPersistence and Transit Tests Passed!")

if __name__ == "__main__":
    test_persistence()
