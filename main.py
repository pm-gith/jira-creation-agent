import os
import pandas as pd
from jira import JIRA
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

file_path = r"C:\Users\prachimishra\OneDrive - LucidMotors\Desktop\jira_excel\Untitled sheet.xlsx"
df = pd.read_excel(file_path)

#Ensure required columns exist
required_cols = ["PN", "Title", "SCA#", "SCA title", "Jira#", "Disposition", "Date In", "Date Out", "Notes"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

#Filter rows with Jira#
df_filtered = df[df["Jira#"].isna()]

#Group by SCA#
groups = df_filtered.groupby("SCA#")

#Build Markdown Table for Description
def build_description(sca_num, group):
    #Header
    desc = f"SCA# {sca_num}\n\n"
    desc += "|PN | Title | Disposition | Date In | Date Out |\n"
    #desc += "|---|-------|-------------|---------|----------|\n"

    for _, row in group.iterrows():
        desc += f"|{row['PN']}|{row['Title']}|{row['Disposition']}|{row['Date In']}|{row['Date Out']}|\n"

    print("... printing description ...")
    print(desc)
    return desc

#Create JIRA ticket
def create_jira_ticket(sca_num, description):
    issue_dict = {
        "project": {"key": "SNPI"},
        "issuetype": {"name": "Epic"},
        "customfield_12401": {"value": "Part Status"}, #Request Type field
        "summary": f"Part Status | Gravity | {sca_title}",
        "description": description
    }
    issue = jira.create_issue(fields=issue_dict)
    return issue.key

#Find Child Task
def find_child_task(epic_key):
    jql_query = f'"customfield_10008" = "{epic_key}" AND summary ~ "Part Status: Design"'
    print(jql_query)
    issues = jira.search_issues(jql_query)
    return issues[0] if issues else None

#Transition Child Task to Completed
def complete_task(issue):
    # Fetch available transitions
    transitions = jira.transitions(issue)
    
    # Find transition ID for "Done"
    done_transition = next((t['id'] for t in transitions if t['name'].lower() in ['done', 'completed']), None)
    
    if done_transition:
        jira.transition_issue(issue, done_transition)
        print(f"Child task {issue.key} marked as Done.")
    else:
        print(f"No 'Done' transition found for {issue.key}.")


#Write Jira Key back to Excel
for sca_num, group in groups:
    sca_title = group["SCA title"].iloc[0]
    description = build_description(sca_num, group)

    #Create ticket in JIRA
    jira_key = create_jira_ticket(sca_num, description)

    # Mark child Part Status: Design task as Done
    child_task = find_child_task(jira_key)
    print(jira_key)
    if child_task:
        complete_task(child_task)
    else:
        print(f"No child task 'Part Status: Design' found for {jira_key}")


    #Update Jira# for this SCA in main df
    jira_url = f"{JIRA_SERVER}/browse/{jira_key}"
    df.loc[df["SCA#"] == sca_num, "Jira#"] = jira_url

    # Current date in mm/dd/yyyy format
    created_date = datetime.now().strftime("%m/%d/%Y")
    note_text = f"Jira created by agent on {created_date}"

    # Append to existing notes if any
    df.loc[df["SCA#"] == sca_num, "Notes"] = df.loc[df["SCA#"] == sca_num, "Notes"].fillna("") + " " + note_text

#Save updated Excel
df.to_excel(file_path, index=False)