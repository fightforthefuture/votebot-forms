from flask_script import Manager
from flask_rq2.script import RQManager
from app.app import app, rq
from scripts import ma_data

manager = Manager(app)
manager.add_command('rq', RQManager(rq))


@manager.command
def generate_ma_data():
    import json
    print "generating MA data"
    d = ma_data.get_archaic()
    json.dump(d, open('app/ovr_forms/massachusetts_data.json', 'w'), indent=2)
    print "wrote %d archaic community names" % len(d['archaic'])
    print "unable to match %d to city or town" % len(d['unmatched'])

if __name__ == "__main__":
    manager.run()
