# lldap-py

Python client library for managing LLDAP servers  [lldap/lldap](https://github.com/lldap/lldap)

## Usage

This package provides a Python interface to interact with LLDAP servers for user and group management. The idea is that it would be used in an onboarding/offboarding automation script and make similar automation tasks easier.

## Requirements
- Python 3.8+
- requests
- ldap3
- toml
- click

## TODO
- Maybe improve error handling and passing of graphql errors to the user.
- Add more examples and documentation.
- Check coverage of tests
- Add support for direct LDAP operations alongside GraphQL(Mainly for password management, to be used for initial random password generation).
- Test against https (and ldaps connections for above point).
- Add support for costum user and group attributes.

## Credit
This project is heavely inspired by and uses alot of code from [Zepmann/lldap-cli](https://github.com/Zepmann/lldap-cli) and [JaidenW/LLDAP-Discord](https://github.com/JaidenW/LLDAP-Discord)


## License

MIT