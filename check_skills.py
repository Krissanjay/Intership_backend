import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def check():
    try:

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "pm_internship_engine"),
            port=int(os.getenv("DB_PORT", "3307"))
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