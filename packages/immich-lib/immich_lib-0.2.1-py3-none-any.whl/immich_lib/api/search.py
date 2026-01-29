from ..base import ImmichBaseClient

class SearchMixin(ImmichBaseClient):
    """
    Mixin for Search related endpoints, including metadata and smart search.
    """
    def search_metadata(self, query=None, **kwargs):
        """
        Search assets by metadata (filename, description, etc.).

        Args:
            query (str, optional): The search query string.
            **kwargs: Additional metadata filters (e.g., isFavorite, type).

        Returns:
            dict: Search results including the list of assets.
        """
        data = kwargs
        if query: data["query"] = query
        return self.post("search/metadata", json=data)

    def search_places(self, query):
        """
        Search for places based on a geographic query.

        Args:
            query (str): The place name or location query.

        Returns:
            list: List of matching places.
        """
        return self.get("search/places", params={"query": query})

    def search_smart(self, query, **kwargs):
        """
        Perform a smart search using CLIP (semantic search).

        Args:
            query (str): The semantic search query (e.g., "sunset at the beach").
            **kwargs: Pagination or other search options.

        Returns:
            list: List of matching assets.
        """
        params = {"query": query}
        params.update(kwargs)
        return self.get("search/smart", params=params)

    def get_explore_data(self):
        """
        Get data for the Explore tab (categories like places, people, objects).

        Returns:
            dict: Explore data categories.
        """
        return self.get("search/explore")
