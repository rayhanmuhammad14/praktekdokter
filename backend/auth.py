from flask import render_template, request, redirect, url_for, jsonify, session, flash

def login(collection):
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = collection.find_one({"username": username, 'password': password})
        
        if user and password:
            session.permanent = True
            session['user'] = username
            msg = "SUKSES"
            return redirect(url_for("home"))
        else:
            flash('Kata Sandi Slaha', 'Info')
    return render_template("index.html")