# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2020-04-05
### Added
- Configuration file
- Logging to file
- Dockerfile
### Changed
- Renamed SshBasedConnection to Connection
- Connection now accepts any instance of Transport
- -c key is now shorthand for --config, not --chat-id
### Fixed
- Send replies to correct chat id, not to owner

## 0.1.0 - 2020-03-26
### Added
- This changelog
- Basic readme
- License
- Initial implementation of ssh transport
- Basic listener

[Unreleased]: https://gitlab.com/personal-assistant-bot/infrastructure/stomp-over-ssh/compare/v0.2.0...master
[0.2.0]: https://gitlab.com/personal-assistant-bot/infrastructure/stomp-over-ssh/compare/v0.1.0...v0.2.0
