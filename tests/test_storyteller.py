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

    def test_context_contains_pinned_passages(self):
        project = StoryProject(concept="A spy story")
        beat = Beat(
            title="The Meeting",
            content="They met in a cafe",
            pinned_passages=[{"text": "Elena", "purpose": "Character name"}]
        )
        project.beats.append(beat)
        context = project.get_context()
        assert "PINNED PASSAGES" in context
        assert "Elena" in context

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

    def test_context_contains_prohibited(self):
        project = StoryProject()
        project.bible.prohibited_elements = ["Elara", "AI-isms"]
        context = project.get_context()
        assert "PROHIBITED ELEMENTS" in context
        assert "Elara" in context
        assert "AI-isms" in context


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
        
        storyteller._call_ai = mock_call_for_critique
        
        critique_data = storyteller.critique_beat(0)
        
        assert storyteller.project.beats[0].critique == {
            "overall_rating": 7,
            "strengths": "Good pacing",
            "weaknesses": "Weak dialogue",
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
        
        def mock_call_for_beat(prompt, max_tokens):
            return "Initial prose"
        
        def mock_call_for_improvement(prompt, max_tokens):
            return "Improved prose"
        
        storyteller._call_ai = mock_call_for_beat
        storyteller.generate_beat("First Beat")
        
        def mock_call_for_critique(prompt, max_tokens):
            return {
                "overall_rating": 7,
                "strengths": "Good pacing",
                "weaknesses": "Weak dialogue",
                "suggestions": "Improve dialogue"
            }
        
        storyteller._call_ai = mock_call_for_critique
        storyteller.critique_beat(0)
        
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

    def test_add_pinned_passage(self):
        """Test that pinned passages can be added to beats."""
        storyteller = Storyteller("sk-fake")
        
        def mock_call(prompt, max_tokens):
            return "Initial prose"
        
        storyteller._call_ai = mock_call
        storyteller.generate_beat("First Beat")
        
        storyteller.add_pinned_passage(0, "Elena", "Main character name")
        
        assert len(storyteller.project.beats[0].pinned_passages) == 1
        assert storyteller.project.beats[0].pinned_passages[0]["text"] == "Elena"
        assert storyteller.project.beats[0].pinned_passages[0]["purpose"] == "Main character name"

    def test_add_multiple_pinned_passages(self):
        """Test that multiple pinned passages can be added."""
        storyteller = Storyteller("sk-fake")
        
        def mock_call(prompt, max_tokens):
            return "Initial prose"
        
        storyteller._call_ai = mock_call
        storyteller.generate_beat("First Beat")
        
        storyteller.add_pinned_passage(0, "Elena", "Character name")
        storyteller.add_pinned_passage(0, "The Whispering Forest", "Setting")
        
        assert len(storyteller.project.beats[0].pinned_passages) == 2
        assert storyteller.project.beats[0].pinned_passages[0]["text"] == "Elena"
        assert storyteller.project.beats[0].pinned_passages[1]["text"] == "The Whispering Forest"

    def test_remove_pinned_passage(self):
        """Test that pinned passages can be removed."""
        storyteller = Storyteller("sk-fake")
        
        def mock_call(prompt, max_tokens):
            return "Initial prose"
        
        storyteller._call_ai = mock_call
        storyteller.generate_beat("First Beat")
        
        storyteller.add_pinned_passage(0, "Elena", "Character name")
        storyteller.add_pinned_passage(0, "Forest", "Setting")
        
        storyteller.remove_pinned_passage(0, 0)
        
        assert len(storyteller.project.beats[0].pinned_passages) == 1
        assert storyteller.project.beats[0].pinned_passages[0]["text"] == "Forest"

    def test_improve_beat_preserves_pinned_passages(self):
        """Test that pinned passages are included in the improvement prompt."""
        storyteller = Storyteller("sk-fake")
        
        def mock_call(prompt, max_tokens):
            return "Initial prose"
        
        storyteller._call_ai = mock_call
        storyteller.generate_beat("First Beat")
        
        storyteller.add_pinned_passage(0, "Elena", "Character name")
        
        def mock_critique(prompt, max_tokens):
            return {
                "overall_rating": 7,
                "strengths": "Good pacing",
                "weaknesses": "Weak dialogue",
                "suggestions": "Improve dialogue"
            }
        
        storyteller._call_ai = mock_critique
        storyteller.critique_beat(0)
        
        improvement_prompt = None
        
        def mock_improvement(prompt, max_tokens):
            nonlocal improvement_prompt
            improvement_prompt = prompt
            return "Improved prose"
        
        storyteller._call_ai = mock_improvement
        
        storyteller.improve_beat(0, "Weak dialogue", "Make dialogue better")
        
        assert improvement_prompt is not None
        assert "Elena" in improvement_prompt
        assert "PINNED PASSAGES" in improvement_prompt
        assert "Character name" in improvement_prompt

    def test_prohibited_elements(self):
        """Test adding and removing prohibited elements."""
        storyteller = Storyteller("sk-fake")
        storyteller.add_prohibited_element("Elara")
        assert "Elara" in storyteller.project.bible.prohibited_elements
        
        storyteller.remove_prohibited_element("Elara")
        assert "Elara" not in storyteller.project.bible.prohibited_elements

    def test_add_prohibited_element_duplicate(self):
        """Test that adding the same prohibited element twice doesn't duplicate."""
        storyteller = Storyteller("sk-fake")
        storyteller.add_prohibited_element("Elara")
        storyteller.add_prohibited_element("Elara")
        assert len(storyteller.project.bible.prohibited_elements) == 1


class TestBeat:
    def test_beat_creation(self):
        beat = Beat(title="Test Beat", content="Test content")
        assert beat.title == "Test Beat"
        assert beat.content == "Test content"
        assert beat.id == ""
        assert beat.critique is None
        assert beat.pinned_passages == []

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

    def test_beat_with_pinned_passages(self):
        beat = Beat(
            title="Test Beat",
            content="Test content",
            pinned_passages=[{"text": "Elena", "purpose": "Character"}]
        )
        assert len(beat.pinned_passages) == 1
        assert beat.pinned_passages[0]["text"] == "Elena"
        assert beat.pinned_passages[0]["purpose"] == "Character"

    def test_beat_model_dump(self):
        beat = Beat(title="Test Beat", content="Test content", id="test")
        result = beat.model_dump()
        assert result["title"] == "Test Beat"
        assert result["content"] == "Test content"
        assert result["id"] == "test"

    def test_beat_model_dump_includes_critique(self):
        beat = Beat(
            title="Test Beat",
            content="Test content",
            critique={"rating": 8}
        )
        result = beat.model_dump()
        assert result["critique"] == {"rating": 8}

    def test_beat_model_dump_includes_pinned_passages(self):
        beat = Beat(
            title="Test Beat",
            content="Test content",
            pinned_passages=[{"text": "Elena", "purpose": "Character"}]
        )
        result = beat.model_dump()
        assert result["pinned_passages"] == [{"text": "Elena", "purpose": "Character"}]


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
        
        import os
        import storyteller
        import importlib

        # Mock the directory used by storyteller
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Reload the module to re-trigger top-level prompt loading
        importlib.reload(storyteller)
        
        try:
            assert "Test concept prompt" in storyteller.PROMPT_CONCEPT
            assert "Test beat prompt" in storyteller.PROMPT_BEAT
            assert "Test critique prompt" in storyteller.PROMPT_CRITIQUE
        finally:
            os.chdir(original_cwd)
