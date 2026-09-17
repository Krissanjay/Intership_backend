import mysql.connector

def check():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="pm_internship_engine"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills LIMIT 5")
        skills = cursor.fetchall()
        print("Skills:", skills)
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check()
