from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "studentverse_secret"

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studentverse.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    reg_no = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(50))
    semester = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Pending")

@app.route("/edit-profile",
           methods=["GET","POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if request.method == "POST":

        user.phone = request.form["phone"]
        user.bio = request.form["bio"]

        file = request.files["profile_pic"]

        if file and file.filename != "":

            filename = secure_filename(file.filename)

            file.save(
                os.path.join(
                    "static/uploads/profiles",
                    filename
                )
            )

            user.profile_pic = filename

        db.session.commit()

        return redirect("/profile")

    return render_template(
        "edit_profile.html",
        user=user
    )

class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    website = db.Column(db.String(200))
    instagram = db.Column(db.String(200))
    join_link = db.Column(db.String(200))

class CommunityMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    community_id = db.Column(db.Integer)  

# Home Page
@app.route("/")
def home():
    return render_template("landing.html")

from flask import request, redirect

@app.route("/register", methods=["GET", "POST"])
def reg():

    if request.method == "POST":

        email = request.form["email"]
        reg_no = request.form["reg_no"]

        existing_email = User.query.filter_by(email=email).first()
        existing_reg = User.query.filter_by(reg_no=reg_no).first()

        if existing_email:
            return "Email already registered!"

        if existing_reg:
            return "Register Number already exists!"

        user = User(
            name=request.form["name"],
            reg_no=reg_no,
            department=request.form["department"],
            semester=request.form["semester"],
            email=email,
            password=request.form["password"],
            role="student",
            status="Pending"
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def log():

    if request.method == "POST":

        reg_no = request.form["reg_no"]
        password = request.form["password"]

        user = User.query.filter_by(
            reg_no=reg_no,
            password=password
        ).first()

        if not user:
            return render_template("login_failed.html")

        if user.status == "Pending":
            return render_template("pending_approval.html")

        if user.status == "Approved":

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role

            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    return render_template(
        "profile.html",
        user=user
    )

@app.route("/approve/<int:user_id>")
def approve_student(user_id):

    user = User.query.get(user_id)

    user.status = "Approved"

    db.session.commit()

    return redirect("/admin/students")

@app.route("/ignore/<int:id>")
def ignore_student(id):

    student = User.query.get_or_404(id)

    db.session.delete(student)

    db.session.commit()

    return redirect("/students")

@app.route("/admin/students")
def students():

    students = User.query.filter_by(
        role="student"
    ).all()

    return render_template(
        "students.html",
        students=students
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/admin")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/admin-login")

    students = User.query.filter_by(
        status="Pending",
        role="student"
    ).all()

    students_count = User.query.filter_by(
        role="student"
    ).count()

    communities_count = Community.query.count()

    events_count = Event.query.count()

    placements_count = Placement.query.count()

    return render_template(
        "admin_dashboard.html",
        students=students,
        students_count=students_count,
        communities_count=communities_count,
        events_count=events_count,
        placements_count=placements_count
    )

@app.route("/communities")
def communities():

    communities = Community.query.all()

    return render_template(
        "communities.html",
        communities=communities
    )

@app.route("/tables")
def tables():

    users = User.query.count()
    communities = Community.query.count()

    return f"Users: {users} | Communities: {communities}"

@app.route("/join/<int:community_id>")
def join_community(community_id):

    if "user_id" not in session:
        return redirect("/login")

    existing = CommunityMember.query.filter_by(
        user_id=session["user_id"],
        community_id=community_id
    ).first()

    if existing:
        return redirect("/my-communities")

    member = CommunityMember(
        user_id=session["user_id"],
        community_id=community_id
    )

    db.session.add(member)
    db.session.commit()

    return redirect("/my-communities")

@app.route("/my-communities")
def my_communities():

    if "user_id" not in session:
        return redirect("/login")

    memberships = CommunityMember.query.filter_by(
        user_id=session["user_id"]
    ).all()

    communities = []

    for member in memberships:

        community = Community.query.get(
            member.community_id
        )

        communities.append(community)

    return render_template(
        "my_communities.html",
        communities=communities
    )

@app.route("/community/<int:id>/updates")
def community_updates(id):

    community = Community.query.get_or_404(id)

    notices = Notice.query.filter_by(
        community_id=id
    ).all()

    return render_template(
        "community_updates.html",
        community=community,
        notices=notices
    )

@app.route("/community/<int:id>")
def community_page(id):

    community = Community.query.get_or_404(id)

    members = CommunityMember.query.filter_by(
        community_id=id
    ).all()

    return render_template(
        "community_page.html",
        community=community,
        members=members
    )

@app.route("/create-admin")
def create_admin():

    admin = User(
        name="Administrator",
        reg_no="ADMIN001",
        department="ADMIN",
        semester="0",
        email="admin@studentverse.com",
        password="admin123",
        role="admin",
        status="Approved"
    )

    db.session.add(admin)
    db.session.commit()

    return "Admin Created"

@app.route("/admin-login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        reg_no = request.form["reg_no"]
        password = request.form["password"]

        admin = User.query.filter_by(
            reg_no=reg_no,
            password=password,
            role="admin"
        ).first()

        if admin:

            session["user_id"] = admin.id
            session["role"] = "admin"

            return redirect("/admin")

        return render_template("admin_login_failed.html")

    return render_template("admin_login.html")

@app.route("/admins")
def admins():

    admins = User.query.filter_by(role="admin").all()

    output = ""

    for admin in admins:
        output += f"""
        {admin.name} |
        {admin.reg_no} |
        {admin.password}<br>
        """

    return output

@app.route("/all-communities")
def all_communities():

    communities = Community.query.all()

    output = ""

    for c in communities:
        output += f"""
        ID: {c.id} |
        {c.name} |
        {c.category}<br>
        """

    return output

@app.route("/manage-communities")
def manage_communities():

    if session.get("role") != "admin":
        return redirect("/admin-login")

    communities = Community.query.all()

    return render_template(
        "manage_communities.html",
        communities=communities
    )

@app.route("/create-community",
           methods=["GET","POST"])
def create_community():

    if session.get("role") != "admin":
        return redirect("/admin-login")

    if request.method == "POST":

        community = Community(

            name=request.form["name"],
            category=request.form["category"],
            description=request.form["description"]

        )

        file = request.files["logo"]

        if file and file.filename != "":

            filename = secure_filename(
                file.filename
            )

            upload_folder = "static/uploads/community_logos"

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            file.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            community.logo = filename

        db.session.add(community)
        db.session.commit()

        return redirect("/manage-communities")

    return render_template(
        "create_community.html"
    )

@app.route("/delete-community/<int:id>")
def delete_community(id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    community = Community.query.get_or_404(id)

@app.route("/edit-community/<int:id>",
           methods=["GET", "POST"])
def edit_community(id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    community = Community.query.get_or_404(id)

    if request.method == "POST":

        community.name = request.form["name"]

        community.category = request.form["category"]

        community.description = request.form["description"]

        db.session.commit()

        return redirect("/manage-communities")

    return render_template(
        "edit_community.html",
        community=community
    )


@app.route("/community-members/<int:community_id>")
def community_members(community_id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    community = Community.query.get_or_404(
        community_id
    )

    memberships = CommunityMember.query.filter_by(
        community_id=community_id
    ).all()

    return render_template(
        "community_members.html",
        community=community,
        memberships=memberships,
        User=User
    )


@app.route("/remove-member/<int:id>")
def remove_member(id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    member = CommunityMember.query.get_or_404(id)

    community_id = member.community_id

    db.session.delete(member)

    db.session.commit()

    return redirect(
        f"/community-members/{community_id}"
    )

class Notice(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    link = db.Column(db.String(200))
    created_at = db.Column(db.String(50))
    community_id = db.Column(db.Integer)

@app.route("/create-notice",
           methods=["GET","POST"])
def create_notice():

    if request.method == "POST":

        notice = Notice(
            title=request.form["title"],
            content=request.form["content"],
            link=request.form["link"],
            community_id=request.form["community_id"]
        )

        file = request.files["image"]

        if file and file.filename != "":

            filename = secure_filename(file.filename)

            upload_folder = "static/uploads/notices"

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            file.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            notice.image = filename

        db.session.add(notice)
        db.session.commit()

        return redirect("/notices")

    communities = Community.query.all()

    return render_template(
        "create_notice.html",
        communities=communities
    )

@app.route("/notices")
def notices():

    notices = Notice.query.all()

    return render_template(
        "notices.html",
        notices=notices
    )

@app.route("/edit-notice/<int:id>",
           methods=["GET","POST"])
def edit_notice(id):

    notice = Notice.query.get_or_404(id)

    if request.method == "POST":

        notice.title = request.form["title"]

        notice.content = request.form["content"]

        notice.link = request.form["link"]

        db.session.commit()

        return redirect("/notices")

    return render_template(
        "edit_notice.html",
        notice=notice
    )

@app.route("/delete-notice/<int:id>")
def delete_notice(id):

    notice = Notice.query.get_or_404(id)

    db.session.delete(notice)

    db.session.commit()

    return redirect("/notices")

class Event(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    date = db.Column(db.String(50))
    category = db.Column(db.String(50))
    organizer = db.Column(db.String(100))
    link = db.Column(db.String(300))

@app.route("/create-event",
           methods=["GET", "POST"])
def create_event():

    if request.method == "POST":
        event = Event(
    title=request.form["title"],
    description=request.form["description"],
    date=request.form["date"],
    organizer=request.form["organizer"],
    category=request.form["category"],
    link=request.form["link"]
)

        db.session.add(event)
        db.session.commit()

        return redirect("/events")

    communities = Community.query.all()

    return render_template(
        "create_event.html",
        communities=communities
    )

@app.route("/events")
def events():

    events = Event.query.all()

    return render_template(
        "events.html",
        events=events
    )

@app.route("/edit-event/<int:id>",
           methods=["GET","POST"])
def edit_event(id):

    event = Event.query.get_or_404(id)

    if request.method == "POST":

        event.title = request.form["title"]
        event.description = request.form["description"]
        event.date = request.form["date"]
        event.organizer = request.form["organizer"]
        event.category = request.form["category"]
        event.link = request.form["link"]

        db.session.commit()

        return redirect("/events")

    return render_template(
        "edit_event.html",
        event=event
    )

@app.route("/delete-event/<int:id>")
def delete_event(id):

    event = Event.query.get_or_404(id)

    db.session.delete(event)

    db.session.commit()

    return redirect("/events")

@app.route("/add-sample-notice")
def add_sample_notice():

    notice = Notice(
        title="IEEE AI Workshop",
        content="Workshop on AI and ML",
        link="https://www.ieee.org",
        community_id=1
    )

    db.session.add(notice)
    db.session.commit()

    return "Notice Added"


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100))
    role = db.Column(db.String(100))
    package = db.Column(db.String(50))
    deadline = db.Column(db.String(50))
    link = db.Column(db.String(300))
    eligibility = db.Column(db.String(200))
    description = db.Column(db.Text)

@app.route("/create-placement",
    methods=["GET","POST"])
def create_placement():

    if request.method == "POST":

        placement = Placement(

            company=request.form["company"],

            role=request.form["role"],

            package=request.form["package"],

            deadline=request.form["deadline"],

            link=request.form["link"],

            eligibility=request.form["eligibility"],

            description=request.form["description"]

        )

        db.session.add(placement)

        db.session.commit()

        return redirect("/placements")

    return render_template(
        "create_placement.html"
    )

@app.route("/placements")
def placements():

    placements = Placement.query.all()

    return render_template(
        "placements.html",
        placements=placements
    )

@app.route("/edit-placement/<int:id>",
           methods=["GET","POST"])
def edit_placement(id):

    placement = Placement.query.get_or_404(id)

    if request.method == "POST":

        placement.company = request.form["company"]

        placement.role = request.form["role"]

        placement.package = request.form["package"]

        placement.deadline = request.form["deadline"]

        placement.link = request.form["link"]

        placement.description = request.form["description"]

        db.session.commit()

        return redirect("/placements")

    return render_template(
        "edit_placement.html",
        placement=placement
    )

@app.route("/delete-placement/<int:id>")
def delete_placement(id):

    placement = Placement.query.get_or_404(id)

    db.session.delete(placement)

    db.session.commit()

    return redirect("/placements")

# Create Database
with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )