# Scheduler plugins for Cherrypy
# Copyright (C) 2025 IKUS Software
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import importlib
import tempfile
from threading import Event

import cherrypy
from cherrypy.test import helper

from .. import scheduler  # noqa

done = Event()

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None
if not HAS_SQLALCHEMY:
    pass
else:
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.exc import IntegrityError

    from .. import db  # noqa

    Base = cherrypy.db.get_base()

    class User2(Base):
        __tablename__ = 'users2'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        def __repr__(self):
            return f"User2(id={self.id}, username='{self.username}')"

    class Root:

        @cherrypy.expose
        def index(self):
            return str(User2.query.all())

        @cherrypy.expose
        def add(self, username):
            try:
                User2(username=username).add().commit()
                return "OK"
            except IntegrityError as e:
                return str(e)

    def create_user(*args, **kwargs):
        user = User2(*args, **kwargs).add()
        user.commit()
        done.set()


class DbSchedulerPluginTest(helper.CPWebCase):
    interactive = False

    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.TemporaryDirectory(prefix='cherrypy-foundation-', suffix='-db-test')
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        cls.tempdir.cleanup()
        super().teardown_class()

    @classmethod
    def setup_server(cls):
        cherrypy.config.update(
            {
                'db.uri': f"sqlite:///{cls.tempdir.name}/data.db",
            }
        )
        cherrypy.tree.mount(Root(), '/')

    def setUp(self) -> None:
        done.clear()
        cherrypy.db.create_all()
        return super().setUp()

    def tearDown(self):
        cherrypy.db.drop_all()
        return super().tearDown()

    def test_add_job_now(self):
        # Given a task
        # When scheduling that task
        scheduled = cherrypy.engine.publish('scheduler:add_job_now', create_user, username='myuser')
        self.assertTrue(scheduled)
        # When waiting for all tasks
        cherrypy.scheduler.wait_for_jobs()
        # Then the task get called
        self.assertTrue(done.is_set())
        # Then database was updated
        User2.query.filter(User2.username == 'myuser').one()
