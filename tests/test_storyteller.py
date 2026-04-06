"""Tests for storyteller.py — keeps the 'tested' guarantee."""

import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storyteller import StoryProject, Storyteller


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
        beat = {"title": "The Plan", "content": "They planned it..."}
        project.beats.append(beat)
        context = project.get_context()
        assert "The Plan" in context
        assert "They planned it..." in context

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
        
        # Monkeypatch to use temp directory
        import storyteller
        original_path = os.path.dirname(storyteller.__file__)
        monkeypatch.setattr(storyteller, "__file__", str(tmp_path / "storyteller.py"))
        
        # Reload to test prompt loading
        import importlib
        importlib.reload(storyteller)
        
        assert "Test concept prompt" in storyteller.PROMPT_CONCEPT
        assert "Test beat prompt" in storyteller.PROMPT_BEAT

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
