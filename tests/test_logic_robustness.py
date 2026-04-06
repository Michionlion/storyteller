import pytest
from unittest.mock import MagicMock, patch
from storyteller import Storyteller, Beat

def test_robust_json_extraction():
    """
    Tests the regex-based JSON extraction in _call_ai with various 'dirty' inputs.
    """
    st = Storyteller(api_key="fake", base_url="http://fake", model_name="fake")
    
    # We patch 'openai.OpenAI' because the import happens inside the method
    with patch('openai.OpenAI') as MockOpenAI:
        mock_client = MockOpenAI.return_value
        
        # Case 1: Perfect JSON in markdown blocks
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="```json\n{\"key\": \"value\"}\n```"))]
        )
        res = st._call_ai("test", 100)
        assert res == {"key": "value"}

        # Case 2: JSON wrapped in curly braces but no markdown
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="The result is {\"key\": \"value\"} and nothing else."))]
        )
        res = st._call_ai("test", 100)
        assert res == {"key": "value"}

        # Case 3: Pure prose (no JSON)
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Just some plain text here."))]
        )
        res = st._call_ai("test", 100)
        assert res["prose"] == "Just some plain text here."

        # Case 4: Reasoning content + JSON block (Simulating DeepSeek style)
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="<thought>I should output JSON</thought> ```json\n{\"status\": \"ok\"}\n```"))]
        )
        res = st._call_ai("test", 100)
        assert res == {"status": "ok"}

def test_remove_methods():
    """Tests the removal logic for pinned passages and prohibited elements."""
    st = Storyteller(api_key="fake")
    
    # Test Prohibited Elements
    st.add_prohibited_element("banana")
    assert "banana" in st.project.bible.prohibited_elements
    st.remove_prohibited_element("banana")
    assert "banana" not in st.project.bible.prohibited_elements
    # Ensure no error if removing non-existent
    st.remove_prohibited_element("banana") 

    # Test Pinned Passages
    beat = Beat(title="Test Beat", content="Content")
    st.project.beats.append(beat)
    
    st.add_pinned_passage(0, "Keep this", "Consistency")
    assert len(st.project.beats[0].pinned_passages) == 1
    
    st.remove_pinned_passage(0, 0)
    assert len(st.project.beats[0].pinned_passages) == 0
    
    with pytest.raises(ValueError):
        st.remove_pinned_passage(0, 99)
