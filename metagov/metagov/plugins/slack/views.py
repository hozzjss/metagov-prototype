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
    logger.info(env("SLACK_CLIENT_ID"))

    code = request.GET.get("code")
    state = request.GET.get("state")
    logger.info(code)
    logger.info(state)

    # curl -F code=1234 -F client_id=3336676.569200954261 -F client_secret=ABCDEFGH https://slack.com/api/oauth.v2.access

    data = {"client_id": env("SLACK_CLIENT_ID"), "client_secret": env("SLACK_CLIENT_SECRET"), "code": code}
    resp = requests.get("https://slack.com/api/oauth.v2.access", data=data)
    if not resp.ok:
        logger.error(f"Slack oauth with {resp.status_code} {resp.reason}")
        raise PluginErrorInternal(resp.text)
    response = resp.json()
    logger.info(response)
    if not response["ok"]:
        logger.error(response)
        raise PluginErrorInternal("Slack oauth failed")

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

    # FIXME: what should happen? Enable Slack plugin for the given Metagov community?
    # Metagov Community Slug should be included in the request state?

    # community = Community.objects.get(...)
    # config = {"team_id": team_id}
    # Slack.objects.create(name="slack", community=community, config=config)

    return HttpResponseRedirect(env("SLACK_AUTH_REDIRECT_URL"))

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
            #fixme..... let plugin define request routing, but pass control back to core
            plugin.receive_event(request)
    return HttpResponse()
