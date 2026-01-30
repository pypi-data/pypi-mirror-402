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


class ConnectedBots(TLObject):
    """Telegram API type.

    Constructor of :obj:`~ftmgram.raw.base.account.ConnectedBots`.

    Details:
        - Layer: ``221``
        - ID: ``17D7F87B``

    Parameters:
        connected_bots (List of :obj:`ConnectedBot <ftmgram.raw.base.ConnectedBot>`):
            N/A

        users (List of :obj:`User <ftmgram.raw.base.User>`):
            N/A

    Functions:
        This object can be returned by 1 function.

        .. currentmodule:: ftmgram.raw.functions

        .. autosummary::
            :nosignatures:

            account.GetConnectedBots
    """

    __slots__: list[str] = ["connected_bots", "users"]

    ID = 0x17d7f87b
    QUALNAME = "types.account.ConnectedBots"

    def __init__(self, *, connected_bots: list["raw.base.ConnectedBot"], users: list["raw.base.User"]) -> None:
        self.connected_bots = connected_bots  # Vector<ConnectedBot>
        self.users = users  # Vector<User>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "ConnectedBots":
        # No flags
        
        connected_bots = TLObject.read(b)
        
        users = TLObject.read(b)
        
        return ConnectedBots(connected_bots=connected_bots, users=users)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Vector(self.connected_bots))
        
        b.write(Vector(self.users))
        
        return b.getvalue()
