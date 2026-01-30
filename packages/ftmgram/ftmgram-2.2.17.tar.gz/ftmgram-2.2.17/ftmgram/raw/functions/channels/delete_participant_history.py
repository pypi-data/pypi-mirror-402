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


class DeleteParticipantHistory(TLObject["raw.base.messages.AffectedHistory"]):
    """Telegram API function.

    Details:
        - Layer: ``221``
        - ID: ``367544DB``

    Parameters:
        channel (:obj:`InputChannel <ftmgram.raw.base.InputChannel>`):
            N/A

        participant (:obj:`InputPeer <ftmgram.raw.base.InputPeer>`):
            N/A

    Returns:
        :obj:`messages.AffectedHistory <ftmgram.raw.base.messages.AffectedHistory>`
    """

    __slots__: list[str] = ["channel", "participant"]

    ID = 0x367544db
    QUALNAME = "functions.channels.DeleteParticipantHistory"

    def __init__(self, *, channel: "raw.base.InputChannel", participant: "raw.base.InputPeer") -> None:
        self.channel = channel  # InputChannel
        self.participant = participant  # InputPeer

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "DeleteParticipantHistory":
        # No flags
        
        channel = TLObject.read(b)
        
        participant = TLObject.read(b)
        
        return DeleteParticipantHistory(channel=channel, participant=participant)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.channel.write())
        
        b.write(self.participant.write())
        
        return b.getvalue()
