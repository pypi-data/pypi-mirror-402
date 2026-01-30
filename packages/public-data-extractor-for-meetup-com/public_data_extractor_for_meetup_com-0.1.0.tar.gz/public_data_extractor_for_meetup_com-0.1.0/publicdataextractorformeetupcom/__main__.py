import argparse
import os

from .worker import Worker


def main():

    meetup_com_authorized_member_id = os.getenv("MEETUP_COM_AUTHORIZED_MEMBER_ID")
    meetup_com_your_client_key = os.getenv("MEETUP_COM_YOUR_CLIENT_KEY")
    meetup_com_private_signing_key = os.getenv("MEETUP_COM_PRIVATE_SIGNING_KEY")

    if (
        not meetup_com_authorized_member_id
        or not meetup_com_your_client_key
        or not meetup_com_private_signing_key
    ):
        raise Exception("Must specify env vars")

    # Now check options ...
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser_name")

    extract_group_parser = subparsers.add_parser("extractgroup")
    extract_group_parser.add_argument("group_url_name")
    extract_group_parser.add_argument("out_directory")

    args = parser.parse_args()

    if args.subparser_name == "extractgroup":
        worker = Worker(
            meetup_com_authorized_member_id,
            meetup_com_your_client_key,
            meetup_com_private_signing_key,
        )
        worker.extract_group(args.group_url_name, args.out_directory)


if __name__ == "__main__":
    main()
