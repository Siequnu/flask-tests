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
	def test_add_peer_review_form (self):
		helper_functions.add_turma ()
		helper_functions.register_admin_user()
		
		# Navigating to form admin page prompts for login
		helper_functions.logout(self)
		response = self.app.get('/assignments/peer-review/forms/admin', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Login', response.data)
		
		# Create a student and test they can not access admin-only test pages
		helper_functions.register_student (self, 'Pablo')
		helper_functions.login(self, 'Pablo', 'test')
		response = self.app.get('/assignments/peer-review/forms/admin', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		response = self.app.get('/assignments/peer-review/forms/add', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# Log-out as student and log-in as admin
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick', 'test')
		
		# Test form admin page displays without any forms
		response = self.app.get('/assignments/peer-review/forms/admin', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Create new form', response.data)
		self.assertNotIn(b'Peer Review Form Description', response.data)
		
		# Test form builder page works
		response = self.app.get('/assignments/peer-review/forms/add', follow_redirects=True)
		self.assertIn(b'Peer review form builder', response.data)
		
		helper_functions.add_peer_review_form ()
		
		# Test this form appears on the admin page
		response = self.app.get('/assignments/peer-review/forms/admin', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Peer Review Form Description', response.data)
	
			
	# Test the assignments section
	def test_assignments (self):
		# Add a class and a new admin user
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.register_admin_user()
		
		# Navigate without logging in to the assignments page to trigger login
		helper_functions.logout(self)
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Login', response.data)
		
		# Log in as student and check there are no assignments
		helper_functions.login(self, 'Pablo', 'test')
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'You have no assignments', response.data)
		self.assertNotIn(b'Create assignment', response.data)
		
		# Test student can not create assignment
		response = self.app.get('/assignments/create', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# Log-in as admin and test assignments view page
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick', 'test')
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'Create assignment', response.data)
		
		# Add peer-review form
		helper_functions.add_peer_review_form ()
		
		# Add assignment
		response = self.app.post(
			'/assignments/create',
			content_type='multipart/form-data', 
			data={
				'title': 'Test assignment title',
				'description': 'Test assignment description',
				'due_date': '2021-03-27',
				'target_turmas': 1,
				'peer_review_necessary': 'n',
				'peer_review_form_id': 1,
			},
			follow_redirects=True)
		self.assertIn(b'Assignment successfully created', response.data)
		
		# Check assignment was added
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'Test assignment title', response.data)
		self.assertIn(b'27', response.data)
		
		# Test edit assignment
		response = self.app.post(
			'/assignments/edit/1',
			content_type='multipart/form-data', 
			data={
				'title': 'Test assignment title',
				'description': 'Test assignment edited description',
				'due_date': '2021-03-28',
				'peer_review_necessary': 'n',
				'peer_review_form_id': 1,
			},
			follow_redirects=True)
		self.assertIn(b'Assignment successfully edited!', response.data)
		
		# Test the assignment edit worked
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'Test assignment edited description', response.data)
		self.assertIn(b'28', response.data)
		
		# Log in as student and try to edit assignment
		helper_functions.logout(self)
		helper_functions.login(self, 'Pablo', 'test')
		# This should fail and throw a 403
		response = self.app.get('/assignments/edit/1', follow_redirects=True)
		self.assertEqual(response.status_code, 403)
		
		# Check the assignment is appearing on the assignments page and index page
		response = self.app.get('/', follow_redirects=True)
		self.assertIn(b'Upcoming assignments', response.data)
		self.assertIn(b'Test assignment edited description', response.data)
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'Test assignment edited description', response.data)
		
		# Try to submit assignment file
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/upload/1',
				content_type='multipart/form-data', 
				data={'file': (fileIO, 'test.pdf')},
				follow_redirects=True)
		self.assertIn(b'submitted successfully', response.data)
		
		# Check to see if the assignment dissapeared from the index page
		response = self.app.get('/', follow_redirects=True)
		self.assertNotIn(b'Test assignment edited description', response.data)
		
		# Try to download the file we just uploaded
		response = self.app.get('/files/download/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Silence Python warnings
		#!# The next upload function throws this warning:
		# ResourceWarning: unclosed file <_io.BufferedReader name (...)
		# To fix?
		warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) 
		
		# Try to change the file we just downloaded
		with open('test2.pdf', 'rb') as different_test_file:
			different_fileIO = BytesIO(different_test_file.read())
			response = self.app.post(
				'/files/upload/replace/1',
				content_type='multipart/form-data', 
				data={'file': (different_fileIO, 'test2.pdf')},
				follow_redirects=True)
		self.assertIn(b'submitted successfully', response.data)
		
		# Try to download the file we just replaced (should be removed from the DB, although not deleted)
		response = self.app.get('/files/download/1', follow_redirects=True)
		self.assertEqual(response.status_code, 404)
		# But the new one should work
		response = self.app.get('/files/download/2', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Test admin download
		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick', 'test')
		# Try downloading all the assignments
		response = self.app.get('/assignments/download/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Try downloading this specific file
		response = self.app.get('/files/download/2?rename=True', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		
		# Try and submit a review, with an uploaded correction file
		response = self.app.get('/assignments/review/create/2/teacher', follow_redirects=True)
		self.assertIn(b'Submit a teacher review', response.data)
		with open('test2.pdf', 'rb') as different_test_file:
			different_fileIO = BytesIO(different_test_file.read())
			response = self.app.post(
				'/assignments/review/create/2/teacher',
				content_type='multipart/form-data', 
				data={'comments:': 'Test comments',
					  'file': (different_fileIO, 'test2.pdf')
					  },
				follow_redirects=True)
		self.assertIn(b'Teacher review submitted', response.data)
		
		# Try to delete this uploaded assignment (+ comment and uploaded grading file)
		response = self.app.get ('/files/delete/2', follow_redirects=True)
		self.assertIn (b'Are you sure you want to delete', response.data)
		response = self.app.post(
				'/files/delete/2',
				content_type='multipart/form-data', 
				data={'submit': 'Confirm'},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'were successfully deleted', response.data)
		
		# Upload a final new file for this student
		response = self.app.get('/files/upload/1/2', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/upload/1/2',
				content_type='multipart/form-data', 
				data={'file': (fileIO, 'test.pdf')},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'submitted successfully', response.data)
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'1 / 1', response.data)
		
		# Try downloading this specific file
		response = self.app.get('/files/download/3?rename=True', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		# The previous (deleted) file should fail
		response = self.app.get('/files/download/2?rename=True', follow_redirects=True)
		self.assertEqual(response.status_code, 404)
		
		# Test registering another student
		helper_functions.logout (self)
		helper_functions.register_student (self, 'Pingkee')
		helper_functions.logout (self)
		helper_functions.login(self, 'Pingkee')
		
		# Check the assignment is appearing on the assignments page and index page
		response = self.app.get('/', follow_redirects=True)
		self.assertIn(b'Upcoming assignments', response.data)
		self.assertIn(b'Test assignment edited description', response.data)
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'Test assignment edited description', response.data)
		
		# Try and fail to download the first student's work
		response = self.app.get('/files/download/3', follow_redirects=True)
		self.assertEqual(response.status_code, 404)
		
		# Try to submit assignment file for the student as an admin
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/upload/1',
				content_type='multipart/form-data', 
				data={'file': (fileIO, 'test.pdf')},
				follow_redirects=True)
			
		test_file.close()
		self.assertIn(b'submitted successfully', response.data)
		
		# Check that both assignments have been uploaded
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'2 / 2', response.data)
		
		# Close the assignment
		response = self.app.get('assignments/close/1', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		helper_functions.logout (self)
		
		# Register as a third student and try to submit the late assignment
		helper_functions.register_student(self, 'Pingrol')
		helper_functions.login(self, 'Pingrol')
		response = self.app.get('/', follow_redirects=True)
		self.assertIn(b'Upcoming assignments', response.data)
		self.assertIn(b'Assignment overdue', response.data)
		
		# Try to submit (late) assignment file
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/upload/1',
				content_type='multipart/form-data', 
				data={'file': (fileIO, 'test.pdf')},
				follow_redirects=True)
		# Upload attempt to overdue assignment should fail
		self.assertEqual(response.status_code, 403)
		
		# Check that there is now an extra student who has received and not submitted the assignment
		helper_functions.logout(self)
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'2 / 3', response.data)
		
		# Try and submit the assignment for the student
		response = self.app.get('/files/upload/1/4', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/files/upload/1/4',
				content_type='multipart/form-data', 
				data={'file': (fileIO, 'test.pdf')},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'submitted successfully', response.data)
		response = self.app.get('/assignments/view', follow_redirects=True)
		self.assertIn(b'3 / 3', response.data)
		
		# Test peer-review?
		
		


if __name__ == '__main__':
	
	unittest.main()