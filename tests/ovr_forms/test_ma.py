from app.ovr_forms import Massachusetts
from app.ovr_forms.base_ovr_form import OVRError
from nose.tools import raises
from tests.run import BaseTestCase

import json
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

    @vcr.use_cassette('ma/test_submit.yml', record_mode='all')
    def test_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        self.form.submit(self.user)
    
    @vcr.use_cassette('ma/test_independent_party.yml', record_mode='all')
    def test_independent_party(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Independent'
        self.form.submit(user)

    @vcr.use_cassette('ma/test_libertarian_designation.yml', record_mode='all')
    def test_libertarian_designation(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Libertarian'
        self.form.submit(user)

    @raises(OVRError)
    @vcr.use_cassette('ma/test_bad_id_number.yml', record_mode='all')
    def test_bad_id_number(self):
        self.setUpClass()
        user = self.user
        user['id_number'] = '012345678'
        response = self.form.submit(user)

    @raises(OVRError)
    @vcr.use_cassette('ma/test_not_meeting_requirements.yml', record_mode='all')
    def test_not_meeting_requirements(self):
        self.setUpClass()
        user = self.user
        user['us_citizen'] = False
        self.form.submit(user)


    ## HTTP powered tests

    @vcr.use_cassette('ma/not_us_citizen.yml')
    def test_not_us_citizen(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['us_citizen'] = False
        post = test_client.post('/registration', data=json.dumps(user))
        self.assertEqual(json.loads(post.data), {u'us_citizen': u'You must be a U.S. Citizen.'})


    @vcr.use_cassette('ma/no_consent_to_use_signature.yml')
    def test_no_consent_to_use_signature(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['consent_use_signature'] = False
        post = test_client.post('/registration', data=json.dumps(user))
        self.assertEqual(json.loads(post.data), {u'consent_use_signature': u'You must consent to using your signature from the Massachusetts RMV.'})
