# Python testing framework
from io import BytesIO, StringIO
import os, unittest, warnings, string, random

# Flask 
from app import create_app
from flask import url_for
from config import basedir
from config import Test
app = create_app(Test)

# Flask models
from app import db
from app.models import User, Turma, LibraryUpload, PeerReviewForm

TEST_DB = 'test.db'

import helper_functions

class TestCase(unittest.TestCase):
	
	def setUp(self):
		self.app = app.test_client()
		db.drop_all()
		db.create_all()
		
	def tearDown(self):
		db.session.remove()
		db.drop_all()

	# Test public pages, without logging in
	def test_public_facing_pages (self):
		# Does main index page display student registration link?
		response = self.app.get('/', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		if app.config['APP_NAME'] == 'Unikey':
			self.assertIn(b'Trusted University Application Consultants', response.data)
		elif app.config['APP_NAME'] == 'workUp':
			self.assertIn(b'Student registration', response.data)
		
		
		# Does attempting to access library trigger a log-in prompt
		response = self.app.get('/files/library/', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Please log in', response.data)
		
		# Does accessing a wrong page trigger a 404?
		response = self.app.get('/wrong/page/', follow_redirects=True)
		self.assertEqual(response.status_code, 404)
		self.assertIn(b'Oops', response.data)
	
	# Add a test user called Peter, who is not part of a class
	def test_add_user(self):
		user = User(username='Peter', email='peter@example.com', student_number='12345', email_confirmed = 1)
		user.set_password('test')
		db.session.add(user)
		db.session.commit()
		
		new_user = db.session.query(User).filter_by(username='Peter').first()
		assert new_user.username == 'Peter'
		
		
	# Create an admin called Patrick with password test
	def test_add_admin_user (self):
		helper_functions.register_admin_user()
		
		new_admin_user = db.session.query(User).filter_by(username='Patrick').first()
		assert new_admin_user.is_admin == True

	
	# Test incorrect user logins    
	def test_user_login(self):
		# Incorrect username
		self.test_add_user()
		response = helper_functions.login(self, 'Peterx' , 'test')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Invalid username', response.data)
		
		# Incorrect password
		response = helper_functions.login(self, 'Peter' , 'testx')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Invalid username', response.data)
		
		# Not part of a class
		response = helper_functions.login(self, 'Peter' , 'test')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'You do not appear to be part of a class', response.data)
		
		# Test 403s
		response = self.app.get('/files/library/edit/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		self.assertIn(b'Access denied', response.data)
		
		response = helper_functions.logout(self)
		self.assertEqual(response.status_code, 200)
		if app.config['APP_NAME'] == 'Unikey':
			self.assertIn(b'Trusted University Application Consultants', response.data)
		elif app.config['APP_NAME'] == 'workUp':
			self.assertIn(b'Student registration', response.data)

		
		
	# Test admin pages  
	def test_admin_pages(self):
		helper_functions.register_admin_user()
		
		# Main index page
		response = helper_functions.login(self, 'Patrick' , 'test')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Professor', response.data)
		
		# Library page displays Upload new library file
		response = self.app.get('/files/library/', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Upload new library file', response.data)
		
		
if __name__ == '__main__':
	
	unittest.main()
