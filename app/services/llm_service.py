"""
LLM Service — User's own API key for personalization
"""

import httpx
import json
import re


class LLMService:
    def __init__(self, llm_config: dict):
        self.provider = llm_config["type"]
        self.model = llm_config["model"]
        self.api_key = llm_config["api_key"]

    async def generate_connection_note(self, prospect: dict) -> str:
        """Generate personalized connection request"""
        
        prompt = f"""
You are a friendly professional reaching out on LinkedIn.

Prospect information:
- Name: {prospect.get('full_name', 'Unknown')}
- Title: {prospect.get('title', 'Unknown')}
- Company: {prospect.get('company', 'Unknown')}
- Headline: {prospect.get('headline', '')}

Write a brief, genuine connection request note (max 300 characters) that:
- Mentions something specific about their profile
- Is friendly and conversational
- Doesn't sound salesy or AI-generated

Just the note, no extra text:
"""
        
        return await self._generate(prompt, max_tokens=100)

    async def generate_first_message(self, prospect: dict) -> str:
        """Generate first message after connection accepted"""
        
        prompt = f"""
{prospect.get('full_name', 'They')} just accepted your LinkedIn connection.

Their profile:
- Title: {prospect.get('title', 'Unknown')}
- Company: {prospect.get('company', 'Unknown')}

Write a friendly first message (max 500 characters) that:
- Thanks them for connecting
- Asks an open-ended question related to their work
- Is conversational, not formal

Just the message:
"""
        
        return await self._generate(prompt, max_tokens=150)

    async def score_prospect(self, prospect: dict, target_criteria: dict) -> dict:
        """Score prospect as a lead (1-10)"""
        
        prompt = f"""
Score this LinkedIn prospect as a lead.

Prospect:
- {prospect.get('full_name')}, {prospect.get('title')} at {prospect.get('company')}
- Headline: {prospect.get('headline', 'N/A')}

Target criteria:
- Looking for: {target_criteria.get('title', 'professionals')}
- Industry: {target_criteria.get('industry', 'any')}

Return ONLY valid JSON (no markdown):
{{
  "score": 1-10,
  "reasoning": "One sentence why",
  "recommended_hook": "Conversation starter"
}}
"""
        
        response = await self._generate(prompt, max_tokens=200)
        return _parse_json(response)

    async def _generate(self, prompt: str, max_tokens: int = 500) -> str:
        if self.provider == "anthropic":
            return await self._call_anthropic(prompt, max_tokens)
        elif self.provider == "openai":
            return await self._call_openai(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_anthropic(self, prompt, max_tokens):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def _call_openai(self, prompt, max_tokens):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("LLM did not return valid JSON")
