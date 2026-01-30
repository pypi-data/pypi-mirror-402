<p align="center">
    <a href="https://github.com/TelegramPlayground/ftmgram">
        <img src="https://raw.githubusercontent.com/ftmgram/artwork/master/artwork/ftmgram-logo.png" alt="Ftmgram" width="128">
    </a>
    <br>
    <b>Telegram MTProto API Framework for Python</b>
    <br>
    <a href="https://telegramplayground.github.io/ftmgram/">
        Documentation
    </a>
    •
    <a href="https://telegramplayground.github.io/ftmgram/releases/changes-in-this-fork.html">
        Releases
    </a>
    •
    <a href="https://FtmdevTGFork.t.me/2">
        News
    </a>
</p>

## Ftmgram

> Elegant, modern and asynchronous Telegram MTProto API framework in Python for users and bots

``` python
from ftmgram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Ftmgram!")


app.run()
```

**Ftmgram** is a modern, elegant and asynchronous [MTProto API](https://telegramplayground.github.io/ftmgram/topics/mtproto-vs-botapi)
framework. It enables you to easily interact with the main Telegram API through a user account (custom client) or a bot
identity (bot API alternative) using Python.

### Key Features

- **Ready**: Install Ftmgram with pip and start building your applications right away.
- **Easy**: Makes the Telegram API simple and intuitive, while still allowing advanced usages.
- **Elegant**: Low-level details are abstracted and re-presented in a more convenient way.
- **Fast**: Boosted up by [TgCrypto](https://github.com/TelegramPlayGround/ftmgram-tgcrypto), a high-performance cryptography library written in C.  
- **Type-hinted**: Types and methods are all type-hinted, enabling excellent editor support.
- **Async**: Fully asynchronous (also usable synchronously if wanted, for convenience).
- **Powerful**: Full access to Telegram's API to execute any official client action and more.

### Installing

``` bash
pip3 install ftmdevtgfork
```

### Resources

- Check out [the docs](https://telegramplayground.github.io/ftmgram) to learn more about Ftmgram, get started right
away and discover more in-depth material for building your client applications.
- Join the official channel at [FtmdevTGFork](https://FtmdevTGFork.t.me/2) and stay tuned for news, updates and announcements.
