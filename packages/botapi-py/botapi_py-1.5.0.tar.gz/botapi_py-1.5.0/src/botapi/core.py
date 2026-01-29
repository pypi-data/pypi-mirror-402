from __future__ import annotations

from . import errors
from . import internals

from typing import Any, Optional, Dict
from pydantic import TypeAdapter

import logging
import httpx
import json

log = logging.getLogger(__name__)

class BaseBot:
	def __init__(
		self,
		token: str,
		api_url: str = 'https://api.telegram.org',
		session: Optional[httpx.AsyncClient] = None,
		test_server: bool = False,
	):
		self.token: str = token.removeprefix('bot')
		self.api_url: str = api_url
		self.session: httpx.AsyncClient = session or httpx.AsyncClient(timeout=120)
		self.test_server: bool = test_server
		
		if not session:
			log.warning('No HTTP session provided, creating a new one.')
			
	@property
	def bot_id(self) -> int:
		'''
		Returns the bot's user ID by extracting it from the token.
		'''
		return int(self.token.split(':')[0])
		
	def _compose_api_url(self, method: str) -> str:
		url = f'{self.api_url}/bot{self.token}/'
		if self.test_server:
			url += 'test/'
		url += method
		return url
		
	def _compose_api_file_url(self, file_path: str) -> str:
		'''
		Composes the URL for file downloads from the Telegram Bot API.
		'''
		# https://api.telegram.org/file/bot<token>/<file_path>
		# https://api.telegram.org/file/bot<token>/test/<file_path>
		url = f'{self.api_url}/file/bot{self.token}/'
		if self.test_server:
			url += 'test/'
		url += file_path
		return url
		
	def _convert_data(self, data: dict[str, Any]) -> tuple[dict[str, Any], internals.MultipartFiles]:
		'''
		Converts the dictionary of class instances and raw types into a format
		suitable to be sent to the Telegram Bot API through an HTTP request, with POST data and multipart files.
		'''
		files: internals.MultipartFiles = {} # (filename, file_content, mime_type)
		
		# We use a TypeAdapter to dump the entire dict tree.
		# Pydantic `mode='json'` automatically converts sub-models to dicts and primitives.
		# The `context` is passed down to every node, and it allows, for example,
		#	the custom `InputFile` serializer to give us access to the multipart data,
		# 	and just serialize as the appropriate `attach://attach_name` string instead of using weird hacks.
		serialized_data: dict[str, Any] = TypeAdapter(dict[str, Any]).dump_python(
			data,
			mode='json', 
			exclude_none=True,
			context={
				'files': files
			}
		)
		
		# Telegram requires root-level lists/dicts to be JSON encoded strings.
		for key, value in serialized_data.items():
			if isinstance(value, (dict, list)):
				serialized_data[key] = json.dumps(value)
				
		return serialized_data, files
		
	async def _send_request(self, method: str, data: Dict[str, Any]) -> Any:
		'''
		Sends a POST request to the Telegram Bot API.
		'''
		converted_data, files = self._convert_data(data)
		
		request = await self.session.post(
			url=self._compose_api_url(method),
			data=converted_data,
			files=files or None
		)
		result: dict[str, Any] = request.json()
		
		if not result['ok']:
			raise errors.BotAPIError(
				method=method,
				response=result
			)
			
		return result['result']

