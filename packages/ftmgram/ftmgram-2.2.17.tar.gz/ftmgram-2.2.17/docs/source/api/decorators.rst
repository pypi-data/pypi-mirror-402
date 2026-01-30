Decorators
==========

Decorators are able to register callback functions for handling updates in a much easier and cleaner way compared to
:doc:`Handlers <handlers>`; they do so by instantiating the correct handler and calling
:meth:`~ftmgram.Client.add_handler` automatically. All you need to do is adding the decorators on top of your
functions.

.. code-block:: python

    from ftmgram import Client

    app = Client("my_account")


    @app.on_message()
    def log(client, message):
        print(message)


    app.run()


-----

.. currentmodule:: ftmgram

Index
-----

.. hlist::
    :columns: 3

    - :meth:`~Client.on_message`
    - :meth:`~Client.on_edited_message`
    - :meth:`~Client.on_bot_business_connection`
    - :meth:`~Client.on_message_reaction_updated`
    - :meth:`~Client.on_message_reaction_count_updated`
    - :meth:`~Client.on_inline_query`
    - :meth:`~Client.on_chosen_inline_result`
    - :meth:`~Client.on_callback_query`
    - :meth:`~Client.on_shipping_query`
    - :meth:`~Client.on_pre_checkout_query`
    - :meth:`~Client.on_bot_purchased_paid_media`
    - :meth:`~Client.on_poll`

    - :meth:`~Client.on_chat_member_updated`
    - :meth:`~Client.on_chat_join_request`


    - :meth:`~Client.on_deleted_messages`
    - :meth:`~Client.on_user_status`
    - :meth:`~Client.on_disconnect`
    - :meth:`~Client.on_story`
    - :meth:`~Client.on_raw_update`

-----

Details
-------

.. Decorators
.. autodecorator:: ftmgram.Client.on_message()
.. autodecorator:: ftmgram.Client.on_edited_message()
.. autodecorator:: ftmgram.Client.on_bot_business_connection()
.. autodecorator:: ftmgram.Client.on_message_reaction_updated()
.. autodecorator:: ftmgram.Client.on_message_reaction_count_updated()
.. autodecorator:: ftmgram.Client.on_inline_query()
.. autodecorator:: ftmgram.Client.on_chosen_inline_result()
.. autodecorator:: ftmgram.Client.on_callback_query()
.. autodecorator:: ftmgram.Client.on_shipping_query()
.. autodecorator:: ftmgram.Client.on_pre_checkout_query()
.. autodecorator:: ftmgram.Client.on_bot_purchased_paid_media()
.. autodecorator:: ftmgram.Client.on_poll()

.. autodecorator:: ftmgram.Client.on_chat_member_updated()
.. autodecorator:: ftmgram.Client.on_chat_join_request()


.. autodecorator:: ftmgram.Client.on_deleted_messages()
.. autodecorator:: ftmgram.Client.on_user_status()
.. autodecorator:: ftmgram.Client.on_disconnect()
.. autodecorator:: ftmgram.Client.on_story()
.. autodecorator:: ftmgram.Client.on_raw_update()
