How to use webhooks?
====================

There is no webhook in Ftmgram, simply because there is no HTTP involved. However, a similar technique is
being used to make receiving updates efficient.

Ftmgram uses persistent connections via TCP sockets to interact with the server and instead of actively asking for
updates every time (polling), Ftmgram will sit down and wait for the server to send updates by itself the very moment
they are available (server push).
