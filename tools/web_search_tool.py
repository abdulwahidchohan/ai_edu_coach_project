from typing import List, Dict, Any, Optional
import aiohttp
import os
import json
from datetime import datetime

class WebSearchTool:
    """A tool for performing web searches to retrieve educational content."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the web search tool with an optional API key.
        
        Args:
            api_key: API key for the search service. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY")
        self.search_endpoint = "https://api.search.provider.com/v1/search"
        self.cache_dir = os.path.join(os.getcwd(), "data", "search_cache")
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    async def search(self, query: str, num_results: int = 5, cache: bool = True) -> List[Dict[str, Any]]:
        """Perform a web search for educational content.
        
        Args:
            query: The search query string
            num_results: Number of results to return
            cache: Whether to use cached results if available
            
        Returns:
            List of search result items
        """
        # Check cache first if enabled
        if cache:
            cached_results = self._get_from_cache(query)
            if cached_results:
                return cached_results[:num_results]
        
        # If no API key, return empty results with a warning
        if not self.api_key:
            print("Warning: No search API key provided. Web search functionality is limited.")
            return [{
                "title": "API Key Required",
                "snippet": "To enable web search functionality, please provide a valid API key.",
                "url": "#"
            }]
        
        try:
            # Perform the actual search request
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "num": num_results,
                    "key": self.api_key
                }
                
                async with session.get(self.search_endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_search_results(data)
                        
                        # Cache the results
                        if cache:
                            self._save_to_cache(query, results)
                        
                        return results[:num_results]
                    else:
                        print(f"Search API error: {response.status}")
                        return []
        except Exception as e:
            print(f"Error performing web search: {str(e)}")
            return []
    
    async def get_content(self, url: str) -> Optional[str]:
        """Retrieve the content from a specific URL.
        
        Args:
            url: The URL to retrieve content from
            
        Returns:
            The text content of the page, or None if retrieval failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"Error retrieving content: {response.status}")
                        return None
        except Exception as e:
            print(f"Error retrieving content: {str(e)}")
            return None
    
    def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the raw search API response into a standardized format.
        
        Args:
            data: The raw API response data
            
        Returns:
            List of search result items in a standardized format
        """
        # This implementation will depend on the specific search API being used
        # Here's a generic implementation that assumes a common structure
        results = []
        
        if "items" in data:
            for item in data["items"]:
                result = {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "web"
                }
                results.append(result)
        
        return results
    
    def _get_cache_path(self, query: str) -> str:
        """Get the file path for caching results of a query.
        
        Args:
            query: The search query
            
        Returns:
            File path for the cache file
        """
        # Create a filename-safe version of the query
        safe_query = "".join(c if c.isalnum() else "_" for c in query)
        safe_query = safe_query[:50]  # Limit length for filesystem compatibility
        return os.path.join(self.cache_dir, f"{safe_query}.json")
    
    def _get_from_cache(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Try to get search results from cache.
        
        Args:
            query: The search query
            
        Returns:
            Cached search results if available and fresh, None otherwise
        """
        cache_path = self._get_cache_path(query)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid (less than 24 hours old)
            cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
            now = datetime.now()
            
            # If cache is older than 24 hours, consider it stale
            if (now - cache_time).total_seconds() > 86400:  # 24 hours in seconds
                return None
            
            return cache_data.get("results", [])
        except (json.JSONDecodeError, IOError, ValueError):
            return None
    
    def _save_to_cache(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Save search results to cache.
        
        Args:
            query: The search query
            results: The search results to cache
        """
        cache_path = self._get_cache_path(query)
        
        cache_data = {
            "query": query,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving to cache: {str(e)}")

    async def search_educational_resources(self, topic: str, grade_level: Optional[str] = None, 
                                          subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search specifically for educational resources on a topic.
        
        Args:
            topic: The educational topic to search for
            grade_level: Optional grade level to target (e.g., "elementary", "middle school", "high school")
            subject: Optional subject area (e.g., "math", "science", "history")
            
        Returns:
            List of educational resources matching the criteria
        """
        # Build a more specific query for educational content
        query_parts = [topic]
        
        if grade_level:
            query_parts.append(grade_level)
        
        if subject:
            query_parts.append(subject)
        
        query_parts.append("educational resources")
        query = " ".join(query_parts)
        
        # Perform the search
        results = await self.search(query, num_results=8)
        
        # Add metadata to the results
        for result in results:
            result["topic"] = topic
            if grade_level:
                result["grade_level"] = grade_level
            if subject:
                result["subject"] = subject
        
        return results