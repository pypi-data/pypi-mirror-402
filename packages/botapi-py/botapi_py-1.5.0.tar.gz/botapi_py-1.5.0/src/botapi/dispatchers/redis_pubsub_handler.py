from __future__ import annotations

import asyncio
import inspect
import json
import logging
import signal
from typing import override

import orjson
import pydantic

from botapi.types import Update

from .common import BaseAsyncDispatcher, UpdateHandler

try:
	import redis.asyncio as redis
	from redis.asyncio.client import PubSub
	_has_redis = True
except ImportError as e:
	_has_redis = False
	raise e
	
logger = logging.getLogger(__name__)


class RedisPubSubAsyncDispatcher(BaseAsyncDispatcher):
	update_handler: UpdateHandler
	update_handler_argcount: int
	tasks_shutdown_timeout: float
	tasks: set[asyncio.Task] # prevent gc from collecting tasks before they finish
	redis_client: redis.Redis
	redis_reconnect_delay: float
	pubsub: PubSub
	pubsub_channel: str
	bot_token_json_key: str
	
	def __init__(
		self,
		update_handler: UpdateHandler,
		bot_token_json_key: str,
		pubsub_channel: str,
		redis_client: redis.Redis,
		redis_reconnect_delay: float = 5,
		shutdown_wait_timeout: float = 3
	) -> None:
		'''
		Dispatcher that receives updates from a Redis PUB/SUB
		and dispatches them to a registered async handler.
		
		This dispatcher is atypical but very useful, especially when you need to handle
		updates coming from a lot of different bots AND from many different projects.
		
		**NOTE:**
		This dispatcher assumes that the bot token is part of the update JSON payload itself
		inside the `bot_token_json_key` key (see constructor), so either:
		- the software handling the `PUBLISH` must manipulate the JSON accordingly, or
		- a custom Bot API Server must do this.
		
		Args:
			update_handler (UpdateHandler):
				Async function to handle received messages.
			bot_token_json_key (str):
				Name of the JSON key in the update payload that contains the bot token.
			redis_client (redis.Redis):
				Redis client instance.
			pubsub_channel (str):
				Name of the Redis PUB/SUB channel to subscribe to.
			redis_reconnect_delay (float, optional):
				Delay in seconds before retrying connection on failure.
			shutdown_wait_timeout (float, optional):
				Timeout in seconds to wait for pending tasks to complete on shutdown.
		'''
		if not _has_redis:
			raise ImportError('redis-py is not installed. Install `botapi-py[redis]` to use this dispatcher.')
			
		self.update_handler = update_handler
		self.bot_token_json_key = bot_token_json_key
		self.redis_client = redis_client
		self.pubsub_channel = pubsub_channel
		self.redis_reconnect_delay = redis_reconnect_delay
		self.shutdown_wait_timeout = shutdown_wait_timeout
		self.tasks = set()
		self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
		self.update_handler_argcount = len(inspect.getfullargspec(update_handler).args)
		
	def _task_done_callback(self, task: asyncio.Task) -> None:
		'''
		Callback that is called by the event loop when an update_handler task is done.
		
		This catches and logs unhandled exceptions, so that they don't pass silently.
		Also, it removes the completed task from the `tasks` set.
		'''
		try:
			task.result()
		except Exception:
			logger.exception('Exception in handler')
			
		finally:
			self.tasks.discard(task)
			
	async def _message_to_update_and_token(self, message: str) -> tuple[Update, str]:
		'''
		Converts raw message (containing a JSON) into a Python dict, then:
		- extracts the bot token from the specified `self.bot_token_json_key` key
		- validates the update into an `Update` object.
		'''
		data: dict = orjson.loads(message)
		
		if self.bot_token_json_key not in data:
			err = f'Missing bot token key "{self.bot_token_json_key}" in the update JSON payload'
			raise KeyError(err)
			
		bot_token = data.pop(self.bot_token_json_key)
		
		return Update.from_dict(data), bot_token
		
	async def _dispatch(self, message: str) -> None:
		'''
		Converts raw message (containing a JSON) into a Python dict,
		then dispatch it, to the registered handler, in a new task.
		'''
		try:
			update, bot_token = await self._message_to_update_and_token(message)
		except json.JSONDecodeError:
			logger.exception('Failed to decode JSON:')
		except pydantic.ValidationError:
			logger.exception('Failed pydantic validation:')
		else:
			if self.update_handler_argcount == 1:
				coro = self.update_handler(update) # pyright: ignore[reportCallIssue]
			else:
				coro = self.update_handler(update, bot_token) # pyright: ignore[reportCallIssue]
				
			task = asyncio.create_task(coro)
			
			self.tasks.add(task)
			task.add_done_callback(self._task_done_callback)
			
	async def _shutdown(self) -> None:
		'''
		Wait for pending/running tasks to complete (with a timeout),
		then close the Redis connection.
		'''
		if self.tasks:
			logger.info('Waiting for %d tasks to complete...', len(self.tasks))
			try:
				await asyncio.wait_for(
					asyncio.gather(*self.tasks, return_exceptions=True),
					timeout=self.shutdown_wait_timeout
				)
			except asyncio.TimeoutError:
				logger.warning('Some tasks were still running after timeout, CancelledError was raised.')
				
		try:
			await self.redis_client.aclose()
		except Exception:
			logger.exception('Exception while closing Redis connection:')
			
	async def _listen_forever(self) -> None:
		'''
		Listen for messages coming from the PUBSUB channel forever.
		In case of connection errors, it will retry after a delay.
		'''
		while True:
			try:
				logger.info('Subscribing to channel %s...', self.pubsub_channel)
				await self.pubsub.subscribe(self.pubsub_channel)
				
				logger.info('Subscribed to %s. Waiting for messages...', self.pubsub_channel)
				
				async for message in self.pubsub.listen():
					if message['type'] == 'message':
						try:
							await self._dispatch(message['data'])
						except Exception:
							logger.exception('Exception raised in the dispatcher:')
							
			except redis.ConnectionError as e:
				# logger.exception('Connection error, attempting to reconnect:')
				logger.error('Connection error, attempting to reconnect: %s', e)
				await asyncio.sleep(delay=self.redis_reconnect_delay)
				
				# await self.pubsub.unsubscribe()
				
			except asyncio.CancelledError:
				logger.info('Received termination signal')
				break
				
			except Exception: # catch-all for unexpected exceptions; NEVER let the bot crash!
				logger.exception('Unexpected exception in listen_forever:')
				await asyncio.sleep(delay=self.redis_reconnect_delay)
				
	async def _register_signal_handlers(self, task_to_cancel: asyncio.Task) -> None:
		'''
		Register signal handlers for graceful shutdown on:
		- SIGTERM
		- SIGINT
		'''
		loop = asyncio.get_running_loop()
		
		for sig in (signal.SIGTERM, signal.SIGINT):
			loop.add_signal_handler(
				sig,
				task_to_cancel.cancel
			)
			
	@override
	async def run_forever(self) -> None:
		'''
		Wait for incoming updates forever. This method **is blocking**.
		Retries automatically after Redis connection errors, terminates on SIGINT/SIGTERM.
		
		Example:
		```python
		redis_client = redis.Redis(
			host='localhost',
			port=6379
		)
		dispatcher = RedisPubSubAsyncDispatcher(
			update_handler=handler,
			pubsub_channel='my_channel',
			redis_client=redis_client
		)
		await dispatcher.run_forever()
		```
		'''
		task = asyncio.create_task(self._listen_forever())
		
		try:
			await task
		except asyncio.CancelledError:
			logger.info('Received termination signal')
		finally:
			logger.warning('Shutting down...')
			await self._shutdown()
			
