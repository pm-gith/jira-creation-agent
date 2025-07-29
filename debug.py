from jira import JIRA
import os
from dotenv import load_dotenv
from datetime import datetime

#Load .env (explicit path for safety)
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("Loading .env from:", env_path)  # Debug

load_dotenv(env_path)

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_SERVER = os.getenv("JIRA_SERVER")

jira = JIRA(
    server=JIRA_SERVER,
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

epic = jira.issue("SNPI-11099")  # replace with your Epic key
print(epic.raw['fields'])
child = jira.issue("SNPI-11100")  # replace with auto-created Design task key
print(child.raw['fields'])
