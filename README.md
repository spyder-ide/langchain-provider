# kite-provider

## Project Info

[![Project License](https://img.shields.io/github/license/spyder-ide/kite-provider)](./LICENSE)
[![Join the chat at https://gitter.im/spyder-ide/public](https://badges.gitter.im/spyder-ide/spyder.svg)](https://gitter.im/spyder-ide/public)
[![OpenCollective Backers](https://opencollective.com/spyder/backers/badge.svg?color=blue)](#backers)
[![OpenCollective Sponsors](https://opencollective.com/spyder/sponsors/badge.svg?color=blue)](#sponsors)

## Build status

![Linux tests](https://github.com/spyder-ide/kite-provider/workflows/Linux%20tests/badge.svg)
![Macos tests](https://github.com/spyder-ide/kite-provider/workflows/Macos%20tests/badge.svg)
![Window tests](https://github.com/spyder-ide/kite-provider/workflows/Windows%20tests/badge.svg)

----

# Overview


## Installation

To use this completions provider you will need to install Spyder 6 (at least 6.0.0a3) and install Kite (latest executable available from the [Kite release page](https://github.com/kiteco/kiteco-public/releases/tag/2021-06-10))

To install the provider package, you can use `pip` with something like:

    pip install git+https://github.com/spyder-ide/kite-provider.git@v0.2.0

**Note:** Support for Kite is not available anymore. The code here is meant to be used for demonstration proposes only, using it could brake your Spyder setup or make Spyder unstable! Use/install at your own risk.

## Common issues

From our testing, there are some common errors that can occur when using the Kite provider on Windows (or more specifically, when using as files End-Of-Line/EOL the `CRLF` value). Here a list of some of them:

* [Can't get results from Kite inside the onboarding file (`kite_tutorial.py`) or a temporary file](https://github.com/spyder-ide/kite-provider/issues/4)
* [When accepting Kite completions the text gets partially overwritten](https://github.com/spyder-ide/kite-provider/issues/3)

The errors above can be avoided by changing the files EOL from `CRLF` to `LF`. You can do this change inside Spyder via the `Source` menu: `Source > Convert end-of-line characters` and selecting the option `LF (Unix)`:

![EOL_conversion_for_file](https://github.com/spyder-ide/kite-provider/assets/42411448/d5142856-0d18-410f-b739-196d704ab648)

Besides the option above, you can also use the Spyder `Convert end-of-line characters to the following on save` option. Inside Spyder go to `Preferences > Editor > Advanced settings > End-of-line characters` and enable the option:

![EOL_conversion_on_save](https://github.com/spyder-ide/kite-provider/assets/16781833/cd856b9e-57cb-41a4-ab7b-986b90993f0a)

## Dependencies

This project depends on [Spyder](https://github.com/spyder-ide/spyder).

## Changelog

Visit our [CHANGELOG](CHANGELOG.md) file to know more about our new features and improvements.

## Development and contribution

Everyone is welcome to contribute!

## Sponsors

Spyder is funded thanks to the generous support of

[![Quansight](https://user-images.githubusercontent.com/16781833/142477716-53152d43-99a0-470c-a70b-c04bbfa97dd4.png)](https://www.quansight.com/)[![Numfocus](https://i2.wp.com/numfocus.org/wp-content/uploads/2017/07/NumFocus_LRG.png?fit=320%2C148&ssl=1)](https://numfocus.org/)

and the donations we have received from our users around the world through [Open Collective](https://opencollective.com/spyder/):

[![Sponsors](https://opencollective.com/spyder/sponsors.svg)](https://opencollective.com/spyder#support)

## More information

[Main Website](https://www.spyder-ide.org/)

[Download Spyder (with Anaconda)](https://www.anaconda.com/download/)

[Online Documentation](https://docs.spyder-ide.org/)

[Spyder Github](https://github.com/spyder-ide/spyder)

[Troubleshooting Guide and FAQ](
https://github.com/spyder-ide/spyder/wiki/Troubleshooting-Guide-and-FAQ)

[Development Wiki](https://github.com/spyder-ide/spyder/wiki/Dev:-Index)

[Gitter Chatroom](https://gitter.im/spyder-ide/public)

[Google Group](https://groups.google.com/group/spyderlib)

[@Spyder_IDE on Twitter](https://twitter.com/spyder_ide)

[@SpyderIDE on Facebook](https://www.facebook.com/SpyderIDE/)

[Support Spyder on OpenCollective](https://opencollective.com/spyder/)
