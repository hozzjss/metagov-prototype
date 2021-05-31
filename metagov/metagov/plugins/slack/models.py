import logging
import json

import metagov.core.plugin_decorators as Registry
import requests
from metagov.core.errors import PluginErrorInternal
from metagov.core.models import Plugin

from django.http import HttpResponse

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
        "properties": {"team_id": {"description": "Slack Team ID", "type": "string"}},
        "required": ["team_id"],
    }

    class Meta:
        proxy = True

    def initialize(self):
        logger.info(">>>>>>>> initializing slack")


    # PLATFORM ACTIONS:
    # TODO: post message
    # TODO: rename conversation
    # TODO: join conversation
    # TODO: pin message
    # TODO: schedule message
    # TODO: kick conversation
    # https://api.slack.com/bot-users#bot_methods

    # Click “Event Subscriptions”->”Enable Events” and enter the request URL
    # [POLICYKIT_URL]/slack/action. Subscribe to bot events and subscribe to
    # events on behalf of users.
    def receive_event(self, request):
        logger.info("received event")
        json_data = json.loads(request.body)
        logger.info(json_data)

        if json_data["type"] == "url_verification":
            challenge = json_data.get("challenge")
            return HttpResponse(challenge)  # help! need to register a custom URL? too django-y

        if json_data["type"] == "app_rate_limited":
            logger.error("Slack app rate limited")
            return HttpResponse()

        if json_data["type"] != "event_callback":
            return HttpResponse()

        #https://api.slack.com/apis/connections/events-api#the-events-api__receiving-events__events-dispatched-as-json
        
        # validate the request:

        #The unique identifier for the workspace/team where this event occurred.
        team_id = json_data["team_id"]
        #The shared-private callback token that authenticates this callback to the application as having come from Slack. Match this against what you were given when the subscription was created. If it does not match, do not process the event and discard it.
        token = json_data["token"]
        #The unique identifier for the application this event is intended for. Your application's ID can be found in the URL of the your application console. If your Request URL manages multiple applications, use this field along with the token field to validate and route incoming requests.
        api_app_id = json_data["api_app_id"]
        logger.info(f"Team id: {team_id}")
        if team_id is not self.config["team_id"]:
            return


        # authorizations = json_data["authorizations"]
        # event_context = json_data["event_context"]
        #A unique identifier for this specific event, globally unique across all workspaces.
        event_id = json_data["event_id"]
        #The epoch timestamp in seconds indicating when this event was dispatched.
        event_time = json_data["event_time"]

        event = json_data["event"]        

        #https://api.slack.com/events
        event_type = event["event_type"]
        # if event_type == "..."

        # "is policykit bot action"