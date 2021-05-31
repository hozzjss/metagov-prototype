import logging
import json

from django.http.response import HttpResponse
import environ
import requests
from django.http import HttpResponseRedirect
from metagov.core.errors import PluginErrorInternal
from metagov.plugins.slack.models import Slack

logger = logging.getLogger(__name__)


def oauth(request):
    """

    https://api.slack.com/authentication/oauth-v2#exchanging

    """
    logger.info(">>> Slack plugin processing auth request:")
    env = environ.Env()
    environ.Env.read_env()
    code = request.GET.get("code")
    state = request.GET.get("state")
    logger.info(f"code: {code}, state: {state}")
    data = {"client_id": env("SLACK_CLIENT_ID"), "client_secret": env("SLACK_CLIENT_SECRET"), "code": code}
    resp = requests.post("https://slack.com/api/oauth.v2.access", data=data)
    if not resp.ok:
        raise PluginErrorInternal(f"Slack auth failed: {resp.status_code} {resp.reason}")
    response = resp.json()
    logger.info(response)
    if not response["ok"]:
        raise PluginErrorInternal(f"Slack auth failed: {response['error']}")

    # {
    #     "ok": true,
    #     "access_token": "xoxb-17653672481-19874698323-pdFZKVeTuE8sk7oOcBrzbqgy",
    #     "token_type": "bot",
    #     "scope": "commands,incoming-webhook",
    #     "bot_user_id": "U0KRQLJ9H",
    #     "app_id": "A0KRD7HC3",
    #     "team": {
    #         "name": "Slack Softball Team",
    #         "id": "T9TK3CUKW"
    #     },
    #     "enterprise": {
    #         "name": "slack-sports",
    #         "id": "E12345678"
    #     },
    #     "authed_user": {
    #         "id": "U1234",
    #         "scope": "chat:write",
    #         "access_token": "xoxp-1234",
    #         "token_type": "user"
    #     }
    # }

    bot_token = response["access_token"]
    team_id = response["team"]["id"]
    team_name = response["team"]["name"]
    # app_id = response["app_id"]
    config = {"team_id": team_id, "bot_token": bot_token, "team_name": team_name}
    return (env("SLACK_AUTH_REDIRECT_URL"), config)


def process_event(request):
    logger.info("received event")
    json_data = json.loads(request.body)
    logger.info(json_data)

    if json_data["type"] == "url_verification":
        challenge = json_data.get("challenge")
        return HttpResponse(challenge)

    if json_data["type"] == "app_rate_limited":
        logger.error("Slack app rate limited")
        return HttpResponse()

    if json_data["type"] != "event_callback":
        for plugin in Slack.objects.all():
            # fixme..... let plugin define request routing, but pass control back to core
            plugin.receive_event(request)
    return HttpResponse()
