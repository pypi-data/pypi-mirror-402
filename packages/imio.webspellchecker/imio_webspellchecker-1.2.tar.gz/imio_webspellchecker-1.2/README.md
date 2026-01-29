# imio.webspellchecker

[![Lint](https://github.com/IMIO/imio.webspellchecker/actions/workflows/lint.yml/badge.svg)](https://github.com/IMIO/imio.webspellchecker/actions/workflows/lint.yml) [![Tests](https://github.com/IMIO/imio.webspellchecker/actions/workflows/tests.yml/badge.svg)](https://github.com/IMIO/imio.webspellchecker/actions/workflows/tests.yml)
![Codecov](https://img.shields.io/codecov/c/github/imio/imio.webspellchecker)

This package provides seamless integration between Plone (versions 4.3, 5.2, and 6.0) and [Webspellchecker WProofReader](https://webspellchecker.com/wsc-proofreader/). It is designed to work out-of-the-box with multiple WYSIWYG editors used in Plone, enhancing the content creation process with advanced spellchecking capabilities.


## Features



- **Easy Integration**: Simplified setup process that integrates WProofReader with Plone's various versions without complicated configuration.
- **Support for Multiple Editors**: Compatible with popular WYSIWYG editors in Plone, ensuring a wide range of usability across different sites.
- **Real-time Spellchecking**: Offers real-time, in-context spelling and grammar checking to improve the quality of content on your Plone site.
- **Customizable Dictionaries**: Users can add custom words and terminologies to their dictionaries, making the tool adaptable to specific jargon and languages.
- **Multilingual Support**: Supports a variety of languages, catering to diverse user bases and content requirements.




## Installation

Install imio.webspellchecker by adding it to your buildout::

    [buildout]

    ...

    eggs =
        imio.webspellchecker


and then running ``bin/buildout``


## Compatibility
Plone versions: 4.3, 5.2, 6.0
Tested with Editors: TinyMCE, CKEditor4


## Contribute

- Issue Tracker: https://github.com/collective/imio.webspellchecker/issues
- Source Code: https://github.com/collective/imio.webspellchecker
- Documentation: https://docs.plone.org/foo/bar


## License

The project is licensed under the GPLv2.

## Disclaimer

This integration is not affiliated with or endorsed by the official Plone Foundation or Webspellchecker. All product names, logos, and brands are property of their respective owners.
