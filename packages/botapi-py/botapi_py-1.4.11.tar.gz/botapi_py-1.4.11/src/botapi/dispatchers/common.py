from abc import ABC
from typing import Any, Callable, Coroutine, TypeAlias, Union

from botapi.types import Update

UpdateHandler1: TypeAlias = Callable[
	[Update],
	Coroutine[Any, Any, None]
]
'''
Represents an async update handler function.
It has the following signature:
- `async def handler(update: Update) -> None: ...`
'''

UpdateHandler2: TypeAlias = Callable[
	[Update, str],
	Coroutine[Any, Any, None]
]
'''
Represents an async update handler function.
It has the following signature:
- `async def handler(update: Update, bot_token: str) -> None: ...`
'''

UpdateHandler: TypeAlias = Union[
	UpdateHandler1,
	UpdateHandler2
]
'''
Represents an async update handler function.

It can have one of the following signatures:
- `async def handler(update: Update) -> None: ...`
- `async def handler(update: Update, bot_token: str) -> None: ...`

The second signature is especially useful when the dispatcher
is used to handle incoming updates from multiple bots.
'''

class BaseAsyncDispatcher(ABC):
	'''
	Abstract base class for all async update dispatchers.
	'''
	
	async def run_forever(self) -> None:
		'''
		Waits for incoming updates forever, and dispatches them to the registered handler.
		This method **is blocking**, it terminates on SIGINT/SIGTERM signals.
		
		This method automatically retries failed `getUpdates` requests after a short delay.
		
		Example:
		```python
		dispatcher = Dispatcher(
			...
		)
		await dispatcher.run_forever()
		```
		'''
		raise NotImplementedError()
		
