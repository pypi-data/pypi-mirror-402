#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from typing import AsyncGenerator, Optional, List

import pyrogram
from pyrogram import types, raw, utils, enums
from pyrogram.errors import ChannelPrivate, PeerIdInvalid


class GetDialogs:
    async def get_dialogs(
        self: "pyrogram.Client",
        limit: int = 0
    ) -> Optional[AsyncGenerator["types.Dialog", None]]:
        """Get a user's dialogs sequentially.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            limit (``int``, *optional*):
                Limits the number of dialogs to be retrieved.
                By default, no limit is applied and all dialogs are returned.

        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Dialog` objects.

        Example:
            .. code-block:: python

                # Iterate through all dialogs
                async for dialog in app.get_dialogs():
                    print(dialog.chat.first_name or dialog.chat.title)
        """
        current = 0
        total = limit or (1 << 31) - 1
        limit = min(100, total)
        offset_date = 0
        offset_id = 0
        offset_peer = raw.types.InputPeerEmpty()

        while True:
            r = await self.invoke(
                raw.functions.messages.GetDialogs(
                    offset_date=offset_date,
                    offset_id=offset_id,
                    offset_peer=offset_peer,
                    limit=limit,
                    hash=0
                ),
                sleep_threshold=60
            )

            users = {i.id: i for i in r.users}
            chats = {i.id: i for i in r.chats}

            messages = {}

            for message in r.messages:
                if isinstance(message, raw.types.MessageEmpty):
                    continue

                chat_id = utils.get_peer_id(message.peer_id)
                try:
                    messages[chat_id] = await types.Message._parse(self, message, users, chats)
                except (ChannelPrivate, PeerIdInvalid):
                    continue

            dialogs = []

            for dialog in r.dialogs:
                if not isinstance(dialog, raw.types.Dialog):
                    continue

                dialogs.append(types.Dialog._parse(self, dialog, messages, users, chats))

            if not dialogs:
                return

            last = dialogs[-1]

            if last.top_message:
                offset_id = last.top_message.id
                offset_date = utils.datetime_to_timestamp(last.top_message.date)
            
            else:
                offset_id = 0
                offset_date = 0
            offset_peer = await self.resolve_peer(last.chat.id)

            for dialog in dialogs:
                yield dialog

                current += 1

                if current >= total:
                    return

    async def get_groups(self: "pyrogram.Client") -> List["types.Dialog"]:
        """Get all groups and supergroups from dialogs.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            ``List``: A list of :obj:`~pyrogram.types.Dialog` objects containing only groups and supergroups.

        Example:
            .. code-block:: python

                groups = await app.get_groups()
                for group in groups:
                    print(group.chat.title)
        """
        groups = []
        async for dialog in self.get_dialogs():
            if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                groups.append(dialog)
        return groups

    async def get_channels(self: "pyrogram.Client") -> List["types.Dialog"]:
        """Get all channels from dialogs.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            ``List``: A list of :obj:`~pyrogram.types.Dialog` objects containing only channels.

        Example:
            .. code-block:: python

                channels = await app.get_channels()
                for channel in channels:
                    print(channel.chat.title)
        """
        channels = []
        async for dialog in self.get_dialogs():
            if dialog.chat.type == enums.ChatType.CHANNEL:
                channels.append(dialog)
        return channels

    async def get_private_chats(self: "pyrogram.Client") -> List["types.Dialog"]:
        """Get all private chats (excluding bots and groups).

        .. include:: /_includes/usable-by/users.rst

        Returns:
            ``List``: A list of :obj:`~pyrogram.types.Dialog` objects containing only private chats.

        Example:
            .. code-block:: python

                users = await app.get_private_chats()
                for user in users:
                    print(user.chat.first_name)
        """
        privates = []
        async for dialog in self.get_dialogs():
            if dialog.chat.type == enums.ChatType.PRIVATE:
                privates.append(dialog)
        return privates

    async def get_bots(self: "pyrogram.Client") -> List["types.Dialog"]:
        """Get all bots from dialogs.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            ``List``: A list of :obj:`~pyrogram.types.Dialog` objects containing only bots.

        Example:
            .. code-block:: python

                bots = await app.get_bots()
                for bot in bots:
                    print(bot.chat.first_name)
        """
        bots = []
        async for dialog in self.get_dialogs():
            if dialog.chat.type == enums.ChatType.BOT:
                bots.append(dialog)
        return bots

    async def get_deleted_users(self: "pyrogram.Client") -> List["types.Dialog"]:
        """Get all deleted accounts (Deleted Account) from dialogs.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            ``List``: A list of :obj:`~pyrogram.types.Dialog` objects containing only deleted accounts.

        Example:
            .. code-block:: python

                deleted = await app.get_deleted_users()
                for acc in deleted:
                    print(acc.chat.id)
        """
        deleted = []
        async for dialog in self.get_dialogs():
            if dialog.chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
                if dialog.chat.first_name == "Deleted Account" or getattr(dialog.chat, "is_deleted", False):
                    deleted.append(dialog)
        return deleted