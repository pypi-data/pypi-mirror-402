import logging, jsonpickle
from fmconsult.utils.url import UrlUtil
from oitoxesystem.appdriverslocationapi.api import AppDriversLocationApi

class Vehicles(AppDriversLocationApi):

  def get_all(self):
    try:
      logging.info(f'get all vehicles records...')
      url = UrlUtil().make_url(self.base_url, ['vehicles', 'location'])
      res = self.call_request('GET', url)
      return jsonpickle.decode(res)
    except Exception as e:
      logging.error(e)
      raise

  def get_by_id(self, vehicle_id):
    try:
      logging.info(f'get vehicle record from id {vehicle_id}...')
      url = UrlUtil().make_url(self.base_url, ['vehicle', vehicle_id])
      res = self.call_request('GET', url)
      return jsonpickle.decode(res)
    except Exception as e:
      logging.error(e)
      raise

  def update_location(self, vehicle_id, data):
    try:
      logging.info(f'update vehicle location from id {vehicle_id}...')
      url = UrlUtil().make_url(self.base_url, ['vehicle', vehicle_id, 'location'])
      res = self.call_request('POST', url, None, data)
      return jsonpickle.decode(res)
    except Exception as e:
      logging.error(e)
      raise
    