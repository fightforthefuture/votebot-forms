from run import BaseTestCase
from app.ovr_forms import Massachusetts


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
