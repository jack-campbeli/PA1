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
from itertools import chain, combinations

from datetime import date

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
				<input type='submit' name='submit' value="Sign In"></input>
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
@flask_login.login_required
def logout():
    name=flask_login.current_user.id
    flask_login.logout_user()
    return render_template('hello.html', topTen=getTopTenScore())


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
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    commentList = getAllComment()

    return render_template('hello.html', message='These are your photos', 
                            photos=getUsersPhotos(user_id), comments=commentList, 
                            userLiked=getAllUserWhoLiked(), countLike=countLikes(), base64=base64)


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
        return render_template('hello.html', name=email, message='Account Created!', 
                                topTen=getTopTenScore())
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))


def getUsersPhotos(user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT imgdata, photo_id, caption FROM Photo WHERE user_id = '{0}'".format(user_id))
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
    return render_template('hello.html', name=flask_login.current_user.id, 
                            message="Here's your profile", topTen=getTopTenScore())


@app.route("/friends", methods=['POST'])
@flask_login.login_required
def add_friend():
    try:
        friend_id = request.form.get('friend_id')
    except:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('friends'))

    cursor = conn.cursor()

    user_id = getUserIdFromEmail(flask_login.current_user.id)
    print(cursor.execute(
        "INSERT INTO Friend (user_id, friend_id) VALUES ('{0}', '{1}')".format(user_id, friend_id)))
    conn.commit()

    return render_template('friends.html', name=flask_login.current_user.id, friends=getUsersFriends(user_id))


@app.route("/friends", methods=['GET'])
@flask_login.login_required
def loadFriend():
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    friendList = getUsersFriends(user_id)
    fofList = getUsersFriendRecommendation(user_id)
    return render_template('friends.html', name=flask_login.current_user.id, friends=friendList, recommended=fofList)


def getUsersFriends(user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM Friend WHERE user_id = '{0}'".format(user_id))
    return cursor.fetchall()


def getUsersFriendRecommendation(user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fof.friend_id, COUNT(fof.friend_Id) "
        "FROM Friend fof, (SELECT T.friend_id FROM Friend T WHERE T.user_id = {0}) AS df "
        "WHERE df.friend_id = fof.user_id "
        "AND fof.friend_id <> {0} "
        "AND fof.friend_id NOT IN (SELECT T.friend_id FROM Friend T WHERE T.user_id = {0}) "
        "GROUP BY fof.friend_id".format(user_id))
    return cursor.fetchall()


# START tags code
@app.route("/view_tags", methods=['POST', 'GET'])
def view_tags():
    if request.method == 'POST':
        tags = request.form.get('tags')
        all_photos = request.form.get('all_photos')
        tagsList = tags.split(' ')
        print("tagsList:")
        print(tagsList)

        if all_photos or not flask_login.current_user.is_authenticated:
            return render_template('hello.html', 
                                    message="Here are all matching photos!", 
                                    photos=getAllTaggedPhotos(tagsList), countLike=countLikes(), base64=base64)
        else:    
            user_id = getUserIdFromEmail(flask_login.current_user.id)
            return render_template('hello.html', name=flask_login.current_user.id, 
                                    message="Here are your matching photos!", 
                                    photos=getUserTaggedPhotos(user_id, tagsList), countLike=countLikes(), base64=base64) 
    else:
        return render_template('tags.html', mostPopularTags=getMostPopularTags())

def getMostPopularTags():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tag_name, COUNT(tag_name) FROM Tag GROUP BY tag_name ORDER BY COUNT(tag_name) DESC LIMIT 3")
    return cursor.fetchall()

def getAllTaggedPhotos(tagsList):
    tagString = "','".join(tagsList)

    cursor = conn.cursor()
    cursor.execute(
        '''SELECT p.imgdata, p.photo_id, p.caption 
            FROM Photo p 
            JOIN Tag t ON p.photo_id = t.photo_id 
            WHERE t.tag_name IN ('{0}') 
            GROUP BY p.photo_id 
            HAVING COUNT(DISTINCT t.tag_name) = {1}'''.format(tagString, len(tagsList)))
    # return a list of tuples, [(imgdata, photo_id, caption), ...]
    return cursor.fetchall()

def getUserTaggedPhotos(user_id, tagsList):
    tagString = "','".join(tagsList)

    cursor = conn.cursor()
    cursor.execute(
        '''SELECT p.imgdata, p.photo_id, p.caption 
            FROM Photo p 
            JOIN Tag t ON p.photo_id = t.photo_id 
            WHERE p.user_id = '{0}' AND t.tag_name IN ('{1}') 
            GROUP BY p.photo_id 
            HAVING COUNT(DISTINCT t.tag_name) = {2}'''.format(user_id, tagString, len(tagsList)))
    # return a list of tuples, [(imgdata, photo_id, caption), ...]
    return cursor.fetchall()

def getOtherTaggedPhotos(user_id, tagsList):
    tagString = "','".join(tagsList)

    cursor = conn.cursor()
    cursor.execute(
        '''SELECT p.imgdata, p.photo_id, p.caption 
            FROM Photo p 
            JOIN Tag t ON p.photo_id = t.photo_id 
            WHERE p.user_id <> '{0}' AND t.tag_name IN ('{1}') 
            GROUP BY p.photo_id 
            HAVING COUNT(DISTINCT t.tag_name) = {2}'''.format(user_id, tagString, len(tagsList)))
    # return a list of tuples, [(imgdata, photo_id, caption), ...]
    return cursor.fetchall()

# START YOU MAY ALSO LIKE code
@app.route('/discover', methods=['GET'])
@flask_login.login_required
def discover():
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('discover.html', name=flask_login.current_user.id, photos=youMayAlsoLike(user_id), comments=getAllComment(), countLike=countLikes(), base64=base64)

# returns a list of lists of tags as strings
def powerset(tags):
    return list([list(comb) for r in range(len(tags)+1, 0, -1) for comb in combinations(tags, r)])

# returns a list of tags as strings
def getTopUserTags(user_id):
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT tag_name 
            FROM Tag 
            JOIN Photo ON Tag.photo_id = Photo.photo_id
            WHERE Photo.user_id = %s 
            GROUP BY tag_name 
            ORDER BY COUNT(tag_name) DESC LIMIT 3''', (user_id,))
    return [tag[0] for tag in cursor.fetchall()]

def youMayAlsoLike(user_id):
    tags = getTopUserTags(user_id)
    tags_powerset_list = powerset(tags)
    visited = set()
    output = []
    for tag_list in tags_powerset_list:
        for photo_tuple in getOtherTaggedPhotos(user_id, tag_list):
            if photo_tuple[1] not in visited:
                visited.add(photo_tuple[1])
                output.append(photo_tuple)
    return output

# END YOU MAY ALSO LIKE code
# END tags code


# START photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        imgdata = imgfile.read()

        caption = request.form.get('caption')

        tags = request.form.get('tags')
        # remove empty strings from list
        tagsList = [tag for tag in tags.split(' ') if tag != ""]

        a_name = request.form.get('a_name')

        if not albumExists(a_name, user_id):
            createAlbum(a_name, user_id)
        
        album_id = getAlbumIdFromName(a_name)

        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Photo (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s)''', (imgdata, user_id, caption, album_id))
        conn.commit()

        # increase contribution score
        increaseByOne(user_id, "Users", "user_id", "contribution_score")

        if len(tagsList):
            
            photo_id = cursor.lastrowid

            for i in range(len(tagsList)):
                cursor.execute(
                    '''INSERT INTO Tag (tag_name, photo_id) VALUES (%s, %s)''', (tagsList[i], photo_id))
                conn.commit()

        return render_template('hello.html', name=flask_login.current_user.id, 
                                message='Photo uploaded!', photos=getUsersPhotos(user_id), 
                                comments=getAllComment(), userLiked=getAllUserWhoLiked(), 
                                countLike=countLikes(), base64=base64)
    # The method is GET so we return a HTML form to upload the a photo.
    else:
        return render_template('upload.html')
# END photo uploading code


# START album creation code
def createAlbum(a_name, user_id):
    creation_date = date.today()

    if albumExists(a_name, user_id):
        return False
    else:
        cursor = conn.cursor()
        cursor.execute(
        "INSERT INTO Album (a_name, user_id, creation_date) VALUES ('{0}', '{1}', '{2}')".format(a_name, user_id, creation_date))
        conn.commit()
    return True

def albumExists(a_name, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Album WHERE a_name = %s AND user_id = %s", (a_name, user_id))
    if cursor.fetchone() is not None:
        return True
    else:
        return False

@app.route('/albums', methods=['GET', 'POST'])
@flask_login.login_required
def album():
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        a_name = request.form.get('a_name')
        if createAlbum(a_name, user_id):
            message = 'Album created!'
        else:
            message = 'Album already exists!'
        return render_template('hello.html', name=flask_login.current_user.id, 
                                message=message, photos=getUsersPhotos(user_id), 
                                comments=getAllComment(), userLiked=getAllUserWhoLiked(), 
                                countLike=countLikes(), base64=base64)
    # The method is GET so we return a HTML form to upload the a photo.
    else:
        return render_template('albums.html')
    
def getAlbumIdFromName(a_name):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT album_id FROM Album WHERE a_name = %s AND user_id = %s", (a_name, user_id))
    result = cursor.fetchone()
    if result is not None:
        return result[0]
    else:
        return None
# END album creation code


# START photo deleting code
@app.route('/delete', methods=['GET', 'POST'])
@flask_login.login_required
def delete_file():
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        photo_id = request.form.get('photo_id')
        a_name = request.form.get('a_name')
        message = 'You can\'t delete that!'
        cursor = conn.cursor()
        if photo_id:
            cursor.execute(
                '''SELECT * FROM Photo WHERE photo_id = %s AND user_id = %s''', (photo_id, user_id))
            if len(cursor.fetchall()) != 0:
                cursor.execute(
                    '''DELETE FROM Photo WHERE photo_id = %s AND user_id = %s''', (photo_id, user_id))
                message = 'Photo deleted!'
        elif a_name:
            album_id = getAlbumIdFromName(a_name)
            cursor.execute(
                '''SELECT * FROM Album WHERE album_id = %s AND user_id = %s''', (album_id, user_id))
            if len(cursor.fetchall()) != 0:
                cursor.execute(
                    '''DELETE FROM Album WHERE album_id = %s AND user_id = %s''', (album_id, user_id))
                message = 'Album deleted!'
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message=message, 
                                photos=getUsersPhotos(user_id), comments=getAllComment(), 
                                userLiked=getAllUserWhoLiked(), countLike=countLikes(), base64=base64)
    # The method is GET so we return a HTML form to upload the a photo.
    else:
        return render_template('delete.html')
# END photo deleting code


# START browsing page code
def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT imgdata, first_name, caption, photo_id \n"
        "FROM Photo \n"
        "INNER JOIN Users \n"
        "ON Photo.user_id = Users.user_id;")
    # return a list of tuples, [(imgdata, first_name, caption, photo_id), ...]
    return cursor.fetchall()


@flask_login.login_required
def getBrowsingPhotos(user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT imgdata, first_name, caption, photo_id "
        "FROM Photo "
        "INNER JOIN Users "
        "ON Photo.user_id = Users.user_id "
        "WHERE Users.user_id <> %s", (user_id,))
    # return a list of tuples, [(imgdata, first_name, caption), ...]
    return cursor.fetchall()


@app.route("/browse", methods=['GET'])
def browse():
    if flask_login.current_user.is_authenticated:
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        photos = getBrowsingPhotos(user_id)
    else:
        photos = getAllPhotos()
    return render_template('hello.html', message='Welcome to Photoshare', allphotos=photos, 
                            comments=getAllComment(), userLiked=getAllUserWhoLiked(), 
                            countLike=countLikes(), base64=base64)
# END browsing page code


@app.route("/hello", methods=['POST'])
@flask_login.login_required
def addComment():
    user_id = getUserIdFromEmail(flask_login.current_user.id)

    try:
        photoVal = request.form
        photo_id = list(photoVal.to_dict().keys())[0]
        text = list(photoVal.to_dict().values())[0]
        currentLoc = request.form.get('source')
    except:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('hello'))

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Comment (user_id, photo_id, date, text) VALUES ('{0}', '{1}', '{2}', '{3}')".format(
            user_id, photo_id, date.today(), text)
    )
    conn.commit()

    # increase contribution score
    increaseByOne(user_id, "Users", "user_id", "contribution_score")

    if currentLoc == "discover":
        return render_template('discover.html', name=flask_login.current_user.id, photos=youMayAlsoLike(user_id), comments=getAllComment(), countLike=countLikes(), base64=base64)
    else:
        return render_template('hello.html', name=flask_login.current_user.id, 
                            allphotos=getBrowsingPhotos(user_id), comments=getAllComment(), 
                            userLiked=getAllUserWhoLiked(), countLike=countLikes(), base64=base64)


def getAllComment():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Comment")
    return cursor.fetchall()


@app.route("/photos", methods=['POST'])
# does not need to be logged in
def giveALike():
    if flask_login.current_user.is_authenticated:
        user_id = getUserIdFromEmail(flask_login.current_user.id)
    else:
        user_id = None
       
    try:
        photoVal = request.form
        photo_id = list(photoVal.to_dict().keys())[0]
        currentLoc = request.form.get('source')
    except:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('hello'))

    # add to the liked table
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Likes (user_id, photo_id) "
        "VALUES (%s, %s) ", (user_id, photo_id)
    )
    conn.commit()

    if currentLoc == "discover":
        return render_template('discover.html', name=flask_login.current_user.id, photos=youMayAlsoLike(user_id), comments=getAllComment(), countLike=countLikes(), base64=base64)
    else:
        return render_template('hello.html', name=flask_login.current_user.id,
                           allphotos=getBrowsingPhotos(user_id), comments=getAllComment(), 
                           userLiked=getAllUserWhoLiked(), countLike=countLikes(), base64=base64)


def getAllUserWhoLiked():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT Users.user_id, first_name, last_name, photo_id "
        "FROM Users INNER JOIN Likes ON Users.user_id = Likes.user_id"
    )
    return cursor.fetchall()


def countLikes():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT Likes.photo_id, COUNT(Likes.user_id) "
        "FROM Likes "
        "GROUP BY Likes.photo_id"
    )
    return cursor.fetchall()


# helper function: increase the value of the cell by 1 given
#                   the table name, column name, and when row name = id
def increaseByOne(id, table_name, row_name, column_name):
    cursor = conn.cursor()
    cursor.execute("UPDATE {1} SET {3} = {3} + 1 WHERE {2} = '{0}'".format(
        id, table_name, row_name, column_name)
    )
    conn.commit()

# helper function: gets the top 10 users with the highest contribution score
def getTopTenScore():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, first_name, last_name "
        "FROM Users "
        "ORDER BY contribution_score DESC "
        "LIMIT 10; "
    )
    return cursor.fetchall()

def searchComment(text):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.first_name, u.last_name, count.num "
        "FROM Users u, (SELECT user_id, COUNT(text) as num "
            "FROM Comment c "
            "WHERE c.text = %s "     
            "GROUP BY c.user_id) AS count "
        "WHERE u.user_id = count.user_id "
        "ORDER BY count.num desc ", (text)
    )
    return cursor.fetchall()

# default page
@app.route("/", methods=['GET', 'POST'])
def hello():
        try:
            text = request.form.get('search')
        except:
            print("couldn't find all tokens")
            return flask.redirect(flask.url_for('hello'))

        if text == None:
            return render_template('hello.html', message='Welcome to Photoshare', 
                                    topTen=getTopTenScore())

        return render_template('hello.html', message='Welcome to Photoshare', 
                                topTen=getTopTenScore(), 
                                relatedC=text, orderedComment=searchComment(text))


if __name__ == "__main__":
    # this is invoked when in the shell you run
    # $ python app.py
    app.run(port=5000, debug=True)
