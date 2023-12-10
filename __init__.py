from flask import Flask, session
from dateutil import tz
from flask_pymongo import PyMongo

app = Flask(__name__)
mongo = PyMongo(app, uri = "mongodb+srv://group:hrtWVuUsBA1TKvpd@cluster0.ctuol90.mongodb.net/SRS")
app.config['SECRET_KEY'] = 'testing_secret_key'
currentTerm = '2023 Autumn Term' # temporary, might implement through database later

# data retrieval and calculation
def userProfile():
    if session['role'] == 'student':
        userProfile = mongo.db.user.find_one({'studName':session['name']})
    else:
        userProfile = mongo.db.user.find_one({'staffName':session['name']})
    return userProfile
# courses
def getCourse(term): # get course from user collection
    course = userProfile()['group'][term]['course']
    return course
def getCourseList(term): # get course from course collection
    userCourse = []
    for x in getCourse(term):
        userCourse += [mongo.db.course.find_one({'courseCode':x})]
    return userCourse
# messages
def getTermMessage(term):
    userTermMessage = []
    for x in getCourse(term):
        message = mongo.db.message.find_one({'target': {'$regex': x, '$options': 'i'}})
        if message is not None:
            message['date'] = message['date'].astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S')
            userTermMessage.append(message)
    return userTermMessage
def getSchoolMessage():
    group = userProfile()['group']
    getSchool = group['program']['programName']
    userSchoolMessage = []
    messages = mongo.db.message.find({'$or': [{'target': {'$regex': getSchool, '$options': 'i'}}, {'target': {'$regex': 'all', '$options': 'i'}}]})
    for message in messages:
        message['date'] = message['date'].astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S')
        userSchoolMessage.append(message)
    return userSchoolMessage
# grades
def OCAS(course, term):
    totalWeight = 0
    weightedScore = 0
    for item in mongo.db.course.find_one({'courseCode':course})['OCAS']:
        name = item['name']
        weight = item['weight']
        if name in getCourse(term)[course]:
            score = getCourse(term)[course][name]
            weightedScore += score * weight
        totalWeight += weight
    weightedScore /= totalWeight
    return round(weightedScore, 1)
def calGrade(course, term):
    totalWeight = 0
    weightedScore = 0
    for item in mongo.db.course.find_one({'courseCode':course})['OCAS'] + mongo.db.course.find_one({'courseCode':course})['OES']:
        name = item['name']
        weight = item['weight']
        if name in getCourse(term)[course]:
            score = getCourse(term)[course][name]
            weightedScore += score * weight
        totalWeight += weight
    weightedScore /= totalWeight
    # not sure the grading criteria lol
    if weightedScore >= 80:
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
    return grade

from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from .student import student as student_blueprint
app.register_blueprint(student_blueprint)

from .teacher import teacher as teacher_blueprint
app.register_blueprint(teacher_blueprint)

from .admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)