from ..pdf_forms.nvra import NVRA
from alaska import Alaska
from arizona import Arizona
from california import California
from colorado import Colorado
from georgia import Georgia
from hawaii import Hawaii
from illinois import Illinois
from kentucky import Kentucky
from massachusetts import Massachusetts
from vermont import Vermont
from virginia import Virginia
from west_virginia import WestVirginia

from dummy_form import DummyForm

OVR_FORMS = {
    'AK': Alaska,
    'AZ': Arizona,
    'CA': California,
    'CO': Colorado,
    'GA': Georgia,
    'HI': Hawaii,
    'IL': Illinois,
    'KY': Kentucky,
    'MA': Massachusetts,
    'VA': Virginia,
    'VT': Vermont,
    'WV': WestVirginia,
    'NVRA': NVRA
}
OVR_FORMS['default'] = OVR_FORMS['NVRA']
