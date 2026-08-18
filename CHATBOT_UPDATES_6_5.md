# CAMPUS AI 6.5 — Chatbot Upgrade Notes

## Critical fixes

1. **False branch hallucination fixed**
   - `My cutoff is 169, BC, I need government college in Chennai` now keeps `branch=ALL`.
   - The old fuzzy matching that could convert `government` into `Industrial Bio Technology` has been removed.

2. **Explicit defaults**
   - Community: OC
   - District: ALL
   - Branch: ALL
   - College type: ALL

3. **Branch normalization**
   - AIDS / AI&DS / AI & DS / Artificial Intelligence and Data Science → same canonical branch.
   - AIML / AI&ML / AI & ML / Artificial Intelligence and Machine Learning → same separate canonical branch.
   - Common TNEA codes and full branch names are supported.

4. **Eligibility**
   - Only records with a published community cutoff at or below the student's cutoff are presented as eligible.
   - No-cutoff records are never labelled eligible.
   - User filters are not silently relaxed.

5. **College details**
   - Specific college names, aliases and college codes are supported.
   - College detail responses include all branch records and community cutoff values available in the dataset.

6. **TNEA knowledge**
   - Official TNEA 2026 procedure, document and brochure references were refreshed.
   - Current dates/rules are explicitly treated as year-specific.

7. **Conversation controls**
   - Previous conversations are shown in the AI Counsellor sidebar.
   - New Chat, Clear Chat, Share and Delete are grouped under the three-dot menu.

8. **Scrolling**
   - No programmatic scrolling is used.
   - The user manually scrolls the fixed-height answer area.
   - `overflow-anchor` is disabled for the chat result region.

9. **Profile**
   - The profile displays cutoff, community, district, branch and college type, including ALL defaults.
