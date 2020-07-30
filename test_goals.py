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

from app.goals.models import StudentGoal

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
		
	# Test goal pages
	def test_goals(self):
		
		#¡# This function only available on Elm, as the workUp user home screen does not show goals
		if app.config['APP_NAME'] == 'workUp':
			print ('Skipping Goal testing as we are running as workUp')
			return True
		
		helper_functions.register_admin_user()
		helper_functions.logout(self)
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.logout(self)
		
		# View goals page
		response = self.app.get('/goals/view', follow_redirects=True)
		self.assertIn(b'Please log in to access this page', response.data)
		
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/goals/view', follow_redirects=True)
		self.assertIn(b'Add new goal', response.data)
		
		# View student search page
		response = self.app.get('/goals/add/search', follow_redirects=True)
		self.assertIn(b'Pablo', response.data)

		# Add a new goal
		response = self.app.get('/goals/add/2', follow_redirects=True)
		self.assertIn(b'Add student goal', response.data)
		
		response = self.app.post(
				'/goals/add/2',
				content_type='multipart/form-data', 
				data={
					'title': 'Goal for Pablo',
					'description': 'Goal description',
					'datefield': '2020-08-08'
					},
				follow_redirects=True)
		self.assertIn(b'Goal saved', response.data)
		
		# View the new goal
		response = self.app.get('/goals/view/2', follow_redirects=True)
		self.assertIn(b'Add new goal', response.data)
		self.assertIn(b'Goal description', response.data)
		self.assertIn(b'Goal for Pablo', response.data)
		self.assertIn(b'Reached milestone', response.data)
		
		# Mark goal as completed
		response = self.app.get('/goals/completed/1', follow_redirects=True)
		self.assertIn(b'Reset milestone', response.data)
		
		# Reset milestone
		response = self.app.get('/goals/completed/1', follow_redirects=True)
		self.assertIn(b'Reached milestone', response.data)

		helper_functions.logout (self)
		helper_functions.login (self, 'Pablo')

		# Log-in as student and check milestones on index page
		response = self.app.get('/', follow_redirects=True)
		self.assertIn(b'Your milestones', response.data)
		self.assertIn(b'Goal for Pablo', response.data)

		# Check goals page
		response = self.app.get('/goals/view/2', follow_redirects=True)
		self.assertIn(b'Your milestones', response.data)
		self.assertIn(b'Goal for Pablo', response.data)
		
		
if __name__ == '__main__':
	
	unittest.main()
