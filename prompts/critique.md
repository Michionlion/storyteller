# prompts/critique.md
# Prose Critique Prompt

Review the following prose and provide constructive criticism
focused on: clarity, emotional impact, sensory details, pacing, and show-don't-tell.
Return structured JSON with keys: overall_rating (1-10), strengths, weaknesses, suggestions.

## Pinned Passages

When reviewing prose that includes pinned passages (marked with "PINNED PASSAGES:" in the context), 
be aware that these exact phrases must be preserved during any rewrite. The critique should focus 
on improving surrounding text while maintaining these key elements.

## Critique Guidelines

## Critique Guidelines

### What to Evaluate
- **Clarity**: Is the scene easy to understand? Are characters and actions clear?
- **Emotional Impact**: Does the prose evoke the intended emotions? Are characters relatable?
- **Sensory Details**: Does the writing engage multiple senses? Is the setting vivid?
- **Pacing**: Does the scene move at an appropriate speed? Are there slow or rushed sections?
- **Show, Don't Tell**: Is the writing showing actions and reactions rather than just stating emotions?

### Critique Structure
1. **Overall Rating** (1-10): A holistic assessment of the writing quality
2. **Strengths**: What's working well that should be preserved
3. **Weaknesses**: Specific issues that need improvement
4. **Suggestions**: Concrete, actionable recommendations for improvement

### Critique Style
- Be specific and actionable
- Balance criticism with genuine praise
- Focus on what's most important for the scene's purpose
- Avoid vague statements like "make it better" — be specific about how

## Example Output

```json
{
  "overall_rating": 7,
  "strengths": "The dialogue feels natural and reveals character dynamics effectively. The opening image of the rain creates immediate atmosphere.",
  "weaknesses": "The protagonist's internal thoughts are stated rather than shown. The pacing slows significantly in the middle section. Some descriptions rely on clichés (e.g., 'dark as night').",
  "suggestions": "1. Show the protagonist's anxiety through physical reactions rather than stating they're nervous. 2. Consider cutting or condensing the middle dialogue section. 3. Replace 'dark as night' with a more specific, original image. 4. Add a sensory detail about sound or smell to ground the scene."
}
```
