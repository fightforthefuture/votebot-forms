from flask_script import Manager
from flask_rq2.script import RQManager
from app.app import app, rq

manager = Manager(app)
manager.add_command('rq', RQManager(rq))

if __name__ == "__main__":
    manager.run()
