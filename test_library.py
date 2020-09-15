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
from app.files import models
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
		
	def test_library_api (self):
		# Add a class and a new admin user
		helper_functions.add_turma ()
		helper_functions.register_admin_user()	
		helper_functions.register_student (self, 'Pablo')
		helper_functions.add_teacher_to_class (teacher_id = 1, turma_id = 1)

		helper_functions.logout (self)
		helper_functions.login (self, 'Patrick')

		# Create a new API key
		api_key = helper_functions.create_api_key ()
		
		# Add a test library file
		#!# This should be done via a new API call, or at least the model, not via the GUI
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/library/upload/',
				content_type='multipart/form-data', 
				data={
					'library_upload_file': (fileIO, 'test.pdf'),
					'title': 'Test library upload',
					'description': 'Test library upload description',
					'target_turmas': 1
					},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New file successfully added to the library!', response.data)
		assert LibraryUpload.query.get(1).title == 'Test library upload'

		# Test get all uploads
		response = self.app.get(
			'/api/v1/library',
			content_type = 'application/json', 
			headers = {'key': api_key}
		)
		json = response.get_json()
		assert len(json) == 1
		item = json.pop()
		assert item['id'] == 1
		assert item['title'] == 'Test library upload'
		assert item['description'] == 'Test library upload description'

		# Test get single upload
		response = self.app.get(
			'/api/v1/library/1', 
			headers = {'key': api_key}
		)
		json = response.get_json()
		assert json['id'] == 1
		assert json['title'] == 'Test library upload'
		assert json['description'] == 'Test library upload description'

		# Test PUT to edit item
		data = {
			'title': 'Test library upload edited',
			'description': 'Test library upload edited description'}
		response = self.app.put(
    		'/api/v1/library/1', 
    		json = data,
			headers = {'key': api_key}
		)
		json = response.get_json()
		assert json['id'] == 1
		assert json['title'] == 'Test library upload edited'
		assert json['description'] == 'Test library upload edited description'





		

	def test_library_gui (self):
		# Add a class and a new admin user
		helper_functions.add_turma ()
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.register_admin_user()
		helper_functions.add_teacher_to_class (teacher_id = 2, turma_id = 1)
		helper_functions.add_teacher_to_class (teacher_id = 2, turma_id = 2)
		
		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick')
		
		response = self.app.get('/files/library', follow_redirects=True)
		self.assertIn(b'Upload new library file', response.data)
		
		# Upload a file for the first class
		response = self.app.get('/files/library/upload', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/library/upload/',
				content_type='multipart/form-data', 
				data={
					'library_upload_file': (fileIO, 'test.pdf'),
					'title': 'Test library upload',
					'description': 'Test library upload description',
					'target_turmas': 1
					},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New file successfully added to the library!', response.data)
		
		# There should be 0 downloads of this  file
		response = self.app.get('/files/library/view/downloads/1', follow_redirects=True)
		self.assertNotIn(b'Pablo', response.data)
		
		# Silence Python warnings
		#!# The next upload function throws this warning:
		# ResourceWarning: unclosed file <_io.BufferedReader name (...)
		# To fix?
		warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) 
		

		# Edit this file
		# This does not trigger the JS/AJAX modal popup, it follows to the old upload form
		response = self.app.get('/files/library/edit/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Edit library file', response.data)
		response = self.app.post(
				'/files/library/edit/1',
				content_type='multipart/form-data', 
				data={
					'title': 'Test library upload edited',
					'description': 'Test library upload description edited',
					},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		response = self.app.get('/files/library', follow_redirects=True)
		self.assertIn(b'Test library upload description edited', response.data)
		
		# Students can see the file
		helper_functions.logout(self)
		helper_functions.login(self, 'Pablo')
		response = self.app.get('/files/library', follow_redirects=True)
		self.assertNotIn(b'Upload new library file', response.data)
		self.assertIn(b'Test library upload description edited', response.data)
		response = self.app.get('/files/library/download/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Student can not edit, delete or view upload form
		response = self.app.get('/files/library/delete/1/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		response = self.app.get('/files/library/delete/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		response = self.app.get('/files/library/edit/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# There should now be one download of this file
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/files/library/view/downloads/1', follow_redirects=True)
		self.assertIn(b'Pablo', response.data)
		
		


if __name__ == '__main__':
	
	unittest.main()