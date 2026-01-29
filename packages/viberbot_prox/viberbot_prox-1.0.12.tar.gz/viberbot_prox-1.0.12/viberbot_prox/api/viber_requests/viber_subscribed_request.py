from viberbot_prox.api.event_type import EventType
from viberbot_prox.api.user_profile import UserProfile
from viberbot_prox.api.viber_requests.viber_request import ViberRequest


class ViberSubscribedRequest(ViberRequest):
	def __init__(self):
		super(ViberSubscribedRequest, self).__init__(EventType.SUBSCRIBED)
		self._user = None
		self._api_version = None

	def from_dict(self, request_dict):
		super(ViberSubscribedRequest, self).from_dict(request_dict)
		self._user = UserProfile().from_dict(request_dict['user'])
		if 'api_version' in request_dict:
			self._api_version = request_dict['api_version']
		return self

	@property
	def user(self):
		return self._user

	@property
	def api_version(self):
		return self._api_version
