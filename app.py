from flask import Flask, render_template, request, redirect, url_for
from accounts import create_parent, create_child, login_parent, login_child

app = Flask(__name__)

@app.route("/")
def landing():
    return render_template("landing.html")

# -----------------------------
# Parent Login
# -----------------------------
@app.route("/parent-login", methods=["GET", "POST"])
def parent_login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        result = login_parent(username, password)

        if "successful" in result:
            return redirect(f"/parent-dashboard?username={username}")

        return result

    return render_template("parent-login.html")

# -----------------------------
# Child Login
# -----------------------------
@app.route("/child-login", methods=["GET", "POST"])
def child_login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        result = login_child(username, password)

        if "successful" in result:
            return redirect(f"/child-dashboard?username={username}")

        return result

    return render_template("child-login.html")

# -----------------------------
# Create Account (Parent or Child)
# -----------------------------
@app.route("/create-account", methods=["GET", "POST"])
def create_account_page():
    if request.method == "POST":
        role = request.form.get("role")
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        if role == "parent":
            result = create_parent(name, username, password)
        else:
            parent_username = request.form["parent_username"]
            result = create_child(name, username, password, parent_username)

        # Check if account creation was successful before rendering success page
        if "successful" in result.lower() or "success" in result.lower():
            return render_template("account_success.html")

        return result

    return render_template("create-account.html")

# -----------------------------
# Parent Dashboard
# -----------------------------
@app.route("/parent-dashboard")
def parent_dashboard():
    username = request.args.get("username")

    from accounts import db

    if username not in db["parents"]:
        return "Parent not found."

    parent = db["parents"][username]

    children_data = []
    for child_username in parent["children"]:
        child = db["children"][child_username]
        children_data.append({
            "username": child_username,
            "name": child["name"],
            "points": child["points"],
            "tasks": child["tasks"]
        })

    return render_template(
        "parent-dashboard.html",
        parent_name=parent["name"],
        parent_username=username,
        children=children_data
    )

@app.route('/parent/add-child', methods=['GET'])
def render_add_child():
    parent_username = request.args.get('username')
    return render_template('add_child.html', parent_username=parent_username)

@app.route('/parent/add-child', methods=['POST'])
def save_child():
    parent_username = request.form.get('parent_username')
    child_name = request.form.get('name')
    child_username = request.form.get('username')
    child_password = request.form.get('password')
    
    # Save the child account and automatically link to the parent using accounts function
    result = create_child(child_name, child_username, child_password, parent_username)
    
    # Redirect back to the parent's kid list dashboard
    return redirect(f'/parent-kids?username={parent_username}')


# -----------------------------
# Parent Kids Page
# -----------------------------
@app.route("/parent-kids")
def parent_kids():
    from accounts import db

    username = request.args.get("username")

    if username not in db["parents"]:
        return "Parent not found."

    parent = db["parents"][username]

    children_data = []
    for child_username in parent["children"]:
        child = db["children"][child_username]
        children_data.append({
            "username": child_username,
            "name": child["name"],
            "points": child["points"],
            "tasks": child["tasks"]
        })

    return render_template(
        "parent-kids.html",
        parent_username=username,
        children=children_data
    )

# -----------------------------
# Parent Tasks Page
# -----------------------------
@app.route('/parent-tasks')
def parent_tasks():
    from accounts import db
    
    parent_username = request.args.get('username')
    parent_data = db["parents"].get(parent_username, {})
    
    # Filter tasks created exclusively by this parent
    all_tasks = parent_data.get("tasks", [])
    parent_tasks_list = [t for t in all_tasks if isinstance(t, dict) and t.get("created_by") == parent_username]
    
    return render_template('parent_tasks.html', 
                           parent_username=parent_username, 
                           tasks=parent_tasks_list)

# -----------------------------
# Assign Task Page
# -----------------------------
@app.route("/assign-task", methods=["GET", "POST"])
def assign_task():
    from accounts import db, assign_task_to_child

    parent_username = request.args.get("username")

    if parent_username not in db["parents"]:
        return "Parent not found."

    parent = db["parents"][parent_username]

    if request.method == "POST":
        child_username = request.form["child_username"]
        task_name = request.form["task_name"]

        message = assign_task_to_child(child_username, task_name)

        return render_template(
            "task-success.html",
            parent_username=parent_username,
            task_name=task_name
        )

    # GET request → show form
    children_list = []
    for child_username in parent["children"]:
        children_list.append({
            "username": child_username,
            "name": db["children"][child_username]["name"]
        })

    return render_template(
        "assign-task.html",
        parent_username=parent_username,
        children=children_list,
        tasks=db["tasks"]
    )

# -----------------------------
# Child Dashboard
# -----------------------------
@app.route("/child-dashboard")
def child_dashboard():
    from accounts import db

    username = request.args.get("username")

    if username not in db["children"]:
        return "Child not found."

    child = db["children"][username]

    return render_template(
        "child-dashboard.html",
        child_name=child["name"],
        tasks=child["tasks"],
        points=child["points"]
    )

# -----------------------------
# Create Task (Parent Only)
# -----------------------------
@app.route('/create-task', methods=['GET', 'POST'])
def create_task():
    from accounts import db, save_db
    
    parent_username = request.args.get('username')

    if request.method == 'POST':
        task_name = request.form.get('task_name')
        
        if parent_username in db["parents"]:
            if "tasks" not in db["parents"][parent_username]:
                db["parents"][parent_username]["tasks"] = []
                
            db["parents"][parent_username]["tasks"].append({
                "name": task_name,
                "created_by": parent_username,
                "completed": False
            })
            save_db(db)
            
        return redirect(url_for('parent_dashboard', username=parent_username))
        
    return render_template('create_task.html', parent_username=parent_username)

@app.route('/update-task-status', methods=['POST'])
def update_task_status():
    from accounts import db, save_db
    
    child_username = request.form.get('child_username')
    task_name = request.form.get('task_name')
    status = request.form.get('status')
    
    is_completed = True if status == 'complete' else False
    
    if child_username in db["children"]:
        child = db["children"][child_username]
        for task in child["tasks"]:
            if isinstance(task, dict) and task.get("name") == task_name:
                task["completed"] = is_completed
                break
            elif isinstance(task, str) and task == task_name:
                idx = child["tasks"].index(task)
                child["tasks"][idx] = {"name": task_name, "completed": is_completed}
                break
        save_db(db)
        
    return redirect(f'/child-dashboard?username={child_username}')

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)