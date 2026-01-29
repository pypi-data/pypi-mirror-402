"""Slack Notifier for NetworkDoctor"""
import json
from typing import Dict, Any
import aiohttp


class SlackNotifier:
    """Slack notification integration"""
    
    async def notify(self, webhook_url: str, results: Dict[str, Any]):
        """
        Send notification to Slack.
        
        Args:
            webhook_url: Slack webhook URL
            results: Diagnosis results
        """
        health_score = results.get("analysis", {}).get("summary", {}).get("health_score", 0)
        total_issues = results.get("analysis", {}).get("summary", {}).get("total_issues", 0)
        
        payload = {
            "text": f"NetworkDoctor Report",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Health Score:* {health_score}/100\n*Total Issues:* {total_issues}",
                    },
                },
            ],
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception:
            return False







