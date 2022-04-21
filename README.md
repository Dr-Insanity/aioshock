AIOSHOCK
=======

An **Asynchronous** version of Python REST API wrapper for the [TShock](https://tshock.co/xf/) RESTful API exposed by [TShock](https://tshock.co/xf/) servers for Terraria.
There are no docs for this yet. However, pretty much all functions have to be awaited. I chose not to preserve old syntax. `get_` --> `fetch_`.

There's no PIP for this module.


TShock
======

[TShock](https://tshock.co/xf/) is a plugin for the TerrariaServer-API which supplies varied conveniences for Terraria server owners. TShock is typically used in conjunction with several other plugins. TShock may be found [here](https://tshock.co/xf/)
They have a discord server on that website. The link for their discord server can be found there.

Issues?
=======

Create a PR [here](https://github.com/Dr-Insanity/aioshock/pulls), please. And I take a look at it.


Contribution
============

No, thanks. But by all means, you can fork it, do with this library as you wish. No license is put on this. Unless the original author updated their library with a license.


Disclaimer
==========

PyShock is not made by me. I only made an async version of it, published it, so that others wouldn't have to make it async for themselves.
I made this for a discord bot, which are asynchronous. Don't put blocking (synchronous) code in an async function 💀.
