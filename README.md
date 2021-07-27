# slashpass [Slack Server]

[![Build Status](https://travis-ci.org/talpor/password-scale.svg?branch=master)](https://travis-ci.org/talpor/password-scale)

slashpass is a Slack command to manage shared passwords between the members of a channel in Slack.

This project was build focused in establishing a communication where the trustness between parties is not required, using the asymmetric algorithm RSA to share encrypted information point to point and where the only participant allowed to read the stored passwords is the _Password Server_, who is different and independent for each client.

## Commands

- `/pass` or `/pass list` list the available passwords in the channel.
- `/pass <secret>` or `/pass show <secret>` retrieve a one time use link with the secret content, this link expires in 15 minutes.
- `/pass insert <secret>` retrieve a link with an editor to create a secret, this link expires in 15 minutes.
- `/pass remove <secret>` make unreachable the secret, to complete deletion in necessary doing it manually from the s3 password storage.
- `/pass configure <password_server_url>` this is the command used for the initial setup, it is only necessary to execute it once.

[![button](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/authorize?client_id=2554558892.385841792964&scope=commands)

### Requirements

#### Installed software
- pipenv
- docker/docker-compose (optional)

## Instalation

- Install requirements `pipenv sync`
- Create _.env_ file based on _example.env
- Create the database specified in _DATABASE_URL_ and create the scheme by doing `import server; server.db.create_all()` from a python shell in the enviroment (pipenv run python)
- Run the server using the command `pipenv run python .` for development or `pipenv run gunicorn --bind 0.0.0.0:8000 wsgi` for production

## Running using docker

- Create _.env_ file based on _example.env_
- Run `docker-compose up`

### Environment variables table

| Key | Description |
| --- | ----------- |
| BIP39 | Mnemonic code for generating deterministic keys, specification: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki |
| DEMO_SERVER | URL of the password storage server, this URL is used to setup the command for testing purposes |
| DATABASE_URL | Database URL where is stored the password storage server addresses of each client |
| SENTRY_DSN | Configuration required by the Sentry SDKs |
| SLACK_SERVER | URL of this server, it is used by the command to show the insert password editor URL |
| SLACK_CLIENT_ID | Slack Client ID |
| SLACK_CLIENT_SECRET | Slack APP Secret |
| VERIFICATION_TOKEN | Slack Verification Token |
