"""AML Watcher API client for performing sanctions and PEP screening."""

import json
import logging
import traceback
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class AMLWatcherClient:
    """Client for interacting with AML Watcher API."""

    def __init__(self, api_key: str):
        """
        Initialize AML Watcher client.
        
        Args:
            api_key: AML Watcher API key
        """
        self.api_key = api_key
        self.base_url = "https://api.amlwatcher.com/api/search"
        self.headers = {
            'Content-Type': 'application/json'
        }

        if not self.api_key:
            raise ValueError("AML Watcher API key is required")

    async def search(
        self,
        name: str,
        countries: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        entity_type: Optional[List[str]] = None,
        birth_incorporation_date: str = "",
        unique_identifier: str = ""
    ) -> Dict[str, Any]:
        """
        Search AML Watcher for sanctions, PEPs, and adverse media.
        
        Args:
            name: The name or entity to screen (2-100 chars, required)
            countries: Array of ISO 3166-1 alpha-2 country codes (e.g., ["CA", "IN"])
            categories: Array of categories to filter (e.g., ["Adverse Media", "SIP"])
            entity_type: Array of entity types (e.g., ["Person", "Company", "Organization"])
            birth_incorporation_date: Date in DD-MM-YYYY format (supports partial: 00-00-1947)
            unique_identifier: Unique identifier like Passport No, National ID (2-50 chars)
            
        Returns:
            Search results from AML Watcher API
        """
        try:
            logger.info(f"AMLWatcher: Screening {name}...")
            
            # Set default categories if not provided (search all)
            if categories is None:
                categories = [
                    'Adverse Media',
                    'Business',
                    'Businessperson',
                    'Fitness and Probity',
                    'Insolvency',
                    'PEP',
                    'PEP Level 1',
                    'PEP Level 2',
                    'PEP Level 3',
                    'PEP Level 4',
                    'SIE',
                    'SIP',
                    'Sanctions',
                    'Warnings and Regulatory Enforcement'
                ]
            
            # Set default countries if not provided (search all)
            if countries is None:
                countries = []
            
            # Set default entity_type if not provided (search all types)
            if entity_type is None:
                entity_type = ['Aircraft', 'Company', 'Crypto_Wallet', 'Organization', 'Person', 'Vessel']
            
            # Prepare the search payload
            payload = {
                "name": name,
                "categories": categories,
                "countries": countries,
                "entity_type": entity_type,
                "match_score": 50,
                "birth_incorporation_date": birth_incorporation_date,
                "unique_identifier": unique_identifier,
                "exact_search": False,
                "api_key": self.api_key,
                "all_adverse_media": True
            }

            logger.info(f"AMLWatcher: Submitting search request...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

            if response.status_code == 200:
                results = response.json()
                logger.info("AMLWatcher: Search completed successfully")
                return results
            else:
                error_msg = f"AML Watcher API returned status code {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error in AML Watcher search: {str(e)}")
            logger.debug(traceback.format_exc())
            return {"error": str(e), "results": []}
