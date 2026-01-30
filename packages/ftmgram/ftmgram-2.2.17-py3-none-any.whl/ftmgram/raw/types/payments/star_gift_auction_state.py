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


class StarGiftAuctionState(TLObject):
    """Telegram API type.

    Constructor of :obj:`~ftmgram.raw.base.payments.StarGiftAuctionState`.

    Details:
        - Layer: ``221``
        - ID: ``6B39F4EC``

    Parameters:
        gift (:obj:`StarGift <ftmgram.raw.base.StarGift>`):
            N/A

        state (:obj:`StarGiftAuctionState <ftmgram.raw.base.StarGiftAuctionState>`):
            N/A

        user_state (:obj:`StarGiftAuctionUserState <ftmgram.raw.base.StarGiftAuctionUserState>`):
            N/A

        timeout (``int`` ``32-bit``):
            N/A

        users (List of :obj:`User <ftmgram.raw.base.User>`):
            N/A

        chats (List of :obj:`Chat <ftmgram.raw.base.Chat>`):
            N/A

    Functions:
        This object can be returned by 1 function.

        .. currentmodule:: ftmgram.raw.functions

        .. autosummary::
            :nosignatures:

            payments.GetStarGiftAuctionState
    """

    __slots__: list[str] = ["gift", "state", "user_state", "timeout", "users", "chats"]

    ID = 0x6b39f4ec
    QUALNAME = "types.payments.StarGiftAuctionState"

    def __init__(self, *, gift: "raw.base.StarGift", state: "raw.base.StarGiftAuctionState", user_state: "raw.base.StarGiftAuctionUserState", timeout: int, users: list["raw.base.User"], chats: list["raw.base.Chat"]) -> None:
        self.gift = gift  # StarGift
        self.state = state  # StarGiftAuctionState
        self.user_state = user_state  # StarGiftAuctionUserState
        self.timeout = timeout  # int
        self.users = users  # Vector<User>
        self.chats = chats  # Vector<Chat>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "StarGiftAuctionState":
        # No flags
        
        gift = TLObject.read(b)
        
        state = TLObject.read(b)
        
        user_state = TLObject.read(b)
        
        timeout = Int.read(b)
        
        users = TLObject.read(b)
        
        chats = TLObject.read(b)
        
        return StarGiftAuctionState(gift=gift, state=state, user_state=user_state, timeout=timeout, users=users, chats=chats)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.gift.write())
        
        b.write(self.state.write())
        
        b.write(self.user_state.write())
        
        b.write(Int(self.timeout))
        
        b.write(Vector(self.users))
        
        b.write(Vector(self.chats))
        
        return b.getvalue()
