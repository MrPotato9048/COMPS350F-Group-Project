from flask import Blueprint, render_template, session, redirect, request, flash
from dateutil import tz
from datetime import date, datetime
from . import mongo, currentTerm, userProfile, getCourseList, getTermMessage, getSchoolMessage
import json

teacher = Blueprint('teacher', __name__)


# navigation
@teacher.route('/sidebar_tc')
def sidebar_tc():
    return render_template("teacher/sidebar.html", name = session['name'])
@teacher.route('/navbar_tc')
def navbar_tc():
    return render_template("teacher/navbar_tc.html", name = session['name'])


# home page
@teacher.route('/teacher')
def index_tc():
    if 'name' in session:
        return render_template("teacher/index_teacher.html", name = session['name'], courses = getCourseList(currentTerm), term_msg = getTermMessage(currentTerm), school_msg = getSchoolMessage())
    return redirect("/login")
#teacher/Academic.html
@teacher.route('/acad_tc')
def acad_tc():
    data =[]
    for term in userProfile()['group']:
        if term != 'program':
            career = userProfile()['group'][term]['career']
            institution = userProfile()['group'][term]['institution']
            data += [[term, career, institution]]
    return render_template("teacher/Academic.html", data = data)
#Browsing the teacher course_list by term
@teacher.route('/term_tc', methods = ['GET'])
def term_tc():
    term = request.args.get('term')
    data = getCourseList(term)
    session['viewTerm'] = term
    return render_template("teacher/course_list.html", data = data, term = term)
#Browsing the Course Info for the teacher (might simplify the code by extracting ocas and grade outside and combined with the one in __init__.py)
@teacher.route('/course_tc', methods = ['GET'])
def course_tc():
    course = request.args.get('course')
    term = mongo.db.course.find_one({'courseCode':course})['term']
    getCAList = mongo.db.course.find_one({'courseCode':course})['OCAS']
    getExamList = mongo.db.course.find_one({'courseCode':course})['OES']
    students = mongo.db.user.find({'studID':{'$exists':True}})
    columns = [['Student ID','stu_name','Assign1','Assign2','Assign3','OCAS','Exam','Total_Score']]
    data = []
    examScore = 0
    ocasTotal = 0
    ocasMax = 0
    studTotal = 0
    gradeValue = {"A": 4, "A-": 3.7, "B+": 3.3, "B": 3, "B-": 2.7, "C+": 2.3, "C": 2, "F": 0}
    gradeValues = []

    for student in students:
        stu_id = student['studID']
        stu_name = student['studName']
        notExamed = False
        CAList = []
        for x in getCAList:
            CA = x['name']
            if CA in student['group'][term]['course'][course]:
                score = student['group'][term]['course'][course][CA]
                if score is not None:
                    CAList += [[score]]
        for x in getExamList:
            Exam = x['name']
            if Exam in student['group'][term]['course'][course]:
                score = student['group'][term]['course'][course][Exam]
                if score is not None:
                    examScore = score
            else:
                notExamed = True
        # calculate ocas
        ocas = 0
        totalWeight = 0
        weightedScore = 0
        for item in mongo.db.course.find_one({'courseCode':course})['OCAS']:
            name = item['name']
            weight = item['weight']
            if name in student['group'][term]['course'][course]:
                score = student['group'][term]['course'][course][name]
                weightedScore += score * weight
            totalWeight += weight
        weightedScore /= totalWeight
        ocas = round(weightedScore, 1)
        ocasTotal += ocas
        ocasMax = max(ocasMax, ocas)
        # grade
        grade = ""
        totalWeight = 0
        weightedScore = 0
        for item in mongo.db.course.find_one({'courseCode':course})['OCAS'] + mongo.db.course.find_one({'courseCode':course})['OES']:
            name = item['name']
            weight = item['weight']
            if name in student['group'][term]['course'][course]:
                score = student['group'][term]['course'][course][name]
                weightedScore += score * weight
            totalWeight += weight
        weightedScore /= totalWeight
        if notExamed == True:
            grade = "NaN"
        elif weightedScore >= 80:
            grade = "A"
        elif weightedScore >= 74:
            grade = "A-"
        elif weightedScore >= 66:
            grade = "B+"
        elif weightedScore >= 60:
            grade = "B"
        elif weightedScore >= 54:
            grade = "B-"
        elif weightedScore >= 48:
            grade = "C+"
        elif weightedScore >= 40:
            grade = "C"
        else:
            grade = "F"
        if grade != "NaN":
            gradeValues.append(gradeValue[grade])
        if grade == "NaN":
            data += [[stu_id, stu_name, CAList, ocas, "NaN", grade]]
        else:
            data += [[stu_id, stu_name, CAList, ocas, examScore, grade]]
        studTotal += 1
    
    high_grade = ""
    avg_grade = ""
    if term == currentTerm:
        high_grade = "NaN"
        avg_grade = "NaN"
    else:
        if gradeValues:
            high_grade = next(grade for grade, value in gradeValue.items() if value == max(gradeValues))
            avg_grade = sum(gradeValues) / len(gradeValues)
            avg_grade = min(gradeValue, key = lambda grade: abs(gradeValue[grade] - avg_grade))
        else:
            high_grade = "NaN"
            avg_grade = "NaN"
    ocasAvg = ocasTotal / studTotal
    return render_template("teacher/course.html", course = course, term = term, data = data, columns = columns, high_grade = high_grade, avg_grade = avg_grade, high_ocas = ocasMax, avg_ocas = ocasAvg, CA = getCAList)
#Change course code
@teacher.route('/code_edit',methods=['GET'])
def course_code():
    code = request.args.get('course')
    course = mongo.db.course.find_one({'courseCode':code})['courseName']
    return render_template("teacher/course_edit.html",title = course,code = code, term = session['viewTerm'])
@teacher.route('/code_r',methods=['POST'])
def code_r():
    code = request.form['code']
    n_code = request.form['new_code']
    if n_code == "" or n_code == code:
        flash('Error: Invalid course code')
        return redirect("/code_edit?course=" + code)
    else:
        mongo.db.course.update_one({'courseCode':code}, {'$set':{'courseCode':n_code}})
        mongo.db.user.update_many(
            {'group.' + session['viewTerm'] + '.course.' + code: {'$exists': True}},
            {'$rename': {'group.' + session['viewTerm'] + '.course.' + code: 'group.' + session['viewTerm'] + '.course.' + n_code}}
        )
        mongo.db.message.update_many({'target': code + " students"}, {'$set': {'target': n_code + " students"}})
        return redirect("/term_tc?term=" + session['viewTerm'])
#Browsing the coures attendance for the student
@teacher.route('/attendance_tc',methods=['GET'])
def attendance():
    code = json.loads(request.args.get('course'))[0]
    term = json.loads(request.args.get('course'))[1]
    aCourse = mongo.db.course.find_one({'courseCode':code})
    lecDate = []
    tutDate = []
    for x in aCourse['date']['lecture']:
        lecDate += [x.astimezone(tz.tzlocal()).strftime('%m/%d')]
    for x in aCourse['date']['tutorial']:
        tutDate += [x.astimezone(tz.tzlocal()).strftime('%m/%d')]
    studList = []
    for student in mongo.db.user.find({'studID': {'$exists': True}, 'group.' + term + '.course.' + code: {'$exists': True}}):
        lecData = []
        tutData = []
        for x in student['group'][term]['course'][code]['attendance']['lecture']:
            lecData += [x]
        for x in student['group'][term]['course'][code]['attendance']['tutorial']:
            tutData += [x]
        attendanceRate = round((sum(lecData + tutData)) / (len(lecData + tutData)) * 100, 1)
        studList += [[student['studID'], student['studName'], lecData, tutData, attendanceRate]]
    return render_template("teacher/attendance.html",term = term, lecDate = lecDate, tutDate = tutDate, code = code, course = aCourse['courseName'], studList = studList)
@teacher.route('/attd_edit',methods=['POST'])
def attendance_edit():
    course = request.form['code']
    term = request.form['term']
    stu_list = request.form['stu_list'] #store the student's attendance status, can be split by ";", the first value is student ID, the second value is student name, the remaining values are the attendance status
    
    lists = stu_list.split(";")
    for list in lists:
        if list:
            elements = list.split(",")
            studID = elements[0]
            attendance = [elem == 'true' for elem in elements[2:]]
            mongo.db.user.update_one({'studID': studID}, {'$set': {'group.' + term + '.course.' + course + '.attendance': {'lecture': attendance[:len(attendance) // 2], 'tutorial': attendance[len(attendance) // 2:]}}})

    return redirect('/attendance_tc?course=' + json.dumps([course, term]))
#List the course assessment
@teacher.route('/assessment',methods=['GET'])
def assessment():
    code = json.loads(request.args.get('course'))[0]
    term = json.loads(request.args.get('course'))[1]
    course_name = mongo.db.course.find_one({'courseCode':code, 'term': term})['courseName']
    stu_num = mongo.db.user.count_documents({'studID': {'$exists': True}, 'group.' + term + '.course.' + code: {'$exists': True}})
    data = []
    for ocas in mongo.db.course.find_one({'courseCode':code})['OCAS']:
        data += [[ocas['name'], ocas['date'].astimezone(tz.tzlocal()).strftime('%d/%m/%Y')]]
    return render_template("teacher/course_Assessment.html",data = data,code = code,course = course_name,stu_num=stu_num, term = term)
#Assessment score
@teacher.route('/asm_score',methods=['GET'])
def assessment_score():
    code = request.args.get('course_code')
    asm = json.loads(request.args.get('asm'))[0] #assessment
    term = json.loads(request.args.get('asm'))[1]
    course = mongo.db.course.find_one({'courseCode':code})['courseName']
    asm_date = mongo.db.course.find_one({'courseCode':code})['OCAS'][0]['date'].astimezone(tz.tzlocal()).strftime('%d/%m/%Y')
    data =[]
    for student in mongo.db.user.find({'studID': {'$exists': True}, 'group.' + term + '.course.' + code: {'$exists': True}}):
        data += [[student['studID'], student['studName'], student['group'][term]['course'][code][asm]]]
    return render_template("teacher/Assessment_score.html",code = code,course = course,Assessment=asm,Date=asm_date, data = data, term = term)
@teacher.route('/assessment_edit',methods=['POST'])
def assessment_edit():
    code = request.form['course_code']
    asm = request.form['assessment']
    term = request.form['term']
    stu_list = request.form['stu_list']  #store the student's attendance status, can be split by ";", the first value is student ID, the second value is the score

    pairs = stu_list.split(";")
    for pair in pairs:
        if pair:
            id, score = pair.split(",")
            mongo.db.user.update_one({'studID': id}, {'$set': {'group.' + term + '.course.' + code + '.' + asm: int(score)}})
    
    return redirect("/asm_score?course_code=" + code + "&asm=" + json.dumps([asm, term]))

#Teacher Post new Announcement
@teacher.route('/post_anno')
def post_anno():
    name = session['name']
    id = userProfile()['staffID']
    currentDate = date.today().strftime("%d/%m/%Y")
    data = []
    for course in getCourseList(currentTerm):
        data += [course['courseCode']]
    return render_template("teacher/anno_edit.html",acc_id=id,name=name,data =data, date = currentDate)
#Teacher Insert new Announcement
@teacher.route('/insert_anno',methods=['POST'])
def insert_anno():
    title = request.form['title']
    target = request.form['target'] + " students"
    content = request.form['text']
    mongo.db.message.insert_one({'noteTitle':title,'date':datetime.now(),'note':content, 'publisher':session['name'],'target':target})
    return redirect("/note_tc")
#Browsing the announcement by teacher
@teacher.route('/note_tc')
def note_tc():
    return render_template("teacher/announcement.html", term_msg = getTermMessage(currentTerm), school_msg = getSchoolMessage())