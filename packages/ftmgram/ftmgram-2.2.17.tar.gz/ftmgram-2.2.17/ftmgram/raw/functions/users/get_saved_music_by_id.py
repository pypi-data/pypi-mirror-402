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


class GetSavedMusicByID(TLObject["raw.base.users.SavedMusic"]):
    """Telegram API function.

    Details:
        - Layer: ``221``
        - ID: ``7573A4E9``

    Parameters:
        id (:obj:`InputUser <ftmgram.raw.base.InputUser>`):
            N/A

        documents (List of :obj:`InputDocument <ftmgram.raw.base.InputDocument>`):
            N/A

    Returns:
        :obj:`users.SavedMusic <ftmgram.raw.base.users.SavedMusic>`
    """

    __slots__: list[str] = ["id", "documents"]

    ID = 0x7573a4e9
    QUALNAME = "functions.users.GetSavedMusicByID"

    def __init__(self, *, id: "raw.base.InputUser", documents: list["raw.base.InputDocument"]) -> None:
        self.id = id  # InputUser
        self.documents = documents  # Vector<InputDocument>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "GetSavedMusicByID":
        # No flags
        
        id = TLObject.read(b)
        
        documents = TLObject.read(b)
        
        return GetSavedMusicByID(id=id, documents=documents)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.id.write())
        
        b.write(Vector(self.documents))
        
        return b.getvalue()
