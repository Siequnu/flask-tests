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
	def test_statements (self):
		if app.config['APP_NAME'] != 'Unikey':
			return
		
		# Register student and admin
		helper_functions.register_admin_user()
		helper_functions.logout(self)
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		
		# Check the empty statement page contains a link to the builder
		response = self.app.get('/statements/', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Are you stuck for ideas?', response.data)
		
		# Go to the builder
		response = self.app.get('/statements/builder', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'What you need to do:', response.data)
		
		# Try and submit a statement to the builder
		response = self.app.post(
			'/statements/builder',
			content_type='multipart/form-data', 
			data={
				'question_one': 'Test question 1',
				'question_two': 'Test question 2',
				'question_three': 'Test question 3',
				'question_four': 'Test question 4',
				'question_five': 'Test question 5'
			},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Attempt to create a statement project
		response = self.app.post(
			'statements/project/create',
			content_type='multipart/form-data', 
			data={'title': 'Test statement project'},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Project successfully created!', response.data)
		
		# Open the project we just created
		response = self.app.get('/statements/project/view/1', follow_redirects = True)
		self.assertIn(b"You haven't uploaded any statements", response.data)
		
		# Upload a first draft statement
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/statements/upload/1',
				content_type='multipart/form-data', 
				data={
					'statement_upload_file': (fileIO, 'test.pdf'),
					'description': 'Test upload description'
				},
				follow_redirects=True)
		self.assertIn(b'New personal statement successfully uploaded!', response.data)
		self.assertIn(b'test.pdf', response.data)
		
		# View empty priject
		response = self.app.get('/statements/project/view/1', follow_redirects = True)
		self.assertNotIn(b"You haven't uploaded any statements", response.data)
		self.assertIn(b'Test upload description', response.data)
		
		# View project: permissions test
		helper_functions.logout(self)
		helper_functions.register_student (self, 'Pingkee')
		helper_functions.logout(self)
		helper_functions.login(self, 'Pingkee')
		response = self.app.get('/statements/project/view/1', follow_redirects = True)
		self.assertEqual(response.status_code, 403)
		
		# View homepage with 'projects needing review'
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/', follow_redirects = True)
		self.assertIn(b'Personal statements needing review', response.data)
		
		# Delete this project
		response = self.app.get('statements/project/delete/1', follow_redirects = True)
		self.assertIn(b'Statement deleted successfully', response.data)
		
		# Create a new project
		helper_functions.logout (self)
		helper_functions.login (self, 'Pablo')
		response = self.app.post(
			'statements/project/create',
			content_type='multipart/form-data', 
			data={'title': 'Test statement project'},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Project successfully created!', response.data)
		
		# View project
		response = self.app.get('/statements/project/view/2', follow_redirects = True)
		self.assertIn(b"You haven't uploaded any statements", response.data)
		
		# Upload a first draft statement
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/statements/upload/2',
				content_type='multipart/form-data', 
				data={
					'statement_upload_file': (fileIO, 'test.pdf'),
					'description': 'Test upload description'
				},
				follow_redirects=True)
		self.assertIn(b'New personal statement successfully uploaded!', response.data)
		self.assertIn(b'test.pdf', response.data)
		
		# Try and submit a teacher response
		helper_functions.logout (self)
		helper_functions.login (self, 'Patrick')
		
		response = self.app.get('/', follow_redirects = True)
		self.assertIn(b'Personal statements needing review', response.data)
		response = self.app.get('/statements/project/view/2', follow_redirects = True)
		self.assertIn(b'Upload a new statement', response.data)
		
		# Upload a first draft statement
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/statements/upload/2',
				content_type='multipart/form-data', 
				data={
					'statement_upload_file': (fileIO, 'test.pdf'),
					'description': 'Teacher uploaded file description'
				},
				follow_redirects=True)
		self.assertIn(b'New personal statement successfully uploaded!', response.data)
		self.assertIn(b'Teacher uploaded file description', response.data)
		
		# Check that the student can access this
		helper_functions.logout (self)
		helper_functions.login (self, 'Pablo')
		response = self.app.get('/statements/project/view/2', follow_redirects = True)
		self.assertIn(b'Teacher uploaded file description', response.data)
		
		# Permissions tests 
		response = self.app.get('/statements/project/delete/1', follow_redirects = True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/statements/project/delete/2', follow_redirects = True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/statements/project/edit/2', follow_redirects = True)
		self.assertEqual(response.status_code, 403)
		
		response = self.app.get('/statements/archive/2', follow_redirects = True)
		self.assertEqual(response.status_code, 403)
		
		


if __name__ == '__main__':
		unittest.main()