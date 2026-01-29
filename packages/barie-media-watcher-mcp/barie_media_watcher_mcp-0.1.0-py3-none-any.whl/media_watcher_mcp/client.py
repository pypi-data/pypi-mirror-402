"""Media Watcher API client for performing sentiment analysis and media monitoring."""

import json
import logging
import asyncio
import traceback
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class MediaWatcherClient:
    """Client for interacting with Media Watcher API."""

    def __init__(self, api_key: str):
        """
        Initialize Media Watcher client.
        
        Args:
            api_key: Media Watcher API key
        """
        self.api_key = api_key
        self.base_url = "https://api.mediawatcher.ai/api"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }

        if not self.api_key:
            raise ValueError("Media Watcher API key is required")

    async def search(
        self,
        query: str,
        source: str = "news",
        country: str = "",
        search_result_timeout: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search Media Watcher for news or youtube content.
        
        Args:
            query: The search query (person, company, etc.)
            source: Source to search ("news" or "youtube")
            country: ISO 3166-1 alpha-2 country code (optional)
            search_result_timeout: Timeout in seconds for waiting for results
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"MediaWatcher: Searching for {query} in {source}...")
            
            # Prepare the search payload
            body = {
                "name": query,
                "sentiment": ["positive", "negative", "neutral"],
                "allowed_sources": [source],
            }
            
            if country:
                body["country"] = country

            async with httpx.AsyncClient() as client:
                # 1. Submit search request
                logger.info("MediaWatcher: Submitting search request...")
                submit_response = await client.post(
                    f"{self.base_url}/search", 
                    headers=self.headers, 
                    json=body,
                    timeout=30.0
                )

                search_reference = None
                if submit_response.status_code == 200:
                    data = submit_response.json().get('data', {})
                    search_reference = data.get('search_reference')
                    if search_reference:
                        logger.info(f"MediaWatcher: Got search_reference: {search_reference}")
                    else:
                        raise Exception(f"No search_reference in response: {submit_response.text}")
                else:
                    raise Exception(f"Search request failed: {submit_response.status_code} - {submit_response.text}")

                # 2. Poll for results
                logger.info("MediaWatcher: Waiting for search results...")
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    # Check timeout
                    if asyncio.get_event_loop().time() - start_time > search_result_timeout:
                        raise TimeoutError(f"Timeout waiting for search results for reference: {search_reference}")

                    body_detail = {
                        "search_reference": search_reference,
                    }
                    
                    detail_response = await client.post(
                        f"{self.base_url}/search/detail", 
                        headers=self.headers, 
                        json=body_detail,
                        timeout=30.0
                    )
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json().get('data', {})
                        status = detail_data.get('status')
                        
                        logger.debug(f"MediaWatcher: Request status: {status}")
                        
                        if status == "resolved":
                            results = detail_data.get('results', [])
                            logger.info(f"MediaWatcher: Search completed, found {len(results)} results")
                            return results
                        elif status == "failed":
                             raise Exception(f"Search failed for reference: {search_reference}")
                        
                        # Wait before next poll
                        await asyncio.sleep(3)
                    else:
                        raise Exception(f"Detail request failed: {detail_response.status_code} - {detail_response.text}")

        except Exception as e:
            logger.error(f"Error in Media Watcher search: {str(e)}")
            logger.debug(traceback.format_exc())
            # Return empty list on error to be safe, or re-raise? 
            # The original code returned [], but passing the error up might be better for an MCP tool.
            # However, to match the robustness of the example, I'll re-raise so the user knows it failed.
            raise e
