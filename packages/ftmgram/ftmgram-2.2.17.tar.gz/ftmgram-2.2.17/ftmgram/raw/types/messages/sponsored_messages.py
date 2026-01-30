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

from io import BytesIO
from typing import TYPE_CHECKING, Optional, Any

from ftmgram.raw.core.primitives import Int, Long, Int128, Int256, Bool, Bytes, String, Double, Vector
from ftmgram.raw.core import TLObject

if TYPE_CHECKING:
    from ftmgram import raw

# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #


class SponsoredMessages(TLObject):
    """Telegram API type.

    Constructor of :obj:`~ftmgram.raw.base.messages.SponsoredMessages`.

    Details:
        - Layer: ``221``
        - ID: ``FFDA656D``

    Parameters:
        messages (List of :obj:`SponsoredMessage <ftmgram.raw.base.SponsoredMessage>`):
            N/A

        chats (List of :obj:`Chat <ftmgram.raw.base.Chat>`):
            N/A

        users (List of :obj:`User <ftmgram.raw.base.User>`):
            N/A

        posts_between (``int`` ``32-bit``, *optional*):
            N/A

        start_delay (``int`` ``32-bit``, *optional*):
            N/A

        between_delay (``int`` ``32-bit``, *optional*):
            N/A

    Functions:
        This object can be returned by 1 function.

        .. currentmodule:: ftmgram.raw.functions

        .. autosummary::
            :nosignatures:

            messages.GetSponsoredMessages
    """

    __slots__: list[str] = ["messages", "chats", "users", "posts_between", "start_delay", "between_delay"]

    ID = 0xffda656d
    QUALNAME = "types.messages.SponsoredMessages"

    def __init__(self, *, messages: list["raw.base.SponsoredMessage"], chats: list["raw.base.Chat"], users: list["raw.base.User"], posts_between: Optional[int] = None, start_delay: Optional[int] = None, between_delay: Optional[int] = None) -> None:
        self.messages = messages  # Vector<SponsoredMessage>
        self.chats = chats  # Vector<Chat>
        self.users = users  # Vector<User>
        self.posts_between = posts_between  # flags.0?int
        self.start_delay = start_delay  # flags.1?int
        self.between_delay = between_delay  # flags.2?int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SponsoredMessages":
        
        flags = Int.read(b)
        
        posts_between = Int.read(b) if flags & (1 << 0) else None
        start_delay = Int.read(b) if flags & (1 << 1) else None
        between_delay = Int.read(b) if flags & (1 << 2) else None
        messages = TLObject.read(b)
        
        chats = TLObject.read(b)
        
        users = TLObject.read(b)
        
        return SponsoredMessages(messages=messages, chats=chats, users=users, posts_between=posts_between, start_delay=start_delay, between_delay=between_delay)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.posts_between is not None else 0
        flags |= (1 << 1) if self.start_delay is not None else 0
        flags |= (1 << 2) if self.between_delay is not None else 0
        b.write(Int(flags))
        
        if self.posts_between is not None:
            b.write(Int(self.posts_between))
        
        if self.start_delay is not None:
            b.write(Int(self.start_delay))
        
        if self.between_delay is not None:
            b.write(Int(self.between_delay))
        
        b.write(Vector(self.messages))
        
        b.write(Vector(self.chats))
        
        b.write(Vector(self.users))
        
        return b.getvalue()
