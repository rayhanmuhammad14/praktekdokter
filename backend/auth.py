from flask import render_template, request, redirect, url_for, jsonify, session, flash, make_response
from functools import wraps

def login(collection):
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        user = collection.find_one({"username": username, 'password': password})
        
        if user and password:
            session.permanent = True
            session['user'] = username
            msg = "SUKSES"
            return redirect(url_for("home"))
        else:
            flash('Kata Sandi Salah', 'Info')
    return render_template("index.html")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
