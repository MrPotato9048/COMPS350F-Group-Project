from flask import Blueprint, render_template, session, redirect, request
from dateutil import tz
from . import mongo, currentTerm, userProfile, getCourse, getCourseList, getTermMessage, getSchoolMessage, OCAS, calGrade
import json

student = Blueprint('student', __name__)


# navigation
@student.route('/sidebar_stu')
def sidebar_stu():
    return render_template('student/sidebar.html', name = session['name'])
@student.route('/navbar_stu')
def navbar_stu():
    return render_template('student/navbar_stu.html', name = session['name'])


# home page
@student.route('/student')
def index():
    if 'name' in session:
        return render_template('student/index_student.html', name = session['name'], courses = getCourseList(currentTerm), term_msg = getTermMessage(currentTerm), school_msg = getSchoolMessage())
    return redirect('/login')
# academic history page
@student.route('/acad')
def acad():
    data = []
    for term in userProfile()['group']:
        if term != 'program':
            career = userProfile()['group'][term]['career']
            institution = userProfile()['group'][term]['institution']
            data += [[term, career, institution]]
    return render_template("student/Academic.html", data = data, identify = userProfile()['studID'])
# student announcement page
@student.route('/note')
def note():
    return render_template("student/announcement.html", term_msg = getTermMessage(currentTerm), school_msg = getSchoolMessage())
# student course page
@student.route('/course', methods = ['GET'])
def course():
    course = request.args.get('course')
    term = mongo.db.course.find_one({'courseCode':course})['term']
    getCAList = mongo.db.course.find_one({'courseCode':course})['OCAS']
    getExamList = mongo.db.course.find_one({'courseCode':course})['OES']
    data = []
    for x in getCAList:
        CA = x['name']
        if CA in getCourse(term)[course]:
            score = getCourse(term)[course][CA]
            if score is not None:
                data += [["CA", x, score]]
    for x in getExamList:
        Exam = x['name']
        if Exam in getCourse(term)[course]:
            score = getCourse(term)[course][Exam]
            if score is not None:
                data += [["Exam", x, score]]
    section = getCourse(term)[course]['section']
    ocas = OCAS(course, term)
    if term == currentTerm:
        grade = ""
    else:
        grade = calGrade(course, term)
    return render_template("student/course.html", data = data, term = term, course = course, section = section, grade = grade, ocas = ocas)
# student profile page
@student.route('/PD')
def personalDetails():
    return render_template("student/personal.html", stu_id = userProfile()['studID'], stu_name = userProfile()['studName'], gender = userProfile()['gender'], phone = userProfile()['phone'], subject = getCourseList(currentTerm), year = userProfile()['year'])
# edit student profile
@student.route('/PD_Edit', methods=['GET'])
def EditPD():
    return render_template("student/personal_edit.html", std_id = userProfile()['studID'], std_name = userProfile()['studName'], gender = userProfile()['gender'], phone = userProfile()['phone'], subject = getCourseList(currentTerm), year = userProfile()['year'])
@student.route('/PD_Edit', methods=['POST'])
def EditPDConfirm():
    studentName = request.form['std_name']
    phone = request.form['phone']
    mongo.db.user.update_one({'studName':session['name']}, {'$set':{'studName':studentName, 'phone':phone}})
    session['name'] = studentName
    return redirect('/PD')
# student term page
@student.route('/term', methods = ['GET'])
def term():
    term = request.args.get('term')
    data = getCourseList(term)
    return render_template("student/course_list.html", data = data, term = term)
# course attendance page
@student.route('/attendance',methods=['GET'])
def attendance_stu():
    code = json.loads(request.args.get('course_code'))[0]
    term = json.loads(request.args.get('course_code'))[1]
    aCourse = mongo.db.course.find_one({'courseCode':code})
    lecDate = []
    tutDate = []
    for x in aCourse['date']['lecture']:
        lecDate += [x.astimezone(tz.tzlocal()).strftime('%m/%d')]
    for x in aCourse['date']['tutorial']:
        tutDate += [x.astimezone(tz.tzlocal()).strftime('%m/%d')]
    lecData = []
    tutData = []
    for x in getCourse(term)[code]['attendance']['lecture']:
        lecData += [x]
    for x in getCourse(term)[code]['attendance']['tutorial']:
        tutData += [x]
    attendanceRate = round((sum(lecData + tutData)) / (len(lecData + tutData)) * 100, 1)
    return render_template("student/attendance.html", lecDate = lecDate, tutDate = tutDate, lecData = lecData, tutData = tutData, code = code, term = term, course = aCourse['courseName'], rate = attendanceRate)