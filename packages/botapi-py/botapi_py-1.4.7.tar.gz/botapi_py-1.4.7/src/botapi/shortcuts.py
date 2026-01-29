from __future__ import annotations

from typing import Optional, Union, List, cast

from . import enums
from . import types

from . import methods


class BotShortcuts:
	'''
	Mixin class containing shortcut bound methods for the `Bot` class.
	These methods provide convenient wrappers around standard API methods.
	'''
	
	async def send_media(
		self,
		chat_id: Union[int, str],
		media: Union[types.InputFile, str],
		file_type: enums.MediaType,
		caption: Optional[str] = None,
		parse_mode: Optional[Union[str, enums.ParseMode]] = enums.ParseMode.HTML,
		caption_entities: Optional[List[types.MessageEntity]] = None,
		show_caption_above_media: Optional[bool] = None,
		has_spoiler: Optional[bool] = None,
		disable_notification: Optional[bool] = None,
		protect_content: Optional[bool] = None,
		reply_parameters: Optional[types.ReplyParameters] = None,
		reply_markup: Optional[Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply]] = None,
		message_effect_id: Optional[str] = None,
		allow_paid_broadcast: Optional[bool] = None,
		business_connection_id: Optional[str] = None,
		message_thread_id: Optional[int] = None,
	) -> types.Message:
		'''
		Method that sends common types of media by automatically routing to the correct `send_<type>` method.
		
		:param chat_id: Unique identifier for the target chat or username of the target channel.
		:param media: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
		:param file_type: The type of media to send. Use `enums.MediaType`.
		:param caption: Media caption, 0-1024 characters.
		:param parse_mode: Mode for parsing entities in the media caption.
		:param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode.
		:param show_caption_above_media: Pass True, if the caption must be shown above the message media.
		:param has_spoiler: Pass True if the media needs to be covered with a spoiler animation.
		:param disable_notification: Sends the message silently. Users will receive a notification with no sound.
		:param protect_content: Protects the contents of the sent message from forwarding and saving.
		:param reply_parameters: Description of the message to reply to.
		:param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove a reply keyboard or to force a reply from the user.
		:param message_effect_id: Unique identifier of the message effect to be added to the message.
		:param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance.
		:param business_connection_id: Unique identifier of the business connection on behalf of which the message will be sent.
		:param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only.
		:param kwargs: Additional arguments specific to the target method (e.g. `duration`, `width`, `height`, `thumbnail`, `performer`, `title`).
		:return: On success, the sent Message is returned.
		'''
		bot = cast(methods.Bot, self)
		
		call_args: dict = {
			'chat_id': chat_id,
			'caption': caption,
			'parse_mode': parse_mode,
			'caption_entities': caption_entities,
			'disable_notification': disable_notification,
			'protect_content': protect_content,
			'reply_parameters': reply_parameters,
			'reply_markup': reply_markup,
			'message_effect_id': message_effect_id,
			'allow_paid_broadcast': allow_paid_broadcast,
			'business_connection_id': business_connection_id,
			'message_thread_id': message_thread_id,
			'has_spoiler': has_spoiler,
			'show_caption_above_media': show_caption_above_media,
		}
		
		match file_type:
			
			case enums.MediaType.PHOTO:
				call_args['photo'] = media
				return await bot.send_photo(**call_args)
				
			case enums.MediaType.VIDEO:
				call_args['video'] = media
				return await bot.send_video(**call_args)
				
			case enums.MediaType.ANIMATION:
				call_args['animation'] = media
				return await bot.send_animation(**call_args)
				
			case enums.MediaType.AUDIO:
				call_args['audio'] = media
				# Audio doesn't support has_spoiler or show_caption_above_media in some versions, 
				# but check API. core.telegram.org/bots/api#sendaudio says no spoiler, no caption above.
				# We should probably filter them out to avoid errors if the underlying method relies on strict matching?
				# generated methods typically accept **kwargs only if defined? No, generated methods have explicit args.
				# If I pass 'has_spoiler' to send_audio and it's not in signature, it might fail if I use **call_args matching a signature.
				# Python's **kwargs unpacking into a function call fails if keys don't match arguments (unless function has **kwargs).
				# The generated methods DO NOT have **kwargs. They have explicit arguments.
				# So I MUST NOT pass extra arguments.
				
				call_args.pop('has_spoiler', None)
				call_args.pop('show_caption_above_media', None)
				return await bot.send_audio(**call_args)
				
			case enums.MediaType.DOCUMENT:
				call_args['document'] = media
				# Document supports disable_content_type_detection
				call_args.pop('has_spoiler', None)
				call_args.pop('show_caption_above_media', None)
				return await bot.send_document(**call_args)
				
			case enums.MediaType.VOICE:
				call_args['voice'] = media
				call_args.pop('has_spoiler', None)
				call_args.pop('show_caption_above_media', None)
				return await bot.send_voice(**call_args)
				
			case enums.MediaType.VIDEO_NOTE:
				call_args['video_note'] = media
				call_args.pop('has_spoiler', None)
				call_args.pop('show_caption_above_media', None)
				call_args.pop('caption', None) # Video notes don't have captions
				call_args.pop('parse_mode', None)
				call_args.pop('caption_entities', None)
				return await bot.send_video_note(**call_args)
				
			case enums.MediaType.STICKER:
				call_args['sticker'] = media
				# Sticker is quite different
				call_args.pop('caption', None)
				call_args.pop('parse_mode', None)
				call_args.pop('caption_entities', None)
				call_args.pop('has_spoiler', None)
				call_args.pop('show_caption_above_media', None)
				return await bot.send_sticker(**call_args)
				
			case _:
				# Fallback or Error
				raise ValueError(f"Unsupported or unknown media type: {file_type}")
				
