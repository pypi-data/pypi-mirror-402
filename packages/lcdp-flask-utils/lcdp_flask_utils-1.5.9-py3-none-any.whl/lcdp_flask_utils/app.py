from connexion.apps.flask import FlaskApp
from connexion.spec import Specification

# Util method to determine an ident func for an HTTP request (See : https://github.com/dtheodor/flask-sqlalchemy-session/issues/14#issuecomment-1227976421)
try:
    from greenlet import getcurrent as _ident_func
except ImportError:
    from threading import get_ident as _ident_func

class ConnexionApp(FlaskApp):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def add_before_request_func(self, func):
    if not callable(func):
      raise TypeError("'{}' object if not callable".format(func))
    self.app.before_request(func)

  def add_teardown_request_func(self, func):
    if not callable(func):
      raise TypeError("'{}' object if not callable".format(func))
    self.app.teardown_request(func)

  def setup_api(self, specification, **kwargs):
    api = self.add_api(specification, name=specification, **kwargs)

    return api

  def app_context(self, *args, **kwargs):  # pragma: no cover
    return self.app.app_context(*args, **kwargs)