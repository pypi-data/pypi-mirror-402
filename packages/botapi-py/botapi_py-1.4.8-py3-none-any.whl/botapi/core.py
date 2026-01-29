from __future__ import annotations

from . import types, errors

from typing import Any, Generic, Literal, Optional, Dict, TypeVar, TypeAlias
from pydantic import BaseModel

import logging
import httpx
import json

log = logging.getLogger(__name__)

MultipartFile: TypeAlias = tuple[
	str | None,
	bytes,
	Optional[str]
] # (filename, file_content, mime_type)

MultipartFiles: TypeAlias = dict[str, MultipartFile]


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

	def _convert_data(self, data: dict[str, Any]) -> tuple[dict[str, Any], MultipartFiles]:
		new_data: dict[str, Any] = {}
		files: MultipartFiles = {} # (filename, file_content, mime_type)
		
		for key, value in data.items():
			
			# Multipart file uploading from local file
			'''
			#TODO (is it a good idea?) infer the parameter even if it's always a string (not wrapped inside a InputFile instance):
			 - if it's a local file path, send the string as-is if in local botapi mode, otherwise open, read and use multipart
			 - if it's a remote file URL or a file_id, send it as-is to the api
			>> but i need to evaluate if it's worth the convenience, because when we pass a local path that points to a non-existing file
				this would consider the string to be a file_id (and yes, it would throw an error, but it would be harder to debug).
			'''
			if isinstance(value, types.InputFile):
				# if value.path:
				# 	with open(value.path, 'rb') as f:
				# 		file_content = f.read()
				# elif value.file_content:
				
				file_content = value.file_content
				files[key] = (value.file_name, file_content, value.mime_type) # if mime_type is None, httpx will infer it with `mimetypes`
				# continue
				
			elif isinstance(value, BaseModel):
				new_data[key] = json.dumps(
					value.model_dump(
						mode='json',
						exclude_none=True,
					)   
				)
				
			elif isinstance(value, list):
				new_data[key] = json.dumps([
					item.model_dump(
						mode='json',
						exclude_none=True,
					)
					if isinstance(item, BaseModel)
					else item for item in value # pyright: ignore[reportUnknownVariableType]
				])
				
			else:
				new_data[key] = value
				
		return new_data, files

	async def _send_request(self, method: str, data: Dict[str, Any]) -> Any:
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

