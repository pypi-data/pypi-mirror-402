import logging, jsonpickle, requests,os
from fmconsult.http.api import ApiBase

class AppDriversLocationApi(ApiBase):

  def __init__(self):
    try:
      self.api_token = os.environ['8xesystem.app.drivers.location.api.token']
      self.base_url = 'https://api-locations-drivers-app.8x-esystem.com.br'
      super().__init__({'x-api-token': self.api_token})
    except:
      raise