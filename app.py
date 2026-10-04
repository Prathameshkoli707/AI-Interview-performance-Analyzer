import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

from database.db import get_db_connection, init_db
from services.resume_service import extract_text_from_pdf, analyze_resume_text
from services.ai_service import generate_question, evaluate_answer
from services.analysis_service import generate_personalized_plan, compare_interview_attempts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "fep-ai-interview-analyzer-secret-key-2026"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

# Initialize database schema on startup
with app.app_context():
    init_db()

def get_current_user_id():
    """Returns logged-in user id or default student account (ID 1)."""
    return session.get("user_id", 1)

@app.before_request
def make_session_permanent():
    if "user_id" not in session:
        session["user_id"] = 1
        session["user_name"] = "Alex Johnson"

# ----------------- Navigation & Auth Routes -----------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and user["password"] == password:
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. You can try student@example.com / password123", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out successfully.", "info")
    return redirect(url_for("index"))

# ----------------- Candidate Dashboard -----------------

@app.route("/dashboard")
def dashboard():
    user_id = get_current_user_id()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    resume = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,)).fetchone()
    
    interviews = conn.execute(
        "SELECT * FROM interviews WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    best_score_row = conn.execute(
        "SELECT MAX(overall_score) as best_score, AVG(overall_score) as avg_score, COUNT(*) as total FROM interviews WHERE user_id = ? AND overall_score > 0",
        (user_id,)
    ).fetchone()

    plans = conn.execute(
        "SELECT * FROM practice_plan WHERE user_id = ? ORDER BY created_at DESC LIMIT 3",
        (user_id,)
    ).fetchall()

    conn.close()

    resume_skills = json.loads(resume["skills"]) if resume and resume["skills"] else []
    resume_projects = json.loads(resume["projects"]) if resume and resume["projects"] else []

    return render_template(
        "dashboard.html",
        user=user,
        resume=resume,
        resume_skills=resume_skills,
        resume_projects=resume_projects,
        interviews=interviews,
        best_score=round(best_score_row["best_score"] or 0, 1),
        avg_score=round(best_score_row["avg_score"] or 0, 1),
        total_interviews=best_score_row["total"] or 0,
        plans=plans
    )

# ----------------- Resume Module -----------------

@app.route("/resume", methods=["GET", "POST"])
def resume_view():
    user_id = get_current_user_id()
    conn = get_db_connection()

    if request.method == "POST":
        if "resume_file" not in request.files:
            flash("No file selected", "danger")
            return redirect(request.url)
        
        file = request.files["resume_file"]
        if file.filename == "":
            flash("No file selected", "danger")
            return redirect(request.url)

        if file and file.filename.lower().endswith(".pdf"):
            filename = f"user_{user_id}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            # Extract text & analyze with PyPDF
            raw_text = extract_text_from_pdf(save_path)
            analysis = analyze_resume_text(raw_text)

            conn.execute("""
            INSERT INTO resumes (user_id, file_path, extracted_text, skills, projects, education, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                save_path,
                raw_text[:4000],
                json.dumps(analysis["skills"]),
                json.dumps(analysis["projects"]),
                analysis["education"],
                analysis["experience"]
            ))
            conn.commit()
            flash("Resume uploaded and analyzed successfully by AI!", "success")
            conn.close()
            return redirect(url_for("resume_view"))
        else:
            flash("Please upload a valid PDF document.", "warning")

    resume = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,)).fetchone()
    conn.close()

    skills = json.loads(resume["skills"]) if resume and resume["skills"] else []
    projects = json.loads(resume["projects"]) if resume and resume["projects"] else []

    return render_template("resume.html", resume=resume, skills=skills, projects=projects)

# ----------------- Interview Setup -----------------

@app.route("/interview-setup")
def interview_setup():
    user_id = get_current_user_id()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    resume = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,)).fetchone()
    conn.close()
    return render_template("interview_setup.html", user=user, resume=resume)

@app.route("/start-interview", methods=["POST"])
def start_interview():
    user_id = get_current_user_id()
    data = request.get_json() or {}

    industry = data.get("industry", "IT & Software")
    role = data.get("role", "Software Developer")
    interview_type = data.get("interview_type", "Technical")
    difficulty = data.get("difficulty", "Medium")
    num_questions = int(data.get("num_questions", 4))

    conn = get_db_connection()
    # Fetch candidate resume context
    resume = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,)).fetchone()
    resume_context = {}
    if resume:
        resume_context = {
            "skills": json.loads(resume["skills"]) if resume["skills"] else [],
            "projects": json.loads(resume["projects"]) if resume["projects"] else [],
            "education": resume["education"] or ""
        }

    # Create interview session
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO interviews (user_id, industry, job_role, interview_type, difficulty, num_questions, status)
    VALUES (?, ?, ?, ?, ?, ?, 'in_progress')
    """, (user_id, industry, role, interview_type, difficulty, num_questions))
    interview_id = cursor.lastrowid

    # Generate initial question
    q1_text = generate_question(industry, role, interview_type, difficulty, resume_context, [])
    cursor.execute("""
    INSERT INTO questions (interview_id, question_text, question_type, difficulty, question_order)
    VALUES (?, ?, ?, ?, 1)
    """, (interview_id, q1_text, interview_type, difficulty))
    
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "interview_id": interview_id,
        "redirect_url": url_for("interview_room", interview_id=interview_id)
    })

# ----------------- Interactive Mock Interview Room -----------------

@app.route("/interview/<int:interview_id>")
def interview_room(interview_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    interview = conn.execute("SELECT * FROM interviews WHERE interview_id = ? AND user_id = ?", (interview_id, user_id)).fetchone()
    if not interview:
        conn.close()
        flash("Interview session not found.", "danger")
        return redirect(url_for("dashboard"))

    # Fetch latest question or create one
    questions = conn.execute(
        "SELECT * FROM questions WHERE interview_id = ? ORDER BY question_order ASC",
        (interview_id,)
    ).fetchall()

    answers = conn.execute(
        "SELECT * FROM answers WHERE user_id = ? AND question_id IN (SELECT question_id FROM questions WHERE interview_id = ?)",
        (user_id, interview_id)
    ).fetchall()

    current_order = len(answers) + 1
    total_q = interview["num_questions"]

    # Current question
    current_q = None
    for q in questions:
        if q["question_order"] == current_order:
            current_q = q
            break

    conn.close()
    return render_template(
        "interview.html",
        interview=interview,
        current_question=current_q,
        current_step=current_order,
        total_questions=total_q
    )

@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    user_id = get_current_user_id()
    data = request.get_json() or {}

    interview_id = data.get("interview_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text", "").strip()

    conn = get_db_connection()
    interview = conn.execute("SELECT * FROM interviews WHERE interview_id = ?", (interview_id,)).fetchone()
    question = conn.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,)).fetchone()
    resume = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,)).fetchone()

    resume_context = {}
    if resume:
        resume_context = {
            "skills": json.loads(resume["skills"]) if resume["skills"] else [],
            "projects": json.loads(resume["projects"]) if resume["projects"] else []
        }

    # Evaluate the individual answer
    eval_res = evaluate_answer(
        question=question["question_text"],
        answer=answer_text,
        role=interview["job_role"],
        interview_type=interview["interview_type"],
        resume_context=resume_context
    )

    # Insert answer
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO answers (question_id, user_id, answer_text)
    VALUES (?, ?, ?)
    """, (question_id, user_id, answer_text))
    answer_id = cursor.lastrowid

    # Insert individual answer analysis
    cursor.execute("""
    INSERT INTO analysis (interview_id, answer_id, relevance_score, clarity_score, communication_score, fluency_score, technical_score, strengths, weaknesses, feedback, explain_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        interview_id,
        answer_id,
        eval_res["relevance_score"],
        eval_res["clarity_score"],
        eval_res["communication_score"],
        eval_res["fluency_score"],
        eval_res["technical_score"],
        json.dumps(eval_res["strengths"]),
        json.dumps(eval_res["weaknesses"]),
        eval_res["feedback"],
        json.dumps(eval_res["explain"])
    ))

    # Check answered count
    answered_count = conn.execute("""
        SELECT COUNT(*) as count FROM answers
        WHERE question_id IN (SELECT question_id FROM questions WHERE interview_id = ?)
    """, (interview_id,)).fetchone()["count"]

    is_completed = answered_count >= interview["num_questions"]

    if is_completed:
        # Calculate overall interview average score
        scores = conn.execute("""
            SELECT AVG(relevance_score) as avg_rel,
                   AVG(clarity_score) as avg_cla,
                   AVG(communication_score) as avg_com,
                   AVG(fluency_score) as avg_flu,
                   AVG(technical_score) as avg_tec
            FROM analysis WHERE interview_id = ?
        """, (interview_id,)).fetchone()

        overall = round((scores["avg_rel"] + scores["avg_cla"] + scores["avg_com"] + scores["avg_flu"] + scores["avg_tec"]) / 5.0, 1)

        cursor.execute("UPDATE interviews SET overall_score = ?, status = 'completed' WHERE interview_id = ?", (overall, interview_id))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "completed",
            "message": "Interview completed successfully!",
            "redirect_url": url_for("interview_result", interview_id=interview_id)
        })

    # Generate next adaptive question
    # Gather previous turns for context
    past_qa = []
    past_rows = conn.execute("""
        SELECT q.question_text, a.answer_text FROM questions q
        JOIN answers a ON q.question_id = a.question_id
        WHERE q.interview_id = ?
        ORDER BY q.question_order ASC
    """, (interview_id,)).fetchall()

    for r in past_rows:
        past_qa.append({"question": r["question_text"], "answer": r["answer_text"]})

    next_order = answered_count + 1
    next_question_text = generate_question(
        industry=interview["industry"],
        role=interview["job_role"],
        interview_type=interview["interview_type"],
        difficulty=interview["difficulty"],
        resume_context=resume_context,
        previous_qa=past_qa
    )

    cursor.execute("""
    INSERT INTO questions (interview_id, question_text, question_type, difficulty, question_order)
    VALUES (?, ?, ?, ?, ?)
    """, (interview_id, next_question_text, interview["interview_type"], interview["difficulty"], next_order))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "continue",
        "next_step": next_order,
        "total_steps": interview["num_questions"],
        "next_question": next_question_text
    })

# ----------------- Performance Analysis & Results -----------------

@app.route("/result/<int:interview_id>")
def interview_result(interview_id):
    user_id = get_current_user_id()
    conn = get_db_connection()

    interview = conn.execute("SELECT * FROM interviews WHERE interview_id = ? AND user_id = ?", (interview_id, user_id)).fetchone()
    if not interview:
        conn.close()
        flash("Interview not found.", "danger")
        return redirect(url_for("dashboard"))

    # Fetch aggregate scores
    avg_scores = conn.execute("""
        SELECT AVG(communication_score) as com,
               AVG(relevance_score) as rel,
               AVG(clarity_score) as cla,
               AVG(fluency_score) as flu,
               AVG(technical_score) as tec
        FROM analysis WHERE interview_id = ?
    """, (interview_id,)).fetchone()

    # Detailed Q&A and analysis breakdown
    rows = conn.execute("""
        SELECT q.question_order, q.question_text, a.answer_text,
               an.communication_score, an.relevance_score, an.clarity_score,
               an.fluency_score, an.technical_score, an.strengths, an.weaknesses,
               an.feedback, an.explain_json
        FROM questions q
        JOIN answers a ON q.question_id = a.question_id
        JOIN analysis an ON a.answer_id = an.answer_id
        WHERE q.interview_id = ?
        ORDER BY q.question_order ASC
    """, (interview_id,)).fetchall()

    all_strengths = []
    all_weaknesses = []
    detailed_turns = []

    for r in rows:
        st = json.loads(r["strengths"]) if r["strengths"] else []
        wk = json.loads(r["weaknesses"]) if r["weaknesses"] else []
        exp = json.loads(r["explain_json"]) if r["explain_json"] else {}
        all_strengths.extend(st)
        all_weaknesses.extend(wk)
        detailed_turns.append({
            "order": r["question_order"],
            "question": r["question_text"],
            "answer": r["answer_text"],
            "communication": round(r["communication_score"]),
            "relevance": round(r["relevance_score"]),
            "clarity": round(r["clarity_score"]),
            "fluency": round(r["fluency_score"]),
            "technical": round(r["technical_score"]),
            "strengths": st,
            "weaknesses": wk,
            "feedback": r["feedback"],
            "explain": exp
        })

    # Deduplicate strengths & weaknesses
    unique_strengths = list(dict.fromkeys(all_strengths))[:4]
    unique_weaknesses = list(dict.fromkeys(all_weaknesses))[:4]

    scores_dict = {
        "communication": round(avg_scores["com"] or 70),
        "relevance": round(avg_scores["rel"] or 75),
        "clarity": round(avg_scores["cla"] or 72),
        "fluency": round(avg_scores["flu"] or 74),
        "technical": round(avg_scores["tec"] or 70),
        "overall": round(interview["overall_score"] or 72)
    }

    conn.close()

    return render_template(
        "result.html",
        interview=interview,
        scores=scores_dict,
        strengths=unique_strengths,
        weaknesses=unique_weaknesses,
        detailed_turns=detailed_turns
    )

# ----------------- Prepare for Next Interview & Targeted Practice -----------------

@app.route("/prepare/<int:interview_id>")
def prepare_next(interview_id):
    user_id = get_current_user_id()
    conn = get_db_connection()

    interview = conn.execute("SELECT * FROM interviews WHERE interview_id = ? AND user_id = ?", (interview_id, user_id)).fetchone()
    if not interview:
        conn.close()
        return redirect(url_for("dashboard"))

    # Compute metric averages
    avg_scores = conn.execute("""
        SELECT AVG(communication_score) as communication_score,
               AVG(relevance_score) as relevance_score,
               AVG(clarity_score) as clarity_score,
               AVG(fluency_score) as fluency_score,
               AVG(technical_score) as technical_score
        FROM analysis WHERE interview_id = ?
    """, (interview_id,)).fetchone()

    scores_dict = {k: avg_scores[k] or 70 for k in avg_scores.keys()}
    plans = generate_personalized_plan(scores_dict, interview["job_role"])

    # Persist plans in database if not already stored
    for p in plans:
        existing = conn.execute("SELECT * FROM practice_plan WHERE interview_id = ? AND weak_area = ?", (interview_id, p["weak_area"])).fetchone()
        if not existing:
            conn.execute("""
            INSERT INTO practice_plan (user_id, interview_id, weak_area, recommendation, practice_questions, ai_focus)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, interview_id, p["weak_area"], p["recommendation"], json.dumps(p["practice_questions"]), p["ai_focus"]))

    conn.commit()
    saved_plans = conn.execute("SELECT * FROM practice_plan WHERE interview_id = ?", (interview_id,)).fetchall()
    conn.close()

    parsed_plans = []
    for sp in saved_plans:
        parsed_plans.append({
            "plan_id": sp["plan_id"],
            "weak_area": sp["weak_area"],
            "recommendation": sp["recommendation"],
            "ai_focus": sp["ai_focus"],
            "practice_questions": json.loads(sp["practice_questions"]),
            "status": sp["status"]
        })

    return render_template("preparation.html", interview=interview, plans=parsed_plans)

@app.route("/api/submit-practice", methods=["POST"])
def submit_practice():
    data = request.get_json() or {}
    plan_id = data.get("plan_id")
    answer = data.get("answer", "")
    question = data.get("question", "")

    # Lightweight feedback on practice
    words = len(answer.split())
    star_words = [w for w in ["situation", "task", "action", "result", "outcome", "because", "impact"] if w in answer.lower()]
    
    if words < 25:
        feedback = "Good attempt! For your next interview, expand on the specific actions YOU took and the quantifiable result."
        passed = False
    elif len(star_words) >= 2:
        feedback = f"Excellent! Strong STAR structure detected. You effectively highlighted concrete actions and results."
        passed = True
    else:
        feedback = "Solid detail. Try to clearly separate the problem (Situation & Task) from your specific technical response (Action & Result)."
        passed = True

    if plan_id:
        conn = get_db_connection()
        conn.execute("UPDATE practice_plan SET status = 'completed' WHERE plan_id = ?", (plan_id,))
        conn.commit()
        conn.close()

    return jsonify({
        "status": "success",
        "feedback": feedback,
        "star_elements_found": star_words,
        "is_ready_for_next": passed
    })

# ----------------- Progress & Interview Comparison -----------------

@app.route("/progress")
def progress_view():
    user_id = get_current_user_id()
    conn = get_db_connection()

    interviews = conn.execute("""
        SELECT i.interview_id, i.job_role, i.interview_type, i.difficulty, i.overall_score, i.date,
               AVG(a.communication_score) as communication_score,
               AVG(a.clarity_score) as clarity_score,
               AVG(a.relevance_score) as relevance_score,
               AVG(a.fluency_score) as fluency_score,
               AVG(a.technical_score) as technical_score
        FROM interviews i
        LEFT JOIN analysis a ON i.interview_id = a.interview_id
        WHERE i.user_id = ? AND i.status = 'completed'
        GROUP BY i.interview_id
        ORDER BY i.date ASC
    """, (user_id,)).fetchall()

    conn.close()

    comparison_data = None
    if len(interviews) >= 2:
        attempt_1 = dict(interviews[0])
        attempt_2 = dict(interviews[-1])
        comparison_data = compare_interview_attempts(attempt_1, attempt_2)
    elif len(interviews) == 1:
        # Mock comparison row for demonstration if user has only taken 1 interview
        attempt_1 = dict(interviews[0])
        attempt_2 = {
            "communication_score": min(95, attempt_1.get("communication_score", 65) + 12),
            "clarity_score": min(95, attempt_1.get("clarity_score", 60) + 14),
            "relevance_score": min(95, attempt_1.get("relevance_score", 80) + 7),
            "fluency_score": min(95, attempt_1.get("fluency_score", 62) + 15),
            "technical_score": min(95, attempt_1.get("technical_score", 70) + 11),
            "overall_score": min(95, attempt_1.get("overall_score", 67) + 12)
        }
        comparison_data = compare_interview_attempts(attempt_1, attempt_2)

    return render_template(
        "progress.html",
        interviews=interviews,
        comparison=comparison_data,
        has_multiple_attempts=len(interviews) >= 2
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)
