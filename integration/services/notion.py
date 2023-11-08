import base64
import json
import logging
import traceback

import requests
from django.conf import settings
from django.db import transaction

from common.exceptions import ServcyOauthCodeException
from inbox.services import InboxRepository
from integration.repository import IntegrationRepository

from .base import BaseService

NOTION_API_BASE_URL = "https://api.notion.com"
NOTION_OAUTH_TOKEN_ENDPOINT = f"{NOTION_API_BASE_URL}/v1/oauth/token"

logger = logging.getLogger(__name__)


class NotionService(BaseService):
    """Service class for Notion integration."""

    _NOTION_PAGE_SEARCH = "https://api.notion.com/v1/search"
    _NOTION_BOT_USER = "https://api.notion.com/v1/users"
    _NOTION_COMMENTS = "https://api.notion.com/v1/comments"
    _NOTION_BLOCK_SEARCH = "https://api.notion.com/v1/blocks"

    def __init__(self, **kwargs) -> None:
        """Initialize the NotionService with an optional authorization code.

        :param code: Authorization code
        """
        self._token = None
        if kwargs.get("code"):
            self._fetch_token(kwargs.get("code"))
        if kwargs.get("token", False):
            self._token = kwargs.get("token")

    def _create_basic_auth_header(self) -> dict:
        """Generate the Basic Authorization header for Notion API requests."""
        authorization = (
            f"{settings.NOTION_APP_CLIENT_ID}:{settings.NOTION_APP_CLIENT_SECRET}"
        ).encode()
        return {
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(authorization).decode()}",
        }

    def _fetch_token(self, code: str) -> dict:
        """Fetch the access token from Notion using an authorization code.

        :param code: Authorization code
        :return: Dictionary containing token details
        """
        response = requests.post(
            url=NOTION_OAUTH_TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.NOTION_APP_REDIRECT_URI,
            },
            headers=self._create_basic_auth_header(),
        ).json()

        if response.get("object") == "error" or "error" in response:
            raise ServcyOauthCodeException(
                f"An error occurred while obtaining access token from Notion.\n{str(response)}"
            )
        self._token = response

    def create_integration(self, user_id: int):
        """Create a user integration in the local database with token and workspace details.

        :param user_id: ID of the user for whom the integration is created
        """
        pages = self.get_authorized_pages()
        return IntegrationRepository.create_user_integration(
            integration_id=IntegrationRepository.get_integration(
                filters={"name": "Notion"}
            ).id,
            user_id=user_id,
            account_id=self._token["workspace_id"],
            account_display_name=self._token["workspace_name"],
            meta_data={"token": self._token},
            configuration={
                "pages": pages,
                "total": len(pages),
            },
        )

    def is_active(self, meta_data, **kwargs):
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        self._token = meta_data["token"]
        response = requests.get(
            url=f"{NOTION_API_BASE_URL}/v1/users",
            headers={
                "Authorization": f"Bearer {self._token['access_token']}",
                "Notion-Version": "2021-05-13",
            },
        )
        return response.status_code == 200

    def get_authorized_pages(self):
        """
        Get all the pages that the user has access to.
        """
        pages = []
        page_results = self.page_search()
        database_results = self.database_search()
        # get page detail
        for page_result in page_results:
            page_id = page_result["id"]
            if "Name" in page_result["properties"]:
                if len(page_result["properties"]["Name"]["title"]) > 0:
                    page_name = page_result["properties"]["Name"]["title"][0][
                        "plain_text"
                    ]
                else:
                    page_name = "Untitled"
            elif "title" in page_result["properties"]:
                if len(page_result["properties"]["title"]["title"]) > 0:
                    page_name = page_result["properties"]["title"]["title"][0][
                        "plain_text"
                    ]
                else:
                    page_name = "Untitled"
            elif "Title" in page_result["properties"]:
                if len(page_result["properties"]["Title"]["title"]) > 0:
                    page_name = page_result["properties"]["Title"]["title"][0][
                        "plain_text"
                    ]
                else:
                    page_name = "Untitled"
            else:
                page_name = "Untitled"
            page_icon = page_result["icon"]
            if page_icon:
                icon_type = page_icon["type"]
                if icon_type == "external" or icon_type == "file":
                    url = page_icon[icon_type]["url"]
                    icon = {
                        "type": "url",
                        "url": url
                        if url.startswith("http")
                        else f"https://www.notion.so{url}",
                    }
                else:
                    icon = {"type": "emoji", "emoji": page_icon[icon_type]}
            else:
                icon = None
            parent = page_result["parent"]
            parent_type = parent["type"]
            if parent_type == "block_id":
                parent_id = self.block_parent_page_id(parent[parent_type])
            elif parent_type == "workspace":
                parent_id = "root"
            else:
                parent_id = parent[parent_type]
            page = {
                "page_id": page_id,
                "page_name": page_name,
                "page_icon": icon,
                "parent_id": parent_id,
                "last_cursor": "",
                "type": "page",
            }
            pages.append(page)
            # get database detail
        for database_result in database_results:
            page_id = database_result["id"]
            if len(database_result["title"]) > 0:
                page_name = database_result["title"][0]["plain_text"]
            else:
                page_name = "Untitled"
            page_icon = database_result["icon"]
            if page_icon:
                icon_type = page_icon["type"]
                if icon_type == "external" or icon_type == "file":
                    url = page_icon[icon_type]["url"]
                    icon = {
                        "type": "url",
                        "url": url
                        if url.startswith("http")
                        else f"https://www.notion.so{url}",
                    }
                else:
                    icon = {"type": icon_type, icon_type: page_icon[icon_type]}
            else:
                icon = None
            parent = database_result["parent"]
            parent_type = parent["type"]
            if parent_type == "block_id":
                parent_id = self.block_parent_page_id(parent[parent_type])
            elif parent_type == "workspace":
                parent_id = "root"
            else:
                parent_id = parent[parent_type]
            page = {
                "page_id": page_id,
                "page_name": page_name,
                "page_icon": icon,
                "parent_id": parent_id,
                "type": "database",
                "last_cursor": "",
            }
            pages.append(page)
        return pages

    def page_search(self):
        """Search for pages in the workspace. Pages are the basic building blocks of Notion, similar to documents in a word processor."""
        data = {"filter": {"value": "page", "property": "object"}}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token['access_token']}",
            "Notion-Version": "2022-06-28",
        }
        response = requests.post(
            url=self._NOTION_PAGE_SEARCH, json=data, headers=headers
        )
        response_json = response.json()
        if "results" in response_json:
            results = response_json["results"]
        else:
            results = []
        return results

    def block_parent_page_id(self, block_id: str):
        """
        Get the parent page id of a block.
        """
        headers = {
            "Authorization": f"Bearer {self._token['access_token']}",
            "Notion-Version": "2022-06-28",
        }
        response = requests.get(
            url=f"{self._NOTION_BLOCK_SEARCH}/{block_id}", headers=headers
        )
        response_json = response.json()
        parent = response_json["parent"]
        parent_type = parent["type"]
        if parent_type == "block_id":
            return self.block_parent_page_id(parent[parent_type])
        return parent[parent_type]

    def database_search(self):
        """
        Search for databases in the workspace. Databases are  collections of pages.
        """
        data = {"filter": {"value": "database", "property": "object"}}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token['access_token']}",
            "Notion-Version": "2022-06-28",
        }
        response = requests.post(
            url=self._NOTION_PAGE_SEARCH, json=data, headers=headers
        )
        response_json = response.json()
        if "results" in response_json:
            results = response_json["results"]
        else:
            results = []
        return results

    def get_new_unresolved_comments(self, page_id: str, last_cursor: str = None):
        """
        Get all the unresolved comments in a page.
        """
        response = requests.request(
            "GET",
            f"{self._NOTION_COMMENTS}?block_id={page_id}&start_cursor={last_cursor}"
            if last_cursor
            else f"{self._NOTION_COMMENTS}?block_id={page_id}",
            headers={
                "Notion-Version": "2022-02-22",
                "Authorization": f"Bearer {self._token['access_token']}",
            },
            data={},
        ).json()
        results = response.get("results", [])
        if response.get("has_more", False):
            results += self.get_unresolved_comments(
                page_id=page_id, last_cursor=response.get("next_cursor", "")
            )
        return results[1:] if last_cursor else results

    def fetch_all_users(self):
        headers = {
            "Notion-Version": "2022-02-22",
            "Authorization": f"Bearer {self._token['access_token']}",
        }
        response = requests.request(
            "GET", self._NOTION_BOT_USER, headers=headers, data={}
        )
        return response.json().get("results", [])


# CRON job to poll new comments from Notion.
def poll_new_comments():
    try:
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "integration__name": "Notion",
            }
        )
        inbox_items = []
        configuration_map = {}
        for user_integration in user_integrations:
            try:
                process_user_integration(
                    user_integration, inbox_items, configuration_map
                )
            except Exception:
                logger.exception(
                    f"An error occurred while fetching notion comments for user {user_integration['user_id']}",
                    extra={
                        "traceback": traceback.format_exc(),
                    },
                )
        with transaction.atomic():
            InboxRepository.add_items(inbox_items)
            for user_integration_id, configuration in configuration_map.items():
                IntegrationRepository.update_integraion_configuration(
                    user_integration_id, configuration=configuration
                )
    except Exception:
        logger.exception(
            "An error occurred while fetching notion comments",
            extra={
                "traceback": traceback.format_exc(),
            },
        )


def process_user_integration(
    user_integration: dict, inbox_items: list, configuration_map: dict
):
    """
    Process a user integration for new comments.
    """
    configuration_map[user_integration["id"]] = user_integration["configuration"]
    service = NotionService(token=user_integration["meta_data"]["token"])
    pages = user_integration["configuration"]["pages"]
    users = service.fetch_all_users()
    user_map = {user["id"]: user for user in users}

    for i, page in enumerate(pages):
        try:
            process_page(
                i,
                page,
                user_integration,
                service,
                user_map,
                inbox_items,
                configuration_map,
            )
        except Exception:
            logger.exception(
                f"An error occurred while fetching notion comments for page {page['page_id']}",
                extra={
                    "traceback": traceback.format_exc(),
                },
            )


def process_page(
    i: int,
    page: dict,
    user_integration: dict,
    service: "NotionService",
    user_map: dict[str, dict],
    inbox_items: list,
    configuration_map: dict,
):
    """
    Process a page for new comments.
    """
    comments = service.get_new_unresolved_comments(
        page["page_id"], page.get("last_cursor", "")
    )
    if comments:
        comment_from = user_map.get(comments[0]["created_by"]["id"])
        inbox_items.extend(
            [
                {
                    "title": f"New comment on {page['page_name']}",
                    "cause": json.dumps(comment_from),
                    "body": json.dumps(comment),
                    "is_body_html": False,
                    "user_integration_id": user_integration["id"],
                    "uid": f"{comment['id']}-{user_integration['id']}",
                    "category": "comment",
                }
                for comment in comments
            ]
        )
        configuration_map[user_integration["id"]]["pages"][i]["last_cursor"] = comments[
            -1
        ]["id"]
