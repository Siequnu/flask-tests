# Python testing framework
from io import BytesIO, StringIO
import os, unittest, warnings, string, random
from datetime import datetime

# Flask 
from app import create_app
from flask import url_for
from config import basedir
from config import Test
app = create_app(Test)

# Flask models
from app import db
from app.models import User, Turma, LibraryUpload, PeerReviewForm

from app.api import models
from app.api.models import ApiKey

import json 

TEST_DB = 'test.db'

from app.tests import helper_functions

class TestCase(unittest.TestCase):
	
	def setUp(self):
		self.app = app.test_client()
		db.drop_all()
		db.create_all()
		
	def tearDown(self):
		db.session.remove()
		db.drop_all()
		
	# Test admin pages  
	def test_consultation(self):
		
		helper_functions.register_admin_user()
		helper_functions.logout(self)
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.logout(self)

		# Create new API key
		api_key = helper_functions.create_api_key
		
		# View student management page
		response = self.app.get('/consultations', follow_redirects=True)
		self.assertIn(b'Please log in to access this page', response.data)
		
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/consultations', follow_redirects=True)
		self.assertIn(b'Book new consultation', response.data)
		
		# View student search page
		response = self.app.get('/consultations/book/search', follow_redirects=True)
		self.assertIn(b'Pablo', response.data)
		return 
		# Add a mentor
		response = self.app.get('consultations/book/2/calendar', follow_redirects=True)
		self.assertIn(b'Schedule a consultation with Pablo', response.data)
		response = self.app.post(
			'/api/v1/consultation/',
			content_type='application/json', 
			headers= {
				'key': api_key
			},
			data=json.dumps(dict(
				date='2020-02-02',
				start_time = '09:00',
				end_time = '10:00',
				teacher_id = '1',
				student_id = '2'
			)))
		print (response.json)
		#self.assertEqual(response.status_code, 200)
		#print (response.data)
		
		
if __name__ == '__main__':
	
	unittest.main()
