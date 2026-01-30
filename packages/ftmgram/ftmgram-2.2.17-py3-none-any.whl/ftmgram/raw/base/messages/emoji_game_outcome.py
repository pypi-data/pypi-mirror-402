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

# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #

from typing import TYPE_CHECKING, Union
from ftmgram import raw
from ftmgram.raw.core import BaseTypeMeta


if TYPE_CHECKING:
    EmojiGameOutcome = Union[raw.types.messages.EmojiGameOutcome]
else:
    # noinspection PyRedeclaration
    class EmojiGameOutcome(metaclass=BaseTypeMeta):  # type: ignore
        """Telegram API base type.

    Constructors:
        This base type has 1 constructor available.

        .. currentmodule:: ftmgram.raw.types

        .. autosummary::
            :nosignatures:

            messages.EmojiGameOutcome
        """

        QUALNAME = "ftmgram.raw.base.messages.EmojiGameOutcome"
        __union_types__ = Union[raw.types.messages.EmojiGameOutcome]

        def __init__(self):
            raise TypeError(
                "Base types can only be used for type checking purposes: "
                "you tried to use a base type instance as argument, "
                "but you need to instantiate one of its constructors instead. "
                "More info: https://telegramplayground.github.io/ftmgram/telegram/base/emoji-game-outcome"
            )
