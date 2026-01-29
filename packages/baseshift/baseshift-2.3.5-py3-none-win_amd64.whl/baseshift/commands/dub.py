import json
import logging
from time import sleep

from .. import utils
from .. import client  # v2 API only (JWT auth required)
from .base import BaseCommand

logger = logging.getLogger(__name__)


class DubCommand(BaseCommand):
    def add_arguments(self, parser):
        dub_subparsers = parser.add_subparsers(dest="action", required=True)

        parser_snapshot = dub_subparsers.add_parser("snapshot", help="Snapshot a dub")
        parser_snapshot.add_argument(
            "--dubUuid",
            required=False,
            default=None,
            type=utils.regex_type_uuid,
            help="Uuid of Dub (CLI > BASESHIFT_DUB_UUID > config)",
        )
        parser_snapshot.add_argument(
            "--wait", action="store_true", help="Wait for snapshot to complete"
        )

        parser_subset = dub_subparsers.add_parser("subset", help="Subset a dub")
        parser_subset.add_argument(
            "--dubUuid",
            required=False,
            default=None,
            type=utils.regex_type_uuid,
            help="Uuid of Dub (CLI > BASESHIFT_DUB_UUID > config)",
        )
        parser_subset.add_argument(
            "--config", required=True, help="Path to subset config file"
        )

        parser_status = dub_subparsers.add_parser("status", help="Get snapshot status")
        parser_status.add_argument(
            "--snapshotUuid",
            required=True,
            type=utils.regex_type_uuid,
            help="Uuid of Snapshot",
        )
        parser_status.add_argument(
            "--orgToken",
            required=False,
            default=None,
            type=utils.regex_type_uuid,
            help="Organization Token (CLI > BASESHIFT_ORG_TOKEN > config)",
        )

        parser_configure_source = dub_subparsers.add_parser(
            "configure-source",
            help="Configure the source database connection for the proxy"
        )
        parser_configure_source.add_argument(
            "--dubUuid",
            required=False,
            default=None,
            type=utils.regex_type_uuid,
            help="Uuid of Dub (CLI > BASESHIFT_DUB_UUID > config)",
        )
        parser_configure_source.add_argument(
            "--host",
            required=False,
            default=None,
            help="New database host address",
        )
        parser_configure_source.add_argument(
            "--port",
            required=False,
            default=None,
            help="New database port",
        )
        parser_configure_source.add_argument(
            "--username",
            required=False,
            default=None,
            help="New database username",
        )
        parser_configure_source.add_argument(
            "--password",
            required=False,
            default=None,
            help="New database password",
        )

    def run(self, args, server):
        if args.action == "snapshot":
            self.snapshot(args, server)
        elif args.action == "subset":
            self.subset(args, server)
        elif args.action == "status":
            self.status(args, server)
        elif args.action == "configure-source":
            self.configure_source(args, server)

    def snapshot(self, args, server):
        try:
            dub_uuid = utils.get_config_value(
                args.dubUuid, "BASESHIFT_DUB_UUID", "dubUuid", required=True
            )
            if not utils.is_valid_uuid(dub_uuid):
                logger.error(f"Invalid Dub UUID format: {dub_uuid}")
                print(
                    f"Error: Invalid Dub UUID format: {dub_uuid}. Please check CLI, BASESHIFT_DUB_UUID, or config file."
                )
                return

        except ValueError as e:
            logger.error(f"Configuration error in snapshot: {e}")
            print(f"Error: {e}")
            return

        try:
            response = client.snapshot_api_sync(dub_uuid=dub_uuid, host=server)
            if response.status_code in [400, 500]:
                logger.error(
                    "Failed API call with status code: %s", response.status_code
                )
                logger.error(response.json())
                return
        except Exception as e:
            logger.exception("Error with sending post request:" + str(e))
            return
        try:
            snapshot_uuid = json.loads(json.dumps(json.loads(response.content)))
            print(f"Creating snapshot {snapshot_uuid}", flush=True)
            if args.wait is True:
                # Get org_token for status polling
                try:
                    org_token = utils.get_config_value(
                        None, "BASESHIFT_ORG_TOKEN", "orgToken", required=True
                    )
                except ValueError as e:
                    logger.error(f"Cannot poll status without org token: {e}")
                    print(f"Error: Cannot poll status without org token. Set BASESHIFT_ORG_TOKEN or add orgToken to config.")
                    return

                print("Waiting for creation to complete", end="", flush=True)
                snapshot_created = False
                while snapshot_created is False:
                    sleep(1)
                    print(".", end="", flush=True)
                    wait_response = client.snapshot_status_api_sync(
                        snapshot_uuid=snapshot_uuid, org_token=org_token, host=server
                    )
                    status_data = wait_response.json()
                    if status_data.get("state") == "READY":
                        snapshot_created = True
                    elif status_data.get("state") == "ERROR":
                        print(f"\nSnapshot creation failed: {status_data.get('msg')}")
                        return
                print(f"\nSnapshot {snapshot_uuid} created successfully")
        except Exception as e:
            logger.exception("Error creating snapshot" + str(e))

    def subset(self, args, server):
        try:
            dub_uuid = utils.get_config_value(
                args.dubUuid, "BASESHIFT_DUB_UUID", "dubUuid", required=True
            )
            if not utils.is_valid_uuid(dub_uuid):
                logger.error(f"Invalid Dub UUID format: {dub_uuid}")
                print(
                    f"Error: Invalid Dub UUID format: {dub_uuid}. Please check CLI, BASESHIFT_DUB_UUID, or config file."
                )
                return

        except ValueError as e:
            logger.error(f"Configuration error in subset: {e}")
            print(f"Error: {e}")
            return

        try:
            with open(args.config, "r") as config_file:
                config_data = json.load(config_file)
            response = client.subset_edit_api_sync(
                dub_uuid=dub_uuid,
                host=server,
                subset_config=json.dumps(config_data),
            )
            if response.status_code in [400, 500]:
                logger.error(
                    "Failed API call with status code: %s", response.status_code
                )
                logger.error(response.json())
                return
            print(response.json())
        except Exception as e:
            logger.exception("Error with sending post request:" + str(e))

    def status(self, args, server):
        try:
            snapshot_uuid = args.snapshotUuid
            if not utils.is_valid_uuid(snapshot_uuid):
                logger.error(f"Invalid Snapshot UUID format: {snapshot_uuid}")
                print(f"Error: Invalid Snapshot UUID format: {snapshot_uuid}")
                return
        except ValueError as e:
            logger.error(f"Configuration error in status: {e}")
            print(f"Error: {e}")
            return

        try:
            org_token = utils.get_config_value(
                args.orgToken, "BASESHIFT_ORG_TOKEN", "orgToken", required=True
            )
            if not utils.is_valid_uuid(org_token):
                logger.error(f"Invalid Organization Token format: {org_token}")
                print(
                    f"Error: Invalid Organization Token format: {org_token}. Please check CLI, BASESHIFT_ORG_TOKEN, or config file."
                )
                return
        except ValueError as e:
            logger.error(f"Configuration error in status: {e}")
            print(f"Error: {e}")
            return

        try:
            response = client.snapshot_status_api_sync(
                snapshot_uuid=snapshot_uuid, org_token=org_token, host=server
            )
            if response.status_code in [400, 403, 404, 500]:
                logger.error(
                    "Failed API call with status code: %s", response.status_code
                )
                logger.error(response.text)
                print(f"Error: {response.text}")
                return
            result = response.json()
            print(json.dumps(result, indent=2))
        except Exception as e:
            logger.exception("Error getting snapshot status: " + str(e))
            print(f"Error getting snapshot status: {e}")

    def configure_source(self, args, server):
        """Configure the source database connection for the proxy."""
        try:
            dub_uuid = utils.get_config_value(
                args.dubUuid, "BASESHIFT_DUB_UUID", "dubUuid", required=True
            )
            if not utils.is_valid_uuid(dub_uuid):
                logger.error(f"Invalid Dub UUID format: {dub_uuid}")
                print(
                    f"Error: Invalid Dub UUID format: {dub_uuid}. Please check CLI, BASESHIFT_DUB_UUID, or config file."
                )
                return

        except ValueError as e:
            logger.error(f"Configuration error in configure_source: {e}")
            print(f"Error: {e}")
            return

        # Check that at least one parameter is provided
        if not any([args.host, args.port, args.username, args.password]):
            print("Error: At least one of --host, --port, --username, or --password must be provided")
            return

        try:
            response = client.configure_source_api_sync(
                dub_uuid=dub_uuid,
                host=server,
                host_addr=args.host,
                port=args.port,
                username=args.username,
                password=args.password,
            )
            if response.status_code in [400, 403, 404, 500]:
                logger.error(
                    "Failed API call with status code: %s", response.status_code
                )
                result = response.json()
                error_msg = result.get("error", response.text)
                logger.error(error_msg)
                print(f"Error: {error_msg}")
                return

            result = response.json()
            if result.get("success"):
                print(f"Successfully configured source for dub {dub_uuid}")
                if result.get("message"):
                    print(result.get("message"))
            else:
                print(f"Failed to configure source: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.exception("Error configuring source: " + str(e))
            print(f"Error configuring source: {e}")
