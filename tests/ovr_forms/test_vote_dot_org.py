from app.ovr_forms import VoteDotOrg
from app.ovr_forms.base_ovr_form import OVRError
from nose.tools import raises
from tests.run import BaseTestCase

import json
import vcr


class TestVoteDotOrg(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.form = VoteDotOrg()
        cls.state = "default"

    def setUp(self):
        super(TestVoteDotOrg, self).setUp()
        self.user = self.test_data[self.state]

    def test_has_user(self):
        self.assertIsNotNone(self.user)

    def test_user_has_required_fields(self):
        for f in self.form.required_fields:
            self.assertIn(f, self.user)

    @vcr.use_cassette('tests/.cassettes/vote_dot_org/test_wa_submit.yml')
    def test_wa_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        
        # for sake of non-PNWers
        if not 'WA' in self.test_data:
            return
        
        user = self.test_data['WA']
        result = self.form.submit(user)
        self.assertEqual(result, {u'status': u'download_ready'})


    @vcr.use_cassette('tests/.cassettes/vote_dot_org/test_ca_submit.yml')
    def test_ca_submit(self):
        # re-calling setUpClass before a new submit
        # trashes the existing session.
        self.setUpClass()
        user = self.test_data['CA']
        result = self.form.submit(user)
        self.assertEqual(result, {u'status': u'download_ready'})

    @vcr.use_cassette('tests/.cassettes/vote_dot_org/test_misspelled_democrat.yml')
    def test_misspelled_democrat(self):
        self.setUpClass()
        user = self.test_data['WA']
        user['political_party'] = 'Democart'
        result = self.form.submit(user)
        self.assertEqual(result, {u'status': u'download_ready'})

    @vcr.use_cassette('tests/.cassettes/vote_dot_org/test_co_submit.yml')
    def test_co_submit(self):
        self.setUpClass()
        
        # for sake of non-PNWers
        if not 'CO' in self.test_data:
            return
        
        user = self.test_data['CO']
        result = self.form.submit(user)
        self.assertEqual(result, {u'status': u'download_ready'})
