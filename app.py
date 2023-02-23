######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

# for image uploading
import os
import base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# BEGIN code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute(
        "SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			    <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			    </form></br>
		        <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            # protected is a function defined in this file
            return flask.redirect(flask.url_for('protected'))

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')

# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')

@app.route("/photos", methods=['GET'])
@flask_login.login_required
def Photo():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('hello.html', message='These are your photos', photos=getUsersPhotos(uid), base64=base64)

@app.route("/register", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
    except:
        # this prints to shell, end users will not see this (all print statements go to shell)
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute(
            "INSERT INTO Users (first_name, last_name, dob, email, password, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(first_name, last_name, dob, email, password, hometown, gender)))
        conn.commit()

        # log user in
        user = User()
        user.id = email
        user.first_name = first_name
        user.last_name = last_name
        user.dob = dob
        user.hometown = hometown
        user.gender = gender
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT imgdata, photo_id, caption FROM Photo WHERE user_id = '{0}'".format(uid))
    # return a list of tuples, [(imgdata, pid, caption), ...]
    return cursor.fetchall()

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True
# END login code


@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


@app.route("/friends", methods=['POST'])
@flask_login.login_required
def add_friend():
    try:
        friend_id = request.form.get('friend_id')
    except:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('friends'))

    cursor = conn.cursor()

    # TESTING: for now assume id is correct
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if 1:
        print(cursor.execute(
            "INSERT INTO Friend (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, friend_id)))
        conn.commit()

        return render_template('friends.html', name=flask_login.current_user.id, friends=getUsersFriends(uid))
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('friends'))


@app.route("/friends", methods=['GET'])
@flask_login.login_required
def loadFriend():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friendList = getUsersFriends(uid)
    fofList = getUsersFriendRecommendation(uid)

    return render_template('friends.html', name=flask_login.current_user.id, friends=friendList, recommended=fofList)

def getUsersFriends(uid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM Friend WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()


def getUsersFriendRecommendation(uid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fof.friend_id, COUNT(fof.friend_Id) "
        "FROM Friend fof, (SELECT T.friend_id FROM Friend T WHERE T.user_id = {0}) AS df "
        "WHERE df.friend_id = fof.user_id "
        "AND fof.friend_id <> {0} "
        "AND fof.friend_id NOT IN (SELECT T.friend_id FROM Friend T WHERE T.user_id = {0}) "
        "GROUP BY fof.friend_id".format(uid))
    return cursor.fetchall()


# begin photo uploading code
# START photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        imgdata = imgfile.read()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Photo (imgdata, user_id, caption) VALUES (%s, %s, %s)''', (imgdata, uid, caption))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
    # The method is GET so we return a HTML form to upload the a photo.
    else:
        return render_template('upload.html')
# END photo uploading code

# START photo deleting code
@app.route('/delete', methods=['GET', 'POST'])
@flask_login.login_required
def delete_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        photo_id = request.form.get('photo_id')
        cursor = conn.cursor()
        cursor.execute(
            '''DELETE FROM Photo WHERE photo_id = %s''', (photo_id,))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo deleted!', photos=getUsersPhotos(uid), base64=base64)
    # The method is GET so we return a HTML form to upload the a photo.
    else:
        return render_template('delete.html')
# END photo deleting code

# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare')

if __name__ == "__main__":
    # this is invoked when in the shell you run
    # $ python app.py
    app.run(port=5000, debug=True)
