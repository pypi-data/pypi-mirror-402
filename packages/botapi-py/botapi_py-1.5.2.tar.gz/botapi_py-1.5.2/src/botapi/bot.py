from __future__ import annotations

from typing import Optional, Union, List

from . import enums
from . import types
from . import methods


class Bot(methods.Methods):
	'''
	A (very lightweight) instance of a Telegram Bot.
	Use this to call API methods and shortcut bound methods.
	
	_Remember to pass an existing `httpx.AsyncClient` instance
	to avoid significant performance degradation in production._
	'''
	
	async def send_media(
		self,
		chat_id: Union[int, str],
		media: Union[types.InputFile, str, None],
		file_type: Optional[enums.MediaType | str],
		caption: Optional[str] = None,
		parse_mode: Optional[Union[str, enums.ParseMode]] = None,
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
		disable_content_type_detection: Optional[bool] = None, # Documents only
	) -> types.Message:
		'''
		Shortcut method that sends common types of media by automatically routing to the correct `send_<type>` method.
		Also supports `send_message` for plaintext-only messages for convenience.
		
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
		:param disable_content_type_detection: Disables automatic server-side content type detection.
		:return: On success, the sent Message is returned.
		'''
		
		# Plain text message
		if not media or not file_type:
			if not caption:
				raise ValueError('Either media or caption must be provided.')
				
			return await self.send_message(
				chat_id=chat_id,
				# media=media,
				text=caption,
				parse_mode=parse_mode,
				entities=caption_entities,
				disable_notification=disable_notification,
				protect_content=protect_content,
				reply_parameters=reply_parameters,
				reply_markup=reply_markup,
				message_effect_id=message_effect_id,
				allow_paid_broadcast=allow_paid_broadcast,
				business_connection_id=business_connection_id,
				message_thread_id=message_thread_id,
				# has_spoiler=has_spoiler,
				# show_caption_above_media=show_caption_above_media
			)
			
		match file_type:
			
			case enums.MediaType.PHOTO:
				return await self.send_photo(
					chat_id=chat_id,
					photo=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					has_spoiler=has_spoiler,
					show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.VIDEO:
				return await self.send_video(
					chat_id=chat_id,
					video=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					has_spoiler=has_spoiler,
					show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.ANIMATION:
				return await self.send_animation(
					chat_id=chat_id,
					animation=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					has_spoiler=has_spoiler,
					show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.AUDIO:
				return await self.send_audio(
					chat_id=chat_id,
					audio=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					# has_spoiler=has_spoiler,
					# show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.DOCUMENT:
				return await self.send_document(
					chat_id=chat_id,
					document=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					# has_spoiler=has_spoiler,
					# show_caption_above_media=show_caption_above_media,
					disable_content_type_detection=disable_content_type_detection
				)
				
			case enums.MediaType.VOICE:
				return await self.send_voice(
					chat_id=chat_id,
					voice=media,
					caption=caption,
					parse_mode=parse_mode,
					caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					# has_spoiler=has_spoiler,
					# show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.VIDEO_NOTE:
				return await self.send_video_note(
					chat_id=chat_id,
					video_note=media,
					# caption=caption,
					# parse_mode=parse_mode,
					# caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					# has_spoiler=has_spoiler,
					# show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.STICKER:
				return await self.send_sticker(
					chat_id=chat_id,
					sticker=media,
					# caption=caption,
					# parse_mode=parse_mode,
					# caption_entities=caption_entities,
					disable_notification=disable_notification,
					protect_content=protect_content,
					reply_parameters=reply_parameters,
					reply_markup=reply_markup,
					message_effect_id=message_effect_id,
					allow_paid_broadcast=allow_paid_broadcast,
					business_connection_id=business_connection_id,
					message_thread_id=message_thread_id,
					# has_spoiler=has_spoiler,
					# show_caption_above_media=show_caption_above_media
				)
				
			case enums.MediaType.STORY | enums.MediaType.PAID_MEDIA:
				raise ValueError(f'Unsupported media type: {file_type}')
				
			case _:
				raise ValueError(f'Unknown media type: {file_type}')
				
