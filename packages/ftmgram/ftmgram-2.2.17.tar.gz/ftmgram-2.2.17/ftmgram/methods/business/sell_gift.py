#  Ftmgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Ftmgram.
#
#  Ftmgram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Ftmgram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Ftmgram.  If not, see <http://www.gnu.org/licenses/>.


from typing import Union

import ftmgram
from ftmgram import raw


class SellGift:
    async def sell_gift(
        self: "ftmgram.Client",
        message_id: int
    ) -> bool:
        """Sells a gift received by the current user for Telegram Stars.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            message_id (``int``):
                Unique identifier of the message with the gift in the chat with the user.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                # Convert gift
                app.sell_gift(message_id=123)

        """

        return await self.invoke(
            raw.functions.payments.ConvertStarGift(
                msg_id=message_id
            )
        )
