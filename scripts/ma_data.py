# MA is hella old, and has a lot of "archaic community" names that still appear in places, but are not legally valid
# this script generates a json file from http://www.sec.state.ma.us/cis/cisuno/unoidx.htm

from robobrowser import RoboBrowser

# list of valid city and town names from MA OVR
# capitalized, to avoid case comparison issues
CITY_TOWN_NAMES = ["ABINGTON", "ACTON", "ACUSHNET", "ADAMS", "AGAWAM", "ALFORD", "AMESBURY", "AMHERST", "ANDOVER", "AQUINNAH", "ARLINGTON", "ASHBURNHAM", "ASHBY", "ASHFIELD", "ASHLAND", "ATHOL", "ATTLEBORO", "AUBURN", "AVON", "AYER", "BARNSTABLE", "BARRE", "BECKET", "BEDFORD", "BELCHERTOWN", "BELLINGHAM", "BELMONT", "BERKLEY", "BERLIN", "BERNARDSTON", "BEVERLY", "BILLERICA", "BLACKSTONE", "BLANDFORD", "BOLTON", "BOSTON", "BOURNE", "BOXBOROUGH", "BOXFORD", "BOYLSTON", "BRAINTREE", "BREWSTER", "BRIDGEWATER", "BRIMFIELD", "BROCKTON", "BROOKFIELD", "BROOKLINE", "BUCKLAND", "BURLINGTON", "CAMBRIDGE", "CANTON", "CARLISLE", "CARVER", "CHARLEMONT", "CHARLTON", "CHATHAM", "CHELMSFORD", "CHELSEA", "CHESHIRE", "CHESTER", "CHESTERFIELD", "CHICOPEE", "CHILMARK", "CLARKSBURG", "CLINTON", "COHASSET", "COLRAIN", "CONCORD", "CONWAY", "CUMMINGTON", "DALTON", "DANVERS", "DARTMOUTH", "DEDHAM", "DEERFIELD", "DENNIS", "DIGHTON", "DOUGLAS", "DOVER", "DRACUT", "DUDLEY", "DUNSTABLE", "DUXBURY", "EAST BRIDGEWATER", "EAST BROOKFIELD", "EAST LONGMEADOW", "EASTHAM", "EASTHAMPTON", "EASTON", "EDGARTOWN", "EGREMONT", "ERVING", "ESSEX", "EVERETT", "FAIRHAVEN", "FALL RIVER", "FALMOUTH", "FITCHBURG", "FLORIDA", "FOXBOROUGH", "FRAMINGHAM", "FRANKLIN", "FREETOWN", "GARDNER", "GEORGETOWN", "GILL", "GLOUCESTER", "GOSHEN", "GOSNOLD", "GRAFTON", "GRANBY", "GRANVILLE", "GREAT BARRINGTON", "GREENFIELD", "GROTON", "GROVELAND", "HADLEY", "HALIFAX", "HAMILTON", "HAMPDEN", "HANCOCK", "HANOVER", "HANSON", "HARDWICK", "HARVARD", "HARWICH", "HATFIELD", "HAVERHILL", "HAWLEY", "HEATH", "HINGHAM", "HINSDALE", "HOLBROOK", "HOLDEN", "HOLLAND", "HOLLISTON", "HOLYOKE", "HOPEDALE", "HOPKINTON", "HUBBARDSTON", "HUDSON", "HULL", "HUNTINGTON", "IPSWICH", "KINGSTON", "LAKEVILLE", "LANCASTER", "LANESBOROUGH", "LAWRENCE", "LEE", "LEICESTER", "LENOX", "LEOMINSTER", "LEVERETT", "LEXINGTON", "LEYDEN", "LINCOLN", "LITTLETON", "LONGMEADOW", "LOWELL", "LUDLOW", "LUNENBURG", "LYNN", "LYNNFIELD", "MALDEN", "MANCHESTER-BY-THE-SEA", "MANSFIELD", "MARBLEHEAD", "MARION", "MARLBOROUGH", "MARSHFIELD", "MASHPEE", "MATTAPOISETT", "MAYNARD", "MEDFIELD", "MEDFORD", "MEDWAY", "MELROSE", "MENDON", "MERRIMAC", "METHUEN", "MIDDLEBOROUGH", "MIDDLEFIELD", "MIDDLETON", "MILFORD", "MILLBURY", "MILLIS", "MILLVILLE", "MILTON", "MONROE", "MONSON", "MONTAGUE", "MONTEREY", "MONTGOMERY", "MOUNT WASHINGTON", "NAHANT", "NANTUCKET", "NATICK", "NEEDHAM", "NEW ASHFORD", "NEW BEDFORD", "NEW BRAINTREE", "NEW MARLBOROUGH", "NEW SALEM", "NEWBURY", "NEWBURYPORT", "NEWTON", "NORFOLK", "NORTH ADAMS", "NORTH ANDOVER", "NORTH ATTLEBOROUGH", "NORTH BROOKFIELD", "NORTH READING", "NORTHAMPTON", "NORTHBOROUGH", "NORTHBRIDGE", "NORTHFIELD", "NORTON", "NORWELL", "NORWOOD", "OAK BLUFFS", "OAKHAM", "ORANGE", "ORLEANS", "OTIS", "OXFORD", "PALMER", "PAXTON", "PEABODY", "PELHAM", "PEMBROKE", "PEPPERELL", "PERU", "PETERSHAM", "PHILLIPSTON", "PITTSFIELD", "PLAINFIELD", "PLAINVILLE", "PLYMOUTH", "PLYMPTON", "PRINCETON", "PROVINCETOWN", "QUINCY", "RANDOLPH", "RAYNHAM", "READING", "REHOBOTH", "REVERE", "RICHMOND", "ROCHESTER", "ROCKLAND", "ROCKPORT", "ROWE", "ROWLEY", "ROYALSTON", "RUSSELL", "RUTLAND", "SALEM", "SALISBURY", "SANDISFIELD", "SANDWICH", "SAUGUS", "SAVOY", "SCITUATE", "SEEKONK", "SHARON", "SHEFFIELD", "SHELBURNE", "SHERBORN", "SHIRLEY", "SHREWSBURY", "SHUTESBURY", "SOMERSET", "SOMERVILLE", "SOUTH HADLEY", "SOUTHAMPTON", "SOUTHBOROUGH", "SOUTHBRIDGE", "SOUTHWICK", "SPENCER", "SPRINGFIELD", "STERLING", "STOCKBRIDGE", "STONEHAM", "STOUGHTON", "STOW", "STURBRIDGE", "SUDBURY", "SUNDERLAND", "SUTTON", "SWAMPSCOTT", "SWANSEA", "TAUNTON", "TEMPLETON", "TEWKSBURY", "TISBURY", "TOLLAND", "TOPSFIELD", "TOWNSEND", "TRURO", "TYNGSBOROUGH", "TYRINGHAM", "UPTON", "UXBRIDGE", "WAKEFIELD", "WALES", "WALPOLE", "WALTHAM", "WARE", "WAREHAM", "WARREN", "WARWICK", "WASHINGTON", "WATERTOWN", "WAYLAND", "WEBSTER", "WELLESLEY", "WELLFLEET", "WENDELL", "WENHAM", "WEST BOYLSTON", "WEST BRIDGEWATER", "WEST BROOKFIELD", "WEST NEWBURY", "WEST SPRINGFIELD", "WEST STOCKBRIDGE", "WEST TISBURY", "WESTBOROUGH", "WESTFIELD", "WESTFORD", "WESTHAMPTON", "WESTMINSTER", "WESTON", "WESTPORT", "WESTWOOD", "WEYMOUTH", "WHATELY", "WHITMAN", "WILBRAHAM", "WILLIAMSBURG", "WILLIAMSTOWN", "WILMINGTON", "WINCHENDON", "WINCHESTER", "WINDSOR", "WINTHROP", "WOBURN", "WORCESTER", "WORTHINGTON", "WRENTHAM", "YARMOUTH"]


def get_archaic():
    browser = RoboBrowser(parser='html.parser')
    browser.open('http://www.sec.state.ma.us/cis/cisuno/unoidx.htm')
    content_list = browser.select('#maincontent p')[4:]

    d = {'archaic': {}, 'unmatched': {}}
    for section in content_list:
        # skip the top-links
        if section.find('a'):
            continue
        for entry in section.text.splitlines():
            entry = entry.strip()
            try:
                (village, city, county) = entry.split(' / ')
            except ValueError:
                # some lines have three / in them
                try:
                    (village, city, county, aka) = entry.split(' / ')
                except ValueError:
                    continue

            village = village.strip()

            # cleanup city names
            city = city.strip()
            city = city.replace('Archaic Name of ', '')
            city = city.replace('Archaic Name and Section of ', '')
            city = city.replace('Archaic Name and section of ', '')
            city = city.replace('Annexed to BOSTON 1867', 'Boston')
            city = city.replace('Annexed to BOSTON 1869', 'Boston')
            city = city.replace('Annexed to BOSTON 1873', 'Boston')
            city = city.replace('Annexed to BOSTON 1911', 'Boston')
            city = city.replace('.', '')

            if city.upper() in CITY_TOWN_NAMES:
                d['archaic'][village] = city
            else:
                d['unmatched'][village] = city
    return d
