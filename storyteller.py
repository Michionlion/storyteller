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
    critique: str = ""  # Store critique for the beat
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
            if beat.critique:
                parts.append(f"CRITIQUE: {beat.critique}")
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

DEFAULT_PROMPT_CRITIQUE = """Review the following prose and provide constructive criticism
focused on: clarity, emotional impact, sensory details, pacing, and show-don't-tell.
Return structured JSON with keys: overall_rating (1-10), strengths, weaknesses, suggestions."""

# Load prompts from files, fallback to defaults if files don't exist
PROMPT_CONCEPT = load_prompt("concept.md")
PROMPT_BEAT = load_prompt("beat.md")
PROMPT_CRITIQUE = load_prompt("critique.md")


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

    def generate_beat(self, title: str, critique: bool = False) -> str:
        """Step 2: Generate prose for a single beat, using all prior context."""
        context = self.project.get_context()
        prompt = f"{PROMPT_BEAT}\n\nContext:\n{context}\n\nBeat: {title}"
        prose = self._call_ai(prompt=prompt, max_tokens=1000)
        beat = Beat(title=title, content=prose, id=title.lower().replace(" ", "_"))
        self.project.beats.append(beat)
        return prose

    def critique_beat(self, beat_index: int) -> Dict:
        """Step 3: Critique an existing beat and store the feedback."""
        if beat_index < 0 or beat_index >= len(self.project.beats):
            raise ValueError("Invalid beat index")
        
        beat = self.project.beats[beat_index]
        context = self.project.get_context()
        prompt = f"{PROMPT_CRITIQUE}\n\nStory Context:\n{context}\n\nBeat to Critique:\n{beat.title}\n\nProse:\n{beat.content}"
        
        critique_data = self._call_ai(prompt=prompt, max_tokens=500)
        beat.critique = critique_data
        
        # Update the project with the critique
        self.project.beats[beat_index] = beat
        return critique_data

    def improve_beat(self, beat_index: int, critique: str, focus_areas: str) -> str:
        """Step 4: Improve a beat based on critique and focus areas."""
        if beat_index < 0 or beat_index >= len(self.project.beats):
            raise ValueError("Invalid beat index")
        
        beat = self.project.beats[beat_index]
        context = self.project.get_context()
        
        prompt = f"""Given the following context, critique, and focus areas, rewrite the beat to address the feedback.

Story Context:
{context}

Original Beat:
{beat.title}

Original Prose:
{beat.content}

Previous Critique:
{critique}

Focus Areas for Improvement:
{focus_areas}

Instructions:
1. Address the specific issues mentioned in the critique
2. Focus on the areas you've identified as needing improvement
3. Keep the scene's purpose intact while enhancing the prose
4. Return only the improved prose, no JSON."""

        improved_prose = self._call_ai(prompt=prompt, max_tokens=1000)
        
        # Update the beat with improved prose
        beat.content = improved_prose
        self.project.beats[beat_index] = beat
        return improved_prose

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
    if "storyteller" in st.session_state:
        storyteller = st.session_state["storyteller"]

        st.hr()

        # Toggle for critique mode
        use_critique_mode = st.toggle("Enable critique loop (improvement workflow)", value=False)
        
        if use_critique_mode:
            st.info("💡 **Critique Mode Enabled**: You can now review and improve your prose through iterative feedback loops.")

        # Show outline
        if storyteller.project.beats:
            st.markdown("## 📋 Outline")
            for i, beat in enumerate(storyteller.get_project().beats):
                status = ""
                if beat.critique:
                    status = " ✅ (critiqued)"
                elif beat.content:
                    status = " ✍️ (draft)"
                st.markdown(f"- **{beat.title}**{status}")

        beat_title = st.text_input("2. Enter a beat title (e.g., 'The Meeting')", "")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Generate Beat", disabled=not beat_title):
                with st.spinner("Writing prose for this beat..."):
                    prose = storyteller.generate_beat(beat_title, critique=use_critique_mode)
                st.success("✍️ Beat written!")
                # Store in session state
                st.session_state["storyteller"] = storyteller
                # Trigger a re-render by using a key
                st.session_state["last_beat_title"] = beat_title

        # Display the most recently generated beat
        if "last_beat_title" in st.session_state:
            last_beat = next((b for b in storyteller.project.beats if b.title == st.session_state["last_beat_title"]), None)
            if last_beat:
                st.markdown(f"## {last_beat.title}")
                st.markdown(last_beat.content)

        # Step 3: Critique and Improve (only if critique mode is enabled)
        if use_critique_mode and len(storyteller.project.beats) > 0:
            st.hr()
            st.markdown("## 📝 Critique & Improve")

            # Select beat to critique
            beat_options = [(i, beat.title) for i, beat in enumerate(storyteller.project.beats)]
            selected_idx = st.selectbox(
                "Select a beat to critique",
                options=[i for i, _ in beat_options],
                format_func=lambda x: beat_options[x][1]
            )

            # Show current beat content
            current_beat = storyteller.project.beats[selected_idx]
            st.markdown(f"### Current: {current_beat.title}")
            st.markdown(current_beat.content)

            # Critique button
            if not current_beat.critique:
                if st.button("🎯 Generate Critique"):
                    with st.spinner("Analyzing prose..."):
                        critique_data = storyteller.critique_beat(selected_idx)
                    st.success("📝 Critique generated!")
                    st.session_state["storyteller"] = storyteller
                    st.session_state["last_critique"] = critique_data
                    st.rerun()

            # Show existing critique
            if current_beat.critique:
                st.markdown("### 📊 Critique Analysis")
                if isinstance(current_beat.critique, dict):
                    st.markdown(f"**Overall Rating:** {current_beat.critique.get('overall_rating', 'N/A')}/10")
                    if 'strengths' in current_beat.critique:
                        st.markdown("**Strengths:**")
                        st.markdown(current_beat.critique['strengths'])
                    if 'weaknesses' in current_beat.critique:
                        st.markdown("**Weaknesses:**")
                        st.markdown(current_beat.critique['weaknesses'])
                    if 'suggestions' in current_beat.critique:
                        st.markdown("**Suggestions:**")
                        st.markdown(current_beat.critique['suggestions'])
                else:
                    st.markdown(current_beat.critique)

                # Focus areas for improvement
                focus_areas = st.text_area(
                    "What would you like to focus on improving?",
                    placeholder="e.g., 'Make the dialogue more natural' or 'Add more sensory details to the setting'",
                    key="focus_areas"
                )

                if st.button("✨ Improve Beat"):
                    if focus_areas:
                        with st.spinner("Rewriting with improvements..."):
                            improved = storyteller.improve_beat(selected_idx, str(current_beat.critique), focus_areas)
                        st.success("✨ Beat improved!")
                        st.session_state["storyteller"] = storyteller
                        st.rerun()
                    else:
                        st.warning("Please describe what you want to improve.")

        st.hr()

        # Step 4: Add Facts for Continuity
        st.markdown("## 📖 Story Bible (Facts)")
        fact_key = st.text_input("Add a narrative fact (key)", "")
        fact_value = st.text_input("Add a narrative fact (value)", "")
        if st.button("Add Fact", disabled=not fact_key or not fact_value):
            storyteller.add_fact(fact_key, fact_value)
            st.success(f"📖 Fact added: {fact_key} = {fact_value}")
            st.session_state["storyteller"] = storyteller
            st.rerun()

        # Show facts
        if storyteller.project.bible.facts:
            for fact in storyteller.project.bible.facts:
                st.markdown(f"- **{fact['key']}:** {fact['value']}")

        st.hr()

        # Step 5: View Full Story
        st.markdown("## 📄 Full Story")
        project = storyteller.get_project()
        if project.beats:
            for beat in project.beats:
                st.markdown(f"### {beat.title}")
                st.markdown(beat.content)
                if beat.critique:
                    st.markdown("*Critique available*")
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
