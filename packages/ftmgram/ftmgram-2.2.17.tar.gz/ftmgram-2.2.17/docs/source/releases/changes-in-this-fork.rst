
Changes in this Fork
=====================

.. admonition :: A Word of Warning
    :class: tip
    
    We merge changes made to few of ftmgram forks plus changes made by us to this repository. All the features are just customized feature mostly for personal use; there is no guarantee in them being stable, **USE AT YOUR OWN RISK**.


This page lists all the documented changes of this fork,
in reverse chronological order. You should read this when upgrading
to this fork to know where your code can break, and where
it can take advantage of new goodies!

`For a more detailed description, please check the commits. <https://github.com/TelegramPlayGround/ftmgram/commits/dev/>`__

If you found any issue or have any suggestions, feel free to make `an issue <https://github.com/TelegramPlayGround/ftmgram/issues>`__ on github.

Breaking Changes in this Fork
==============================

- In :meth:`~ftmgram.Client.copy_message`, ``ValueError`` is raised instead of ``logging`` it.
- In :meth:`~ftmgram.Client.download_media`, if the message is a :obj:`~ftmgram.types.PaidMediaInfo` with more than one ``paid_media`` **and** ``idx`` was not specified, then a list of paths or binary file-like objects is returned.
- PR `#115 <https://github.com/TelegramPlayGround/ftmgram/pull/115>`_ This `change <https://github.com/ftmgram/ftmgram/pull/966#issuecomment-1108858881>`_ breaks some usages with offset-naive and offset-aware datetimes.
- PR from upstream: `#1411 <https://github.com/ftmgram/ftmgram/pull/1411>`_ without attribution.
- If you relied on internal types like ``import ftmgram.file_id`` OR ``import ftmgram.utils``, Then read this full document to know where `else <https://t.me/FtmgramChat/42497>`_ your code will break.
- :obj:`~ftmgram.types.InlineKeyboardButton` only accepts keyword arguments instead of positional arguments.


Changes in this Fork
=====================

+------------------------+
| Scheme layer used: 220 |
+------------------------+

- fix: set description correctly in :obj:`~ftmgram.types.InlineQueryResultAnimation` (contributed by @Krau in `#262 <https://github.com/KurimuzonAkuma/kurigram/pull/262>`__).
- Add generic return type for :meth:`~ftmgram.Client.invoke` (contributed by @ZeN220 in `#252 <https://github.com/KurimuzonAkuma/kurigram/pull/252>`__).
- fix: :meth:`~ftmgram.Client.copy_message` and :meth:`~ftmgram.types.Message.copy` (contributed by @beepsound in `#210 <https://github.com/TelegramPlayground/ftmgram/pull/210>`__).
- fix: file pointer position before returning file (contributed by @anonymousx97)
- Add ``offset_date`` and ``offset_message_id`` in :meth:`~ftmgram.Client.get_dialogs` and :meth:`~ftmgram.Client.search_global`.
- Enhance ``full_name`` property of :obj:`~ftmgram.types.Chat` (contributed by @Ling-ex in `#206 <https://github.com/TelegramPlayground/ftmgram/pull/206>`__).
- fix: :meth:`~ftmgram.Client.set_chat_permissions` method (contributed by @sudo-py-dev in `#204 <https://github.com/TelegramPlayground/ftmgram/pull/204>`__).
- Add ``message_effect_id`` in :meth:`~ftmgram.Client.forward_messages` and :meth:`~ftmgram.types.Message.forward`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=214&to=220>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=214&to=220>`__.

+------------------------+
| Scheme layer used: 214 |
+------------------------+

- `fix get_chat_photos <https://github.com/TelegramPlayground/ftmgram/pull/203>`.
- `support filters.regex for ChosenInlineResult <https://github.com/TelegramPlayground/ftmgram/pull/198>`__.
- Update :meth:`~ftmgram.types.Message.reply_game`, :meth:`~ftmgram.types.Message.reply_text`, :meth:`~ftmgram.types.Message.reply_animation`, :meth:`~ftmgram.types.Message.reply_audio`, :meth:`~ftmgram.types.Message.reply_contact`, :meth:`~ftmgram.types.Message.reply_document`, :meth:`~ftmgram.types.Message.reply_location`, :meth:`~ftmgram.types.Message.reply_media_group`, :meth:`~ftmgram.types.Message.reply_photo`, :meth:`~ftmgram.types.Message.reply_poll`, :meth:`~ftmgram.types.Message.reply_sticker`, :meth:`~ftmgram.types.Message.reply_venue`, :meth:`~ftmgram.types.Message.reply_video`, :meth:`~ftmgram.types.Message.reply_video_note`, :meth:`~ftmgram.types.Message.reply_voice`, :meth:`~ftmgram.types.Message.reply_invoice`, :meth:`~ftmgram.types.Message.forward`, :meth:`~ftmgram.types.Message.copy`, :meth:`~ftmgram.types.Message.reply_cached_media` methods to support direct_messages_topic_id.
- `Fix get_dialogs <https://github.com/TelegramPlayground/ftmgram/pull/195>`__.
- `Fix timestamp_to_datetime to correctly handle timezone conversion <https://github.com/TelegramPlayground/ftmgram/commit/fc838cf>`__.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=211&to=214>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=211&to=214>`__.

+------------------------+
| Scheme layer used: 211 |
+------------------------+

- Rename direct_message_topic_id to ``direct_messages_topic_id`` in :obj:`~ftmgram.types.ReplyParameters`. This parameter can be used to send a message to a direct messages chat topic.
- Added the field ``checklist_task_id`` to the class :obj:`~ftmgram.types.ReplyParameters`, allowing bots to reply to a specific checklist task.
- Added the field ``reply_to_checklist_task_id`` to the class :obj:`~ftmgram.types.Message`.
- Added the field ``can_manage_direct_messages`` to :obj:`~ftmgram.types.ChatPrivileges`.
- Added the field ``is_direct_messages`` to the classes :obj:`~ftmgram.types.Chat` which can be used to identify supergroups that are used as channel direct messages chats.
- Added the fields ``parent_chat`` and ``direct_messages_chat_id`` to the class :obj:`~ftmgram.types.Chat` which indicates the parent channel chat for a channel direct messages chat.
- Added the class :obj:`~ftmgram.types.DirectMessagesTopic` and the field ``direct_messages_topic`` to the class :obj:`~ftmgram.types.Message`, describing a topic of a direct messages chat.
- Added :meth:`~ftmgram.Client.get_direct_messages_topics_by_id`, :meth:`~ftmgram.Client.get_direct_messages_topics`, :meth:`~ftmgram.Client.set_chat_direct_messages_group`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=205&to=211>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=205&to=211>`__.

+------------------------+
| Scheme layer used: 205 |
+------------------------+

- Added the :obj:`~ftmgram.types.ChecklistTask` representing a task in a checklist.
- Added the :obj:`~ftmgram.types.Checklist` representing a checklist.
- Added the :obj:`~ftmgram.types.InputChecklistTask` representing a task to add to a checklist.
- Added the :obj:`~ftmgram.types.InputChecklist` representing a checklist to create.
- Added the field ``checklist`` to the :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.ExternalReplyInfo`, describing a checklist in a message.
- Added the :obj:`~ftmgram.types.ChecklistTasksDone` and the field ``checklist_tasks_done`` to the :obj:`~ftmgram.types.Message`, describing a service message about status changes for tasks in a checklist (i.e., marked as done/not done).
- Added the :obj:`~ftmgram.types.ChecklistTasksAdded` and the field ``checklist_tasks_added`` to the :obj:`~ftmgram.types.Message`, describing a service message about the addition of new tasks to a checklist.
- Added the :meth:`~ftmgram.Client.send_checklist`, allowing bots to send a checklist on behalf of a business account.
- Added the :meth:`~ftmgram.Client.edit_message_checklist`, allowing bots to edit a checklist on behalf of a business account.
- Added the :obj:`~ftmgram.types.DirectMessagePriceChanged` and the field ``direct_message_price_changed`` to the :obj:`~ftmgram.types.Message`, describing a service message about a price change for direct messages sent to the channel chat.
- `Fix conditions for recover_gaps <https://github.com/KurimuzonAkuma/ftmgram/commit/b59ae77>`__.
- Added ``reply_parameters`` in :meth:`~ftmgram.Client.forward_messages`.
- Increased the maximum number of options in a poll to 12.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=202&to=205>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=202&to=205>`__.

+------------------------+
| Scheme layer used: 202 |
+------------------------+

- Added the method :meth:`~ftmgram.Client.post_story` allowing bots to post a story on behalf of a managed business account.
- Added the method :meth:`~ftmgram.Client.edit_story` and :meth:`~ftmgram.Client.edit_business_story`, allowing bots to edit stories they had previously posted on behalf of a managed business account.
- Added the methods :meth:`~ftmgram.Client.delete_stories` and :meth:`~ftmgram.Client.delete_business_story`, allowing bots to delete stories they had previously posted on behalf of a managed business account.
- Added the classes :obj:`~ftmgram.types.InputStoryContentPhoto` and :obj:`~ftmgram.types.InputStoryContentVideo` representing the content of a story to post.
- Added the classes :obj:`~ftmgram.types.StoryArea`, :obj:`~ftmgram.types.StoryAreaPosition`, :obj:`~ftmgram.types.LocationAddress`, :obj:`~ftmgram.types.StoryAreaTypeLocation`, :obj:`~ftmgram.types.StoryAreaTypeSuggestedReaction`, :obj:`~ftmgram.types.StoryAreaTypeLink`, :obj:`~ftmgram.types.StoryAreaTypeWeather`, :obj:`~ftmgram.types.StoryAreaTypeUniqueGift`, :obj:`~ftmgram.types.StoryAreaTypeFoundVenue` and :obj:`~ftmgram.types.StoryAreaTypeMessage` describing clickable active areas on stories.
- Added the classes :obj:`~ftmgram.types.StoryPrivacySettings`, :obj:`~ftmgram.types.StoryPrivacySettingsEveryone`, :obj:`~ftmgram.types.StoryPrivacySettingsContacts`, :obj:`~ftmgram.types.StoryPrivacySettingsCloseFriends`, :obj:`~ftmgram.types.StoryPrivacySettingsSelectedUsers` to describe the privacy settings of a story.
- Added the methods :meth:`~ftmgram.Client.can_post_story`, :meth:`~ftmgram.Client.hide_my_story_view`, :meth:`~ftmgram.Client.forward_story`,  :meth:`~ftmgram.Client.toggle_story_is_posted_to_chat_page`,  :meth:`~ftmgram.Client.get_chat_active_stories`,  :meth:`~ftmgram.Client.get_chat_archived_stories`.
- Add support for parsing story links in :meth:`~ftmgram.Client.get_messages`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=201&to=202>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=200&to=202>`__.

+------------------------+
| Scheme layer used: 201 |
+------------------------+

- Renamed the field ``paid_message_star_count`` to ``paid_star_count`` in the :obj:`~ftmgram.types.Message`, containing the number of Telegram Stars that were paid to send the message.
- Added the classes :obj:`~ftmgram.types.PaidMessagePriceChanged` and :obj:`~ftmgram.types.PaidMessagesRefunded` and the fields ``paid_message_price_changed`` and ``paid_messages_refunded`` to the :obj:`~ftmgram.types.Message`, describing the appropriate service message.
- Added the :meth:`~ftmgram.Client.get_business_account_star_balance`, allowing bots to check the current Telegram Star balance of a managed business account.
- Added the :obj:`~ftmgram.types.BusinessBotRights` and replaced the field ``can_reply`` with the field ``rights`` of the type :obj:`~ftmgram.types.BusinessBotRights` in the :obj:`~ftmgram.types.BusinessConnection`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=200&to=201>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=200&to=201>`__.

+------------------------+
| Scheme layer used: 200 |
+------------------------+

- Added ``sizes`` to :obj:`~ftmgram.types.Photo` to return all available sizes.
- Add :meth:`~ftmgram.Client.send_screenshot_notification`.
- Add ``media`` in :obj:`~ftmgram.types.ExternalReplyInfo`.
- Add :obj:`~ftmgram.enums.MessageOriginType` as enum instead of str, and updated the appropriate filters.
- Document about `the issue #161 <https://github.com/TelegramPlayGround/ftmgram/issues/161>`__.
- Make `User.block/unblock/get_common_chats async <https://github.com/KurimuzonAkuma/ftmgram/commit/7cab86a9eee4bd57ac96a1713f9bd37a7fc0ac09>`__, `Fix examples <https://github.com/KurimuzonAkuma/ftmgram/commit/f7f83de4331d6358332dbd0458755e28d59ec0f0>`__ and `Fix docs <https://github.com/KurimuzonAkuma/ftmgram/commit/f98b92765634f862310b21783b186fce66877a24>`__.
- Try to return the service message (when applicable) in the method :meth:`~ftmgram.Client.set_chat_title`.
- Added :meth:`~ftmgram.Client.delete_chat_history`.
- Rename ``UserGift`` to :obj:`~ftmgram.types.ReceivedGift`, ``get_user_gifts`` to :meth:`~ftmgram.Client.get_received_gifts` and the corresponding fields appropriately.
- Added the field ``paid_message_star_count`` to the classes :obj:`~ftmgram.types.Chat`, :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.User`.
- Added the parameter ``paid_message_star_count`` to the methods :meth:`~ftmgram.Client.copy_media_group`, :meth:`~ftmgram.Client.send_game`, :meth:`~ftmgram.Client.send_invoice`, :meth:`~ftmgram.Client.forward_messages`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_cached_media`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_media_group`, :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_paid_media`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_voice` and the bound methods :meth:`~ftmgram.types.Message.forward` and :meth:`~ftmgram.types.Message.copy`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=199&to=200>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=199&to=200>`__.

+------------------------+
| Scheme layer used: 199 |
+------------------------+

- Added the class :obj:`~ftmgram.types.InlineQueryResultGame`.
- Added the bound methods :meth:`~ftmgram.types.ChosenInlineResult.edit_message_text`, :meth:`~ftmgram.types.ChosenInlineResult.edit_message_caption`, :meth:`~ftmgram.types.ChosenInlineResult.edit_message_media` and :meth:`~ftmgram.types.ChosenInlineResult.edit_message_reply_markup`.
- Renamed the fields ``thumb_url``, ``thumb_width``, and ``thumb_height`` in the classes :obj:`~ftmgram.types.InlineQueryResultArticle`, :obj:`~ftmgram.types.InlineQueryResultContact`, :obj:`~ftmgram.types.InlineQueryResultDocument`, :obj:`~ftmgram.types.InlineQueryResultLocation`, and :obj:`~ftmgram.types.InlineQueryResultVenue` to ``thumbnail_url``, ``thumbnail_width``, and ``thumbnail_height`` respectively.
- Renamed the field ``thumb_url`` in the classes :obj:`~ftmgram.types.InlineQueryResultPhoto` and :obj:`~ftmgram.types.InlineQueryResultVideo` to ``thumbnail_url``.
- Added the field ``animation_mime_type`` and renamed the fields ``thumb_url`` and ``thumb_mime_type`` in the classes :obj:`~ftmgram.types.InlineQueryResultAnimation` to ``thumbnail_url`` and ``thumbnail_mime_type`` respectively.
- Fixed a bug with ``_client`` being None in :obj:`~ftmgram.handlers.ChosenInlineResultHandler`.
- Added the parameters ``video_cover`` and ``video_start_timestamp`` to the method :meth:`~ftmgram.Client.copy_message`, allowing bots to change the start timestamp for copied videos.
- Added ``for_paid_reactions`` in :meth:`~ftmgram.Client.get_send_as_chats`.
- `Updated documentation and parameter names according to BOT API 8.3 <https://github.com/TelegramPlayGround/ftmgram/commit/7675b40>`__
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=198&to=199>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=198&to=199>`__.

+------------------------+
| Scheme layer used: 198 |
+------------------------+

- Updated :doc:`Text Formatting <../../topics/text-formatting>` documentation.
- Splitted the :meth:`~ftmgram.Client.get_messages` into :meth:`~ftmgram.Client.get_chat_pinned_message`, :meth:`~ftmgram.Client.get_callback_query_message`, and :meth:`~ftmgram.Client.get_replied_message`.
- Added ``message.content`` property.
- Added the ``cover`` and ``start_timestamp`` parameters in :meth:`~ftmgram.Client.send_video` and :obj:`~ftmgram.types.InputPaidMediaVideo`.
- Added the ``video_start_timestamp`` and renamed the ``send_copy`` and ``remove_caption`` parameters in :meth:`~ftmgram.Client.forward_messages` and :meth:`~ftmgram.types.Message.forward`.
- Added the ``gift_count`` to the :obj:`~ftmgram.types.Chat`.
- Added the :meth:`~ftmgram.Client.get_similar_bots`.
- Changed types in :obj:`~ftmgram.types.UpgradedGift`, :obj:`~ftmgram.types.UserGift`.
- PR from upstream: `701 <https://github.com/ftmgram/ftmgram/pull/701>`_
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=196&to=198>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=196&to=198>`__.

+------------------------+
| Scheme layer used: 196 |
+------------------------+

- Added the :meth:`~ftmgram.Client.get_owned_star_count` and a possibly temporary :obj:`~ftmgram.types.StarAmount`.
- Added the :obj:`~ftmgram.types.UpgradedGift` and changed return type :meth:`~ftmgram.Client.get_available_gifts` and :meth:`~ftmgram.Client.get_user_gifts`.
- Added the ``pay_for_upgrade`` in the :meth:`~ftmgram.Client.send_gift`.
- Added the parameters ``upgrade_star_count`` and ``is_for_birthday`` in :obj:`~ftmgram.types.Gift`.
- Added the :meth:`~ftmgram.Client.on_bot_purchased_paid_media` and :meth:`~ftmgram.Client.on_bot_business_connection`.
- Added the parameters ``can_be_upgraded``, ``was_refunded``, ``prepaid_upgrade_star_count``, ``can_be_transferred``, ``transfer_star_count``, ``export_date`` in :obj:`~ftmgram.types.UserGift`.
- Renamed the parameter ``only_in_channels`` to ``chat_type_filter`` in the :meth:`~ftmgram.Client.search_global_count` and :meth:`~ftmgram.Client.search_global`.
- Removed ``sender_user_id`` parameter from :meth:`~ftmgram.Client.sell_gift` and :meth:`~ftmgram.Client.toggle_gift_is_saved`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=195&to=196>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=195&to=196>`__.

+------------------------+
| Scheme layer used: 195 |
+------------------------+

- Added the :meth:`~ftmgram.Client.get_owned_bots` to return the list of owned by the current user bots.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=194&to=195>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=194&to=195>`__.

+------------------------+
| Scheme layer used: 194 |
+------------------------+

- Added the field ``schedule_date`` and changed the return type of the :meth:`~ftmgram.Client.send_inline_bot_result`.
- Added the field ``subscription_expiration_date`` in the :obj:`~ftmgram.types.SuccessfulPayment`.
- Added the parameter ``subscription_period`` in the :meth:`~ftmgram.Client.create_invoice_link`.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=192&to=194>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=192&to=194>`__.

+------------------------+
| Scheme layer used: 192 |
+------------------------+

- Added :obj:`~ftmgram.enums.ChatEventAction.SHOW_MESSAGE_SENDER_ENABLED`, :obj:`~ftmgram.enums.ChatEventAction.AGGRESSIVE_ANTI_SPAM_TOGGLED`, :obj:`~ftmgram.enums.ChatEventAction.PROTECTED_CONTENT_TOGGLED`, :obj:`~ftmgram.enums.ChatEventAction.CHAT_IS_FORUM_TOGGLED`, :obj:`~ftmgram.enums.ChatEventAction.USERNAMES_CHANGED`, :obj:`~ftmgram.enums.ChatEventAction.MEMBER_SUBSCRIPTION_EXTENDED`, :obj:`~ftmgram.enums.ChatEventAction.MEMBER_JOINED_BY_LINK`, :obj:`~ftmgram.enums.ChatEventAction.MEMBER_JOINED_BY_REQUEST`, and updated :obj:`~ftmgram.types.ChatEventFilter` with the corresponding attributes.
- Added the parameter ``show_caption_above_media`` to the :meth:`~ftmgram.Client.edit_inline_caption`.
- Added the parameter ``allow_paid_broadcast`` to the methods :meth:`~ftmgram.Client.copy_media_group`, :meth:`~ftmgram.Client.send_game`, :meth:`~ftmgram.Client.send_invoice`, :meth:`~ftmgram.Client.forward_messages`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_cached_media`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_media_group`, :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_paid_media`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_voice` and the bound methods :meth:`~ftmgram.types.Message.reply_game`, :meth:`~ftmgram.types.Message.reply_text`, :meth:`~ftmgram.types.Message.reply_animation`, :meth:`~ftmgram.types.Message.reply_audio`, :meth:`~ftmgram.types.Message.reply_contact`, :meth:`~ftmgram.types.Message.reply_document`, :meth:`~ftmgram.types.Message.reply_location`, :meth:`~ftmgram.types.Message.reply_media_group`, :meth:`~ftmgram.types.Message.reply_photo`, :meth:`~ftmgram.types.Message.reply_poll`, :meth:`~ftmgram.types.Message.reply_sticker`, :meth:`~ftmgram.types.Message.reply_venue`, :meth:`~ftmgram.types.Message.reply_video`, :meth:`~ftmgram.types.Message.reply_video_note`, :meth:`~ftmgram.types.Message.reply_voice`, :meth:`~ftmgram.types.Message.reply_invoice`, :meth:`~ftmgram.types.Message.forward`, :meth:`~ftmgram.types.Message.copy`, :meth:`~ftmgram.types.Message.reply_cached_media`.
- Introduced the ability to add media to existing text messages using the method :meth:`~ftmgram.Client.edit_message_media`, :meth:`~ftmgram.Client.edit_cached_media`, :meth:`~ftmgram.types.Message.edit_media`, :meth:`~ftmgram.types.Message.edit_cached_media`.
- Added the class :obj:`~ftmgram.types.CopyTextButton` and the field ``copy_text`` in the class :obj:`~ftmgram.types.InlineKeyboardButton` allowing bots to send and receive inline buttons that copy arbitrary text.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=190&to=192>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=190&to=192>`__.

+------------------------+
| Scheme layer used: 190 |
+------------------------+

- Added the methods :meth:`~ftmgram.Client.get_available_gifts`, :meth:`~ftmgram.Client.get_user_gifts`, :meth:`~ftmgram.Client.sell_gift`, :meth:`~ftmgram.Client.send_gift`, :meth:`~ftmgram.Client.toggle_gift_is_saved`, :meth:`~ftmgram.types.UserGift.toggle` and the types :obj:`~ftmgram.types.UserGift` and :obj:`~ftmgram.types.Gift`.
- Added the parameter ``send_as`` in the appropriate methods and bound methods `PR 107 <https://github.com/TelegramPlayGround/ftmgram/pull/107>`_.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=189&to=190>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=189&to=190>`__.

+------------------------+
| Scheme layer used: 189 |
+------------------------+

- Added :meth:`~ftmgram.Client.toggle_forum_topic_is_pinned` to pin / unpin a :obj:`~ftmgram.types.ForumTopic`.
- Added :meth:`~ftmgram.types.Message.star` bound method to the :obj:`~ftmgram.types.Message`.
- Added the field ``alternative_videos`` to the :obj:`~ftmgram.types.Message`.
- Added the fields ``connected_website`` and ``write_access_allowed`` to the :obj:`~ftmgram.types.Message`.
- Fix ``chat`` being None in some cases in the :obj:`~ftmgram.types.Message`.
- Fix deleting messages does not return the count in some cases.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=187&to=189>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=187&to=189>`__.

+------------------------+
| Scheme layer used: 187 |
+------------------------+

- Added the parameter ``emoji`` in :meth:`~ftmgram.Client.send_sticker` and :meth:`~ftmgram.types.Message.reply_sticker`. `#86 <https://github.com/KurimuzonAkuma/ftmgram/pull/86>`__.
- `Return list of photos and videos instead of bool in send_payment_form <https://github.com/KurimuzonAkuma/ftmgram/commit/6684eaf4273b0f2084a8709e2e852486f17cb67c>`__.
- Added the field ``prize_star_count`` to the classes :obj:`~ftmgram.types.GiveawayCreated`, :obj:`~ftmgram.types.Giveaway`, :obj:`~ftmgram.types.GiveawayWinners`.
- Added the field ``is_star_giveaway`` to the class :obj:`~ftmgram.types.GiveawayCompleted`.
- Added the ability to specify a payload in :meth:`~ftmgram.Client.send_paid_media` that is unused currently.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=186&to=187>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=186&to=187>`__.

+------------------------+
| Scheme layer used: 186 |
+------------------------+

- Try to return the service message (when applicable) in the methods :meth:`~ftmgram.Client.set_chat_photo`, :meth:`~ftmgram.types.Chat.set_photo`.
- Added the methods :meth:`~ftmgram.Client.get_payment_form` and :meth:`~ftmgram.Client.send_payment_form` `#89 <https://github.com/TelegramPlayGround/ftmgram/pull/89>`__.
- Added the fields ``expired_member_count``, ``subscription_period`` and ``subscription_price`` to the class :obj:`~ftmgram.types.ChatInviteLink`.
- Added the field ``can_enable_paid_reaction`` to the class :obj:`~ftmgram.types.Chat`.
- Added ``link`` property to :obj:`~ftmgram.types.Story` and fixed the ``link`` property in :obj:`~ftmgram.types.Message`.
- Introduced :obj:`~ftmgram.types.DraftMessage` type.
- Added the ability to send paid media to any chat and the parameter ``business_connection_id`` to the :meth:`~ftmgram.Client.send_paid_media`, allowing bots to send paid media on behalf of a business account.
- Added the field ``until_date`` to the class :obj:`~ftmgram.types.ChatMember` for members with an active subscription.
- Added :meth:`~ftmgram.Client.add_paid_message_reaction` and :obj:`~ftmgram.types.ReactionTypePaid`
- Updated `errors list <https://core.telegram.org/api/errors>`__ and improved documentation of some of the methods.
- Added missing parameters to :meth:`~ftmgram.Client.get_dialogs` and :obj:`~ftmgram.types.Dialog`.
- Added :obj:`~ftmgram.enums.MessageServiceType.UNKNOWN` type of service message `#1147 <https://github.com/ftmgram/ftmgram/issues/1147>`__.
- Added a :obj:`~ftmgram.enums.ChatJoinType` to distinguish the different types of :obj:`~ftmgram.enums.MessageServiceType.NEW_CHAT_MEMBERS`.
- Added :obj:`~ftmgram.enums.MessageServiceType.CONTACT_REGISTERED` and :obj:`~ftmgram.enums.MessageServiceType.SCREENSHOT_TAKEN` types of service messages.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=185&to=186>`__ raw API methods.


+------------------------+
| Scheme layer used: 185 |
+------------------------+

- Added the parameter ``chat_list`` to the methods :meth:`~ftmgram.Client.get_dialogs` and :meth:`~ftmgram.Client.get_dialogs_count`.
- Added ``gifted_stars`` service message to the class :obj:`~ftmgram.types.Message`.
- Added the fields ``have_access``, ``has_main_web_app``, ``active_user_count`` to the class :obj:`~ftmgram.types.User`, which is returned in response to  :meth:`~ftmgram.Client.get_me`.
- Added the parameter ``business_connection_id`` to the methods :meth:`~ftmgram.Client.pin_chat_message` and :meth:`~ftmgram.Client.unpin_chat_message`, allowing bots to manage pinned messages on behalf of a business account.
- View `new and changed <https://telegramplayground.github.io/TG-APIs/TL/diff/tdlib.html?from=184&to=185>`__ `raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=184&to=185>`__.


+------------------------+
| Scheme layer used: 184 |
+------------------------+

- Updated :obj:`~ftmgram.filters.via_bot`, to optionally support filtering invalid bot ``user_id``.
- Added the :meth:`~ftmgram.Client.get_active_sessions`, :meth:`~ftmgram.Client.terminate_session`, :meth:`~ftmgram.types.ActiveSession.terminate`, and :meth:`~ftmgram.Client.terminate_all_other_sessions`.
- Added the ``is_automatic_forward`` to the :obj:`~ftmgram.types.Message`.
- Added the parameters ``offset_id`` to the :meth:`~ftmgram.Client.search_messages` and the parameters ``min_date``, ``max_date``, ``min_id``, ``max_id``, ``saved_messages_topic_id`` to the :meth:`~ftmgram.Client.search_messages_count`.
- Dynamic session ReStart + restart optimizations (`#56 <https://github.com/TelegramPlayGround/ftmgram/pull/56>`__)
- Added the :meth:`~ftmgram.Client.delete_account`, :meth:`~ftmgram.Client.transfer_chat_ownership`, :meth:`~ftmgram.Client.update_status` (`#49 <https://github.com/TelegramPlayGround/ftmgram/pull/49>`__, `#51 <https://github.com/TelegramPlayGround/ftmgram/pull/51>`__)
- Added the class :obj:`~ftmgram.types.RefundedPayment`, containing information about a refunded payment.
- Added the field ``refunded_payment`` to the class :obj:`~ftmgram.types.Message`, describing a service message about a refunded payment.
- `View new and changed raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=183&to=184>`__.


+------------------------+
| Scheme layer used: 183 |
+------------------------+

- Added the classes :obj:`~ftmgram.types.PaidMedia`, :obj:`~ftmgram.types.PaidMediaInfo`, :obj:`~ftmgram.types.PaidMediaPreview`, :obj:`~ftmgram.types.PaidMediaPhoto` and :obj:`~ftmgram.types.PaidMediaVideo`, containing information about paid media.
- Added the method :meth:`~ftmgram.Client.send_paid_media` and the classes :obj:`~ftmgram.types.InputPaidMedia`, :obj:`~ftmgram.types.InputPaidMediaPhoto` and :obj:`~ftmgram.types.InputPaidMediaVideo`, to support sending paid media.
- Added the field ``paid_media`` to the classes :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.ExternalReplyInfo`.
- Added :meth:`~ftmgram.Client.get_stories`.
- Added filters :obj:`~ftmgram.filters.thread` and :obj:`~ftmgram.filters.self_destruct`.
- Added the field ``can_send_paid_media`` to the class :obj:`~ftmgram.types.Chat`.
- Added support for launching Web Apps via ``t.me`` link in the class :obj:`~ftmgram.types.MenuButtonWebApp`.
- `View new and changed raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=181&to=183>`__.

+------------------------+
| Scheme layer used: 182 |
+------------------------+

- Updated the parameter ``business_connection_id`` to the methods :meth:`~ftmgram.types.Message.edit_text`, :meth:`~ftmgram.types.Message.edit_media`, :meth:`~ftmgram.types.Message.edit_reply_markup`, :meth:`~ftmgram.types.CallbackQuery.edit_message_text`, :meth:`~ftmgram.types.CallbackQuery.edit_message_media`, :meth:`~ftmgram.types.CallbackQuery.edit_message_reply_markup`.
- Added the parameter ``business_connection_id`` to the methods :meth:`~ftmgram.Client.edit_message_text`, :meth:`~ftmgram.Client.edit_message_media`, :meth:`~ftmgram.Client.edit_cached_media`, :meth:`~ftmgram.Client.edit_message_caption` and :meth:`~ftmgram.Client.edit_message_reply_markup`, allowing the bot to edit business messages.
- Added the parameter ``business_connection_id`` to the method :meth:`~ftmgram.Client.stop_poll`, allowing the bot to stop polls it sent on behalf of a business account.
- Added support for callback queries originating from a message sent on behalf of a business account.

+------------------------+
| Scheme layer used: 181 |
+------------------------+

- Added the classes :obj:`~ftmgram.types.InputLocationMessageContent`, :obj:`~ftmgram.types.InputVenueMessageContent`, :obj:`~ftmgram.types.InputContactMessageContent`, :obj:`~ftmgram.types.InputInvoiceMessageContent`.`
- Added ``background`` to :obj:`~ftmgram.types.Chat` (`#40 <https://github.com/TelegramPlayGround/ftmgram/pull/40>`_)
- Added the methods :meth:`~ftmgram.Client.translate_text`, :meth:`~ftmgram.Client.translate_message_text`, :meth:`~ftmgram.types.Message.translate` and the type :obj:`~ftmgram.types.TranslatedText` (`#39 <https://github.com/TelegramPlayGround/ftmgram/pull/39>`_).
- Added the methods :meth:`~ftmgram.Client.create_video_chat`, :meth:`~ftmgram.Client.discard_group_call`, :meth:`~ftmgram.Client.get_video_chat_rtmp_url` and the type :obj:`~ftmgram.types.RtmpUrl` (`#37 <https://github.com/TelegramPlayGround/ftmgram/pull/37>`_).
- Added :meth:`~Client.on_story` to listen to story updates.
- Ability to run in `replit` environment without creating `a deployment <https://ask.replit.com/t/ftmgram-network-issue/33679/46>`_. Set the environment variable ``FTMGRAM_REPLIT_NWTRAFIK_PORT`` value to ``5222`` if you want to connect to Production Telegram Servers, **OR** Set the environment variable ``FTMGRAM_REPLIT_WNTRAFIK_PORT`` value to ``5223`` if you want to connect to Test Telegram Servers, before starting the :obj:`~ftmgram.Client`.
- Added the :meth:`~ftmgram.Client.invite_group_call_participants` (`#35 <https://github.com/TelegramPlayGround/ftmgram/pull/35>`_).
- Added the types :obj:`~ftmgram.types.LabeledPrice`, :obj:`~ftmgram.types.OrderInfo`, :obj:`~ftmgram.types.PreCheckoutQuery`, :obj:`~ftmgram.types.ShippingAddress`, :obj:`~ftmgram.types.ShippingOption`, :obj:`~ftmgram.types.ShippingQuery` and :obj:`~ftmgram.types.SuccessfulPayment`.
- Added the ``successful_payment`` parameter to the :obj:`~ftmgram.types.Message`. Added the filter :obj:`~ftmgram.filters.successful_payment` to detect service messages of Successful Payment type.
- Added the methods :meth:`~ftmgram.Client.send_invoice`, :meth:`~ftmgram.Client.answer_pre_checkout_query` (:meth:`~ftmgram.types.PreCheckoutQuery.answer`), :meth:`~ftmgram.Client.answer_shipping_query` (:meth:`~ftmgram.types.ShippingQuery.answer`), :meth:`~ftmgram.Client.refund_star_payment` and :meth:`~ftmgram.Client.create_invoice_link`.
- Added the :meth:`~ftmgram.Client.send_web_app_custom_request`.
- Added the :meth:`~ftmgram.Client.search_public_messages_by_tag` and :meth:`~ftmgram.Client.count_public_messages_by_tag`.
- Added the ``fetch_replies`` parameter to :obj:`~ftmgram.Client`.
- Added the :meth:`~ftmgram.Client.get_message_effects`.
- Added the parameter ``message_effect_id`` to the methods :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_voice`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_game`, and :meth:`~ftmgram.Client.send_media_group`, and the corresponding ``reply_*`` methods in the class :obj:`~ftmgram.types.Message`.
- Added the field ``effect_id`` to the class :obj:`~ftmgram.types.Message`.
- Added the field ``show_caption_above_media`` to the classes :obj:`~ftmgram.types.Message`, :obj:`~ftmgram.types.InputMediaAnimation`, :obj:`~ftmgram.types.InputMediaPhoto`, :obj:`~ftmgram.types.InputMediaVideo`, :obj:`~ftmgram.types.InlineQueryResultAnimation`, :obj:`~ftmgram.types.InlineQueryResultCachedAnimation`,  :obj:`~ftmgram.types.InlineQueryResultPhoto`, :obj:`~ftmgram.types.InlineQueryResultCachedPhoto`, :obj:`~ftmgram.types.InlineQueryResultVideo`, :obj:`~ftmgram.types.InlineQueryResultCachedVideo`, :meth:`~ftmgram.Client.send_cached_media`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.copy_message` and :meth:`~ftmgram.Client.edit_message_caption`, and the corresponding ``reply_*`` methods.
- Added support for :obj:`~ftmgram.enums.MessageEntityType.EXPANDABLE_BLOCKQUOTE` entities in received messages.
- Added support for :obj:`~ftmgram.enums.MessageEntityType.EXPANDABLE_BLOCKQUOTE` entity parsing in :obj:`~ftmgram.enums.ParseMode.HTML` parse mode.
- Allowed to explicitly specify :obj:`~ftmgram.enums.MessageEntityType.EXPANDABLE_BLOCKQUOTE` entities in formatted texts.
- `View new and changed raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop.html?from=178&to=181>`__.

+------------------------+
| Scheme layer used: 179 |
+------------------------+

- Add ``invoice`` to :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.ExternalReplyInfo`.
- Add ``link_preview_options`` to :obj:`~ftmgram.Client`.
- Support for the updated Channel ID format. `#28 <https://github.com/TelegramPlayGround/ftmgram/pull/28>`_
- Improvements to :meth:`~ftmgram.Client.save_file` and :meth:`~ftmgram.Client.get_file` to handle the new `FLOOD_PREMIUM_WAIT <https://t.me/swiftgram/72>`_ errors.
- Added ``has_animation``, ``is_personal``, ``minithumbnail`` parameters to :obj:`~ftmgram.types.ChatPhoto`.
- Changed return type of :meth:`~ftmgram.Client.get_chat_photos` to return :obj:`~ftmgram.types.Photo` or :obj:`~ftmgram.types.Animation`.
- Added :meth:`~ftmgram.Client.get_chat_sponsored_messages` and the type :obj:`~ftmgram.types.SponsoredMessage`, by stealing unauthored changes from `KurimuzonAkuma/ftmgram#55 <https://github.com/KurimuzonAkuma/ftmgram/pull/55>`_.
- Added :meth:`~ftmgram.Client.load_group_call_participants` and the type :obj:`~ftmgram.types.GroupCallParticipant`, by stealing unauthored changes from `6df467f <https://github.com/KurimuzonAkuma/ftmgram/commit/6df467f89c0f6fa513a3f56ff1b517574fd3d164>`_.
- Added :meth:`~ftmgram.Client.view_messages` and the bound methods :meth:`~ftmgram.types.Message.read` and :meth:`~ftmgram.types.Message.view`.
- Added the field ``question_entities`` to the class :obj:`~ftmgram.types.Poll`.
- Added the field ``text_entities`` to the class :obj:`~ftmgram.types.PollOption`.
- Added the parameters ``question_parse_mode`` and ``question_entities`` to the method :meth:`~ftmgram.Client.send_poll`.
- Added the class :obj:`~ftmgram.types.InputPollOption` and changed the type of the parameter ``options`` in the method :meth:`~ftmgram.Client.send_poll` to Array of :obj:`~ftmgram.types.InputPollOption`.
- Added the field ``max_reaction_count`` to the class :obj:`~ftmgram.types.Chat`.
- Added the field ``via_join_request`` to the class :obj:`~ftmgram.types.ChatMemberUpdated`.
- Added the class :obj:`~ftmgram.types.TextQuote` and the field ``quote`` of type :obj:`~ftmgram.types.TextQuote` to the class :obj:`~ftmgram.types.Message`, which contains the part of the replied message text or caption that is quoted in the current message.
- Added ``full_name`` to :obj:`~ftmgram.types.Chat` and :obj:`~ftmgram.types.User` only for :obj:`~ftmgram.enums.ChatType.PRIVATE`.
- Added ``revoke_messages`` parameter to :meth:`~ftmgram.Client.ban_chat_member` and :meth:`~ftmgram.types.Chat.ban_member`.
- Added :meth:`~ftmgram.Client.get_collectible_item_info`.
- Added ``reverse`` parameter to :meth:`~ftmgram.Client.get_chat_history`. (`855e69e <https://github.com/ftmgram/ftmgram/blob/855e69e3f881c8140781c1d5e42e3098b2134dd2/ftmgram/methods/messages/get_history.py>`_, `a086b49 <https://github.com/dyanashek/ftmgram/commit/a086b492039687dd1b807969f9202061ce5305da>`_)
- `View new and changed raw API methods <https://telegramplayground.github.io/TG-APIs/TL/diff/tdesktop?from=176&to=178>`__.

+------------------------+
| Scheme layer used: 178 |
+------------------------+

- Added :meth:`~ftmgram.Client.search_chats`.
- Added :meth:`~ftmgram.Client.get_bot_name`, :meth:`~ftmgram.Client.get_bot_info_description`, :meth:`~ftmgram.Client.get_bot_info_short_description`, :meth:`~ftmgram.Client.set_bot_name`, :meth:`~ftmgram.Client.set_bot_info_description`, :meth:`~ftmgram.Client.set_bot_info_short_description`.
- Added :meth:`~ftmgram.Client.edit_cached_media` and :meth:`~ftmgram.types.Message.edit_cached_media`.
- Steal `d51eef3 <https://github.com/FtmgramMod/FtmgramMod/commit/d51eef31dc28724405ff473e45ca21b7d835d8b4>`_ without attribution.
- Added ``max_reaction_count`` to :obj:`~ftmgram.types.ChatReactions`.
- Added ``personal_chat_message`` to :obj:`~ftmgram.types.Chat`.
- Added ``only_in_channels`` parameter to :meth:`~ftmgram.Client.search_global` and :meth:`~ftmgram.Client.search_global_count`.

+------------------------+
| Scheme layer used: 177 |
+------------------------+

- Added ``emoji_message_interaction`` parameter to :meth:`~ftmgram.Client.send_chat_action` and :meth:`~ftmgram.types.Message.reply_chat_action`.
- **BOTS ONLY**: Updated :obj:`~ftmgram.handlers.ChatMemberUpdatedHandler` to handle updates when the bot is blocked or unblocked by a user.
- Added missing parameters in :meth:`~ftmgram.Client.create_group`, :meth:`~ftmgram.Client.create_supergroup`, :meth:`~ftmgram.Client.create_channel`.
- Try to return the service message (when applicable) in the methods :meth:`~ftmgram.Client.add_chat_members`, :meth:`~ftmgram.Client.promote_chat_member`
- Add :obj:`~ftmgram.enums.ChatAction.TRIGGER_EMOJI_ANIMATION` and :obj:`~ftmgram.enums.ChatAction.WATCH_EMOJI_ANIMATION` in :meth:`~ftmgram.Client.send_chat_action` and :meth:`~ftmgram.types.Message.reply_chat_action`.
- Attempted to revert the Backward Incompatible changes in the commits `fb118f95d <https://github.com/TelegramPlayGround/ftmgram/commit/fb118f9>`_ and `848bc8644 <https://github.com/TelegramPlayGround/ftmgram/commit/848bc86>`_.
- Added ``callback_data_with_password`` to :obj:`~ftmgram.types.InlineKeyboardButton` and added support in :meth:`~ftmgram.types.Message.click` for such buttons.
- PR from upstream: `1391 <https://github.com/ftmgram/ftmgram/pull/1391>`_ without attribution.
- Added ``gifted_premium`` service message to :obj:`~ftmgram.types.Message`.
- Added :meth:`~ftmgram.Client.get_stickers`.
- Added ``filters.users_shared`` and ``filters.chat_shared``.
- Added the field ``origin`` of type :obj:`~ftmgram.types.MessageOrigin` in the class :obj:`~ftmgram.types.ExternalReplyInfo`.
- Added the class :obj:`~ftmgram.types.MessageOrigin` and replaced the fields ``forward_from``, ``forward_from_chat``, ``forward_from_message_id``, ``forward_signature``, ``forward_sender_name``, and ``forward_date`` with the field ``forward_origin`` of type :obj:`~ftmgram.types.MessageOrigin` in the class :obj:`~ftmgram.types.Message`.
- Added ``accent_color``, ``profile_color``, ``emoji_status``, ``is_close_friend`` to :obj:`~ftmgram.types.Chat` and :obj:`~ftmgram.types.User`.
- Added the method :meth:`~ftmgram.Client.get_created_chats`.
- Added the class :obj:`~ftmgram.types.ForumTopic` and the methods :meth:`~ftmgram.Client.get_forum_topics`, :meth:`~ftmgram.Client.get_forum_topic`.
- Install the version, from PyPI, using ``pip uninstall -y ftmgram && pip install ftmdevtgfork==2.1.17``.
- Added the classes :obj:`~ftmgram.types.BusinessOpeningHours` and :obj:`~ftmgram.types.BusinessOpeningHoursInterval` and the field       ``business_opening_hours`` to the class :obj:`~ftmgram.types.Chat`.
- Added the class :obj:`~ftmgram.types.BusinessLocation` and the field ``business_location`` to the class :obj:`~ftmgram.types.Chat`.
- Added the class :obj:`~ftmgram.types.BusinessIntro` and the field ``business_intro`` to the class :obj:`~ftmgram.types.Chat`.
- Added the parameter ``business_connection_id`` to the methods :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_voice`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_game`, :meth:`~ftmgram.Client.send_media_group`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_chat_action`, :meth:`~ftmgram.Client.send_cached_media` and :meth:`~ftmgram.Client.copy_message` and the corresponding reply_* methods.
- Added :meth:`~ftmgram.Client.get_business_connection`.
- Added ``active_usernames`` to :obj:`~ftmgram.types.Chat` and :obj:`~ftmgram.types.User`.
- Added :obj:`~ftmgram.types.BusinessConnection`.
- Added support for ``https://t.me/m/blah`` links in the ``link`` parameter of :meth:`~ftmgram.Client.get_messages`
- Added the parameter ``message_thread_id`` to the :meth:`~ftmgram.Client.search_messages` and :meth:`~ftmgram.Client.search_messages_count`.
- Added the parameter ``chat_list`` to :meth:`~ftmgram.Client.search_global` and :meth:`~ftmgram.Client.search_global_count`.
- **BOTS ONLY**: Handled the parameter ``business_connection_id`` to the update handlers :obj:`~ftmgram.handlers.MessageHandler`, :obj:`~ftmgram.handlers.EditedMessageHandler`, :obj:`~ftmgram.handlers.DeletedMessagesHandler`.
- Added the field ``business_connection_id`` to the class :obj:`~ftmgram.types.Message`.
- Bug fix for the ``users_shared``, ``chat_shared`` logic in :obj:`~ftmgram.types.Message`.
- Added :meth:`~ftmgram.Client.set_birthdate` and :meth:`~ftmgram.Client.set_personal_chat`, for user accounts only.
- Added the field ``birthdate`` to the class :obj:`~ftmgram.types.Chat`.
- Added the field ``is_from_offline`` to the class :obj:`~ftmgram.types.Message`.
- Added the field ``sender_business_bot`` to the class :obj:`~ftmgram.types.Message`.
- Added the fields ``users_shared``, ``chat_shared`` to the class :obj:`~ftmgram.types.Message`.
- Added the field ``personal_chat`` to the class :obj:`~ftmgram.types.Chat`.
- Added the field ``can_connect_to_business`` to the class :obj:`~ftmgram.types.User`.
- Rearrange :meth:`~ftmgram.Client.send_sticker` parameter names.
- Added the fields ``request_title``, ``request_username``, and ``request_photo`` to the class :obj:`~ftmgram.types.KeyboardButtonRequestChat`.
- Added the fields ``request_name``, ``request_username``, and ``request_photo`` to the class :obj:`~ftmgram.types.KeyboardButtonRequestUsers`.

+------------------------+
| Scheme layer used: 176 |
+------------------------+

- Add ``message_thread_id`` parameter to :meth:`~ftmgram.Client.unpin_all_chat_messages`.
- Add :meth:`~ftmgram.Client.create_forum_topic`, :meth:`~ftmgram.Client.edit_forum_topic`, :meth:`~ftmgram.Client.close_forum_topic`, :meth:`~ftmgram.Client.reopen_forum_topic`, :meth:`~ftmgram.Client.hide_forum_topic`, :meth:`~ftmgram.Client.unhide_forum_topic`, :meth:`~ftmgram.Client.delete_forum_topic`, :meth:`~ftmgram.Client.get_forum_topic_icon_stickers`.
- Add ``AioSQLiteStorage``, by stealing the following commits:
    - `fded06e <https://github.com/KurimuzonAkuma/ftmgram/commit/fded06e7bdf8bb591fb5857d0f126986ccf357c8>`_
- Add ``skip_updates`` parameter to :obj:`~ftmgram.Client` class, by stealing the following commits:
    - `c16c83a <https://github.com/KurimuzonAkuma/ftmgram/commit/c16c83abc307e4646df0eba34aad6de42517c8bb>`_
    - `55aa162 <https://github.com/KurimuzonAkuma/ftmgram/commit/55aa162a38831d79604d4c10df1a046c8a1c3ea6>`_
- Add ``public``, ``for_my_bot`` to :meth:`~ftmgram.Client.delete_profile_photos`.
- Make ``photo_ids`` parameter as optional in :meth:`~ftmgram.Client.delete_profile_photos`.
- Add ``supergroup_chat_created`` to :obj:`~ftmgram.types.Message`.
- Add ``forum_topic_created``, ``forum_topic_closed``, ``forum_topic_edited``, ``forum_topic_reopened``, ``general_forum_topic_hidden``, ``general_forum_topic_unhidden`` to :obj:`~ftmgram.types.Message`.
- Add ``custom_action`` to :obj:`~ftmgram.types.Message`.
- Add ``public``, ``for_my_bot``, ``photo_frame_start_timestamp`` to :meth:`~ftmgram.Client.set_profile_photo`.
- Add ``inline_need_location``, ``can_be_edited`` to :obj:`~ftmgram.types.User`.
- Add ``giveaway``, ``giveaway_created``, ``giveaway_completed`` and ``giveaway_winners`` in :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.ExternalReplyInfo`.
- Bug fix for :meth:`~ftmgram.Client.send_message` with the ``message_thread_id`` parameter.
- Added ``request_users`` and ``request_chat`` to :obj:`~ftmgram.types.KeyboardButton`.
- **NOTE**: using the ``scheduled`` parameter, please be aware about using the correct :doc:`Message Identifiers <../../topics/message-identifiers>`.
    - Add ``is_scheduled`` parameter to :meth:`~ftmgram.Client.delete_messages`.
    - Add ``schedule_date`` parameter to :meth:`~ftmgram.Client.edit_message_caption`, :meth:`~ftmgram.Client.edit_message_media`, :meth:`~ftmgram.Client.edit_message_text`.
    - Added ``is_scheduled`` to :meth:`~ftmgram.Client.get_messages`.
    - Added ``is_scheduled`` to :meth:`~ftmgram.Client.get_chat_history`.
- Added new parameter ``client_platform`` to :obj:`~ftmgram.Client`.
- PR from upstream: `1403 <https://github.com/ftmgram/ftmgram/pull/1403>`_.
- Added ``story`` to :obj:`~ftmgram.types.ExternalReplyInfo`.
- Added ``story_id`` to :obj:`~ftmgram.types.ReplyParameters`.
- Added support for clicking (:obj:`~ftmgram.types.WebAppInfo`, :obj:`~ftmgram.types.LoginUrl`, ``user_id``, ``switch_inline_query_chosen_chat``) buttons in :meth:`~ftmgram.types.Message.click`.
- Rewrote :meth:`~ftmgram.Client.download_media` to support Story, and also made it future proof.
- `Fix bug in clicking UpdateBotCallbackQuery buttons <https://t.me/ftmgramchat/610636>`_

+-------------+
|  PmOItrOAe  |
+-------------+

- Renamed ``placeholder`` to ``input_field_placeholder`` in :obj:`~ftmgram.types.ForceReply` and :obj:`~ftmgram.types.ReplyKeyboardMarkup`.
- Add ``link`` parameter in :meth:`~ftmgram.Client.get_messages`
- `fix(filters): add type hints in filters.py <https://github.com/TelegramPlayGround/ftmgram/pull/8>`_
- Documentation Builder Fixes
- `faster-ftmgram <https://github.com/cavallium/faster-ftmgram>`__ is not polished or documented for anyone else's use. We don't have the capacity to support `faster-ftmgram <https://github.com/TelegramPlayGround/ftmgram/pull/6>`__ as an independent open-source project, nor any desire for it to become an alternative to Ftmgram. Our goal in making this code available is a unified faster Ftmgram. `... <https://github.com/cavallium/faster-ftmgram/blob/b781909/README.md#L28>`__

+-----------------------------+
|   Leaked Scheme Layers (2)  |
+-----------------------------+

- `Add ttl_seconds attribute to Voice and VideoNote class <https://github.com/KurimuzonAkuma/ftmgram/commit/7556d3e3864215386f018692947cdf52a82cb420>`_
- `#713 <https://github.com/ftmgram/ftmgram/pull/713>`_
- Removed :obj:`~ftmgram.types.ChatPreview` class, and merged the parameters with the :obj:`~ftmgram.types.Chat` class.
- Added ``description``, ``accent_color_id``, ``is_verified``, ``is_scam``, ``is_fake``, ``is_public``, ``join_by_request`` attributes to the class :obj:`~ftmgram.types.ChatPreview`.
- Added ``force_full`` parameter to :meth:`~ftmgram.Client.get_chat`.
- Bug Fix for :meth:`~ftmgram.Client.get_chat` and :meth:`~ftmgram.Client.join_chat` when ``https://t.me/username`` was passed.
- Added missing attributes to the class :obj:`~ftmgram.types.Story` when it is available.
- Added the field ``reply_to_story`` to the class :obj:`~ftmgram.types.Message`.
- Added the field ``user_chat_id`` to the class :obj:`~ftmgram.types.ChatJoinRequest`.
- Added the field ``switch_inline_query_chosen_chat`` of the type :obj:`~ftmgram.types.SwitchInlineQueryChosenChat` to the class :obj:`~ftmgram.types.InlineKeyboardButton`, which allows bots to switch to inline mode in a chosen chat of the given type.
- Add support for ``pay`` in :obj:`~ftmgram.types.InlineKeyboardButton`
- `#1345 <https://github.com/ftmgram/ftmgram/issues/1345>`_
- `Add undocumented things <https://github.com/TelegramPlayGround/ftmgram/commit/8a72939d98f343eae1e07981f95769efaa741e4e>`_
- `Add missing enums.SentCodeType <https://github.com/KurimuzonAkuma/ftmgram/commit/40ddcbca6062f13958f4ca2c9852f8d1c4d62f3c>`_
- `#693 <https://github.com/KurimuzonAkuma/ftmgram/pull/693>`_
- Revert `e678c05 <https://github.com/TelegramPlayGround/ftmgram/commit/e678c054d4aa0bbbb7d583eb426ca8753a4c9354>`_ and stole squashed unauthored changes from `bcd18d5 <https://github.com/Masterolic/ftmgram/commit/bcd18d5e04f18f949389a03f309816d6f0f9eabe>`_

+------------------------+
| Scheme layer used: 174 |
+------------------------+

- Added the field ``story`` to the class :obj:`~ftmgram.types.Message` for messages with forwarded stories. Currently, it holds no information.
- Added the class :obj:`~ftmgram.types.ChatBoostAdded` and the field ``boost_added`` to the class :obj:`~ftmgram.types.Message` for service messages about a user boosting a chat.
- Added the field ``custom_emoji_sticker_set_name`` to the class :obj:`~ftmgram.types.Chat`.
- Added the field ``unrestrict_boost_count`` to the class :obj:`~ftmgram.types.Chat`.
- Added the field ``sender_boost_count`` to the class :obj:`~ftmgram.types.Message`.

+------------------------+
| Scheme layer used: 173 |
+------------------------+

- Fix ConnectionResetError when only ping task (`#24 <https://github.com/KurimuzonAkuma/ftmgram/pull/24>`_)
- Added ``is_topic_message`` to the :obj:`~ftmgram.types.Message` object.
- Added ``has_visible_history``, ``has_hidden_members``, ``has_aggressive_anti_spam_enabled``, ``message_auto_delete_time``, ``slow_mode_delay``, ``slowmode_next_send_date``, ``is_forum`` to the :obj:`~ftmgram.types.Chat` object.
- Added ``add_to_recent``, ``story_id`` parameters in :meth:`~ftmgram.Client.set_reaction`.
- Bug fix in parsing ``Vector<Bool>`` (Thanks to `@AmarnathCJD <https://github.com/AmarnathCJD/>`_ and `@roj1512 <https://github.com/roj1512>`_).
- Documentation Fix of ``max_concurrent_transmissions`` type hint.
- Bug Fix in the ``get_file`` method. (Thanks to `@ALiwoto <https://github.com/ALiwoto>`_).
- Added missing attributes to :obj:`~ftmgram.types.ChatPermissions` and :obj:`~ftmgram.types.ChatPrivileges`.
- `Bug Fix for MIN_CHAT_ID <https://t.me/ftmgramchat/593090>`_.
- Added new parameter ``no_joined_notifications`` to :obj:`~ftmgram.Client`.
- Fix history TTL Service Message Parse.
- Thanks to `... <https://t.me/ftmgramchat/607757>`_. If you want to change the location of the ``unknown_errors.txt`` file that is created by :obj:`~ftmgram.Client`, set the environment variable ``FTMGRAM_LOG_UNKNOWN_ERRORS_FILENAME`` value to the path where the file should get created.
- Renamed ``force_document`` to ``disable_content_type_detection`` in :meth:`~ftmgram.Client.send_document` and :meth:`~ftmgram.types.Message.reply_document`.
- Added missing attributes ``added_to_attachment_menu``, ``can_be_added_to_attachment_menu``, ``can_join_groups``, ``can_read_all_group_messages``, ``supports_inline_queries``, ``restricts_new_chats`` to the :obj:`~ftmgram.types.User`.
- Migrate project to ``pyproject.toml`` from ``setup.py``.
- PRs from upstream: `1366 <https://github.com/ftmgram/ftmgram/pull/1366>`_, `1305 <https://github.com/ftmgram/ftmgram/pull/1305>`_, `1288 <https://github.com/ftmgram/ftmgram/pull/1288>`_, `1262 <https://github.com/ftmgram/ftmgram/pull/1262>`_, `1253 <https://github.com/ftmgram/ftmgram/pull/1253>`_, `1234 <https://github.com/ftmgram/ftmgram/pull/1234>`_, `1210 <https://github.com/ftmgram/ftmgram/pull/1210>`_, `1201 <https://github.com/ftmgram/ftmgram/pull/1201>`_, `1197 <https://github.com/ftmgram/ftmgram/pull/1197>`_, `1143 <https://github.com/ftmgram/ftmgram/pull/1143>`_, `1059 <https://github.com/ftmgram/ftmgram/pull/1059>`_.
- Bug fix for :meth:`~ftmgram.Client.send_audio` and :meth:`~ftmgram.Client.send_voice`. (Thanks to `... <https://t.me/c/1220993104/1360174>`_).
- Add `waveform` parameter to :meth:`~ftmgram.Client.send_voice`.
- Added `view_once` parameter to :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_voice`.
- Add missing parameters to :meth:`~ftmgram.types.Message.reply_photo`, :meth:`~ftmgram.types.Message.reply_video`, :meth:`~ftmgram.types.Message.reply_video_note`, :meth:`~ftmgram.types.Message.reply_voice`.

+------------------------+
| Scheme layer used: 170 |
+------------------------+

- Stole documentation from `FtmgramMod <https://github.com/FtmgramMod/FtmgramMod>`_.
- Renamed ``send_reaction`` to :meth:`~ftmgram.Client.set_reaction`.
- Added support for :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_voice` messages that could be played once.
- Added the field ``via_chat_folder_invite_link`` to the class :obj:`~ftmgram.types.ChatMemberUpdated`.
- **BOTS ONLY**: Added updates about a reaction change on a message with non-anonymous reactions, represented by the class :obj:`~ftmgram.handlers.MessageReactionUpdatedHandler` and the field ``message_reaction`` in the class Update.
- **BOTS ONLY**: Added updates about reaction changes on a message with anonymous reactions, represented by the class :obj:`~ftmgram.handlers.MessageReactionCountUpdatedHandler` and the field ``message_reaction_count`` in the class Update.
- Replaced the parameter ``disable_web_page_preview`` with :obj:`~ftmgram.types.LinkPreviewOptions` in the methods :meth:`~ftmgram.Client.send_message` and :meth:`~ftmgram.Client.edit_message_text`.
- Replaced the field ``disable_web_page_preview`` with :obj:`~ftmgram.types.LinkPreviewOptions` in the class :obj:`~ftmgram.types.InputTextMessageContent`.
- Added missing parameters to :meth:`~ftmgram.Client.forward_messages`.
- Added the class :obj:`~ftmgram.types.ReplyParameters` and replaced parameters ``reply_to_message_id`` in the methods :meth:`~ftmgram.Client.copy_message`, :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_voice`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_game`, :meth:`~ftmgram.Client.send_media_group`, :meth:`~ftmgram.Client.copy_media_group`, :meth:`~ftmgram.Client.send_inline_bot_result`, :meth:`~ftmgram.Client.send_cached_media`, and the corresponding reply_* methods with the field ``reply_parameters`` of type :obj:`~ftmgram.types.ReplyParameters`.
- Bug fixes for sending ``ttl_seconds`` and ``has_spoiler``.

+------------------------+
| Scheme layer used: 169 |
+------------------------+

- Changed condition in :meth:`~ftmgram.Client.join_chat` and :meth:`~ftmgram.Client.get_chat`.
- Added ``disable_content_type_detection`` parameter to :obj:`~ftmgram.types.InputMediaVideo`.
- Added ``has_spoiler`` parameter to :meth:`~ftmgram.Client.copy_message`.
- Improved :meth:`~ftmgram.Client.get_chat_history`: add ``min_id`` and ``max_id`` params.
- `Prevent connection to dc every time in get_file <https://github.com/TelegramPlayGround/ftmgram/commit/f2581fd7ab84ada7685645a6f80475fbea5e743a>`_
- Added ``_raw`` to the :obj:`~ftmgram.types.Chat`, :obj:`~ftmgram.types.Dialog`, :obj:`~ftmgram.types.Message` and :obj:`~ftmgram.types.User` objects.
- Fix downloading media to ``WORKDIR`` when ``WORKDIR`` was not specified.
- `Update multiple fragment chat usernames <https://github.com/TelegramPlayGround/ftmgram/commit/39aea4831ee18e5263bf6755306f0ca49f075bda>`_
- `Custom Storage Engines <https://github.com/TelegramPlayGround/ftmgram/commit/cd937fff623759dcac8f437a8c524684868590a4>`_
- Documentation fix for ``user.mention`` in :obj:`~ftmgram.types.User`.

+------------------------+
| Scheme layer used: 167 |
+------------------------+

- Fixed the TL flags being Python reserved keywords: ``from`` and ``self``.

+------------------------+
| Scheme layer used: 161 |
+------------------------+

- Added ``my_stories_from`` to the :meth:`~ftmgram.Client.block_user` and :meth:`~ftmgram.Client.unblock_user` methods.

+------------------------+
| Scheme layer used: 160 |
+------------------------+

- Added ``message_thread_id`` to the methods :meth:`~ftmgram.Client.copy_message`, :meth:`~ftmgram.Client.forward_messages`, :meth:`~ftmgram.Client.send_message`, :meth:`~ftmgram.Client.send_photo`, :meth:`~ftmgram.Client.send_video`, :meth:`~ftmgram.Client.send_animation`, :meth:`~ftmgram.Client.send_audio`, :meth:`~ftmgram.Client.send_document`, :meth:`~ftmgram.Client.send_sticker`, :meth:`~ftmgram.Client.send_video_note`, :meth:`~ftmgram.Client.send_voice`, :meth:`~ftmgram.Client.send_location`, :meth:`~ftmgram.Client.send_venue`, :meth:`~ftmgram.Client.send_contact`, :meth:`~ftmgram.Client.send_poll`, :meth:`~ftmgram.Client.send_dice`, :meth:`~ftmgram.Client.send_game`, :meth:`~ftmgram.Client.send_media_group`, :meth:`~ftmgram.Client.copy_media_group`, :meth:`~ftmgram.Client.send_inline_bot_result`, :meth:`~ftmgram.Client.send_cached_media`.
