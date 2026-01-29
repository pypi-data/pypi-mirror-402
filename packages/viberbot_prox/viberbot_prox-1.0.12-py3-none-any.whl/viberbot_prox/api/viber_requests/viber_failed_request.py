import warnings
from viberbot_prox.api.event_type import EventType
from viberbot_prox.api.viber_requests.viber_request import ViberRequest


class ViberFailedRequest(ViberRequest):
	def __init__(self):
		super(ViberFailedRequest, self).__init__(EventType.FAILED)
		self._message_token = None
		self._user_id = None
		self._desc = None

	def from_dict(self, request_dict):
		super(ViberFailedRequest, self).from_dict(request_dict)
		self._message_token = request_dict['message_token']
		self._user_id = request_dict['user_id']
		self._desc = request_dict['desc']
		return self

	@property
	def meesage_token(self):
		warnings.warn('Property `meesage_token` had typo and now is deprecated, please use `message_token` instead')
		return self._message_token

	@property
	def message_token(self):
		return self._message_token

	@property
	def user_id(self):
		return self._user_id

	@property
	def desc(self):
		return self._desc
