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

from app.api import models
from app.api.models import ApiKey

from app.consultations.models import Consultation

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
		api_key = helper_functions.create_api_key ()
		
		# View student management page
		response = self.app.get('/consultations', follow_redirects=True)
		self.assertIn(b'Please log in to access this page', response.data)
		
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/consultations', follow_redirects=True)
		self.assertIn(b'Book new consultation', response.data)
		
		# View student search page
		response = self.app.get('/consultations/book/search', follow_redirects=True)
		self.assertIn(b'Pablo', response.data)

		# Add details to the consultation
		response = self.app.get('consultations/book/2', follow_redirects=True)
		self.assertIn(b'Save consultation details', response.data)
		
		response = self.app.post(
				'/consultations/details/1/edit',
				content_type='multipart/form-data', 
				data={
					'title': 'Consultation title',
					'description': 'Consultation description',
					},
				follow_redirects=True)
		self.assertIn(b'Saved the consultation details', response.data)
		
		# Add scheduling time slots
		response = self.app.get('/consultations/1/book/calendar', follow_redirects=True)
		self.assertIn(b'Scheduling options', response.data)
		
		# Go to the javascript scheduling page
		response = self.app.get('/consultations/book/schedule/1/', follow_redirects=True)
		
		# Submit a schedule via the API
		response = self.app.post(
			'/api/v1/consultation/schedule',
			content_type='application/json', 
			headers= {
				'key': api_key
			},
			data=json.dumps(dict(
				consultation_id = '1',
				date='2020-08-12',
				start_time = '18:18',
				end_time = '18:19'
			)))

		json_response = response.get_json ()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(json_response['date'], '2020-08-12')
		self.assertEqual(json_response['consultation_id'], 1)
		self.assertEqual(json_response['start_time'], '2020-08-12T18:18:00')
		self.assertEqual(json_response['end_time'], '2020-08-12T18:19:00')
		
		# View added time slot
		response = self.app.get('/consultations/1/book/calendar', follow_redirects=True)
		self.assertIn(b'Scheduling options', response.data)
		self.assertIn(b'18:18', response.data)

		# Use this time slot
		response = self.app.get('/consultations/book/schedule/set/1/', follow_redirects=True)
		self.assertIn(b'Time slot saved.', response.data)
		self.assertIn(b'12', response.data)

		# Add pre-reading files?

		# Add a report
		response = self.app.get('/consultations/1/report/add', follow_redirects=True)
		self.assertIn(b'Save report details', response.data)
		
		response = self.app.post(
				'/consultations/1/report/add',
				content_type='multipart/form-data', 
				data={
					'summary': 'Report summary',
					'report': 'Report details',
					},
				follow_redirects=True)
		self.assertIn(b'Added the consultation report', response.data)
		self.assertIn(b'Report by Patrick', response.data)
		self.assertIn(b'Report summary', response.data)
		self.assertIn(b'Report details', response.data)

		# Edit the report
		response = self.app.get('/consultations/1/report/view/1', follow_redirects=True)
		self.assertIn(b'Save report details', response.data)
		
		response = self.app.post(
				'/consultations/1/report/view/1',
				content_type='multipart/form-data', 
				data={
					'summary': 'Report edited summary',
					'report': 'Report edited details',
					},
				follow_redirects=True)
		self.assertIn(b'Added the consultation report', response.data)
		self.assertIn(b'Report by Patrick', response.data)
		self.assertIn(b'Report edited summary', response.data)
		self.assertIn(b'Report edited details', response.data)

		#!# Upload report files
		
		
if __name__ == '__main__':
	
	unittest.main()
