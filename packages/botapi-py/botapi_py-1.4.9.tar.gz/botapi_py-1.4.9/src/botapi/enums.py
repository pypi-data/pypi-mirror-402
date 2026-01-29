import enum
from typing import Union


class ChatType(enum.StrEnum):
	PRIVATE = 'private'
	GROUP = 'group'
	SUPERGROUP = 'supergroup'
	CHANNEL = 'channel'
	
class UpdateType(enum.StrEnum):
	'''
	Types of updates that a bot can receive.
	
	You can use these to filter updates, using the `allowed_updates`
	parameter in `getUpdates` and `setWebhook` methods.
	
	Source: https://github.com/tdlib/telegram-bot-api/blob/3b6a0b769c4a7fbe064087a4ad9fe6b1dbda498f/telegram-bot-api/Client.cpp#L15491
	'''
	MESSAGE = 'message'
	EDITED_MESSAGE = 'edited_message'
	CHANNEL_POST = 'channel_post'
	EDITED_CHANNEL_POST = 'edited_channel_post'
	INLINE_QUERY = 'inline_query'
	CHOSEN_INLINE_RESULT = 'chosen_inline_result'
	CALLBACK_QUERY = 'callback_query'
	CUSTOM_EVENT = 'custom_event'
	CUSTOM_QUERY = 'custom_query'
	SHIPPING_QUERY = 'shipping_query'
	PRE_CHECKOUT_QUERY = 'pre_checkout_query'
	POLL = 'poll'
	POLL_ANSWER = 'poll_answer'
	MY_CHAT_MEMBER = 'my_chat_member'
	CHAT_MEMBER = 'chat_member'
	CHAT_JOIN_REQUEST = 'chat_join_request'
	CHAT_BOOST = 'chat_boost'
	REMOVED_CHAT_BOOST = 'removed_chat_boost'
	MESSAGE_REACTION = 'message_reaction'
	MESSAGE_REACTION_COUNT = 'message_reaction_count'
	BUSINESS_CONNECTION = 'business_connection'
	BUSINESS_MESSAGE = 'business_message'
	EDITED_BUSINESS_MESSAGE = 'edited_business_message'
	DELETED_BUSINESS_MESSAGES = 'deleted_business_messages'
	PURCHASED_PAID_MEDIA = 'purchased_paid_media'
	
class MediaType(enum.StrEnum):
	'''
	Subset of `MessageType`.
	
	This represents **messages** containing some kind of **multimedia/visual content**.
	'''
	ANIMATION = 'animation'
	AUDIO = 'audio'
	DOCUMENT = 'document'
	PHOTO = 'photo'
	STICKER = 'sticker'
	VIDEO = 'video'
	VIDEO_NOTE = 'video_note'
	VOICE = 'voice'
	STORY = 'story'
	PAID_MEDIA = 'paid_media'
	
class ServiceMessage(enum.StrEnum):
	'''
	Subset of `MessageType`.
	
	This represents special types of **service messages**.
	
	These messages are ALL represented as semi-transparent bubbles in Telegram apps UI,
	containing text (e.g. "user joined the group") and/or graphical elements (e.g. gifts, giveaways).
	'''
	NEW_CHAT_MEMBERS = 'new_chat_members'
	LEFT_CHAT_MEMBER = 'left_chat_member'
	NEW_CHAT_TITLE = 'new_chat_title'
	NEW_CHAT_PHOTO = 'new_chat_photo'
	DELETE_CHAT_PHOTO = 'delete_chat_photo'
	GROUP_CHAT_CREATED = 'group_chat_created'
	SUPERGROUP_CHAT_CREATED = 'supergroup_chat_created'
	CHANNEL_CHAT_CREATED = 'channel_chat_created'
	MESSAGE_AUTO_DELETE_TIMER_CHANGED = 'message_auto_delete_timer_changed'
	MIGRATE_TO_CHAT_ID = 'migrate_to_chat_id'
	MIGRATE_FROM_CHAT_ID = 'migrate_from_chat_id'
	PINNED_MESSAGE = 'pinned_message'
	SUCCESSFUL_PAYMENT = 'successful_payment'
	REFUNDED_PAYMENT = 'refunded_payment'
	USERS_SHARED = 'users_shared'
	CHAT_SHARED = 'chat_shared'
	GIFT = 'gift'
	UNIQUE_GIFT = 'unique_gift'
	CONNECTED_WEBSITE = 'connected_website'
	WRITE_ACCESS_ALLOWED = 'write_access_allowed'
	PASSPORT_DATA = 'passport_data'
	PROXIMITY_ALERT_TRIGGERED = 'proximity_alert_triggered'
	BOOST_ADDED = 'boost_added'
	CHAT_BACKGROUND_SET = 'chat_background_set'
	CHECKLIST_TASKS_DONE = 'checklist_tasks_done'
	CHECKLIST_TASKS_ADDED = 'checklist_tasks_added'
	DIRECT_MESSAGE_PRICE_CHANGED = 'direct_message_price_changed'
	FORUM_TOPIC_CREATED = 'forum_topic_created'
	FORUM_TOPIC_EDITED = 'forum_topic_edited'
	FORUM_TOPIC_CLOSED = 'forum_topic_closed'
	FORUM_TOPIC_REOPENED = 'forum_topic_reopened'
	GENERAL_FORUM_TOPIC_HIDDEN = 'general_forum_topic_hidden'
	GENERAL_FORUM_TOPIC_UNHIDDEN = 'general_forum_topic_unhidden'
	GIVEAWAY = 'giveaway'
	GIVEAWAY_CREATED = 'giveaway_created'
	GIVEAWAY_WINNERS = 'giveaway_winners'
	GIVEAWAY_COMPLETED = 'giveaway_completed'
	PAID_MESSAGE_PRICE_CHANGED = 'paid_message_price_changed'
	SUGGESTED_POST_APPROVED = 'suggested_post_approved'
	SUGGESTED_POST_APPROVAL_FAILED = 'suggested_post_approval_failed'
	SUGGESTED_POST_DECLINED = 'suggested_post_declined'
	SUGGESTED_POST_PAID = 'suggested_post_paid'
	SUGGESTED_POST_REFUNDED = 'suggested_post_refunded'
	VIDEO_CHAT_SCHEDULED = 'video_chat_scheduled'
	VIDEO_CHAT_STARTED = 'video_chat_started'
	VIDEO_CHAT_ENDED = 'video_chat_ended'
	VIDEO_CHAT_PARTICIPANTS_INVITED = 'video_chat_participants_invited'
	WEB_APP_DATA = 'web_app_data'
	SUGGESTED_POST = 'suggested_post_info'
	
class OtherMessageType(enum.StrEnum):
	'''
	Subset of `MessageType`.
	
	This represents other possible types of messages, that do NOT contain
	multimedia nor service content.
	'''
	TEXT = 'text'
	CHECKLIST = 'checklist'
	POLL = 'poll'
	GAME = 'game'
	INVOICE = 'invoice'
	DICE = 'dice'
	VENUE = 'venue'
	LOCATION = 'location'
	CONTACT = 'contact'
	
MessageType = Union[
	MediaType,
	ServiceMessage,
	OtherMessageType
]
'''
Possible types of a `UpdateType.Message` update.

The type of the **actual** message content.

All of the fields are mutually exclusive, since a message
can only be of one 'type' at a time.
'''

class ChatMemberStatus(enum.StrEnum):
	'''
	Possible statuses of a `ChatMember`.
	
	Remember that left members that are also restricted (muted), are represented as
	`RESTRICTED` with the `is_member` flag set to `False`.
	
	See: https://core.telegram.org/bots/api#chatmember
	'''
	CREATOR = 'creator'
	ADMINISTRATOR = 'administrator'
	MEMBER = 'member'
	RESTRICTED = 'restricted'
	LEFT = 'left'
	BANNED = 'kicked'
	
class ParseMode(enum.StrEnum):
	'''
	Available parse modes for formatting text messages.
	
	See: https://core.telegram.org/bots/api#formatting-options
	'''
	MARKDOWN = 'Markdown'
	MARKDOWN_V2 = 'MarkdownV2'
	HTML = 'HTML'
	
class ChatAction(enum.StrEnum):
	'''
	Types of actions that a bot can send using the `sendChatAction` method.
	
	See: https://core.telegram.org/bots/api#sendchataction
	'''
	TYPING = 'typing'
	UPLOAD_PHOTO = 'upload_photo'
	RECORD_VIDEO = 'record_video'
	UPLOAD_VIDEO = 'upload_video'
	RECORD_VOICE = 'record_voice'
	UPLOAD_VOICE = 'upload_voice'
	UPLOAD_DOCUMENT = 'upload_document'
	CHOOSE_STICKER = 'choose_sticker'
	FIND_LOCATION = 'find_location'
	RECORD_VIDEO_NOTE = 'record_video_note'
	UPLOAD_VIDEO_NOTE = 'upload_video_note'
	
