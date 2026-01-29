"""Webhook Integration for NetworkDoctor"""
import json
from typing import Dict, Any
import aiohttp


class WebhookSender:
    """Webhook integration"""
    
    async def send(self, webhook_url: str, results: Dict[str, Any]):
        """
        Send results to webhook.
        
        Args:
            webhook_url: Webhook URL
            results: Diagnosis results
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=results) as response:
                    return response.status == 200
        except Exception:
            return False







