"""Tests for storyteller.py — keeps the 'tested' guarantee."""

import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storyteller import StoryProject, Storyteller, Beat


class TestStoryProject:
    def test_empty_project(self):
        project = StoryProject()
        assert project.concept == ""
        assert project.beats == []
        assert project.get_context() == ""

    def test_context_contains_concept(self):
        project = StoryProject(concept="A heist story")
        context = project.get_context()
        assert "STORY CONCEPT" in context
        assert "A heist story" in context

    def test_context_contains_beats(self):
        project = StoryProject(concept="A heist story")
        beat = Beat(title="The Plan", content="They planned it...")
        project.beats.append(beat)
        context = project.get_context()
        assert "The Plan" in context
        assert "They planned it..." in context

    def test_context_contains_critique(self):
        project = StoryProject(concept="A spy story")
        beat = Beat(title="The Meeting", content="They met in a cafe", 
                   critique={"strengths": "Good pacing", "weaknesses": "Weak dialogue"})
        project.beats.append(beat)
        context = project.get_context()
        assert "CRITIQUE" in context
        assert "The Meeting" in context

    def test_add_fact_to_bible(self):
        project = StoryProject()
        project.bible.facts.append({"key": "Location", "value": "Paris"})
        assert len(project.bible.facts) == 1
        assert project.bible.facts[0]["key"] == "Location"
        assert project.bible.facts[0]["value"] == "Paris"

    def test_context_contains_facts(self):
        project = StoryProject(concept="A spy story")
        project.bible.facts.append({"key": "Agent", "value": "007"})
        context = project.get_context()
        assert "FACT" in context
        assert "Agent" in context
        assert "007" in context


class TestStoryteller:
    def test_initialization(self):
        storyteller = Storyteller("sk-fake")
        assert storyteller.api_key == "sk-fake"
        assert storyteller.project.concept == ""
        assert storyteller.project.beats == []

    def test_add_fact(self):
        storyteller = Storyteller("sk-fake")
        storyteller.add_fact("Location", "Paris")
        assert len(storyteller.project.bible.facts) == 1
        assert storyteller.project.bible.facts[0] == {"key": "Location", "value": "Paris"}

    def test_add_multiple_facts(self):
        storyteller = Storyteller("sk-fake")
        storyteller.add_fact("Location", "Paris")
        storyteller.add_fact("Hero", "John")
        assert len(storyteller.project.bible.facts) == 2

    def test_get_project_returns_instance(self):
        storyteller = Storyteller("sk-fake")
        project = storyteller.get_project()
        assert isinstance(project, StoryProject)
        assert project is storyteller.project

    def test_generate_beat_adds_to_project(self):
        """Test that generate_beat properly adds a beat to the project."""
        storyteller = Storyteller("sk-fake")
        # Mock the _call_ai method to return a simple prose
        original_call = storyteller._call_ai
        
        def mock_call(prompt, max_tokens):
            return "Generated prose content"
        
        storyteller._call_ai = mock_call
        
        prose = storyteller.generate_beat("The Beginning")
        
        assert len(storyteller.project.beats) == 1
        assert storyteller.project.beats[0].title == "The Beginning"
        assert storyteller.project.beats[0].content == "Generated prose content"
        assert storyteller.project.beats[0].id == "the_beginning"

    def test_critique_beat_stores_critique(self):
        """Test that critique_beat properly stores critique for a beat."""
        storyteller = Storyteller("sk-fake")
        
        # Add a beat first
        original_call = storyteller._call_ai
        
        def mock_call_for_beat(prompt, max_tokens):
            return "Initial prose"
        
        def mock_call_for_critique(prompt, max_tokens):
            return {
                "overall_rating": 7,
                "strengths": "Good pacing",
                "weaknesses": "Weak dialogue",
                "suggestions": "Improve dialogue"
            }
        
        storyteller._call_ai = mock_call_for_beat
        storyteller.generate_beat("First Beat")
        
        # Now mock critique call
        storyteller._call_ai = mock_call_for_critique
        
        critique_data = storyteller.critique_beat(0)
        
        assert storyteller.project.beats[0].critique == {
            "overall_rating": 7,
            "strengths": "Good pacing",
            "weaknesses": "Weaknesses",
            "suggestions": "Improve dialogue"
        }
        assert isinstance(critique_data, dict)
        assert "overall_rating" in critique_data

    def test_critique_beat_invalid_index(self):
        """Test that critique_beat raises error for invalid index."""
        storyteller = Storyteller("sk-fake")
        
        with pytest.raises(ValueError):
            storyteller.critique_beat(-1)
        
        with pytest.raises(ValueError):
            storyteller.critique_beat(0)

    def test_improve_beat_updates_content(self):
        """Test that improve_beat updates beat content."""
        storyteller = Storyteller("sk-fake")
        
        # Add a beat with critique
        original_call = storyteller._call_ai
        
        def mock_call_for_beat(prompt, max_tokens):
            return "Initial prose"
        
        def mock_call_for_improvement(prompt, max_tokens):
            return "Improved prose"
        
        storyteller._call_ai = mock_call_for_beat
        storyteller.generate_beat("First Beat")
        
        # Mock critique call
        def mock_call_for_critique(prompt, max_tokens):
            return {
                "overall_rating": 7,
                "strengths": "Good pacing",
                "weaknesses": "Weak dialogue",
                "suggestions": "Improve dialogue"
            }
        
        storyteller._call_ai = mock_call_for_critique
        storyteller.critique_beat(0)
        
        # Mock improvement call
        storyteller._call_ai = mock_call_for_improvement
        
        improved = storyteller.improve_beat(0, "Weak dialogue", "Make dialogue more natural")
        
        assert storyteller.project.beats[0].content == "Improved prose"
        assert improved == "Improved prose"

    def test_improve_beat_invalid_index(self):
        """Test that improve_beat raises error for invalid index."""
        storyteller = Storyteller("sk-fake")
        
        with pytest.raises(ValueError):
            storyteller.improve_beat(-1, "Critique", "Focus")
        
        with pytest.raises(ValueError):
            storyteller.improve_beat(0, "Critique", "Focus")


class TestBeat:
    def test_beat_creation(self):
        beat = Beat(title="Test Beat", content="Test content")
        assert beat.title == "Test Beat"
        assert beat.content == "Test content"
        assert beat.id == ""
        assert beat.critique == ""

    def test_beat_with_id(self):
        beat = Beat(title="Test Beat", content="Test content", id="test_beat_1")
        assert beat.id == "test_beat_1"

    def test_beat_with_critique(self):
        beat = Beat(
            title="Test Beat",
            content="Test content",
            critique={"rating": 8, "feedback": "Good"}
        )
        assert beat.critique == {"rating": 8, "feedback": "Good"}

    def test_beat_dict_method(self):
        beat = Beat(title="Test Beat", content="Test content", id="test")
        result = beat.dict()
        assert result["title"] == "Test Beat"
        assert result["content"] == "Test content"
        assert result["id"] == "test"

    def test_beat_dict_includes_critique(self):
        beat = Beat(
            title="Test Beat",
            content="Test content",
            critique={"rating": 8}
        )
        result = beat.dict()
        assert result["critique"] == {"rating": 8}


class TestPromptLoading:
    def test_load_prompt_file_exists(self, tmp_path, monkeypatch):
        """Test that prompts are loaded from files when they exist."""
        # Create a temporary prompts directory
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        concept_file = prompts_dir / "concept.md"
        concept_file.write_text("Test concept prompt")
        
        beat_file = prompts_dir / "beat.md"
        beat_file.write_text("Test beat prompt")
        
        critique_file = prompts_dir / "critique.md"
        critique_file.write_text("Test critique prompt")
        
        # Monkeypatch to use temp directory
        import storyteller
        original_path = os.path.dirname(storyteller.__file__)
        monkeypatch.setattr(storyteller, "__file__", str(tmp_path / "storyteller.py"))
        
        # Reload to test prompt loading
        import importlib
        importlib.reload(storyteller)
        
        assert "Test concept prompt" in storyteller.PROMPT_CONCEPT
        assert "Test beat prompt" in storyteller.PROMPT_BEAT
        assert "Test critique prompt" in storyteller.PROMPT_CRITIQUE

    def test_load_prompt_file_not_found(self, tmp_path, monkeypatch):
        """Test fallback when prompt file doesn't exist."""
        import storyteller
        original_path = os.path.dirname(storyteller.__file__)
        monkeypatch.setattr(storyteller, "__file__", str(tmp_path / "storyteller.py"))
        
        importlib = __import__("importlib")
        importlib.reload(storyteller)
        
        # Should have default fallback text when file not found
        assert storyteller.PROMPT_CONCEPT
        assert storyteller.PROMPT_BEAT
        assert storyteller.PROMPT_CRITIQUE
