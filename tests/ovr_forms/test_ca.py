from tests.run import BaseTestCase
from app.ovr_forms import California


class TestCalifornia(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.form = California()
        cls.state = "CA"

    def setUp(self):
        super(TestCalifornia, self).setUp()
        self.user = self.test_data[self.state]

    def test_has_user(self):
        self.assertIsNotNone(self.user)

    def test_user_has_required_fields(self):        
        for f in self.form.required_fields:
            self.assertIn(f, self.user)
