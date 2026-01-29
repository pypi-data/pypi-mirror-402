# homeassistant_enocean
This is a wrapper library to integrate the [EnOcean](https://www.enocean.com/) protocol into [Home Assistant](https://www.home-assistant.io).


## Usage
This library is specifically written for Home Assistant's [EnOcean integration](https://www.home-assistant.io/integrations/enocean/). You can therefore best see how to use it by viewing its [source code on GitHub](https://github.com/henningkerstan/home-assistant-core/tree/enocean-options-flow). The library follows these [rules](https://developers.home-assistant.io/docs/api_lib_index).

## Development
After cloning this repository, execute the provided [scripts/setup.sh](scripts/setup.sh) to set up the development environment.

## Dependencies
This library only has one dependency, namely

- [enocean4ha](https://github.com/topic2k/enocean4ha/tree) in version 0.71.0, which is MIT-licensed.

The reason for using this library instead of the previously used [enocean](https://github.com/kipe/enocean) library is a more extended set of supported EnOcean Equipment Profiles (EEP).

## Copyright & license
Copyright 2026 Henning Kerstan

Licensed under the Apache License, Version 2.0 (the "License"). See [LICENSE](./LICENSE) file for details.

