from tests.run import BaseTestCase
from app.ovr_forms import Colorado

import json
import vcr


class TestColorado(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.form = Colorado()
        cls.state = "CO"

    def setUp(self):
        super(TestColorado, self).setUp()
        self.user = self.test_data[self.state]

    def test_has_user(self):
        self.assertIsNotNone(self.user)

    def test_user_has_required_fields(self):
        for f in self.form.required_fields:
            self.assertIn(f, self.user)

    @vcr.use_cassette('tests/.cassettes/co/test_submit.yml')
    def test_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        result = self.form.submit(self.user)