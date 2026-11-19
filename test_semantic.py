
from services.semantic_matching import calculate_semantic_score

resume = """
Developed web applications using Python, Flask, MySQL,
REST APIs, JavaScript and React.
"""

internship = """
We are looking for a Python backend developer with experience
in Flask, MySQL, REST API development and web applications.
"""

score = calculate_semantic_score(resume, internship)

print("Semantic Score:", score)
