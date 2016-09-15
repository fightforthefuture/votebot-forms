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
        self.user = self.test_data.get(self.state)
        if not self.user:
            self.skip('CO')

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

    @vcr.use_cassette('tests/.cassettes/co/test_independent_party.yml')
    def test_independent_party(self):
        self.setUpClass()
        self.user['political_party'] = 'Independent'
        result = self.form.submit(self.user)

    @vcr.use_cassette('tests/.cassettes/co/test_libertarian_designation.yml')
    def test_libertarian_designation(self):
        self.setUpClass()
        self.user['political_party'] = 'Libertarian'
        result = self.form.submit(self.user)

    @vcr.use_cassette('tests/.cassettes/co/test_bad_id_number.yml')
    def test_bad_id_number(self):
        self.setUpClass()
        self.user['state_id_number'] = '11-222-3445'
        result = self.form.submit(self.user)
        self.assertEqual(result, {'errors': [{'state_id_number': "We could not find your record. Please double-check your first name, last name, date of birth, and driver's license number."}]})

    @vcr.use_cassette('tests/.cassettes/co/test_not_meeting_requirements.yml')
    def test_not_meeting_requirements(self):
        self.setUpClass()
        self.user['legal_resident'] = False
        result = self.form.submit(self.user)
        self.assertEqual(result, {'errors': [{'legal_resident': "You must be a legal resident of Colorado."}]})

    @vcr.use_cassette('tests/.cassettes/co/test_eligible_and_providing_accurate_info.yml')
    def test_eligible_and_providing_accurate_info(self):
        test_client = self.create_app().test_client()
        user = self.user
        user['eligible_and_providing_accurate_information'] = False
        post = test_client.post('/registration', data=json.dumps({'user': user}))
        expected = {u'errors': [{u'eligible_and_providing_accurate_information': u'You must be eligible to vote and provide accurate information in order to register.'}]}
        self.assertEqual(json.loads(post.data), expected)

    # @vcr.use_cassette('tests/.cassettes/co/test_multiple_errors.yml')
    # def test_multiple_errors(self):
    #     self.setUpClass()
    #     # self.user[...] = ''
    #     result = self.form.submit(self.user)

    # @vcr.use_cassette('tests/.cassettes/co/test_no_consent_to_use_signature.yml')
    # def test_no_consent_to_use_signature(self):
    #     self.setUpClass()
    #     # self.user[...] = ''
    #     result = self.form.submit(self.user)
