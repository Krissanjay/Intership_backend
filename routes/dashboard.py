from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db_connection


def dashboard_routes(app):

    @app.route("/api/dashboard", methods=["GET"])
    @jwt_required()
    def get_dashboard():

        student_id = get_jwt_identity()

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Student information
        cursor.execute("""
            SELECT student_id, name, email, phone
            FROM students
            WHERE student_id = %s
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        # Profile
        cursor.execute("""
            SELECT *
            FROM profiles
            WHERE student_id = %s
        """, (student_id,))

        profile = cursor.fetchone()

        # Skills count
        cursor.execute("""
            SELECT COUNT(*) AS total_skills
            FROM student_skills
            WHERE student_id = %s
        """, (student_id,))

        total_skills = cursor.fetchone()["total_skills"]

        # Resume count
        cursor.execute("""
            SELECT COUNT(*) AS total_resumes
            FROM resumes
            WHERE student_id = %s
        """, (student_id,))

        total_resumes = cursor.fetchone()["total_resumes"]

        # Recommendations count
        cursor.execute("""
            SELECT COUNT(*) AS total_recommendations
            FROM recommendations
            WHERE student_id = %s
        """, (student_id,))

        total_recommendations = cursor.fetchone()["total_recommendations"]

        # Saved internships count
        cursor.execute("""
            SELECT COUNT(*) AS total_saved
            FROM saved_internships
            WHERE student_id = %s
        """, (student_id,))

        total_saved = cursor.fetchone()["total_saved"]

        # Applications count
        cursor.execute("""
            SELECT COUNT(*) AS total_applications
            FROM applications
            WHERE student_id = %s
        """, (student_id,))

        total_applications = cursor.fetchone()["total_applications"]

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "student": student,
            "profile": profile,
            "statistics": {
                "total_skills": total_skills,
                "total_resumes": total_resumes,
                "total_recommendations": total_recommendations,
                "total_saved": total_saved,
                "total_applications": total_applications
            }
        }), 200