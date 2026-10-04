# AI Interview Performance Analyzer
### Academic Field Engineering Project (FEP) — Level: BTech Computer Engineering (2nd Year)

> **Core Philosophy:** "We are not just conducting an AI interview. We are using every interview attempt to understand the candidate, identify what needs improvement, and prepare them for the next interview."

---

## 🌟 The Continuous Improvement Cycle
```
RESUME ➔ TARGET ➔ INTERVIEW ➔ ANALYZE ➔ PREPARE ➔ PRACTICE ➔ NEXT INTERVIEW ➔ IMPROVE
```

---

## 🚀 How to Run the Web Application

1. Open PowerShell or Command Prompt.
2. Navigate to the project directory:
   ```powershell
   cd C:\Users\HP\.gemini\antigravity\scratch\ai_interview_analyzer
   ```
3. Start the Flask server:
   ```powershell
   python app.py
   ```
4. Open your web browser and visit:
   ```
   http://127.0.0.1:5000
   ```

---

## 🏗️ Architecture & Features Built

| Feature / Page | Technical Details |
| :--- | :--- |
| **1. Landing & Concept (`/`)** | Modern UI following Section 24 design guidelines (light blue & soft purple accent, navy typography, clean cards). Outlines the academic FEP journey. |
| **2. Candidate Profile (`/dashboard`)** | Candidate information, active resume status, best score, average performance, and past interview sessions. |
| **3. Resume Parser (`/resume`)** | Uploads PDF resumes and extracts technical skills, education, and project titles using `pypdf` to personalize interview questions. |
| **4. Setup Wizard (`/interview-setup`)** | Configures Industry (IT, Banking, Healthcare, E-Commerce, etc.), Role (Software Dev, Web Dev, Data Analyst, AI/ML, Cybersecurity), Type (HR, Technical, Role-based), and Difficulty. |
| **5. Adaptive Interview Room (`/interview/<id>`)** | **Video Mode**: Live webcam preview.<br>**Audio Mode**: Speech-to-text dictation via the browser's Web Speech API + AI speech synthesis to vocalize questions aloud.<br>**Adaptive Logic**: Dynamically adjusts follow-up questions depending on answer length and depth. |
| **6. AI Analysis Dashboard (`/result/<id>`)** | Evaluates answers across 5 core dimensions: **Communication, Relevance, Clarity, Fluency** (with filler word detection), and **Technical Knowledge**. Features interactive **"Explain My Score"** breakdown. |
| **7. "Prepare for My Next Interview" (`/prepare/<id>`)** | Identifies lowest-scoring areas and automatically generates a targeted preparation curriculum using the **STAR methodology** (Situation, Task, Action, Result) with interactive practice drills. |
| **8. Attempt Comparison (`/progress`)** | Compares **Attempt 1 vs Attempt 2** side-by-side with exact percentage deltas and improvement metrics. |

---

## 📂 Project Directory Structure

```
ai_interview_analyzer/
│── app.py                   # Main Flask routes & controllers
│── requirements.txt         # Dependencies (Flask, pypdf, google-generativeai)
│── seed_demo.py             # Pre-populates sample Attempt 1 data for immediate demo
│── test_app.py              # Automated verification test suite for all routes
│── interview_analyzer.db    # SQLite relational database
│
├── database/
│   └── db.py                # Schema for users, resumes, interviews, questions, answers, analysis, practice_plan
│
├── services/
│   ├── ai_service.py        # Adaptive question generator & 5-metric evaluation engine
│   ├── resume_service.py    # PDF resume text extraction & skill/project parser
│   └── analysis_service.py  # Personalized preparation planner & attempt comparison
│
├── static/
│   ├── css/
│   │   └── style.css        # Clean UI styling (Section 24 specification)
│   └── js/
│       └── interview.js     # Webcam preview, speech-to-text mic recording, timers
│
└── templates/
    ├── base.html            # Common navigation header & footer
    ├── index.html           # Landing page & How It Works
    ├── dashboard.html       # Candidate profile & interview history
    ├── resume.html          # PDF upload & extracted insights
    ├── interview_setup.html # Setup wizard (Industry, Role, Type)
    ├── interview.html       # Adaptive interview room (Split-screen Audio/Video)
    ├── result.html          # AI Performance Analysis & "Explain My Score"
    ├── preparation.html     # Personalized next-interview plan & STAR practice
    ├── progress.html        # Longitudinal attempt comparison dashboard
    └── login.html           # Authentication / demo candidate switch
```

---

## 🛡️ Academic Project Limitation Notice
*As mandated in Section 26 of the project specification:*
> "The platform helps candidates become better prepared for their targeted interview by identifying weaknesses and providing personalized practice. It does not claim to make a candidate 100% ready or guarantee job selection, as real hiring outcomes depend on employer requirements, competition, and actual interview conditions."
