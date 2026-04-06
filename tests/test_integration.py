import pytest
import sys
import os

# Add the root directory to sys.path to ensure 'storyteller' is found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from storyteller import Storyteller
except ImportError:
    try:
        from src.storyteller.storyteller import Storyteller
    except ImportError:
        raise ImportError("Could not find 'storyteller' module.")

@pytest.fixture
def real_storyteller():
    """Provides a Storyteller instance connected to the local LLM server."""
    st = Storyteller(
        api_key="not-needed", 
        base_url="http://100.91.59.1:8080/v1", 
        model_name="gemma4-26B-A4B-long"
    )
    return st

def test_ai_connection_smoke_test(real_storyteller):
    """
    A very fast smoke test to ensure the Storyteller can 
    successfully communicate with the local LLM server.
    """
    st = real_storyteller
    seed = "Quick test"
    
    # We only run ONE call to keep it under 30-60 seconds
    concept_response = st.generate_concept(seed)
    
    assert "concept" in concept_response
    assert len(concept_response["concept"]) > 0
    print("\n✅ AI Connection Smoke Test Passed!")

if __name__ == "__main__":
    pytest.main([__file__])
