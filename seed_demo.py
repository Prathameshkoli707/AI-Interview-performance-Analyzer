import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interview_analyzer.db")

def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Update/Verify User 1
    cursor.execute("""
    UPDATE users SET 
        name = 'Alex Johnson',
        education = 'B.Tech Computer Science & Engineering (2nd Year)',
        experience_level = 'Fresher',
        target_industry = 'IT & Software',
        target_role = 'Software Developer'
    WHERE user_id = 1
    """)

    # 2. Seed a Resume for User 1 if not exists
    cursor.execute("SELECT COUNT(*) FROM resumes WHERE user_id = 1")
    if cursor.fetchone()[0] == 0:
        skills = ["Python", "Flask", "SQL", "JavaScript", "HTML", "CSS", "Git", "Problem Solving", "REST API"]
        projects = [
            "AI Interview Performance Analyzer (Continuous feedback web platform with Speech & Video)",
            "Library Management System with SQLite and Flask",
            "Responsive Portfolio Website with interactive JavaScript"
        ]
        sample_text = """
        ALEX JOHNSON
        Email: student@example.com | B.Tech Computer Science (2nd Year)
        
        SKILLS:
        Python, Flask, JavaScript, SQL, HTML, CSS, Git, GitHub, REST APIs, Problem Solving
        
        PROJECTS:
        1. AI Interview Performance Analyzer: Built an adaptive mock interview web application using Flask, SQLite, and Web Speech API.
        2. Database Management System: Implemented relational schema for student cataloging.
        
        EDUCATION:
        B.Tech Computer Engineering - 2nd Year Field Engineering Project
        """
        cursor.execute("""
        INSERT INTO resumes (user_id, file_path, extracted_text, skills, projects, education, experience)
        VALUES (1, 'sample_resume.pdf', ?, ?, ?, ?, ?)
        """, (sample_text, json.dumps(skills), json.dumps(projects), 'B.Tech Computer Engineering (2nd Year)', 'Fresher / Student'))

    # 3. Seed Attempt 1 Interview to demonstrate continuous improvement & comparison
    cursor.execute("SELECT COUNT(*) FROM interviews WHERE user_id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO interviews (interview_id, user_id, industry, job_role, interview_type, difficulty, num_questions, overall_score, status, date)
        VALUES (1, 1, 'IT & Software', 'Software Developer', 'Technical', 'Medium', 3, 67.0, 'completed', '2026-10-04 14:30:00')
        """)

        # Seed Questions & Answers for Interview 1
        q1 = "Tell me about your Python project and how you handled database queries efficiently."
        a1 = "I built a Flask app with SQLite. I used indexing on primary keys to make select queries faster, but I did not implement caching."
        
        q2 = "What is the difference between synchronous and asynchronous operations in web applications?"
        a2 = "Synchronous blocks the thread until done. Asynchronous allows other tasks to run while waiting for I/O operations."

        q3 = "Can you describe a challenging bug you encountered and how you debugged it?"
        a3 = "I had a CORS error when fetching data from the backend. I fixed it by installing flask-cors and setting headers."

        # Insert Q1
        cursor.execute("INSERT INTO questions (interview_id, question_text, question_type, difficulty, question_order) VALUES (1, ?, 'Technical', 'Medium', 1)", (q1,))
        q1_id = cursor.lastrowid
        cursor.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (?, 1, ?)", (q1_id, a1))
        ans1_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO analysis (interview_id, answer_id, relevance_score, clarity_score, communication_score, fluency_score, technical_score, strengths, weaknesses, feedback, explain_json)
        VALUES (1, ?, 78, 65, 68, 64, 72, ?, ?, ?, ?)
        """, (
            ans1_id,
            json.dumps(["Directly answered database indexing technique."]),
            json.dumps(["Answer was brief; missed explaining transaction rollback or connection pooling."]),
            "Good foundational understanding. Detail the architecture and measurable query performance improvements.",
            json.dumps({"communication": "68% - Clear but concise.", "relevance": "78% - Relevant to Python database queries.", "clarity": "65% - Needs more structured points.", "fluency": "64% - Slightly rushed.", "technical": "72% - Mentioned indexing."})
        ))

        # Insert Q2
        cursor.execute("INSERT INTO questions (interview_id, question_text, question_type, difficulty, question_order) VALUES (1, ?, 'Technical', 'Medium', 2)", (q2,))
        q2_id = cursor.lastrowid
        cursor.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (?, 1, ?)", (q2_id, a2))
        ans2_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO analysis (interview_id, answer_id, relevance_score, clarity_score, communication_score, fluency_score, technical_score, strengths, weaknesses, feedback, explain_json)
        VALUES (1, ?, 82, 60, 64, 60, 70, ?, ?, ?, ?)
        """, (
            ans2_id,
            json.dumps(["Accurately defined asynchronous non-blocking I/O concept."]),
            json.dumps(["Lacked concrete framework examples like async/await or event loops."]),
            "Accurate definition. Elevate your response by providing an event-loop or API fetch example.",
            json.dumps({"communication": "64% - Could use more conversational flow.", "relevance": "82% - Answered prompt.", "clarity": "60% - Brief.", "fluency": "60% - Could elaborate.", "technical": "70% - Solid definition."})
        ))

        # Insert Q3
        cursor.execute("INSERT INTO questions (interview_id, question_text, question_type, difficulty, question_order) VALUES (1, ?, 'Technical', 'Medium', 3)", (q3,))
        q3_id = cursor.lastrowid
        cursor.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (?, 1, ?)", (q3_id, a3))
        ans3_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO analysis (interview_id, answer_id, relevance_score, clarity_score, communication_score, fluency_score, technical_score, strengths, weaknesses, feedback, explain_json)
        VALUES (1, ?, 80, 55, 63, 62, 68, ?, ?, ?, ?)
        """, (
            ans3_id,
            json.dumps(["Demonstrated practical troubleshooting of CORS headers in full-stack dev."]),
            json.dumps(["Did not follow the STAR method (missing Situation, Task, Action, Result framing)."]),
            "Great real-world scenario. Next time, frame the debugging story with the STAR methodology to highlight your methodical problem-solving process.",
            json.dumps({"communication": "63% - Missed STAR narrative framing.", "relevance": "80% - Good debugging example.", "clarity": "55% - Jumped straight to solution.", "fluency": "62% - Average pacing.", "technical": "68% - Practical CORS knowledge."})
        ))

        # 4. Seed Targeted Practice Drills (Section 8 & 9)
        cursor.execute("""
        INSERT INTO practice_plan (user_id, interview_id, weak_area, recommendation, practice_questions, ai_focus, status)
        VALUES (1, 1, 'Clarity & Structure (60%)', 'Structure responses into 3 clear bullet points: Problem statement, Solution design, and Key takeaways.', ?, 'Structure answers using the STAR method: Situation, Task, Action, Result.', 'pending')
        """, (json.dumps([
            "Tell me about a difficult bug or architectural problem you solved using the STAR method.",
            "Describe the high-level architecture of your most recent software project in 3 concise bullet points.",
            "How do you prioritize code readability versus rapid prototyping when developing a new feature?"
        ]),))

        cursor.execute("""
        INSERT INTO practice_plan (user_id, interview_id, weak_area, recommendation, practice_questions, ai_focus, status)
        VALUES (1, 1, 'Fluency & Pacing (62%)', 'Complete 3 timed 90-second voice drills. Replace filler words (um, uh, like) with deliberate 1-second pauses.', ?, 'Pacing control: target 120-140 words per minute with purposeful pauses.', 'pending')
        """, (json.dumps([
            "Walk me through your resume in under 90 seconds without rushing.",
            "What is a recent technology or framework that excited you, and why?",
            "Explain how you debug an urgent production issue under time pressure."
        ]),))

    conn.commit()
    conn.close()
    print("Demo data seeded successfully.")

if __name__ == "__main__":
    seed_demo_data()
