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

	
	# Test adding a peer review form
	def test_references (self):
		if app.config['APP_NAME'] != 'Unikey':
			return
		
		# Register student and admin
		helper_functions.register_admin_user()
		helper_functions.logout(self)
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.logout(self)
		
		# View main references public log-in page
		response = self.app.get('/references/', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Please enter the log-in code to submit a reference', response.data)
		
		
		# Log-in with public password
		signup_code = app.config['SIGNUP_CODES'].pop() # Python sets are not sortable
		app.config['SIGNUP_CODES'].add(signup_code)
		
		# Attempt with wrong password
		response = self.app.post(
			'/references/compose',
			data={'password': 'wrong_code'},
			follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		self.assertNotIn(b'Personal information', response.data)
		
		# Attempt with wrong password
		response = self.app.post(
			'/references/compose',
			data={'password': signup_code},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Personal information', response.data)
		
		response = self.app.post(
			'/references/submit',
			content_type='multipart/form-data', 
			data={
				'referee_name': 'Test referee',
				'student_name': 'Test student name',
				'referee_position': 'Position',
				'contact_information': 'Contact information',
				'school_information': 'School information',
				'suitability': 'Test'
				},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Your reference was submitted successfully', response.data)
		
		# View main references public log-in page
		response = self.app.get('/references/login/admin', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Login', response.data)
		
		# View main admin page (and verify redirect works)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/references', follow_redirects=True)
		self.assertIn(b'Search for students or references', response.data)
		self.assertIn(b'Test student name', response.data)
		
		# View reference project
		response = self.app.get('/references/view/project/1', follow_redirects=True)
		self.assertIn(b"You haven't uploaded any versions!", response.data)

		response = self.app.get('/references/view/1', follow_redirects=True)
		self.assertIn(b"What is your relation to the student?", response.data)
		self.assertIn(b"Position", response.data)
		
		response = self.app.get('/references/view/pdf/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"Unikey Student Reference", response.data)
		
		# Upload a reference version
		response = self.app.get('/references/1/version/upload', follow_redirects=True)
		self.assertIn(b"Upload reference version", response.data)
		
		# Silence Python warnings
		#!# The next upload function throws this warning:
		# ResourceWarning: unclosed file <_io.BufferedReader name (...)
		# To fix?
		warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) 
		
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/references/1/version/upload',
				content_type='multipart/form-data', 
				data={
					'reference_upload_file': (fileIO, 'test.pdf'),
					'description': 'Teacher uploaded reference'
				},
				follow_redirects=True)
		self.assertIn(b'New reference version successfully added library!', response.data)
		self.assertIn(b'Teacher uploaded reference', response.data)
		
		# Students can not see references
		helper_functions.logout(self)
		helper_functions.login(self, 'Pablo')
		response = self.app.get('/references/view/project/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# Archive reference
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/references/archive/project/1', follow_redirects=True)
		self.assertIn(b'Successfully archived the reference project', response.data)
		
		response = self.app.get('/references/admin', follow_redirects=True)
		self.assertNotIn(b'Test student name', response.data)
		
		response = self.app.get('/references/archive', follow_redirects=True)
		self.assertIn(b'Test student name', response.data)
		
		response = self.app.get('/references/unarchive/project/1', follow_redirects=True)
		self.assertIn(b'Successfully unarchived the reference project', response.data)
		
		response = self.app.get('/references/admin', follow_redirects=True)
		self.assertIn(b'Test student name', response.data)
		
		# Permissions checks
		helper_functions.logout(self)
		helper_functions.register_student (self, 'Pingkee')
		helper_functions.login(self, 'Pingkee')
		
		response = self.app.get('/references/view/project/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/references/1/version/upload', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/references/view/pdf/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/references/unarchive/project/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/references/archive/project/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# Delete the project
		helper_functions.logout(self)
		helper_functions.login (self, 'Patrick')
		response = self.app.get('/references/delete/project/1', follow_redirects=True)
		self.assertIn(b'Successfully deleted', response.data)
		self.assertNotIn(b'Test student name', response.data)
		
		response = self.app.get('/references/delete/project/123', follow_redirects=True)
		self.assertIn(b'This reference could not be found', response.data)
		
if __name__ == '__main__':
		unittest.main()