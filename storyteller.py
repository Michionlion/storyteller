from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# =============================================================================
# 📋 Data Models
# =============================================================================

class Beat(BaseModel):
    """A single scene/section in the story."""
    title: str
    content: str = ""
    id: str = ""
    critique: Optional[Dict[str, Any]] = None
    pinned_passages: List[Dict[str, str]] = Field(default_factory=list)

    def dict(self, **kwargs):
        return super().dict(by_alias=False, **kwargs)


class StoryBible(BaseModel):
    """Shared narrative facts for continuity."""
    facts: List[Dict[str, str]] = []
    prohibited_elements: List[str] = Field(default_factory=list) # Global "Don't use" list


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
        
        if self.bible.prohibited_elements:
            parts.append(f"PROHIBITED ELEMENTS (DO NOT USE THESE NAMES OR PHRASES): {', '.join(self.bible.prohibited_elements)}")

        for fact in self.bible.facts:
            parts.append(f"FACT: {fact['key']}: {fact['value']}")
            
        for beat in self.beats:
            parts.append(f"BEAT: {beat.title}")
            parts.append(f"PROSE: {beat.content}")
            if beat.critique:
                parts.append(f"CRITIQUE: {beat.critique}")
            if beat.pinned_passages:
                pinned = ", ".join([f"{p['text']} ({p['purpose']})" for p in beat.pinned_passages])
                parts.append(f"PINNED PASSAGES (MUST PRESERVE): {pinned}")
                
        return "\n\n".join(parts) if parts else ""


# =============================================================================
# 🧠 AI Prompt Definitions (Loaded from files)
# =============================================================================

def load_prompt(name: str) -> str:
    try:
        with open(f"prompts/{name}.md", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Fallback prompt for {name}"

PROMPT_CONCEPT = load_prompt("concept")
PROMPT_BEAT = load_prompt("beat")
PROMPT_CRITIQUE = load_prompt("critique")


# =============================================================================
# 🔧 Core Service
# =============================================================================

class Storyteller:
    """All-in-one story creation service."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.project: StoryProject = StoryProject()

    def generate_concept(self, seed: str) -> Dict:
        """Step 1: Generate a story concept from a seed idea."""
        response = self._call_ai(
            prompt=f"{PROMPT_CONCEPT}\n\nSeed: {seed}",
            max_tokens=500
        )
        self.project.concept = response.get("concept", "")
        return response

    def generate_beat(self, title: str) -> str:
        """Step 2: Generate prose for a single beat, using all prior context."""
        context = self.project.get_context()
        prompt = f"{PROMPT_BEAT}\n\nContext:\n{context}\n\nBeat: {title}"
        response = self._call_ai(prompt=prompt, max_tokens=1000)
        
        prose = response.get("prose", response.get("content", ""))
        if not prose and isinstance(response, dict):
            prose = str(response)
        elif not prose:
            prose = str(response)

        beat = Beat(title=title, content=prose, id=title.lower().replace(" ", "_"))
        self.project.beats.append(beat)
        return prose

    def critique_beat(self, beat_index: int) -> Dict:
        """Step 3: Critique an existing beat."""
        if not (0 <= beat_index < len(self.project.beats)):
            raise ValueError("Invalid beat index")
        
        beat = self.project.beats[beat_index]
        context = self.project.get_context()
        prompt = f"{PROMPT_CRITIQUE}\n\nContext:\n{context}\n\nProse to critique:\n{beat.content}"
        
        critique_data = self._call_ai(prompt=prompt, max_tokens=500)
        beat.critique = critique_data
        return critique_data

    def improve_beat(self, beat_index: int, critique_text: str, focus_areas: str) -> str:
        """Step 4: Rewrite a beat based on critique and user focus."""
        if not (0 <= beat_index < len(self.project.beats)):
            raise ValueError("Invalid beat index")
            
        beat = self.project.beats[beat_index]
        context = self.project.get_context()
        
        prompt = (
            f"{PROMPT_BEAT}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"CRITIQUE TO ADDRESS:\n{critique_text}\n\n"
            f"USER FOCUS AREAS:\n{focus_areas}\n\n"
            f"REWRITE THE FOLLOWING BEAT:\n{beat.content}"
        )
        
        response = self._call_ai(prompt=prompt, max_tokens=1000)
        new_prose = response.get("prose", response.get("content", ""))
        if not new_prose and isinstance(response, dict):
            new_prose = str(response)
        elif not new_prose:
            new_prose = str(response)

        beat.content = new_prose
        return new_prose

    def add_pinned_passage(self, beat_index: int, text: str, purpose: str):
        """Add a passage that the AI must not change."""
        if not (0 <= beat_index < len(self.project.beats)):
            raise ValueError("Invalid beat index")
        self.project.beats[beat_index].pinned_passages.append({"text": text, "purpose": purpose})

    def add_fact(self, key: str, value: str):
        """Add a narrative fact for continuity."""
        self.project.bible.facts.append({"key": key, "value": value})

    def add_prohibited_element(self, element: str):
        """Add a global element to avoid."""
        if element and element not in self.project.bible.prohibited_elements:
            self.project.bible.prohibited_elements.append(element)

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
                content = response.choices[0].message.content
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    parts = content.split("```")
                    if len(parts) >= 3:
                        try:
                            json.loads(parts[1].strip())
                            content = parts[1].strip()
                        except:
                            content = parts[1].strip()
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"prose": content, "content": content}

            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"AI calls failed after 3 attempts: {e}")
                time.sleep(2)
        return {}


# =============================================================================
# 💻 Streamlit UI
# =============================================================================

import streamlit as st

def main():
    st.set_page_config(page_title="Storyteller", page_icon="📝", layout="wide")

    st.title("📝 Storyteller")
    
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("OpenAI API Key", type="password")
        enable_critique = st.checkbox("Enable critique loop", value=True)

    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar.")
        return

    if "storyteller" not in st.session_state:
        st.session_state["storyteller"] = Storyteller(api_key)
    
    storyteller = st.session_state["storyteller"]

    seed = st.text_area("1. Enter a story seed", "")
    if st.button("Generate Concept", disabled=not seed):
        with st.spinner("Generating concept..."):
            concept = storyteller.generate_concept(seed)
            st.success("Concept generated!")
            st.session_state["concept_generated"] = True
            st.rerun()

    if st.session_state.get("concept_generated"):
        project = storyteller.get_project()
        st.markdown(f"### Concept: {project.concept}")

        st.divider()
        st.subheader("📋 Outline & Prose")
        
        for i, beat in enumerate(project.beats):
            with st.expander(f"Beat {i+1}: {beat.title}", expanded=True):
                st.write(beat.content)
                
                if enable_critique:
                    st.divider()
                    st.markdown("#### 🛠 Refinement Tools")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Critique Beat {i+1}", key=f"crit_{i}"):
                            with st.spinner("Critiquing..."):
                                critique = storyteller.critique_beat(i)
                                st.session_state[f"critique_{i}"] = critique
                                st.rerun()
                    
                    if f"critique_{i}" in st.session_state:
                        crit = st.session_state[f"critique_{i}"]
                        st.info(f"**Rating: {crit.get('overall_rating', '?')}/10**")
                        st.write(f"**Strengths:** {crit.get('strengths', '')}")
                        st.write(f"**Weaknesses:** {crit.get('weaknesses', '')}")
                        st.write(f"**Suggestions:** {crit.get('suggestions', '')}")
                        with col2:
                            focus = st.text_input("Focus areas (e.g. 'more tension')", key=f"focus_{i}")
                            if st.button(f"Improve Beat {i+1}", key=f"imp_{i}"):
                                with st.spinner("Rewriting..."):
                                    storyteller.improve_beat(i, str(crit), focus)
                                    st.rerun()

                    with st.expander("Pin Passages (Keep these constant)"):
                        p_text = st.text_input("Text to pin", key=f"ptext_{i}")
                        p_purp = st.text_input("Purpose", key=f"ppurp_{i}")
                        if st.button("Pin Passage", key=f"ppin_{i}"):
                            storyteller.add_pinned_passage(i, p_text, p_purp)
                            st.rerun()
                        for p_idx, p in enumerate(beat.pinned_passages):
                            st.text(f"📌 '{p['text']}' ({p['purpose']})")
                            if st.button("Remove", key=f"premove_{i}_{p_idx}"):
                                beat.pinned_passages.pop(p_idx)
                                st.rerun()

        st.divider()
        st.subheader("Add New Beat")
        new_beat_title = st.text_input("New beat title", key="new_beat_input")
        if st.button("Add Beat", key="add_beat_btn"):
            if new_beat_title:
                with st.spinner("Generating beat..."):
                    storyteller.generate_beat(new_beat_title)
                st.rerun()

        st.divider()
        st.subheader("📖 Story Bible")
        
        st.markdown("#### 🚫 Prohibited Elements (Global Avoidance)")
        pro_col1, pro_col2 = st.columns([3, 1])
        with pro_col1:
            new_prohibited = st.text_input("Add a name/phrase to prohibit (e.g. 'Elara')")
        with pro_col2:
            if st.button("Prohibit"):
                if new_prohibited:
                    storyteller.add_prohibited_element(new_prohibited)
                    st.rerun()
        
        if project.bible.prohibited_elements:
            st.caption("Currently Prohibited:")
            for item in project.bible.prohibited_elements:
                st.markdown(f"- `{item}`")
            if st.button("Clear Prohibited List"):
                project.bible.prohibited_elements = []
                st.rerun()

        st.divider()
        st.markdown("#### 📝 Narrative Facts")
        c1, c2 = st.columns(2)
        with c1:
            f_key = st.text_input("Fact Key (e.g. 'Character Name')")
        with c2:
            f_val = st.text_input("Fact Value (e.g. 'Elena')")
        if st.button("Add Fact"):
            storyteller.add_fact(f_key, f_val)
            st.rerun()
        for fact in project.bible.facts:
            st.text(f"{fact['key']}: {fact['value']}")

        st.divider()
        if st.button("Export Project (JSON)"):
            st.download_button("Download", project.json(), "story.json", "application/json")

if __name__ == "__main__":
    main()
