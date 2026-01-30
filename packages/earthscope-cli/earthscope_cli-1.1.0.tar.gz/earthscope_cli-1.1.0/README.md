# EarthScope CLI

A CLI for interacting with EarthScope's APIs

## Getting Started

### Requirements

To use the CLI you must have:

- Registered an account with Earthscope ([sign up now](https://earthscope.org/user/login)). See [here](https://www.earthscope.org/data/authentication) for more information
- Python >= 3.9

### Installation

Install from PyPI

```shell
pip install earthscope-cli
```

### Usage

A new `es` command is available in your terminal. Use `--help` with any command to explore commands and options.

```shell
es --help
es user --help
```

#### Login to your EarthScope account

```shell
es login
```

This will open your browser to a confirmation page with the same code shown on your command line.
If you are on a device that does not have a web browser, you can copy the displayed url in a browser on another device (personal computer, mobile device, etc...) and complete the confirmation there.

The `es login` command will save your token locally. If this token is deleted, you will need to re-authenticate (login) to retrieve your token again.

#### Get your access token

```shell
es user get-access-token
```

The `get-access-token` command will display your access token. If your access token is close to expiration or expired,
the default behavior is to automatically refresh your token.

If you want to manually refresh your token:

```shell
es user refresh-access-token
```

Never share your tokens. If you think your token has been compromised, please revoke your refresh token and re-authenticate (login):

```shell
es user revoke-refresh-token
es login
```

#### Get your user profile

```shell
es user get-profile
```

## Documentation

For detailed usage examples, authentication guides, and advanced features, see the [full documentation](https://docs.earthscope.org/projects/CLI).

## EarthScope SDK

If you would like to use EarthScope APIs from python, please use the [earthscope-sdk](https://gitlab.com/earthscope/public/earthscope-sdk/) directly.

## FAQ/troubleshooting

- **How long does my access token last?**
  - Your access token lasts 24 hours. Your refresh token can be used to refresh your access token.
- **How long does my refresh token last?**
  - Your refresh token will never expire - unless you are inactive (do not use it) for one year.
    If it does expire, you will need to re-authenticate to get a new access and refresh token.
- **What is a refresh token and how does the CLI use it?**
  - A refresh token is a special token that is used to renew your access token without you needing to log in again.
    The refresh token is obtained from your access token, and using the `es user get-access-token` command will automatically
    renew your access token if it is close to expiration. You can 'manually' refresh your access token by using the command `es user refresh-access-token`.
    If your access token is compromised, you can revoke your refresh token using `es user revoke-refresh-token`. Once your access token expires,
    it can no longer be renewed and you will need to re-login.
- **Should I hard-code my access token into my script?**
  - No. We recommend you use the cli commands to retrieve your access tokens in your scripts.
    This way your access token will not be compromised by anyone viewing your script.
    The access token only lasts 24 hours and cannot be used afterwards unless refreshed.
