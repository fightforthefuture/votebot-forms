from votedotorg import VoteDotOrg
from arizona import Arizona
from california import California
from georgia import Georgia
from illinois import Illinois
from massachusetts import Massachusetts
from virginia import Virginia
from colorado import Colorado

from dummy_form import DummyForm

from ..pdf_forms.nvra import NVRA

OVR_FORMS = {
    'AZ': Arizona,
    'CA': California,
    'CO': Colorado,
    'GA': Georgia,
    'IL': Illinois,
    'MA': Massachusetts,
    # 'MN': DummyForm, # JL DEBUG ~ disable in production
    #'VA': Virginia,
    'ZZ': NVRA,
    'default': VoteDotOrg
}
# ONLY ENABLE FORMS HERE THAT ACTUALLY WORK AND HAVE BEEN TESTED END-END
