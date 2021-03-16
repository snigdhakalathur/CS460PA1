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
from datetime import date

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'sdfds'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
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
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
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
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
    try:
        email=request.form.get('email')
        password=request.form.get('password')
        first_name=request.form.get('first_name') 
        last_name = request.form.get('last_name') 
        dob = request.form.get('dob')
        hometown = request.form.get('hometown') 
        gender = request.form.get('gender')
        print("broke below this line")
        print("gender is:", gender, "   datadfa")
        print(first_name, last_name, dob, hometown, gender)
    except:
        print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        #print(cursor.execute("INSERT INTO Users (email, password) VALUES ('{0}', '{1}')".format(email, password)))
        try:
            print(cursor.execute("INSERT INTO Users (email, password, fName, lName, DOB, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, first_name, last_name, dob, hometown, gender)))
        except:
            print(cursor.execute("INSERT INTO Users (email, password, fName, lName, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(email, password, first_name, last_name, hometown, gender)))
        conn.commit()
		#log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Albums.albumName, Albums.albumID FROM Albums WHERE Albums.albumOwnedBy = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getPhotoByID(photoID):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(photoID))
	return cursor.fetchall()[0] #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

def getAllPhotosByTag(tagDescription):
	cursor = conn.cursor()
	cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption, TaggedWith.tagDescription FROM Pictures INNER JOIN taggedWith ON Pictures.picture_id = taggedWith.photoID WHERE TaggedWith.tagDescription = '{0}'".format(tagDescription))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotosByTag(uid, tagDescription):
	cursor = conn.cursor()
	sql = "SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption, TaggedWith.tagDescription FROM Pictures INNER JOIN taggedWith ON Pictures.picture_id = taggedWith.photoID WHERE TaggedWith.tagDescription = '{0}' AND Pictures.user_id = '{1}'".format(tagDescription, getUserIdFromEmail(uid))
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET THE POPULAR TAGS
def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT taggedWith.tagDescription FROM taggedWith GROUP BY taggedwith.tagDescription ORDER BY COUNT(*) DESC")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL THE PICTURES
def getPictures():
    cursor = conn.cursor()
    cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption FROM Pictures")
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL THE ALBUMS
def getAlbums():
    cursor = conn.cursor()
    cursor.execute("SELECT Albums.albumName, Albums.albumID FROM Albums")
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


#GET ALL THE PICTURES THAT BELONG TO AN ALBUM
def getAlbumPictures(albumID):
    cursor = conn.cursor()
    cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption FROM Pictures WHERE Pictures.belongs = {0}".format(albumID))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#INSERT LIKE RELATIONSHIP INTO LIKES TABLE
def likePhotos(uid, photoID):
	cursor = conn.cursor()
	sql = "REPLACE INTO Likes VALUES ({0},{1})".format(uid, photoID)
	print(sql)
	cursor.execute(sql)
	conn.commit()

#VIEW ALL USERS THAT LIKED A PHOTO
def viewAllLikes(photoID):
	cursor = conn.cursor()
	sql = "SELECT fName, lName, email, photoID FROM Likes INNER JOIN Users ON Users.user_id = Likes.userID HAVING photoID = {0};".format(photoID)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#COUNT TOTAL LIKES A PHOTO HAS
def countTotalLikes(photoID):
	cursor = conn.cursor()
	sql = "SELECT COUNT(*) FROM Likes WHERE photoID = {0};".format(photoID)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchone()[0] #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL FRIENDS OF A USER
def getUserFriends(uid):
	cursor = conn.cursor()
	sql = "SELECT fName, lName, email, userID1, userID2 FROM FriendsWith INNER JOIN Users ON Users.user_id = FriendsWith.userID2 HAVING userID1 = {0}".format(uid)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#SELECT FRIENDS WITH EMAIL LIKE SEARCH
def getUsersByEmail(uid, email):
	cursor = conn.cursor()
	sql = "SELECT fName, lName, email, user_id FROM Users WHERE email LIKE '%{0}%' AND user_id NOT IN (SELECT FriendsWith.userID2 FROM FriendsWith WHERE FriendsWith.userID1 = {1}) HAVING user_id <> {2} ".format(email, uid, uid)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#INSERT FRIENDSHIP INTO FRIENDSWITH TABLE
def addFriendship(my_uid, friend_uid):
	cursor = conn.cursor()
	sql = "INSERT INTO FriendsWith VALUES ({0},{1}), ({2},{3});".format(my_uid, friend_uid, friend_uid, my_uid)
	print(sql)
	cursor.execute(sql)
	conn.commit()

#SEARCH PHOTOS BY TAG
def searchPhotosByTag(tag):
	cursor = conn.cursor()
	numWords = len(tag.split(" "))
	tagEdited = tag.replace(" ", "','")
	tagEdited = "'" + tagEdited + "'"
	#sql = "(SELECT photoID, tagDescription FROM taggedWith WHERE tagDescription IN ({0}))".format(tagEdited)
	sql = "(SELECT photoID FROM taggedWith WHERE tagDescription IN ({0}) GROUP BY photoID HAVING COUNT(*) = {1})".format(tagEdited, numWords) 
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL PHOTOS BY PHOTOID
def getAllPhotosByPhotoIDS(ids):
	cursor = conn.cursor()
	if (ids == []):
		return []
	acc = ""
	for num in ids:
		acc += "'" + str(num) + "',"
	acc = acc[:-1]
	sql = "SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id in ({0})".format(acc)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL TAG DESCRIPTIONS
def getAllTagDescriptions():
	cursor = conn.cursor()
	sql = "SELECT * FROM Tags;"
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL USER'S TAG DESCRIPTIONS
def getAllUsersTagDescription(uid):
	cursor = conn.cursor()
	sql = "SELECT distinct A.tagDescription FROM (SELECT * FROM taggedWith INNER JOIN Pictures ON picture_id = photoID) as A WHERE user_id = {0}".format(uid)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall()

#ADD COMMENT TO PHOTO
def addCommentToPhoto(pid, uid, comm):
	cursor = conn.cursor()
	comDate = date.today()
	#if (uid != 0):
	sql = "INSERT INTO Comments (commentText, commentDate, commentOwnedBy, commentedUnder) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comm, comDate, uid, pid)
	#else:
		#sql = "INSERT INTO Comments (commentText, commentDate, commentedUnder) VALUES ('{0}', '{1}', '{2}')".format(comm, comDate, pid)
	
	print(sql)
	cursor.execute(sql)
	conn.commit()
	
#ADD ANON COMMENT TO PHOTO
def addAnonCommentToPhoto(pid, comm):
	cursor = conn.cursor()
	comDate = date.today()
	sql = "INSERT INTO Comments (commentText, commentDate, commentedUnder) VALUES ('{0}', '{1}', '{2}')".format(comm, comDate, pid)

	print(sql)
	cursor.execute(sql)
	conn.commit()

#GET ALL PHOTO'S COMMENTS
def getComments(photoID):
	cursor = conn.cursor()
	#sql = "SELECT * FROM photoshare.Comments WHERE commentedUnder = {0}".format(photoID)
	sql = "SELECT * FROM (SELECT * FROM Comments WHERE commentedUnder = {0}) as A INNER JOIN Users B ON B.user_id = A.commentOwnedBy".format(photoID)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET ALL ANON PHOTO COMMENTS
def getAnonComment(photoID):
	cursor = conn.cursor()
	sql = "SELECT * FROM Comments WHERE commentedUnder = {0} AND commentOwnedBy IS NULL".format(photoID)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

# "YOU MAY LIKE" PHOTOS
def getRecommendedPhotoIDs(tags):
	if tags == []:
		return []
	cursor = conn.cursor()
	acc = ""
	for t in tags:
		acc += "'" + str(t) + "',"
	acc = acc[:-1]
	sql = "SELECT * From (SELECT photoID, Count(photoID) AS C1 From taggedWith as B Group by photoID) AS B INNER JOIN (SELECT A.photoID, COUNT(*) as C2 FROM taggedWith A WHERE A.tagDescription IN ({0}) GROUP BY A.photoID ORDER BY COUNT(A.photoID) DESC) AS Q ON B.photoID = Q.photoID GROUP BY B.photoID ORDER BY C2 DESC, C1 ASC".format(acc)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET TOP 5 MOST USED TAGS OF USER
def getTopFiveUserTags(uid):
	cursor = conn.cursor()
	sql = "SELECT user_id, tagDescription, COUNT(*) FROM (taggedWith inner join Pictures on photoID = picture_id) WHERE user_id = {0} GROUP BY tagDescription ORDER BY COUNT(*) DESC LIMIT 5".format(uid)
	print(sql)
	cursor.execute(sql)
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#GET PHOTO OWNER
def getPhotoOwner(pid):
	cursor = conn.cursor()
	sql = "SELECT user_id FROM Pictures WHERE picture_id = {0}".format(pid)
	cursor.execute(sql)
	return cursor.fetchone()[0]

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid),base64=base64)
	#return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)


#begin photo uploading code
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
		album = request.form.get('albums')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		print("ALBUM IS: ", album)
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, belongs) VALUES (%s, %s, %s, %s )''' ,(photo_data,uid, caption, album))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
                
                return render_template('upload.html', albums = getAlbums())
#end photo uploading code

@app.route('/viewAllTags', methods=['GET'])
#@flask_login.login_required
def viewAllTags():
	if request.method == 'GET':
		tagDescription = request.args.get('tag')
		print("tags are:", tagDescription)
		return render_template('hello.html', message='All Photos By Tag', photos=getAllPhotosByTag(tagDescription),base64=base64)

@app.route('/viewUsersTags', methods=['GET'])
@flask_login.login_required
def viewUsersTags():
	if request.method == 'GET':
		tagDescription = request.args.get('tag')
		return render_template('hello.html', message='All Photos By Tag', photos=getUsersPhotosByTag(flask_login.current_user.id, tagDescription),base64=base64)

#GETTING MOST POPULAR TAG
@app.route('/viewPopularTags', methods=['GET'])
@flask_login.login_required
def viewPopularTag():
    if request.method == 'GET':
        tag = getAllTags()
        tagsWithoutExtraStuff = []
        for t in range(len(tag)):
                tagsWithoutExtraStuff += [tag[t][0]]
        print(tagsWithoutExtraStuff)
        #return render_template('hello.html', name=flask_login.current_user.id, message = "Most popular tag is: " + tag[0][0] + ". Here are the photos with the tag",base64=base64)
        return render_template('popularTags.html', name=flask_login.current_user.id, message = "Most popular tag is: " + tag[0][0] + ". Here are the photos with the tag",tags = tagsWithoutExtraStuff, base64=base64)
		
@app.route('/createAlbum', methods=['POST', 'GET'])
@flask_login.login_required
def createAlbum():
    if request.method == 'POST':
        albumName = request.form.get('albumName')
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        todayDate = date.today()
        cursor.execute("INSERT INTO Albums (albumName, albumOwnedBy, albumDate) VALUES ('{0}', '{1}', '{2}')".format(albumName, uid, todayDate))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Album created!')
	#The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('makeAlbum.html')
    
@app.route('/viewPhotos', methods=['GET'])
def viewPhotos():
    if request.method == 'GET':
        return render_template('hello.html', message='Here are all the photos', photos=getPictures(),base64=base64)

@app.route('/viewYourPhotos', methods=['GET'])
@flask_login.login_required
def viewYourPhotos():
    if request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('yourPhotos.html', message='Here are your photos', photos=getUsersPhotos(uid),base64=base64)

@app.route('/viewAlbums', methods=['GET'])
def viewAlbums():
    if request.method == 'GET':
        return render_template('hello.html', message='Here are all the albums', albums=getAlbums(), base64=base64)

@app.route('/viewYourAlbums', methods=['GET'])
@flask_login.login_required
def viewYourAlbums():
    if request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('yourAlbums.html', message='Here are your albums', albums=getUsersAlbums(uid), base64=base64)
    
@app.route('/deletePhoto', methods=['POST', 'GET'])
@flask_login.login_required
def deletePhoto():
    if request.method == 'GET':
        photoID = request.args.get('photoID')
        cursor = conn.cursor()
        #cursor.execute("INSERT INTO Albums (albumName) VALUES ('{0}')".format(albumName))
        cursor.execute("DELETE FROM taggedWith WHERE taggedWith.photoID = {0}".format(photoID))
        cursor.execute("DELETE FROM Pictures WHERE Pictures.picture_id = {0}".format(photoID))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo Deleted')
	#The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('hello.html')
    
@app.route('/deleteAlbum', methods=['POST', 'GET'])
@flask_login.login_required
def deleteAlbum():
    if request.method == 'GET':
        albumID = request.args.get('albumID')
        #uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Albums WHERE Albums.albumID = {0}".format(albumID))
        conn.commit()
        return render_template('yourAlbums.html', name=flask_login.current_user.id, message='Album Deleted')
	#The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('hello.html')
    
@app.route('/viewAlbumPictures', methods=['GET'])
def viewAlbumsPictures():
    if request.method == 'GET':
        albumID = request.args.get('albumID')
    
        #photos =  photos.encode("utf-8")
        #print("ALBUMS ARE ", photos)
        return render_template('hello.html', message='Here are all the photos in this album', photos=getAlbumPictures(albumID), base64=base64)
    
@app.route('/viewYourAlbumPictures', methods=['GET'])
@flask_login.login_required
def viewYourAlbumPictures():
    if request.method == 'GET':
        albumID = request.args.get('albumID')
        #photos =  photos.encode("utf-8")
        #print("ALBUMS ARE ", photos)
        return render_template('yourPhotos.html', message='Here are all the photos in this album', photos=getAlbumPictures(albumID), base64=base64)

@app.route('/reccomendFriends', methods=['GET'])
@flask_login.login_required
def reccomendFriends():
    if request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("SELECT t2.userID2, count(*), u.email FROM FriendsWith t1 INNER JOIN FriendsWith t2 ON t2.userID1 = t1.userID2 and t2.userID2 != t1.userID1 INNER JOIN Users u on t2.userID2 = u.user_id WHERE t1.userID1 = {0} and t1.userID2 and t2.userID2 NOT IN (Select t3.userID2 from friendsWith t3 where t3.userID1 = {1}) GROUP BY t2.userId2, u.email ORDER BY count(*) desc, userId2".format(uid, uid))
        recs = cursor.fetchall()
        
        print(recs)
        #cursor.execute("DELETE FROM taggedWith WHERE taggedWith.photoID = {0}".format(photoID))
        #photos =  photos.encode("utf-8")
        #print("ALBUMS ARE ", photos)
        return render_template('friendReccomendation.html', message='Here are some reccomended friends', friends=recs, base64=base64)

@app.route('/searchComments', methods=['POST', 'GET'])
def searchComments():
    if request.method == 'POST':
        cursor = conn.cursor()
        comment = request.form.get('comment')
        cursor.execute("Select COUNT(Comments.commentID), Users.email From Comments INNER JOIN Users Where Comments.commentText = '{0}' and Comments.commentOwnedBy = Users.user_id Group By Comments.commentText, Users.email Order by Count(Comments.commentID) desc".format(comment))
        recs = cursor.fetchall()
        print("recs are:", recs)
        return render_template('searchComments.html', message='Here are the results!', searchResults = recs)
	#The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('searchComments.html')

@app.route('/like', methods=['GET'])
@flask_login.login_required
def likePhoto():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		photoID = request.args.get('photoID')
		likePhotos(getUserIdFromEmail(flask_login.current_user.id),photoID)
		return render_template('hello.html', name=flask_login.current_user.id, message='All Photos By Tag', photos=getUsersPhotos(uid),base64=base64)


@app.route('/viewLikes', methods=['GET'])
@flask_login.login_required
def viewLikes():
	if request.method == 'GET':
		photoID = request.args.get('photoID')
		return render_template('likes.html', name=flask_login.current_user.id, message='Users that liked this photo:', photoID = photoID, photo=getPhotoByID(photoID), likes = viewAllLikes(photoID), count = countTotalLikes(photoID), base64=base64)

@app.route('/friends', methods=['GET','POST'])
@flask_login.login_required
def friends():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('friends.html', message='Friend Dashboard', notFriends = '', currentFriends=getUserFriends(uid), base64=base64)

	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		
		email = request.form.get('email')
		
		return render_template('friends.html', message='Friend Dashbaord', notFriends = getUsersByEmail(uid, email), currentFriends=getUserFriends(uid), base64=base64)

@app.route('/addFriend', methods=['GET'])
@flask_login.login_required
def addFriend():
	if request.method == 'GET':
		my_uid = uid = getUserIdFromEmail(flask_login.current_user.id)
		friend_uid = request.args.get('userID')
		addFriendship(my_uid,friend_uid)
		return flask.redirect(flask.url_for('friends'))

@app.route('/userActivity', methods=['GET'])
@flask_login.login_required
def userActivity():
	if request.method == 'GET':
                cursor = conn.cursor()
                cursor.execute("Select Users.email, COUNT(picture_id)+ COUNT(Comments.commentID) From Users left Outer Join Pictures on Users.user_id = Pictures.user_id left outer join Comments on Users.user_id = Comments.commentOwnedBy Group By Users.user_id having COUNT(picture_id)+ COUNT(Comments.commentID)>0 Order by COUNT(picture_id)+ COUNT(Comments.commentID) DESC Limit 10")
                recs = cursor.fetchall()
                return render_template('userActivity.html', message='Here are the top users with their contribution scores', activities=recs, base64=base64)

@app.route('/photoSearch', methods=['GET','POST'])
#@flask_login.login_required
def photoSearch():
		if request.method == 'POST':
			tag = request.form.get('photoSearch')
			pics = searchPhotosByTag(tag)
			res = []
			for i in pics:
				res.append(i[0])
			print("RESRES", res)
			return render_template('photoSearch.html', message='Photo Search Dashboard', photos = getAllPhotosByPhotoIDS(res), base64=base64)
		else:
			return render_template('photoSearch.html', message='Photo Search Dashboard', photos = [], base64=base64)

@app.route('/tags', methods=['GET'])
#@flask_login.login_required
def tags():
	if request.method == 'GET':
		t = getAllTagDescriptions()
		res = []
		for i in t:
			res.append(i[0])

		if (flask_login.current_user.is_anonymous != True):
			uid = getUserIdFromEmail(flask_login.current_user.id)
			
			myT = getAllUsersTagDescription(uid)
			myRes = []
			for i in myT:
				myRes.append(i[0])

			return render_template('tags.html', message='Tag Dashboard', allTags = res, myTags = myRes, base64=base64)
		else:
			return render_template('tags.html', message='Tag Dashboard', allTags = res, myTags = [], base64=base64)

@app.route('/comments', methods=['GET','POST'])
def comments():
	if (flask_login.current_user.is_anonymous != True):
		if request.method == 'POST':
				
			uid = getUserIdFromEmail(flask_login.current_user.id)
			comm = request.form.get('comment')
			pid = request.form.get('photoID')
			print(pid)
			addCommentToPhoto(pid, uid, comm)
			#return flask.redirect(flask.url_for('hello'))
			return render_template('comments.html', message='Comment Dashboard', allowed = True, photo=getPhotoByID(pid), comments = getComments(pid), anonComments = getAnonComment(pid), base64=base64)
		
		else:
			photoID = request.args.get('photoID')
			print(photoID)
			uid = getUserIdFromEmail(flask_login.current_user.id)
			user = getPhotoOwner(photoID)
			if uid == user:
				return render_template('comments.html', message='Comment Dashboard', allowed = False, photo=getPhotoByID(photoID), comments = getComments(photoID), anonComments = getAnonComment(photoID), base64=base64)

			else:
				return render_template('comments.html', message='Comment Dashboard', allowed = True, photo=getPhotoByID(photoID), comments = getComments(photoID), anonComments = getAnonComment(photoID), base64=base64)
	else:
		if request.method == 'POST':

			comm = request.form.get('comment')
			pid = request.form.get('photoID')
			print(pid)
			addAnonCommentToPhoto(pid, comm)
			return render_template('comments.html', message='Comment Dashboard', allowed = True, photo=getPhotoByID(pid), comments = getComments(pid), anonComments = getAnonComment(pid), base64=base64)
		
		else:

			photoID = request.args.get('photoID')
			print(photoID)			
			return render_template('comments.html', message='Comment Dashboard', allowed = True, photo=getPhotoByID(photoID), comments = getComments(photoID), anonComments = getAnonComment(photoID), base64=base64)

	
@app.route('/photoRecs', methods=['GET'])
@flask_login.login_required
def photoRecs():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tags = getTopFiveUserTags(uid)
		res = []
		for i in tags:
			res.append(i[1])

		if res != []:
			pids = getRecommendedPhotoIDs(res)
			res2 = []
			for i in pids:
				res2.append(i[0])
			
			return render_template('photoRecs.html', message='You May Also Like Dashboard', photos = getAllPhotosByPhotoIDS(res2),  base64=base64)	
		else:
			return render_template('photoRecs.html', message='You May Also Like Dashboard', photos = [],  base64=base64)	

	
#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
