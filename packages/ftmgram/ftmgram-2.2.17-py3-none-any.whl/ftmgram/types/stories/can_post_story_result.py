#  Ftmgram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present <https://github.com/TelegramPlayGround>
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


from ..object import Object


class CanPostStoryResult(Object):
    """This object represents result of checking whether the current user can post a story on behalf of the specific chat.

    Currently, it can be one of:

    - :obj:`~ftmgram.types.CanPostStoryResultOk`
    - :obj:`~ftmgram.types.CanPostStoryResultPremiumNeeded`
    - :obj:`~ftmgram.types.CanPostStoryResultBoostNeeded`
    - :obj:`~ftmgram.types.CanPostStoryResultActiveStoryLimitExceeded`
    - :obj:`~ftmgram.types.CanPostStoryResultWeeklyLimitExceeded`
    - :obj:`~ftmgram.types.CanPostStoryResultMonthlyLimitExceeded`
    """

    def __init__(self):
        super().__init__()
