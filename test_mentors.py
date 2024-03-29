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
		
	# Test admin pages  
	def test_mentors(self):
		
		helper_functions.register_admin_user() # Registers Patrick as an admin user
		helper_functions.logout(self)
		helper_functions.register_admin_user('Pingkee') # Registers Pingkee
		helper_functions.add_turma ()
		helper_functions.register_student (self, 'Pablo')
		helper_functions.logout(self)
		
		# View student management page
		response = self.app.get('/user/students/manage', follow_redirects=True)
		self.assertIn(b'Please log in to access this page', response.data)
		
		helper_functions.login(self, 'Patrick')
		response = self.app.get('/user/students/manage', follow_redirects=True)
		self.assertIn(b'Pablo', response.data)
		
		# View mentors admin page
		response = self.app.get('/mentors/student/3', follow_redirects=True)
		self.assertIn(b'Pablo currently has 0 mentors.', response.data)
		
		# Add a mentor
		response = self.app.get('/mentors/search/3', follow_redirects=True)
		self.assertIn(b'Pingkee', response.data)
		
		response = self.app.get('/mentors/add/3/2', follow_redirects=True)
		self.assertIn(b'Mentor added successfully.', response.data)
		
		# Add another mentor
		response = self.app.get('/mentors/search/3', follow_redirects=True)
		# Patrick is now in the footer
		self.assertNotIn(b'Pingkee', response.data)
		
		# Remove mentor
		response = self.app.get('/mentors/remove/3/2', follow_redirects=True)
		self.assertIn(b'Mentor removed successfully.', response.data)
		
		
		
		
if __name__ == '__main__':
	
	unittest.main()
