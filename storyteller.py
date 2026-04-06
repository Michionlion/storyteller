"""
storyteller.py — A single-file AI story writing tool for rapid prototyping.

Design goals:
- One file, one dependency (Streamlit + openai)
- No database, no complex architecture
- Directly exposes the AI workflow
- Still testable with pytest
"""

import os
import streamlit as st
from typing import Optional, Dict, List
from pydantic import BaseModel


# =============================================================================
# 📋 Data Models (Replaces the entire `core/models.py` layer)
# =============================================================================

class Beat(BaseModel):
    """A single scene/section in the story."""
    title: str
    content: str = ""
    id: str = ""

    def dict(self, **kwargs):
        return super().dict(by_alias=False, **kwargs)


class StoryBible(BaseModel):
    """Shared narrative facts for continuity."""
    facts: List[Dict[str, str]] = []


class StoryProject(BaseModel):
    """The complete story in memory."""
    concept: str = ""
    beats: List[Beat] = []
    bible: StoryBible = StoryBible()

    def get_context(self) -> str:
        """Build the context packet for the AI — the continuity engine."""
        parts = []
        if self.concept:
            parts.append(f"STORY CONCEPT: {self.concept}")
        for fact in self.bible.facts:
            parts.append(f"FACT: {fact['key']}: {fact['value']}")
        for beat in self.beats:
            parts.append(f"BEAT: {beat.title}")
            parts.append(f"PROSE: {beat.content}")
        return "\n\n".join(parts) if parts else ""


# =============================================================================
# 🧠 AI Prompt Definitions (Replaces `agents/orchestrator.py`)
# =============================================================================

def load_prompt(filename: str) -> str:
    """Load a prompt from a markdown file in the prompts directory."""
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    filepath = os.path.join(prompts_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        st.error(f"Prompt file not found: {filepath}")
        return f"[Prompt file '{filename}' not found]"


# Default prompts (can be overridden by markdown files)
DEFAULT_PROMPT_CONCEPT = """You are a creative story concept generator. Given a seed idea,
generate a compelling story concept including genre, setting, characters, and
a central conflict. Return structured JSON with keys: concept, genre, setting,
characters, conflict."""

DEFAULT_PROMPT_BEAT = """Given the story context and a beat title, write immersive prose
for that beat. Show, don't tell. Include dialogue, sensory details, and
emotional resonance. Return only the prose, no JSON."""

# Load prompts from files, fallback to defaults if files don't exist
PROMPT_CONCEPT = load_prompt("concept.md")
PROMPT_BEAT = load_prompt("beat.md")


# =============================================================================
# 🔧 Core Service (Collapses `project_manager.py` + `story_creation_service.py`)
# =============================================================================

class Storyteller:
    """All-in-one story creation service. No separation of concerns — that's
    the tradeoff for a single-file prototype."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.project: StoryProject = StoryProject()

    def generate_concept(self, seed: str) -> Dict:
        """Step 1: Generate a story concept from a seed idea."""
        response = self._call_ai(
            prompt=f"{PROMPT_CONCEPT}\n\nSeed: {seed}",
            max_tokens=500
        )
        self.project.concept = response["concept"]
        return response

    def generate_beat(self, title: str) -> str:
        """Step 2: Generate prose for a single beat, using all prior context."""
        context = self.project.get_context()
        prompt = f"{PROMPT_BEAT}\n\nContext:\n{context}\n\nBeat: {title}"
        prose = self._call_ai(prompt=prompt, max_tokens=1000)
        beat = Beat(title=title, content=prose, id=title.lower().replace(" ", "_"))
        self.project.beats.append(beat)
        return prose

    def add_fact(self, key: str, value: str):
        """Add a narrative fact for continuity."""
        self.project.bible.facts.append({"key": key, "value": value})

    def get_project(self) -> StoryProject:
        return self.project

    def _call_ai(self, prompt: str, max_tokens: int) -> Dict:
        import json
        import time
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful story writing assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=0.8,
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        raise RuntimeError("AI calls failed after 3 attempts")


# =============================================================================
# 💻 Streamlit UI (Replaces the Flet `ui/` layer)
# =============================================================================

def main():
    st.set_page_config(
        page_title="Storyteller",
        page_icon="📝",
        layout="wide"
    )

    st.title("📝 Storyteller")
    st.markdown("""
        A minimal AI-powered story writing tool. Enter a seed idea, let AI
        generate a concept, then step through beats to build your story.
    """)

    # --- Side panel (configuration) ---

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required to generate AI content"
        )
        if api_key:
            st.success("API key accepted")

    # --- Main flow ---

    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar.")
        return

    storyteller = Storyteller(api_key)

    # Step 1: Generate Concept
    seed = st.text_area("1. Enter a story seed (one sentence or phrase)", "")
    if st.button("Generate Concept", disabled=not seed):
        with st.spinner("Generating story concept..."):
            concept = storyteller.generate_concept(seed)
        st.success("🎯 Story concept generated!")
        st.markdown(f"## Concept")
        st.markdown(f"**Genre:** {concept['genre']}")
        st.markdown(f"**Setting:** {concept['setting']}")
        st.markdown(f"**Characters:** {', '.join(concept['characters'])}")
        st.markdown(f"**Conflict:** {concept['conflict']}")

        # Store in session state so it persists
        st.session_state["storyteller"] = storyteller

    # Step 2: Generate Beats
    if "storyteller" in st.session_state and st.session_state["storyteller"].project.beats:
        storyteller = st.session_state["storyteller"]

        st.hr()

        st.markdown("## 📋 Outline")
        for beat in storyteller.get_project().beats:
            st.markdown(f"- **{beat.title}**")

        beat_title = st.text_input("2. Enter a beat title (e.g., 'The Meeting')", "")
        if st.button("Generate Beat", disabled=not beat_title):
            with st.spinner("Writing prose for this beat..."):
                prose = storyteller.generate_beat(beat_title)
            st.success("✍️ Beat written!")
            st.markdown(f"## {beat_title}")
            st.markdown(prose)

        st.hr()

        # Step 3: Add Facts for Continuity
        fact_key = st.text_input("3. Add a narrative fact (key)", "")
        fact_value = st.text_input("3. Add a narrative fact (value)", "")
        if st.button("Add Fact", disabled=not fact_key or not fact_value):
            storyteller.add_fact(fact_key, fact_value)
            st.success(f"📖 Fact added: {fact_key} = {fact_value}")
            st.session_state["storyteller"] = storyteller

        st.hr()

        # Step 4: View Full Story
        st.markdown("## 📄 Full Story")
        project = storyteller.get_project()
        if project.beats:
            for beat in project.beats:
                st.markdown(f"### {beat.title}")
                st.markdown(beat.content)
                st.markdown("---")

        # Export
        if st.button("Export as JSON"):
            st.json(project.dict(by_alias=False))
            st.download_button(
                label="Download JSON",
                data=project.json(by_alias=False, indent=2),
                file_name="storyteller_project.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()
