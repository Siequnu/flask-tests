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
from app.classes.models import AbsenceJustificationUpload

TEST_DB = 'test.db'

from . import helper_functions

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
		self.assertIn(b'Create new lesson', response.data)

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
		self.assertIn(b'Create new lesson', response.data)

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
		self.assertIn(b'Lessons', response.data)
		self.assertIn(b'0 / 1', response.data)

		helper_functions.logout (self)
		helper_functions.login(self, 'Pablo')

		# Check the attendance code entry page
		response = self.app.get('/classes/attendance/code/', follow_redirects=True)
		self.assertIn(b'To register attendance scan', response.data)
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
		self.assertIn(b'View uploaded justification', response.data)

		# View this absence justification
		response = self.app.get('/classes/absence/view/1', follow_redirects=True)
		self.assertIn(b'Absence justification for your', response.data)		
		self.assertIn(b'Justification description', response.data)

		helper_functions.logout (self)
		helper_functions.login(self, 'Patrick')

		# As a teacher, view the class attendance again
		response = self.app.get('/classes/attendance/view/1', follow_redirects=True)
		self.assertIn(b'0 / 1', response.data)		

		#¡# What about deleting the absence justification

		# As a teacher, view the absence justification
		response = self.app.get('/classes/absence/view/1', follow_redirects=True)
		self.assertIn(b'Absence justification for', response.data)
		self.assertIn(b'Justification description', response.data)
		
		# Approve this justification
		response = self.app.get('/classes/attendance/present/2/1', follow_redirects=True)
		self.assertIn(b'as in attendance', response.data)
		self.assertIn(b'1 / 1', response.data)	
		

if __name__ == '__main__':
	
	unittest.main()
