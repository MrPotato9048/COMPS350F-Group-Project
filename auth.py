from flask import Blueprint, render_template, request, redirect, session, flash
from datetime import timedelta
from . import mongo, app
import bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/')
def init():
    if session and session['role'] == 'student':
        return redirect('/student')
    elif session and session['role'] == 'staff':
        return redirect('/staff')
    else:
        return redirect('/logout')

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    user = mongo.db.user
    studLogin = user.find_one({'studID' : request.form['accId']})
    remember = request.form.get('remember')
    if remember:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days = 14)
    if studLogin:
        if bcrypt.hashpw(request.form['pw'].encode('utf-8'), studLogin['password'].encode('utf-8')) == studLogin['password'].encode('utf-8'):
            session['name'] = studLogin['studName']
            session['role'] = 'student'
            return redirect('/student')
    staffLogin = user.find_one({'staffID' : request.form['accId']})
    if staffLogin:
        if bcrypt.hashpw(request.form['pw'].encode('utf-8'), staffLogin['password'].encode('utf-8')) == staffLogin['password'].encode('utf-8'):
            if staffLogin['staffID'] == 'admin':
                session['name'] = staffLogin['staffName']
                session['role'] = 'admin'
                return redirect('/admin')
            else: 
                session['name'] = staffLogin['staffName']
                session['role'] = 'staff'
                return redirect('/teacher')
    else:
        flash('Invalid username/password combination')
        return redirect('/login')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/login')