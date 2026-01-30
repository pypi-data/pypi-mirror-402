import requests
from typing import Optional, List
from datetime import datetime
from os import path
from ._odata_utils import build_query_url
from ._base import SharePointBase
from .list_item import SharePointListItem
from typing import TYPE_CHECKING
from .list_field import SharePointListField

if TYPE_CHECKING:
    from .site import SharePointSite


class SharePointList(SharePointBase):
    """
    Base class representing a SharePoint list.

    Provides common functionality for handling list items, including
    retrieval, addition, and serialization to JSON.
    """

    @classmethod
    def from_relative_url(
        cls,
        base_sharepoint_url: str,
        relative_url: str,
        session: requests.Session,
    ) -> "SharePointList":
        """
        Initialise a :class:`SharePointList` using a base SharePoint URL and a
        server‑relative URL.

        Parameters
        ----------
        base_sharepoint_url : str
            The root URL of the SharePoint tenant (e.g. ``https://example.com``).
        relative_url : str
            The server‑relative path to the list (e.g. ``/sites/demo/Lists/Tasks``).
        session : requests.Session
            A pre‑configured session with authentication.

        Returns
        -------
        SharePointList
            An instance configured with the combined list URL.
        """
        _url = path.join(base_sharepoint_url, relative_url)
        return cls(_url, session)

    settings = None
    _items = None
    _fields = None
    _base_url = None
    sharepoint_site = None
    SPItem = SharePointListItem

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def _items_url(self) -> str:
        return self.get('Items', {}).get(
            '__deferred', {}).get('uri')

    @property
    def _fields_url(self) -> str:
        return self.get('Fields', {}).get(
            '__deferred', {}).get('uri')

    @property
    def _form_digestive_value(self):
        r = self._api.post(
            path.join(
                self.base_url,
                '_api/contextinfo'
            ), {})

        return r.json()["d"]["GetContextWebInformation"]["FormDigestValue"]

    @property
    def base_url(self) -> str:
        if not self._base_url:
            self._base_url = self._url.split('_api')[0]
        return self._base_url

    @property
    def title(self) -> str:
        """List title."""
        return self.get('Title')

    @property
    def id(self) -> str:
        """List identifier."""
        return self.get('Id')

    def get_fields(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None
    ) -> List[SharePointListItem]:
        """Return a collection of items for this site."""

        item_url = build_query_url(
            self._fields_url,
            filters=filters,
            select_fields=select_fields if select_fields else ["Id"],
            top=top
        )

        r = self._api.get(item_url)
        return [SharePointListField(sp_list.get('__metadata', {}).get(
            "uri"), self._api.session) for sp_list in r.json()["d"]["results"]]

    def get_items(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None,
        skiptoken: Optional[str] = None
    ) -> List[SharePointListItem]:
        """Return a collection of items for this site."""

        item_url = build_query_url(
            self._items_url,
            filters=filters,
            select_fields=select_fields if select_fields else ["Id"],
            top=top,
            skiptoken=skiptoken
        )

        r = self._api.get(item_url)
        return [SharePointListItem(sp_list.get('__metadata', {}).get(
            "uri"), self._api.session) for sp_list in r.json()["d"]["results"]]

    def get_items_paged(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None,
        skiptoken: Optional[str] = None
    ) -> dict:
        """
        Return a collection of items for this site along with pagination information.
        
        Returns
        -------
        dict
            A dictionary containing:
            - items: List of SharePointListItem objects
            - next_skiptoken: Token for next page (None if no more pages)
            - has_next: Boolean indicating if there are more pages
        """

        item_url = build_query_url(
            self._items_url,
            filters=filters,
            select_fields=select_fields if select_fields else ["Id"],
            top=top,
            skiptoken=skiptoken
        )

        r = self._api.get(item_url)
        response_data = r.json()["d"]
        items = [SharePointListItem(sp_list.get('__metadata', {}).get(
            "uri"), self._api.session) for sp_list in response_data["results"]]
        
        # Extract next skiptoken from __next link if present
        next_skiptoken = None
        has_next = False
        
        if "__next" in response_data:
            has_next = True
            next_link = response_data["__next"]
            # Extract skiptoken from the next link
            if "$skiptoken=" in next_link:
                # Extract the skiptoken parameter from the URL
                import urllib.parse
                parsed_url = urllib.parse.urlparse(next_link)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if "$skiptoken" in query_params:
                    # The skiptoken value is already properly encoded
                    next_skiptoken = query_params["$skiptoken"][0]

        return {
            "items": items,
            "next_skiptoken": next_skiptoken,
            "has_next": has_next
        }

    def iterate_all_items(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        page_size: int = 1000
    ):
        """
        Generator that yields all items from the list, handling pagination automatically.
        
        Parameters
        ----------
        filters : Optional[str]
            OData filter expression
        select_fields : Optional[List[str]]
            Fields to include in the response
        page_size : int
            Number of items to retrieve per page (default: 1000)
            
        Yields
        ------
        SharePointListItem
            Individual list items
        """
        skiptoken = None
        
        while True:
            page_result = self.get_items_paged(
                filters=filters,
                select_fields=select_fields,
                top=page_size,
                skiptoken=skiptoken
            )
            
            # Yield each item in the current page
            for item in page_result["items"]:
                yield item
                
            # If there are no more pages, break the loop
            if not page_result["has_next"]:
                break
                
            # Set the skiptoken for the next iteration
            skiptoken = page_result["next_skiptoken"]

    def get_item(
        self,
        item_id: str,
    ) -> SharePointListItem:
        """Return a :class:`SharePointListItem` for the given GUID.

        Parameters
        ----------
        item_id : str
            The GUID string of the item.

        """
        list_item_url = path.join(
            self._url, f"items({item_id})"
        )
        return SharePointListItem(list_item_url, self._api.session)

    def get_parent_site(self) -> "SharePointSite":
        """
        Retrieve the parent SharePoint site of this list.
        """
        from .site import SharePointSite
        site_url = f"{self.base_url}/_api/Web"
        return SharePointSite(url=site_url, session=self._api.session)

    def create_item(self, data) -> SharePointListItem:
        base_url = self._url.split('_api')[0]
        r = self._api.post(
            path.join(
                base_url,
                '_api/contextinfo'
            ), {})

        form_digest_value = r.json(
        )["d"]["GetContextWebInformation"]["FormDigestValue"]

        r = self._api.post(
            self._items_url, data, form_digest_value)

        list_item_url = r.json()["d"].get('__metadata').get('uri')
        return SharePointListItem(list_item_url, self._api.session)
