from votedotorg import VoteDotOrg
from arizona import Arizona
from california import California
from georgia import Georgia
from illinois import Illinois
from massachusetts import Massachusetts
from virginia import Virginia
from colorado import Colorado
from minnesota_test import MinnesotaTest


OVR_FORMS = {
    'AZ': Arizona,
    'CA': California,
    'CO': Colorado,
    #'GA': Georgia,
    'IL': Illinois,
    'MA': Massachusetts,
    'MN': MinnesotaTest, # JL DEBUG ~ disable in production
    #'VA': Virginia,
    'default': VoteDotOrg
}
# ONLY ENABLE FORMS HERE THAT ACTUALLY WORK AND HAVE BEEN TESTED END-END
