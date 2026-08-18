# CAMPUS AI — TNEA Counselling Advisor 6.5

This version upgrades the existing AI Counsellor without rebuilding the project's Home, AI Counsellor, College Finder or Cutoff Calculator pages.

## 1. Project overview

Campus AI is a dataset-grounded TNEA counselling assistant. The chatbot accepts English, Tamil and Tanglish, understands unordered natural-language inputs, maintains a counselling profile, retrieves eligible college/branch records and answers general TNEA procedure questions.

## 2. Important behaviour

- Cutoff is extracted from natural language and can be calculated from Mathematics + Physics/2 + Chemistry/2.
- Community defaults to **OC** when omitted.
- District defaults to **ALL** when omitted.
- Branch defaults to **ALL** when omitted.
- College type defaults to **ALL** when omitted.
- Government/private/autonomous/university filters are applied only when the user actually requests them.
- Branch abbreviations and full names are normalized. In particular, AIDS / AI&DS / AI & DS / Artificial Intelligence and Data Science are treated as the same branch family; AIML / AI&ML / Artificial Intelligence and Machine Learning are treated as a separate branch family.
- A false branch cannot be inferred from unrelated prose such as `My cutoff is 169, BC, I need government college in Chennai`.
- College-code queries return all branch records for that college.
- Eligible recommendations use the supplied community closing cutoff and return all matching eligible records within the request filters.
- Records without a published community cutoff are not presented as eligible.
- Missing college type never silently becomes Government, Private or Autonomous.

## 3. Folder structure

```text
Campus-AI-FINAL/
├── backend/
│   ├── app/
│   │   ├── chatbot.py
│   │   ├── data.py
│   │   ├── knowledge.py
│   │   ├── nlp.py
│   │   └── aliases.py
│   ├── data/
│   │   ├── tnea_2025_cleaned.csv
│   │   └── tnea_2025_processed.json
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   └── package.json
└── README.md
```

## 4. Installation

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Frontend

```powershell
cd frontend
npm install
```

## 5. Start backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

## 6. Start frontend

```powershell
cd frontend
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## 7. Run tests

```powershell
cd backend
python -m unittest discover -s tests -v
```

The current upgrade includes tests for context memory, missing filters, branch aliases, false branch prevention, college-code lookup, college-type filtering, cutoff calculation and Clear Chat.

## 8. Dataset

Primary college/branch/cutoff source:

`backend/data/tnea_2025_processed.json`

The dataset contains the supplied TNEA 2025 college/branch/community cutoff records. College-specific facts are never fabricated when a field is absent.

## 9. Chatbot architecture

```text
User message
   ↓
Normalization (English / Tamil / Tanglish)
   ↓
Entity extraction
   ├── cutoff
   ├── community
   ├── district
   ├── branch
   └── college type
   ↓
Conversation profile update
   ↓
Intent detection
   ↓
Dataset retrieval / eligibility filtering
   ↓
TNEA knowledge or branch explanation
   ↓
Deterministic response + optional Groq language generation
```

## 10. Supported query types

- Eligible college recommendations
- Government / private / autonomous / university filtering
- District-specific college lists
- Branch-specific college lists
- Branch explanations
- Branch comparisons
- College details
- College-code lookup
- College branch/cutoff lists
- Cutoff/community/district/branch follow-ups
- TNEA registration
- Documents
- Eligibility
- Choice filling
- Rank list
- Allotment
- Confirmation
- Reporting
- Fees/payment procedure
- Special reservations
- Current-year schedule guidance

## 11. Official TNEA sources

- https://www.tneaonline.org/
- https://static.tneaonline.org/docs/2_Information_Brochure_2026.pdf
- https://static.tneaonline.org/docs/4_Instructions_for_Registration_in_English_2026.pdf
- https://static.tneaonline.org/docs/TNEA_Tentative_Schedule_2026.pdf

Official TNEA procedure and document information is preferred over blogs or unofficial summaries. Current dates/rules should always be verified on the live portal.

For branch/course naming and curriculum references, Anna University's Centre for Academic Courses is also used as an official academic reference:

- https://cac.annauniv.edu/aidetails/ai_ug_courses.html
- https://cac.annauniv.edu/uddetails/ud_ug_courses.html

## 12. Conversation controls

The AI Counsellor keeps the active counselling profile until Clear Chat/New Chat is selected.

The sidebar provides:

- Previous conversations
- New Chat
- Clear Chat
- Share
- Delete

The actions are grouped under the three-dot menu as requested.

## 13. Scrolling behaviour

The chatbot does **not** call `scrollIntoView`, `scrollTo`, or programmatically set `scrollTop`. The answer area is a fixed-height scrollable chat box. The user manually scrolls through answers and results.

## 14. Troubleshooting

### FastAPI port already in use

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Then set the frontend API URL if required.

### Groq is unavailable

The core chatbot still works with deterministic NLP + dataset retrieval. Groq is optional and should only be added through environment variables.

### Frontend dependencies missing

```powershell
cd frontend
npm install
npm run dev
```

### No matching colleges

The chatbot reports that no eligible dataset record matched the exact filters. It does not silently relax the user's requirements or invent colleges.

## CAMPUS AI 6.7 Chatbot/UI fixes

This upgrade keeps the existing Home, AI Counsellor, College Finder and Cutoff Calculator pages and focuses on conversation correctness and the AI Counsellor presentation.

### Conversation intent separation
- Branch comparisons such as `Which is best CSE or ECE?` are handled as branch comparisons and do not trigger college records.
- Informational questions such as `What is ECE?` do not silently change the student's branch preference or trigger a college search.
- A branch becomes a counselling filter only when the user clearly asks for college recommendations/searches, or makes a contextual follow-up such as `Show ECE colleges`.
- College-code/detail questions remain college-information queries.
- Unspecified profile fields remain `null` internally; recommendation defaults are applied only at retrieval time (community OC, district ALL, branch ALL, college type ALL). This prevents defaults from being presented as facts the student supplied.

### Result presentation
- The backend still returns all eligible records.
- The AI Counsellor initially displays only the first 5 matching eligible colleges.
- `Show more eligible colleges` reveals more results in small increments.
- `View all ... eligible colleges` opens the complete result set when requested.
- This keeps the chat box a fixed size instead of making one answer grow the page indefinitely.

### Scrolling/layout
- The message area is a fixed-height, independently scrollable container.
- Programmatic scrolling is not used.
- The user controls scrolling inside the chat area.
- Sidebar and counsellor workspace are kept at a consistent desktop height; the chat message list scrolls internally.

### Regression tests
Run:

```powershell
cd backend
$env:PYTHONPATH='.'
pytest -q tests/test_chatbot_regressions.py
```

The included regression suite covers false branch detection, college-code lookups, unordered counselling context, branch information vs. recommendation intent, contextual branch follow-ups, and non-invented profile defaults.
#   C H A T B O T - A I -  
 