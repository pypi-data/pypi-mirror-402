import json

from typing import Any, Optional

from . import types


class BotAPIError(Exception):
	"""
	Exception raised for Bot API request failures.
	
	Args:
		method (`str`): The method name of the failed API call.
		error_code (`int`, optional): Numeric error code when request fails.
		description (`str`, optional): Human-readable error description.
		parameters (`ResponseParameters`, optional): Additional error handling parameters.
	"""
	
	method: str
	response: dict[str, Any]
	error_code: Optional[int] = None
	description: Optional[str] = None
	parameters: Optional[types.ResponseParameters] = None
	
	def __init__(self, method: str, response: dict[str, Any]):
		self.method = method
		self.response = response
		self.error_code = response.get('error_code')
		self.description = response.get('description')
		_parameters = response.get('parameters')
		self.parameters = types.ResponseParameters.model_validate(_parameters) if _parameters else None
		
		Exception.__init__(self, f'BotAPI request failed: /{self.method}: {json.dumps(self.response, indent=True)}')
		