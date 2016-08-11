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

    @vcr.use_cassette('tests/.cassettes/ma/test_submit.yml')
    def test_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        result = self.form.submit(self.user)
        self.assertEqual(result, {'status': 'OK'})
    
    @vcr.use_cassette('tests/.cassettes/ma/test_independent_party.yml')
    def test_independent_party(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Independent'
        result = self.form.submit(user)
        self.assertEqual(result, {'status': 'OK'})


    @vcr.use_cassette('tests/.cassettes/ma/test_libertarian_designation.yml')
    def test_libertarian_designation(self):
        self.setUpClass()
        user = self.user
        user['political_party'] = 'Libertarian'
        result = self.form.submit(user)
        self.assertEqual(result, {'status': 'OK'})

    @vcr.use_cassette('tests/.cassettes/ma/test_bad_id_number.yml')
    def test_bad_id_number(self):
        self.setUpClass()
        user = self.user
        user['state_id_number'] = '012345678'
        result = self.form.submit(user)
        self.assertEqual(result, {'errors': [{'state_id_number': "Your Massachusetts RMV ID cannot be verified."}]})

    @vcr.use_cassette('tests/.cassettes/ma/test_not_meeting_requirements.yml')
    def test_not_meeting_requirements(self):
        self.setUpClass()
        user = self.user
        user['us_citizen'] = False
        result = self.form.submit(user)
        self.assertEqual(result, {'errors': [{'us_citizen': "You must be a U.S. Citizen."}]})


    ## HTTP powered tests

    @vcr.use_cassette('tests/.cassettes/ma/not_us_citizen.yml')
    def test_not_us_citizen(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['us_citizen'] = False
        post = test_client.post('/registration', data=json.dumps({'user': user}))
        expected = {u'errors': [{u'us_citizen': u'You must be a U.S. Citizen.'}]}
        self.assertEqual(json.loads(post.data), expected)


    @vcr.use_cassette('tests/.cassettes/ma/multiple_errors.yml')
    def test_multiple_errors(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['us_citizen'] = False
        user['will_be_18'] = False
        post = test_client.post('/registration', data=json.dumps({'user': user}))
        expected = {u'errors': [{u'us_citizen': u'You must be a U.S. Citizen.'}, {u'will_be_18': u'You must be 18 by Election Day.'}]}
        self.assertEqual(json.loads(post.data), expected)


    @vcr.use_cassette('tests/.cassettes/ma/no_consent_to_use_signature.yml')
    def test_no_consent_to_use_signature(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['consent_use_signature'] = False
        post = test_client.post('/registration', data=json.dumps({'user': user}))
        expected = {u'errors': [{u"consent_use_signature": u"You must consent to using your signature from the Massachusetts RMV."}]}
        self.assertEqual(json.loads(post.data), expected)
