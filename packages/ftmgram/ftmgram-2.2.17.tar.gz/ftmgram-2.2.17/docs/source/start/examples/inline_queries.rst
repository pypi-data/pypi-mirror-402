inline_queries
==============

This example shows how to handle inline queries.

Two results are generated when users invoke the bot inline mode, e.g.: @ftmgrambot hi.
It uses the :meth:`~ftmgram.Client.on_inline_query` decorator to register an :obj:`~ftmgram.handlers.InlineQueryHandler`.

.. include:: /_includes/usable-by/bots.rst

.. code-block:: python

    from ftmgram import Client
    from ftmgram.types import (InlineQueryResultArticle, InputTextMessageContent,
                                InlineKeyboardMarkup, InlineKeyboardButton)

    app = Client("my_bot", bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")


    @app.on_inline_query()
    async def answer(client, inline_query):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Installation",
                    input_message_content=InputTextMessageContent(
                        "Here's how to install **Ftmgram**"
                    ),
                    url="https://telegramplayground.github.io/ftmgram/intro/install",
                    description="How to install Ftmgram",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(
                                "Open website",
                                url="https://telegramplayground.github.io/ftmgram/intro/install"
                            )]
                        ]
                    )
                ),
                InlineQueryResultArticle(
                    title="Usage",
                    input_message_content=InputTextMessageContent(
                        "Here's how to use **Ftmgram**"
                    ),
                    url="https://telegramplayground.github.io/ftmgram/start/invoking",
                    description="How to use Ftmgram",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(
                                "Open website",
                                url="https://telegramplayground.github.io/ftmgram/start/invoking"
                            )]
                        ]
                    )
                )
            ],
            cache_time=1
        )


    app.run()  # Automatically start() and idle()