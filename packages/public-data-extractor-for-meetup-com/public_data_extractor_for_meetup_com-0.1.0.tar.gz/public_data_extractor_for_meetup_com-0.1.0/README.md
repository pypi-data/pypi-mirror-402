# Public Data Extractor for Meetup.com

Do you organise an event on meetup.com? Would you like basic details of the event to be available as Open Data for reuse elsewhere?

(Public details only - this does NOT extract any information about the people attending your events.)

This is an unofficial tool not endorsed by Meetup.com - use at your own risk!

## Install

```commandline
pip install public-data-extractor-for-meetup-com
```

## Configure

Log into https://www.meetup.com/ and go to "View Profile".
You'll be at a URL like: https://www.meetup.com/members/123456789/
That number is your member ID.
Set it as the environmental Variable `MEETUP_COM_AUTHORIZED_MEMBER_ID`

Go to https://www.meetup.com/graphql/oauth/list/ and create a new API client.

Set the Client Key as the environmental Variable `MEETUP_COM_YOUR_CLIENT_KEY`

Create a new signing key for the client (Make sure you save the private certificate as you won't see it again!)
Set it as the environmental Variable `MEETUP_COM_PRIVATE_SIGNING_KEY`

## Run

Run:

```commandline
python -m publicdataextractorformeetupcom extractgroup your_group_slug output_directory
```

The output directory will then hold files with public information that you can publish.

## For Developers

The GraphQL Playground at https://www.meetup.com/graphql/playground/#graphQl-playground is very handy to explore.

