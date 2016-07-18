from app.ovr_forms import Massachusetts
from app.ovr_forms.base_ovr_form import OVRError
from nose.tools import raises
from run import BaseTestCase

import vcr


class TestMassachusetts(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.form = Massachusetts()
        cls.state = "MA"

    def setUp(self):
        super(TestMassachusetts, self).setUp()
        self.user = self.test_data[self.state]

    def test_has_user(self):
        self.assertIsNotNone(self.user)

    def test_user_has_required_fields(self):
        for f in self.form.required_fields:
            self.assertIn(f, self.user)

    @vcr.use_cassette('ma/test_submit.yml')
    def test_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        self.form.submit(self.user)
    
    @vcr.use_cassette('ma/test_independent_party.yml')
    def test_independent_party(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Independent'
        self.form.submit(user)

    @vcr.use_cassette('ma/test_libertarian_designation.yml')
    def test_libertarian_designation(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Libertarian'
        self.form.submit(user)

    @raises(OVRError)
    @vcr.use_cassette('ma/test_bad_id_number.yml')
    def test_bad_id_number(self):
        self.setUpClass()
        user = self.user
        user['id_number'] = '012345678'
        self.form.submit(user)

    @raises(OVRError)
    @vcr.use_cassette('ma/test_not_meeting_requirements.yml')
    def test_not_meeting_requirements(self):
        self.setUpClass()
        user = self.user
        user['us_citizen'] = False
        self.form.submit(user)
