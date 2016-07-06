import logging
import nose
import yaml
from app import app as application
from flask_testing import TestCase


class BaseTestCase(TestCase):
    def create_app(self):
        application.config.TESTING = True
        return application

    def setUp(self):
        f = open('tests/secrets.yml')
        self.test_data = yaml.load(f)
        logging.info("got %d test users" % len(self.test_data.keys()))

if __name__ == '__main__':
    nose.main()
