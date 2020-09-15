# Python testing framework
from io import BytesIO, StringIO
import os, unittest, warnings, string, random, secrets

# Flask 
from app import create_app
from flask import url_for
from config import basedir
from config import Test
app = create_app(Test)

# Flask models
from app import db
from app.models import User, Turma, LibraryUpload, PeerReviewForm
from app.classes.models import ClassManagement
from app.api import models
from app.api.models import ApiKey

# Set the test DB
TEST_DB = 'test.db'


### Generic helper functions
# Function to log-in
def login(self, username, password = 'test'):
	return self.app.post('/user/login', data=dict(username=username, password=password), follow_redirects=True)

# Function to log-out
def logout(self):
	return self.app.get('/user/logout',follow_redirects=True)

# Create an admin called Patrick (default) with password test
def register_admin_user (username = 'Patrick'):
	random_email = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
	random_student_number = ''.join(str(random.randint(1,9)) for i in range(8))
	admin_user = User(username=username, email=random_email, student_number=random_student_number, email_confirmed = 1, is_admin = 1, is_superintendant = 1)
	admin_user.set_password('test')
	db.session.add(admin_user)
	db.session.commit()
	
	new_admin_user = db.session.query(User).filter_by(username=username).first()
	assert new_admin_user.is_admin == True
	assert new_admin_user.is_superintendant == True


def add_teacher_to_class (teacher_id, turma_id):
		new_management = ClassManagement (user_id = teacher_id, turma_id = turma_id)	
		db.session.add(new_management)
		db.session.commit ()

# Register a test student, with random email address and student number
def register_student(self, username, password = 'test', confirm_email = True, ):
	
	# Test navigating to the registration page
	response = self.app.get('/user/register', follow_redirects=True)
	self.assertEqual(response.status_code, 200)
	self.assertIn(b'Register', response.data)
	
	# Create random email and student number
	random_email = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
	random_student_number = ''.join(str(random.randint(1,9)) for i in range(8))
	
	response = self.app.post('/user/register', content_type='multipart/form-data', 
								data={'username': username,
									  'email': random_email + '@mailinator.com',
									  'password': 'test',
									  'student_number': random_student_number,
									  'target_turmas': 1,
									  'signUpCode': 'testsignup'},
								follow_redirects=True)
	
	self.assertEqual(response.status_code, 200)
	self.assertIn(b'An email has been sent', response.data)
	
	# Test the user email validation check
	response = login(self, username, 'test')
	self.assertEqual(response.status_code, 200)
	self.assertIn(b'Please click the confirmation link', response.data)
	
	if confirm_email == True:
		user = User.query.filter_by(username = username).first()
		user.email_confirmed = True
		db.session.flush()
		db.session.commit()
		
		# Check that the user can now log-in properly
		response = login(self, username, 'test')
		self.assertEqual(response.status_code, 200)
			
	else:
		pass

# Add a class 
def add_turma ():
	random_turma_number = ''.join(str(random.randint(1,9)) for i in range(8))
	random_turma_label = 'Writing ' + str(random.randint(1,9))
	turma = Turma(turma_number = random_turma_number, turma_label = random_turma_label, turma_term = 'Fall', turma_year = '2020')
	
	db.session.add(turma)
	db.session.commit()
	
	new_turma = db.session.query(Turma).filter_by(turma_label=random_turma_label).first()
	assert new_turma.turma_term == 'Fall'
	assert new_turma.turma_year != '2019'

	#¡# Add a shim to ensure that each turma gets added as belonging to all administrators
	#¡# This should be removed and a proper testing mechanism put into place that manualyl enables this and tests it
	for user in User.query.all():
		new_management = ClassManagement (user_id = user.id, turma_id = new_turma.id)
		db.session.add(new_management)
		db.session.commit

# Add a peer review form
def add_peer_review_form ():
	# Add new form via the DB
	peer_review_form = PeerReviewForm (
		title = 'Teacher Feedback',
		description = 'Peer Review Form Description',
		serialised_form_data = '{"title": "Teacher Feedback", "description": "Peer Review Form Description", "fields": [{"title": "Feedback", "type": "element-paragraph-text", "required": false, "position": 1}]}'
	)
	
	db.session.add(peer_review_form)
	db.session.flush ()
	db.session.commit ()


# Create new API key
def create_api_key ():
		key = secrets.token_urlsafe(40)
		description = 'Key for testing the API'
		models.create_new_api_key(key, description)
		return key
