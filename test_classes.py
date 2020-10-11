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
from app.classes.models import AbsenceJustificationUpload, AttendanceCode

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
		
	def test_class_attendance_justification (self):

		# Silence Python warnings
		#!# The next upload function throws this warning:
		# ResourceWarning: unclosed file <_io.BufferedReader name (...)
		# To fix?
		warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) 

		# Add a class and a new admin user
		helper_functions.add_turma ()
		helper_functions.register_admin_user()	
		helper_functions.add_teacher_to_class (teacher_id = 1, turma_id = 1)
		helper_functions.register_student (self, 'Pablo')

		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick')
		
		# Check class admin page
		response = self.app.get('/classes/admin', follow_redirects=True)
		self.assertIn(b'Writing', response.data)
		self.assertIn(b'Fall', response.data)
		self.assertIn(b'2020', response.data)

		# Check class attendance page
		response = self.app.get('/classes/attendance/1', follow_redirects=True)
		self.assertIn(b'Writing', response.data)
		self.assertIn(b'Fall', response.data)
		self.assertIn(b'2020', response.data)
		self.assertIn(b'New lesson', response.data)

		# Check create new lesson page
		response = self.app.get('/classes/lesson/create/1', follow_redirects=True)
		self.assertIn(b'Writing', response.data)
		self.assertIn(b'Fall', response.data)
		self.assertIn(b'2020', response.data)
		self.assertIn(b'Class end time', response.data)
		self.assertIn(b'Class start time', response.data)

		# Add a new lesson
		response = self.app.post(
			'/classes/lesson/create/1',
			content_type='multipart/form-data',
			data={
				'start_time': '10:00',
				'end_time': '11:30',
				'date': '2020-06-10'
			},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New lesson added for', response.data)

		# Check if new lesson appeared on the class page
		response = self.app.get('/classes/attendance/1', follow_redirects=True)
		self.assertIn(b'2020-06-10', response.data)
		self.assertIn(b'New lesson', response.data)

		# View attendance
		response = self.app.get('/classes/attendance/view/1/', follow_redirects=True)
		self.assertIn(b'0 / 1', response.data)

		# Open attendance QR code
		response = self.app.get('/classes/attendance/qr/1/', follow_redirects=True)
		self.assertIn(b'The registration code is:', response.data)
		self.assertIn(b'Close attendance', response.data)

		# Close the QR code
		response = self.app.get('/classes/attendance/close/1/', follow_redirects=True)
		self.assertIn(b'Attendance closed for', response.data)
		self.assertIn(b'Bulk create lessons', response.data)
		self.assertIn(b'0 / 1', response.data)

		helper_functions.logout (self)
		helper_functions.login(self, 'Pablo')

		# Check the attendance code entry page
		response = self.app.get('/classes/attendance/code/', follow_redirects=True)
		self.assertIn(b'Scan the QR code to register your attendance,', response.data)
		self.assertIn(b'Enter class word here', response.data)
		
		# View own attendance record
		response = self.app.get('/classes/attendance/record/', follow_redirects=True)
		self.assertIn(b'Submit justification', response.data)

		# View attendance justification upload page
		response = self.app.get('/classes/absence/justification/1', follow_redirects=True)
		self.assertIn(b'Upload absence justification', response.data)

		# Add an absence justification
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/classes/absence/justification/1',
				content_type='multipart/form-data', 
				data={
					'absence_justification_file': (fileIO, 'test.pdf'),
					'justification': 'Justification description'
					},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New justification uploaded successfully!', response.data)
		self.assertIn(b'View uploaded', response.data)

		# View this absence justification
		response = self.app.get('/classes/absence/view/1', follow_redirects=True)
		self.assertIn(b'Absence justification for your', response.data)		
		self.assertIn(b'Justification description', response.data)

		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick')

		# As a teacher, view the class attendance again
		response = self.app.get('/classes/attendance/view/1', follow_redirects=True)
		self.assertIn(b'0 / 1', response.data)		

		# Delete the absence justification
		response = self.app.get('/classes/absence/justification/delete/1', follow_redirects=True)
		self.assertIn(b'Deleted student absence justification', response.data)

		# Resubmit as a student
		helper_functions.logout (self)
		helper_functions.login(self, 'Pablo')

		# Add an absence justification
		with open('test.pdf', 'rb') as test_file:
			fileIO = BytesIO(test_file.read())
			response = self.app.post(
				'/classes/absence/justification/1',
				content_type='multipart/form-data', 
				data={
					'absence_justification_file': (fileIO, 'test.pdf'),
					'justification': 'Justification description again'
					},
				follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New justification uploaded successfully!', response.data)
		self.assertIn(b'View uploaded', response.data)

		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick')

		# As a teacher, view the absence justification
		response = self.app.get('/classes/absence/view/2', follow_redirects=True)
		self.assertIn(b'Absence justification for', response.data)
		self.assertIn(b'Justification description again', response.data)
		
		# Approve this justification
		response = self.app.get('/classes/attendance/present/2/1', follow_redirects=True)
		self.assertIn(b'as in attendance', response.data)
		self.assertIn(b'1 / 1', response.data)	

		# Create a new lesson
		# Add a new lesson
		response = self.app.post(
			'/classes/lesson/create/1',
			content_type='multipart/form-data',
			data={
				'start_time': '10:00',
				'end_time': '11:30',
				'date': '2020-12-12'
			},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'New lesson added for', response.data)

		# Check non-existent lesson
		response = self.app.get('/classes/attendance/view/999999', follow_redirects=True)
		self.assertIn(b'Could not locate the lesson you wanted', response.data)	
		
		# As a teacher, view the class attendance again
		response = self.app.get('/classes/attendance/view/1', follow_redirects=True)
		self.assertIn(b'1 / 1', response.data)	
		response = self.app.get('/classes/attendance/view/2', follow_redirects=True)
		self.assertIn(b'0 / 1', response.data)	

		# Register a new student 
		helper_functions.logout (self)
		helper_functions.register_student (self, 'Pingkee')

		# Try to sign up to the class without a valid log-in code
		response = self.app.post(
			'/classes/attendance/code/',
			content_type='multipart/form-data',
			data={
				'attendance': 'nonvalidcode'
			},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Your code was invalid', response.data)

		# Log-in as admin and create a code for this class
		helper_functions.logout (self)
		helper_functions.login (self, 'Patrick')

		# As a teacher, view the class attendance again
		response = self.app.get('/classes/attendance/view/1', follow_redirects=True)
		self.assertIn(b'1 / 2', response.data)	

		response = self.app.get('/classes/attendance/qr/1/', follow_redirects=True)
		self.assertIn(b'The registration code is:', response.data)	
		
		# This will be the second attendance code
		attendance_code = AttendanceCode.query.get(2).code

		# Log-in as student and try this code
		helper_functions.logout (self)
		helper_functions.login (self, 'Pingkee')
		response = self.app.post(
			'/classes/attendance/code/',
			content_type='multipart/form-data',
			data={
				'attendance': attendance_code
			},
			follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		# On successful entry, will display {{greeting}}, user.username 
		self.assertIn(b', Pingkee', response.data)

		# Log-in as admin and view class attendance
		helper_functions.logout (self)
		helper_functions.login (self, 'Patrick')
		response = self.app.get('/classes/attendance/view/1', follow_redirects=True)
		self.assertIn(b'2 / 2', response.data)	
		
		# Delete the class
		#!# Can class be delete with open attendance code?
		response = self.app.get('/classes/lesson/delete/2', follow_redirects=True)
		self.assertIn(b'Lesson removed!', response.data)	


		

if __name__ == '__main__':
	
	unittest.main()
