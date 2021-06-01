import logging
import json

import metagov.core.plugin_decorators as Registry
import requests
from metagov.core.errors import PluginErrorInternal
from metagov.core.models import Plugin

logger = logging.getLogger(__name__)

"""

App Manifest
https://app.slack.com/app-settings/TMQ3PKXT9/A01HT9U26NT/app-manifest


1. Upload the App Manifest
2. Copy the Client ID/Secret/etc onto the server

"""


@Registry.plugin
class Slack(Plugin):
    name = "slack"
    config_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            # these are set automatically if using the oauth flow
            "team_id": {"description": "Slack Team ID", "type": "string"},
            "team_name": {"description": "Slack Team Name", "type": "string"},
            "bot_token": {"description": "Bot Token", "type": "string"},
            "bot_user_id": {"description": "Bot User ID", "type": "string"},
        },
    }

    class Meta:
        proxy = True

    def initialize(self):
        logger.info(f"Initializing Slack Plugin for {self.community}")
        logger.info(self.config["team_name"])

    # PLATFORM ACTIONS:
    # TODO: post message
    # TODO: rename conversation
    # TODO: join conversation
    # TODO: pin message
    # TODO: schedule message
    # TODO: kick conversation
    # https://api.slack.com/bot-users#bot_methods

    @Registry.webhook_receiver(event_schemas=[])
    def receive_event(self, request):
        json_data = json.loads(request.body)
        if json_data["type"] != "event_callback":
            return

        # TODO: move this check to a separate handler for routing incoming events to the correct plugin instance
        if json_data["team_id"] != self.config["team_id"]:
            return

        # https://api.slack.com/apis/connections/events-api#the-events-api__receiving-events__events-dispatched-as-json

        # authorizations = json_data["authorizations"]
        # event_context = json_data["event_context"]
        # A unique identifier for this specific event, globally unique across all workspaces.
        event_id = json_data["event_id"]
        # The epoch timestamp in seconds indicating when this event was dispatched.
        event_time = json_data["event_time"]

        event = json_data["event"]

        # https://api.slack.com/events
        event_type = event["type"]
        logger.info(f"Received event {event_type}")
        logger.info(str(json_data["token"] == self.config["bot_token"]))
        if event_type == "channel_rename":
            pass
        elif event_type == "message":
            logger.info(event["subtype"])
        elif event_type == "member_joined_channel":
            pass
        elif event_type == "pin_added":
            pass
        elif event_type == "reaction_added":
            pass
        elif event_type == "reaction_removed":
            pass

        # can check if this is a bot action- special flag for that ?

    @Registry.action(slug="pin-message", description="Pin a message")
    def pin(self, parameters):
        data = {
            "token": self.config["bot_token"],
            "channel": parameters["channel"],
            "timestamp": parameters["timestamp"],  # unique ts of the message to pin
        }
        return self.slack_request("POST", "pins.add", data=data)

    @Registry.action(slug="unpin-message", description="Unpin a message")
    def unpin(self, parameters):
        data = {
            "token": self.config["bot_token"],
            "channel": parameters["channel"],
            "timestamp": parameters["timestamp"],  # unique ts of the message to unpin
        }
        return self.slack_request("POST", "pins.remove", data=data)

    @Registry.action(slug="method", description="Perform any Slack method (provided sufficient scopes)")
    def method(self, parameters):
        """
        Catch-all action for any method in https://api.slack.com/methods
        See: https://api.slack.com/web#basics
        """
        data = {"token": self.config["bot_token"], **parameters}
        return self.slack_request("POST", "pins.remove", data=data)

    def slack_request(self, method, route, json=None, data=None):
        url = f"https://slack.com/api/{route}"
        logger.info(f"{method} {url}")
        resp = requests.request(method, url, json=json, data=data)
        if not resp.ok:
            logger.error(f"{resp.status_code} {resp.reason}")
            logger.error(resp.request.body)
            raise PluginErrorInternal(resp.text)
        if resp.content:
            return resp.json()
        return None
