from dotenv import load_dotenv

load_dotenv()
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import mysql.connector
import bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from database import get_db_connection
from routes.dashboard import dashboard_routes
from services.eligibility import check_eligibility
from services.matching import calculate_skill_match
from services.scoring import calculate_overall_score
from services.profile_matching import calculate_profile_match
import os
from werkzeug.utils import secure_filename

from services.resume_parser import extract_resume_text
from services.resume_skill_extractor import extract_skills
from services.semantic_matching import calculate_semantic_score
from services.explanation import generate_explanation

app = Flask(__name__)
CORS(app)

# app.config["JWT_SECRET_KEY"] = "your-secret-key-change-this"
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
jwt = JWTManager(app)
def admin_required():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    return None

# def get_db_connection():
#     return mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="pm_internship_engine"
#     )


@app.route("/")
def home():
    return jsonify({
        "message": "PM Internship Recommendation Engine API is running"
    })


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")

    # Validate input
    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check whether email already exists
    cursor.execute(
        "SELECT student_id FROM students WHERE email = %s",
        (email,)
    )

    existing_student = cursor.fetchone()

    if existing_student:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    # Hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    # Insert student
    cursor.execute(
        """
        INSERT INTO students
        (name, email, password, phone)
        VALUES (%s, %s, %s, %s)
        """,
        (
            name,
            email,
            hashed_password.decode("utf-8"),
            phone
        )
    )

    connection.commit()

    student_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "student_id": student_id
    }), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE email = %s",
        (email,)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if not student:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    password_correct = bcrypt.checkpw(
        password.encode("utf-8"),
        student["password"].encode("utf-8")
    )

    if not password_correct:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(student["student_id"]),
        additional_claims={"role": "student"}
    )

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": access_token,
        "student": {
            "student_id": student["student_id"],
            "name": student["name"],
            "email": student["email"]
        }
    }), 200
@app.route("/api/me", methods=["GET"])
@jwt_required()
def get_current_student():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT student_id, name, email, phone FROM students WHERE student_id = %s",
        (student_id,)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    return jsonify({
        "success": True,
        "student": student
    })

@app.route("/api/profile", methods=["POST"])
@jwt_required()
def create_profile():

    student_id = get_jwt_identity()
    data = request.get_json()

    college = data.get("college")
    degree = data.get("degree")
    branch = data.get("branch")
    cgpa = data.get("cgpa")
    graduation_year = data.get("graduation_year")
    location = data.get("location")
    preferred_location = data.get("preferred_location")
    career_interest = data.get("career_interest")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check whether profile already exists
    cursor.execute(
        "SELECT profile_id FROM profiles WHERE student_id = %s",
        (student_id,)
    )

    existing_profile = cursor.fetchone()

    if existing_profile:
        cursor.execute(
            """
            UPDATE profiles
            SET college = %s,
                degree = %s,
                branch = %s,
                cgpa = %s,
                graduation_year = %s,
                location = %s,
                preferred_location = %s,
                career_interest = %s
            WHERE student_id = %s
            """,
            (
                college,
                degree,
                branch,
                cgpa,
                graduation_year,
                location,
                preferred_location,
                career_interest,
                student_id
            )
        )

        message = "Profile updated successfully"

    else:
        cursor.execute(
            """
            INSERT INTO profiles
            (
                student_id,
                college,
                degree,
                branch,
                cgpa,
                graduation_year,
                location,
                preferred_location,
                career_interest
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                student_id,
                college,
                degree,
                branch,
                cgpa,
                graduation_year,
                location,
                preferred_location,
                career_interest
            )
        )

        message = "Profile created successfully"

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": message
    })

@app.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE student_id = %s
        """,
        (student_id,)
    )

    profile = cursor.fetchone()

    cursor.close()
    connection.close()

    if not profile:
        return jsonify({
            "success": False,
            "message": "Profile not found"
        }), 404

    return jsonify({
        "success": True,
        "profile": profile
    })


@app.route("/api/skills", methods=["GET"])
def get_skills():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT skill_id, skill_name FROM skills ORDER BY skill_name"
    )

    skills = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "skills": skills
    })

@app.route("/api/student-skills", methods=["POST"])
@jwt_required()
def save_student_skills():

    student_id = get_jwt_identity()
    data = request.get_json()

    skills = data.get("skills", [])

    connection = get_db_connection()
    cursor = connection.cursor()

    # Remove previous skills
    cursor.execute(
        "DELETE FROM student_skills WHERE student_id = %s",
        (student_id,)
    )

    # Add selected skills
    for skill in skills:

        skill_id = skill.get("skill_id")
        proficiency = skill.get("proficiency_level", "Beginner")

        cursor.execute(
            """
            INSERT INTO student_skills
            (student_id, skill_id, proficiency_level)
            VALUES (%s, %s, %s)
            """,
            (
                student_id,
                skill_id,
                proficiency
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Skills saved successfully"
    })

@app.route("/api/student-skills/add", methods=["POST"])
@jwt_required()
def add_student_skill():

    student_id = get_jwt_identity()
    data = request.get_json()

    skill_id = data.get("skill_id")
    skill_name = data.get("skill_name")
    proficiency = data.get("proficiency_level", "Beginner")

    if not skill_id and not skill_name:
        return jsonify({
            "success": False,
            "message": "Either skill_id or skill_name is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # If skill_name is provided but no skill_id, find or create the skill
        if not skill_id and skill_name:
            cursor.execute(
                "SELECT skill_id FROM skills WHERE LOWER(skill_name) = LOWER(%s)",
                (skill_name.strip(),)
            )
            existing_skill = cursor.fetchone()
            
            if existing_skill:
                skill_id = existing_skill["skill_id"]
            else:
                # Add new skill to skills table
                cursor.execute(
                    "INSERT INTO skills (skill_name) VALUES (%s)",
                    (skill_name.strip(),)
                )
                skill_id = cursor.lastrowid
                
        # Check if skill already exists for this student
        cursor.execute(
            "SELECT * FROM student_skills WHERE student_id = %s AND skill_id = %s",
            (student_id, skill_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Update proficiency if it already exists
            cursor.execute(
                """
                UPDATE student_skills 
                SET proficiency_level = %s 
                WHERE student_id = %s AND skill_id = %s
                """,
                (proficiency, student_id, skill_id)
            )
            message = "Skill proficiency updated successfully"
        else:
            # Insert new student skill
            cursor.execute(
                """
                INSERT INTO student_skills (student_id, skill_id, proficiency_level)
                VALUES (%s, %s, %s)
                """,
                (student_id, skill_id, proficiency)
            )
            message = "Skill added successfully"

        connection.commit()
        return jsonify({
            "success": True,
            "message": message,
            "skill_id": skill_id
        })

    except Exception as e:
        connection.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to add skill",
            "error": str(e)
        }), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/api/student-skills", methods=["GET"])
@jwt_required()
def get_student_skills():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            ss.proficiency_level
        FROM student_skills ss
        JOIN skills s
            ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
        ORDER BY s.skill_name
        """,
        (student_id,)
    )

    skills = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "skills": skills
    })
@app.route("/api/admin/internships", methods=["POST"])
@jwt_required()
def add_admin_internship():

    admin_check = admin_required()

    if admin_check:
        return admin_check

    data = request.get_json()

    company_name = data.get("company_name")
    role = data.get("role")
    description = data.get("description")
    location = data.get("location")
    duration = data.get("duration")
    stipend = data.get("stipend")
    minimum_cgpa = data.get("minimum_cgpa")
    eligible_degree = data.get("eligible_degree")
    eligible_branch = data.get("eligible_branch")
    application_deadline = data.get("application_deadline")

    if not company_name or not role:
        return jsonify({
            "success": False,
            "message": "Company name and role are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO internships
        (
            company_name,
            role,
            description,
            location,
            duration,
            stipend,
            minimum_cgpa,
            eligible_degree,
            eligible_branch,
            application_deadline
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            company_name,
            role,
            description,
            location,
            duration,
            stipend,
            minimum_cgpa,
            eligible_degree,
            eligible_branch,
            application_deadline
        )
    )

    internship_id = cursor.lastrowid

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Internship added successfully",
        "internship_id": internship_id
    }), 201

@app.route("/api/internships", methods=["GET"])
def get_internships():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            i.*,
            GROUP_CONCAT(s.skill_name SEPARATOR ', ') AS required_skills
        FROM internships i
        LEFT JOIN internship_skills isk ON i.internship_id = isk.internship_id
        LEFT JOIN skills s ON isk.skill_id = s.skill_id
        GROUP BY i.internship_id
        ORDER BY i.created_at DESC
        """
    )

    internships = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "internships": internships
    })

@app.route("/api/internships/<int:internship_id>/skills", methods=["POST"])
def add_internship_skills(internship_id):

    data = request.get_json()
    skills = data.get("skills", [])

    if not skills:
        return jsonify({
            "success": False,
            "message": "At least one skill is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check internship exists
    cursor.execute(
        "SELECT internship_id FROM internships WHERE internship_id = %s",
        (internship_id,)
    )

    internship = cursor.fetchone()

    if not internship:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Remove old skills
    cursor.execute(
        "DELETE FROM internship_skills WHERE internship_id = %s",
        (internship_id,)
    )

    # Add new skills
    for skill in skills:

        skill_id = skill.get("skill_id")
        importance = skill.get("importance", "Medium")

        if not skill_id:
            continue

        cursor.execute(
            """
            INSERT INTO internship_skills
            (internship_id, skill_id, importance)
            VALUES (%s, %s, %s)
            """,
            (
                internship_id,
                skill_id,
                importance
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Internship skills saved successfully"
    })

@app.route("/api/internships/<int:internship_id>/skills", methods=["GET"])
def get_internship_skills(internship_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            isk.importance
        FROM internship_skills isk
        JOIN skills s
            ON isk.skill_id = s.skill_id
        WHERE isk.internship_id = %s
        ORDER BY s.skill_name
        """,
        (internship_id,)
    )

    skills = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "skills": skills
    })

@app.route("/api/internships/<int:internship_id>/eligibility", methods=["GET"])
@jwt_required()
def check_internship_eligibility(internship_id):

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get student profile
    cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE student_id = %s
        """,
        (student_id,)
    )

    student_profile = cursor.fetchone()

    if not student_profile:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please complete your profile first"
        }), 404

    # Get internship
    cursor.execute(
        """
        SELECT *
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    cursor.close()
    connection.close()

    if not internship:
        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    result = check_eligibility(
        student_profile,
        internship
    )

    return jsonify({
        "success": True,
        "internship_id": internship_id,
        "eligible": result["eligible"],
        "reasons": result["reasons"]
    })

@app.route("/api/internships/<int:internship_id>/skill-match", methods=["GET"])
@jwt_required()
def skill_match(internship_id):

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get student's skills
    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            ss.proficiency_level
        FROM student_skills ss
        JOIN skills s
            ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
        """,
        (student_id,)
    )

    student_skills = cursor.fetchall()

    # Get internship required skills
    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            isk.importance
        FROM internship_skills isk
        JOIN skills s
            ON isk.skill_id = s.skill_id
        WHERE isk.internship_id = %s
        """,
        (internship_id,)
    )

    internship_skills = cursor.fetchall()

    cursor.close()
    connection.close()

    if not internship_skills:
        return jsonify({
            "success": False,
            "message": "No required skills found for this internship"
        }), 404

    result = calculate_skill_match(
        student_skills,
        internship_skills
    )

    return jsonify({
        "success": True,
        "internship_id": internship_id,
        "skill_match_score": result["score"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"]
    })

@app.route(
    "/api/internships/<int:internship_id>/score",
    methods=["GET"]
)
@jwt_required()
def calculate_internship_score(internship_id):

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Student profile
    cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE student_id = %s
        """,
        (student_id,)
    )

    student_profile = cursor.fetchone()

    if not student_profile:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please complete your profile first"
        }), 404

    # Internship
    cursor.execute(
        """
        SELECT *
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    cursor.close()
    connection.close()

    if not internship:
        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Eligibility
    from services.eligibility import check_eligibility

    eligibility_result = check_eligibility(
        student_profile,
        internship
    )

    eligibility_score = (
        100
        if eligibility_result["eligible"]
        else 0
    )

    # Student skill matching
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            ss.proficiency_level
        FROM student_skills ss
        JOIN skills s
            ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
        """,
        (student_id,)
    )

    student_skills = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            isk.importance
        FROM internship_skills isk
        JOIN skills s
            ON isk.skill_id = s.skill_id
        WHERE isk.internship_id = %s
        """,
        (internship_id,)
    )

    internship_skills = cursor.fetchall()

    cursor.close()
    connection.close()

    from services.matching import calculate_skill_match

    skill_result = calculate_skill_match(
        student_skills,
        internship_skills
    )

    skill_match_score = skill_result["score"]

    # Profile match
    profile_match_score = calculate_profile_match(
        student_profile,
        internship
    )

    # Overall score
    overall_score = calculate_overall_score(
        eligibility_score,
        skill_match_score,
        profile_match_score
    )

    return jsonify({
        "success": True,
        "internship_id": internship_id,
        "eligibility_score": eligibility_score,
        "skill_match_score": skill_match_score,
        "profile_match_score": profile_match_score,
        "overall_score": overall_score,
        "matched_skills": skill_result["matched_skills"],
        "missing_skills": skill_result["missing_skills"],
        "eligibility_reasons": eligibility_result["reasons"]
    })

@app.route("/api/resume/upload", methods=["POST"])
@jwt_required()
def upload_resume():

    student_id = get_jwt_identity()

    if "resume" not in request.files:
        return jsonify({
            "success": False,
            "message": "Resume file is required"
        }), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "No file selected"
        }), 400

    allowed_extensions = [".pdf", ".docx"]

    filename = secure_filename(file.filename)

    extension = os.path.splitext(filename)[1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "success": False,
            "message": "Only PDF and DOCX files are supported"
        }), 400

    upload_folder = os.path.join(
        os.path.dirname(__file__),
        "uploads"
    )

    os.makedirs(upload_folder, exist_ok=True)

    saved_filename = f"{student_id}_{filename}"

    file_path = os.path.join(
        upload_folder,
        saved_filename
    )

    file.save(file_path)

    try:

        extracted_text = extract_resume_text(file_path)

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Could not extract resume text",
            "error": str(e)
        }), 500

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO resumes
        (
            student_id,
            file_name,
            file_path,
            extracted_text
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            student_id,
            filename,
            file_path,
            extracted_text
        )
    )

    connection.commit()

    resume_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Resume uploaded successfully",
        "resume_id": resume_id,
        "file_name": filename,
        "extracted_text": extracted_text
    }), 201

@app.route("/api/resume", methods=["GET"])
@jwt_required()
def get_resume():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            resume_id,
            file_name,
            file_path,
            extracted_text,
            uploaded_at
        FROM resumes
        WHERE student_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (student_id,)
    )

    resume = cursor.fetchone()

    cursor.close()
    connection.close()

    if not resume:
        return jsonify({
            "success": False,
            "message": "No resume uploaded"
        }), 404

    return jsonify({
        "success": True,
        "resume": resume
    })

@app.route("/api/resume/extract-skills", methods=["GET"])
@jwt_required()
def extract_resume_skills():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get latest resume
    cursor.execute(
        """
        SELECT resume_id, extracted_text
        FROM resumes
        WHERE student_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (student_id,)
    )

    resume = cursor.fetchone()

    if not resume:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please upload a resume first"
        }), 404

    # Get all known skills
    cursor.execute(
        """
        SELECT skill_id, skill_name
        FROM skills
        ORDER BY skill_name
        """
    )

    available_skills = cursor.fetchall()

    cursor.close()
    connection.close()

    detected_skills = extract_skills(
        resume["extracted_text"],
        available_skills
    )

    return jsonify({
        "success": True,
        "resume_id": resume["resume_id"],
        "detected_skills": detected_skills
    })

@app.route(
    "/api/internships/<int:internship_id>/semantic-score",
    methods=["GET"]
)
@jwt_required()
def semantic_score(internship_id):

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT extracted_text
        FROM resumes
        WHERE student_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (student_id,)
    )

    resume = cursor.fetchone()

    if not resume:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please upload a resume first"
        }), 404

    cursor.execute(
        """
        SELECT internship_id, company_name, role, description
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    cursor.close()
    connection.close()

    if not internship:
        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    score = calculate_semantic_score(
        resume["extracted_text"],
        internship["description"]
    )

    return jsonify({
        "success": True,
        "internship_id": internship_id,
        "semantic_score": score
    })

@app.route("/api/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get student profile
    cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE student_id = %s
        """,
        (student_id,)
    )

    student_profile = cursor.fetchone()

    if not student_profile:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please complete your profile first"
        }), 404

    # Get latest resume
    cursor.execute(
        """
        SELECT extracted_text
        FROM resumes
        WHERE student_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (student_id,)
    )

    resume = cursor.fetchone()

    if not resume:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Please upload your resume first"
        }), 404

    # Get student skills
    cursor.execute(
        """
        SELECT
            s.skill_id,
            s.skill_name,
            ss.proficiency_level
        FROM student_skills ss
        JOIN skills s
            ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
        """,
        (student_id,)
    )

    student_skills = cursor.fetchall()

    # Get internships
    cursor.execute(
        """
        SELECT *
        FROM internships
        WHERE is_active = True
        ORDER BY created_at DESC
        """
    )

    internships = cursor.fetchall()

    recommendations = []

    from services.eligibility import check_eligibility
    from services.matching import calculate_skill_match
    from services.profile_matching import calculate_profile_match
    from services.semantic_matching import calculate_semantic_score
    from services.scoring import calculate_overall_score

    for internship in internships:

        # -------------------------
        # 1. Eligibility
        # -------------------------

        eligibility_result = check_eligibility(
            student_profile,
            internship
        )

        # Do not recommend ineligible internships
        if not eligibility_result["eligible"]:
            continue

        # -------------------------
        # 2. Internship Skills
        # -------------------------

        cursor.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                isk.importance
            FROM internship_skills isk
            JOIN skills s
                ON isk.skill_id = s.skill_id
            WHERE isk.internship_id = %s
            """,
            (internship["internship_id"],)
        )

        internship_skills = cursor.fetchall()

        # -------------------------
        # 3. Skill Match
        # -------------------------

        skill_result = calculate_skill_match(
            student_skills,
            internship_skills
        )

        skill_match_score = skill_result["score"]

        # -------------------------
        # 4. Profile Match
        # -------------------------

        profile_match_score = calculate_profile_match(
            student_profile,
            internship
        )

        # -------------------------
        # 5. Semantic Match
        # -------------------------

        semantic_score = calculate_semantic_score(
            resume["extracted_text"],
            internship["description"]
        )

        # -------------------------
        # 6. Overall Score
        # -------------------------

        overall_score = calculate_overall_score(
            skill_match_score,
            semantic_score,
            profile_match_score
        )
        explanation_result = generate_explanation(
    overall_score,
    skill_match_score,
    semantic_score,
    profile_match_score,
    skill_result["matched_skills"],
    skill_result["missing_skills"]
)

        # -------------------------
        # 7. Recommendation
        # -------------------------

        recommendations.append({

            "internship_id":
                internship["internship_id"],

            "company_name":
                internship["company_name"],

            "role":
                internship["role"],

            "description":
                internship["description"],

            "location":
                internship["location"],

            "duration":
                internship["duration"],

            "stipend":
                internship["stipend"],

            "application_deadline":
                internship["application_deadline"],

            "skill_match_score":
                skill_match_score,

            "semantic_score":
                semantic_score,

            "profile_match_score":
                profile_match_score,

            "overall_score":
                overall_score,

            "matched_skills":
                skill_result["matched_skills"],

            "missing_skills":
                skill_result["missing_skills"],

            "eligibility_reasons":
                eligibility_result["reasons"],
            "explanation":
        explanation_result["explanation"],
            "skill_gap":
        explanation_result["skill_gap"]
        })

    

    # -------------------------
    # Rank internships
    # -------------------------

    recommendations.sort(
        key=lambda x: x["overall_score"],
        reverse=True
    )
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
    """
    DELETE FROM recommendations
    WHERE student_id = %s
    """,
    (student_id,)
    )

    for recommendation in recommendations:
        cursor.execute(
        """
        INSERT INTO recommendations
        (
            student_id,
            internship_id,
            eligibility_score,
            skill_match_score,
            semantic_score,
            overall_score,
            explanation,
            skill_gap
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            student_id,
            recommendation["internship_id"],
            100,
            recommendation["skill_match_score"],
            recommendation["semantic_score"],
            recommendation["overall_score"],
            recommendation["explanation"],
            recommendation["skill_gap"]
        )
    )
        connection.commit()

    # Close database
    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "student_id": int(student_id),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    })
    

@app.route("/api/recommendations/saved", methods=["GET"])
@jwt_required()
def get_saved_recommendations():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            r.recommendation_id,
            r.internship_id,
            r.eligibility_score,
            r.skill_match_score,
            r.semantic_score,
            r.overall_score,
            r.explanation,
            r.skill_gap,
            r.recommended_at,

            i.company_name,
            i.role,
            i.description,
            i.location,
            i.duration,
            i.stipend,
            i.minimum_cgpa,
            i.eligible_degree,
            i.eligible_branch,
            i.application_deadline

        FROM recommendations r

        JOIN internships i
            ON r.internship_id = i.internship_id

        WHERE r.student_id = %s

        ORDER BY r.overall_score DESC
        """,
        (student_id,)
    )

    recommendations = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    })

@app.route("/api/saved-internships", methods=["POST"])
@jwt_required()
def save_internship():

    student_id = get_jwt_identity()

    data = request.get_json()
    internship_id = data.get("internship_id")

    if not internship_id:
        return jsonify({
            "success": False,
            "message": "Internship ID is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check internship exists
    cursor.execute(
        """
        SELECT internship_id
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    if not internship:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Check if already saved
    cursor.execute(
        """
        SELECT student_id
        FROM saved_internships
        WHERE student_id = %s
        AND internship_id = %s
        """,
        (student_id, internship_id)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship already saved"
        }), 409

    # Save internship
    cursor.execute(
        """
        INSERT INTO saved_internships
        (
            student_id,
            internship_id
        )
        VALUES (%s, %s)
        """,
        (student_id, internship_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Internship saved successfully"
    }), 201

@app.route("/api/saved-internships", methods=["GET"])
@jwt_required()
def get_saved_internships():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            s.internship_id,
            s.saved_at,
            i.company_name,
            i.role,
            i.description,
            i.location,
            i.duration,
            i.stipend,
            i.minimum_cgpa,
            i.eligible_degree,
            i.eligible_branch,
            i.application_deadline

        FROM saved_internships s

        JOIN internships i
            ON s.internship_id = i.internship_id

        WHERE s.student_id = %s

        ORDER BY s.saved_at DESC
        """,
        (student_id,)
    )

    internships = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "total_saved": len(internships),
        "internships": internships
    })

@app.route("/api/applications", methods=["POST"])
@jwt_required()
def apply_internship():

    student_id = get_jwt_identity()

    data = request.get_json()
    internship_id = data.get("internship_id")

    if not internship_id:
        return jsonify({
            "success": False,
            "message": "Internship ID is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check internship exists
    cursor.execute(
        """
        SELECT internship_id, company_name, role
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    if not internship:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Check if already applied
    cursor.execute(
        """
        SELECT application_id, status
        FROM applications
        WHERE student_id = %s
        AND internship_id = %s
        """,
        (student_id, internship_id)
    )

    existing_application = cursor.fetchone()

    if existing_application:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "You have already applied for this internship",
            "application_id": existing_application["application_id"],
            "status": existing_application["status"]
        }), 409

    # Create application
    cursor.execute(
        """
        INSERT INTO applications
        (
            student_id,
            internship_id,
            status
        )
        VALUES (%s, %s, 'Applied')
        """,
        (student_id, internship_id)
    )

    connection.commit()

    application_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Application submitted successfully",
        "application_id": application_id,
        "status": "Applied"
    }), 201

@app.route("/api/applications", methods=["GET"])
@jwt_required()
def get_applications():

    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            a.application_id,
            a.internship_id,
            i.company_name,
            i.role,
            i.description,
            i.location,
            i.duration,
            i.stipend,
            i.application_deadline,
            a.status,
            a.applied_at,
            a.updated_at
        FROM applications a
        JOIN internships i
            ON a.internship_id = i.internship_id
        WHERE a.student_id = %s
        ORDER BY a.applied_at DESC
        """,
        (student_id,)
    )

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "total_applications": len(applications),
        "applications": applications
    }), 200

@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT admin_id, name, email, password
        FROM admins
        WHERE email = %s
        """,
        (email,)
    )

    admin = cursor.fetchone()

    cursor.close()
    connection.close()

    if not admin:
        return jsonify({
            "success": False,
            "message": "Invalid admin credentials"
        }), 401

    if password != admin["password"]:
        return jsonify({
            "success": False,
            "message": "Invalid admin credentials"
        }), 401

    access_token = create_access_token(
        identity=str(admin["admin_id"]),
        additional_claims={"role": "admin"}
    )

    return jsonify({
        "success": True,
        "message": "Admin login successful",
        "token": access_token,
        "admin": {
            "admin_id": admin["admin_id"],
            "name": admin["name"],
            "email": admin["email"]
        }
    }), 200

@app.route("/api/admin/applications", methods=["GET"])
@jwt_required()
def get_all_applications():
    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            a.application_id,
            a.student_id,
            s.name AS student_name,
            s.email AS student_email,
            i.internship_id,
            i.company_name,
            i.role,
            i.location,
            a.status,
            a.applied_at,
            a.updated_at
        FROM applications a

        JOIN students s
            ON a.student_id = s.student_id

        JOIN internships i
            ON a.internship_id = i.internship_id

        ORDER BY a.applied_at DESC
        """
    )

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "total_applications": len(applications),
        "applications": applications
    }), 200
@app.route("/api/admin/applications/<int:application_id>/status", methods=["PATCH"])
@jwt_required()
def update_application_status(application_id):

    admin_check = admin_required()

    if admin_check:
        return admin_check

    data = request.get_json()
    new_status = data.get("status")

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Interview",
        "Selected",
        "Rejected"
    ]

    if not new_status:
        return jsonify({
            "success": False,
            "message": "Status is required"
        }), 400

    if new_status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid application status"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get application and student information
    cursor.execute(
        """
        SELECT
            application_id,
            student_id,
            internship_id
        FROM applications
        WHERE application_id = %s
        """,
        (application_id,)
    )

    application = cursor.fetchone()

    if not application:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Application not found"
        }), 404

    # Update application status
    cursor.execute(
        """
        UPDATE applications
        SET status = %s
        WHERE application_id = %s
        """,
        (new_status, application_id)
    )

    # Create notification
    title = "Application Status Updated"

    message = (
        f"Your internship application status has been updated "
        f"to {new_status}."
    )

    cursor.execute(
        """
        INSERT INTO notifications
        (
            student_id,
            title,
            message,
            type,
            is_read
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            application["student_id"],
            title,
            message,
            "application_status",
            0
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Application status updated successfully",
        "application_id": application_id,
        "status": new_status
    }), 200


@app.route("/api/notifications/<int:student_id>", methods=["GET"])
@jwt_required()
def get_notifications(student_id):

    # Get logged-in student ID from JWT
    current_student_id = get_jwt_identity()

    # Make sure the URL student ID matches logged-in student
    if str(student_id) != str(current_student_id):

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            student_id,
            title,
            message,
            type,
            is_read,
            created_at
        FROM notifications
        WHERE student_id = %s
        ORDER BY created_at DESC
        """,
        (current_student_id,)
    )

    notifications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "notifications": notifications
    }), 200



@app.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["PUT"]
)
@jwt_required()
def mark_notification_read(notification_id):

    # Get logged-in student ID from JWT
    student_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check notification belongs to logged-in student
    cursor.execute(
        """
        SELECT
            id,
            student_id
        FROM notifications
        WHERE id = %s
        AND student_id = %s
        """,
        (
            notification_id,
            student_id
        )
    )

    notification = cursor.fetchone()

    if not notification:

        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    # Mark notification as read
    cursor.execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE id = %s
        AND student_id = %s
        """,
        (
            notification_id,
            student_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Notification marked as read"
    }), 200


@app.route(
    "/api/notifications/<int:student_id>/unread-count",
    methods=["GET"]
)
@jwt_required()
def get_unread_notification_count(student_id):

    # Get logged-in student ID from JWT
    current_student_id = get_jwt_identity()

    # Make sure the URL student ID matches logged-in student
    if str(student_id) != str(current_student_id):

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT COUNT(*) AS unread_count
        FROM notifications
        WHERE student_id = %s
        AND is_read = 0
        """,
        (current_student_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "unread_count": result["unread_count"]
    }), 200



@app.route("/api/student/<int:student_id>/applications", methods=["GET"])
@jwt_required()
def get_student_applications(student_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            application_id,
            internship_id,
            status,
            created_at
        FROM applications
        WHERE student_id = %s
        ORDER BY created_at DESC
        """,
        (student_id,)
    )

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "applications": applications
    }), 200


@app.route("/api/admin/application-stats", methods=["GET"])
@jwt_required()
def get_application_stats():

    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_applications,

            SUM(
                CASE
                    WHEN status = 'Applied'
                    THEN 1
                    ELSE 0
                END
            ) AS applied,

            SUM(
                CASE
                    WHEN status = 'Shortlisted'
                    THEN 1
                    ELSE 0
                END
            ) AS shortlisted,

            SUM(
                CASE
                    WHEN status = 'Interview'
                    THEN 1
                    ELSE 0
                END
            ) AS interview,

            SUM(
                CASE
                    WHEN status = 'Selected'
                    THEN 1
                    ELSE 0
                END
            ) AS selected,

            SUM(
                CASE
                    WHEN status = 'Rejected'
                    THEN 1
                    ELSE 0
                END
            ) AS rejected

        FROM applications
        """
    )

    stats = cursor.fetchone()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "stats": {
            "total_applications": int(stats["total_applications"] or 0),
            "applied": int(stats["applied"] or 0),
            "shortlisted": int(stats["shortlisted"] or 0),
            "interview": int(stats["interview"] or 0),
            "selected": int(stats["selected"] or 0),
            "rejected": int(stats["rejected"] or 0)
        }
    }), 200
@app.route(
    "/api/admin/applications/<int:application_id>",
    methods=["GET"]
)
@jwt_required()
def get_application_details(application_id):

    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            a.application_id,
            a.status,
            a.applied_at,
            a.updated_at,

            s.student_id,
            s.name AS student_name,
            s.email AS student_email,

            i.internship_id,
            i.company_name,
            i.role,
            i.description,
            i.location,
            i.duration,
            i.stipend,
            i.minimum_cgpa,
            i.eligible_degree,
            i.eligible_branch,
            i.application_deadline,
            i.created_at

        FROM applications a

        JOIN students s
            ON a.student_id = s.student_id

        JOIN internships i
            ON a.internship_id = i.internship_id

        WHERE a.application_id = %s
        """,
        (application_id,)
    )

    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if not application:
        return jsonify({
            "success": False,
            "message": "Application not found"
        }), 404

    return jsonify({
        "success": True,
        "application": application
    }), 200

@app.route("/api/admin/internships", methods=["GET"])
@jwt_required()
def get_admin_internships():

    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            internship_id,
            company_name,
            role,
            description,
            location,
            duration,
            stipend,
            minimum_cgpa,
            eligible_degree,
            eligible_branch,
            application_deadline,
            is_active,
            created_at
        FROM internships
        ORDER BY created_at DESC
        """
    )

    internships = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "total_internships": len(internships),
        "internships": internships
    }), 200



@app.route("/api/admin/internships/<int:internship_id>", methods=["PUT"])
@jwt_required()
def update_admin_internship(internship_id):

    admin_check = admin_required()

    if admin_check:
        return admin_check

    data = request.get_json()

    company_name = data.get("company_name")
    role = data.get("role")
    description = data.get("description")
    location = data.get("location")
    duration = data.get("duration")
    stipend = data.get("stipend")
    minimum_cgpa = data.get("minimum_cgpa")
    eligible_degree = data.get("eligible_degree")
    eligible_branch = data.get("eligible_branch")
    application_deadline = data.get("application_deadline")

    if not company_name or not role:
        return jsonify({
            "success": False,
            "message": "Company name and role are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check internship exists
    cursor.execute(
        """
        SELECT internship_id
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    if not internship:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Update internship
    cursor.execute(
        """
        UPDATE internships
        SET
            company_name = %s,
            role = %s,
            description = %s,
            location = %s,
            duration = %s,
            stipend = %s,
            minimum_cgpa = %s,
            eligible_degree = %s,
            eligible_branch = %s,
            application_deadline = %s
        WHERE internship_id = %s
        """,
        (
            company_name,
            role,
            description,
            location,
            duration,
            stipend,
            minimum_cgpa,
            eligible_degree,
            eligible_branch,
            application_deadline,
            internship_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Internship updated successfully",
        "internship_id": internship_id
    }), 200

@app.route("/api/admin/internships/<int:internship_id>", methods=["GET"])
@jwt_required()
def get_admin_internship(internship_id):

    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            internship_id,
            company_name,
            role,
            description,
            location,
            duration,
            stipend,
            minimum_cgpa,
            eligible_degree,
            eligible_branch,
            application_deadline,
            created_at
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    cursor.close()
    connection.close()

    if not internship:
        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    return jsonify({
        "success": True,
        "internship": internship
    }), 200

@app.route("/api/admin/internships/<int:internship_id>", methods=["DELETE"])
@jwt_required()
def delete_admin_internship(internship_id):

    admin_check = admin_required()

    if admin_check:
        return admin_check

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check whether internship exists
    cursor.execute(
        """
        SELECT internship_id
        FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    internship = cursor.fetchone()

    if not internship:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Internship not found"
        }), 404

    # Check whether students have applied
    cursor.execute(
        """
        SELECT COUNT(*) AS application_count
        FROM applications
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    application_data = cursor.fetchone()

    application_count = application_data["application_count"]

    # Do not delete if applications exist
    if application_count > 0:

        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": (
                "Cannot delete this internship because students "
                "have already applied to it."
            ),
            "application_count": application_count
        }), 409

    # Delete internship if there are no applications
    cursor.execute(
        """
        DELETE FROM internships
        WHERE internship_id = %s
        """,
        (internship_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Internship deleted successfully",
        "internship_id": internship_id
    }), 200

@app.route("/api/admin/internships/<int:internship_id>/status", methods=["PATCH"])
@jwt_required()
def update_internship_status(internship_id):

    try:

        admin_check = admin_required()

        if admin_check:
            return admin_check

        data = request.get_json()

        print("STATUS UPDATE REQUEST")
        print("Internship ID:", internship_id)
        print("Request data:", data)

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is missing"
            }), 400

        is_active = data.get("is_active")

        print("is_active:", is_active)

        if is_active is None:
            return jsonify({
                "success": False,
                "message": "is_active is required"
            }), 400

        if is_active not in [0, 1, True, False]:
            return jsonify({
                "success": False,
                "message": "Invalid active status"
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT internship_id
            FROM internships
            WHERE internship_id = %s
            """,
            (internship_id,)
        )

        internship = cursor.fetchone()

        print("Internship found:", internship)

        if not internship:
            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Internship not found"
            }), 404

        new_status = 1 if is_active else 0

        cursor.execute(
            """
            UPDATE internships
            SET is_active = %s
            WHERE internship_id = %s
            """,
            (
                new_status,
                internship_id
            )
        )

        connection.commit()

        print("Database updated successfully")
        print("New status:", new_status)

        cursor.close()
        connection.close()

        if new_status == 1:
            message = "Internship activated successfully"
        else:
            message = "Internship archived successfully"

        return jsonify({
            "success": True,
            "message": message,
            "internship_id": internship_id,
            "is_active": new_status
        }), 200

    except Exception as e:

        print("ERROR UPDATING INTERNSHIP STATUS:")
        print(str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500



dashboard_routes(app)

# if __name__ == "__main__":
#     app.run(debug=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )