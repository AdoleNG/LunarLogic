import json
import os

# -----------------------------
# Load or create database file
# -----------------------------
DB_FILE = "lunar_logic_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "parents": {},
            "children": {},
            "tasks": []
        }

    with open(DB_FILE, "r") as f:
        data = json.load(f)

    if "tasks" not in data:
        data["tasks"] = []

    return data

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()


# -----------------------------
# Create Parent Account
# -----------------------------
def create_parent(name, username, password):
    if username in db["parents"]:
        return "Parent username already exists."

    db["parents"][username] = {
        "name": name,
        "password": password,
        "children": []
    }

    save_db(db)
    return "Your account has been created successfully! 😊 Welcome to Lunar Logic — you’re all set to begin."


# -----------------------------
# Create Child Account
# -----------------------------
def create_child(name, username, password, parent_username):
    if parent_username not in db["parents"]:
        return "Parent does not exist."

    if username in db["children"]:
        return "Child username already exists."

    db["children"][username] = {
        "name": name,
        "password": password,
        "parent": parent_username,
        "points": 0,
        "tasks": []  # Child-specific assigned tasks
    }

    db["parents"][parent_username]["children"].append(username)

    save_db(db)
    return "Your account has been created successfully! 😊 Welcome to Lunar Logic — you’re all set to begin."


# -----------------------------
# Login Functions
# -----------------------------
def login_parent(username, password):
    if username in db["parents"] and db["parents"][username]["password"] == password:
        return "Parent login successful!"
    return "Invalid parent login."

def login_child(username, password):
    if username in db["children"] and db["children"][username]["password"] == password:
        return "Child login successful!"
    return "Invalid child login."


# -----------------------------
# Create Reusable Task (NEW)
# -----------------------------
def create_reusable_task(task_name):
    # Check if task already exists
    for task in db["tasks"]:
        if task["name"].lower() == task_name.lower():
            return "This task already exists."

    db["tasks"].append({
        "name": task_name
    })

    save_db(db)
    return "Task created successfully!"


# -----------------------------
# Assign Task to Child (NEW)
# -----------------------------
def assign_task_to_child(child_username, task_name):
    if child_username not in db["children"]:
        return "Child does not exist."

    # Ensure task exists globally
    task_exists = any(t["name"] == task_name for t in db["tasks"])
    if not task_exists:
        return "Task does not exist in the global task list."

    # Check if child already has this task
    for t in db["children"][child_username]["tasks"]:
        if t["name"] == task_name:
            return "Task already assigned to this child."

    # Assign task to child (new structure)
    db["children"][child_username]["tasks"].append({
        "name": task_name,
        "completed": False
    })

    save_db(db)
    return "Task assigned successfully!"
