"""
LinkedIn Automation Service
Uses user's LinkedIn credentials to perform actions
"""

import asyncio
from playwright.async_api import async_playwright
import random


class LinkedInService:
    def __init__(self, credentials: dict):
        self.email = credentials["email"]
        self.password = credentials["password"]
        self.session = credentials.get("session")  # Cookies if already logged in
        self.browser = None
        self.page = None

    async def login(self):
        """Login to LinkedIn"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Load existing session if available
            if self.session:
                try:
                    await context.add_cookies(self.session)
                except Exception as e:
                    print(f"Could not restore session: {e}")
                    self.session = None
            
            self.page = await context.new_page()
            await self.page.goto('https://www.linkedin.com/login', timeout=30000)
            
            # If not logged in, perform login
            if not self.session or '/login' in self.page.url:
                # Wait for login form
                await self.page.wait_for_selector('input[name="session_key"]', timeout=10000)
                
                await self.page.fill('input[name="session_key"]', self.email)
                await self.page.fill('input[name="session_password"]', self.password)
                await self.page.click('button[type="submit"]')
                
                # Wait for navigation
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=30000)
                except Exception:
                    # Sometimes networkidle doesn't trigger, check URL instead
                    await asyncio.sleep(3)
                
                # Check if login was successful
                if '/checkpoint/challenge' in self.page.url:
                    raise ValueError("LinkedIn security challenge detected - manual login required")
                elif '/login' in self.page.url:
                    raise ValueError("Login failed - check credentials")
                
                # Save session
                self.session = await context.cookies()
                
        except Exception as e:
            if self.browser:
                await self.browser.close()
            raise ValueError(f"LinkedIn login failed: {str(e)}")

    async def send_connection_request(self, profile_url: str, note: str = "") -> dict:
        """Send connection request to prospect"""
        try:
            await self.page.goto(profile_url)
            await self._random_delay(2, 4)
            
            # Find Connect button
            connect_btn = await self.page.query_selector('button:has-text("Connect")')
            if not connect_btn:
                return {"success": False, "error": "Connect button not found"}
            
            await connect_btn.click()
            await self._random_delay(1, 2)
            
            # Add note if provided
            if note:
                add_note_btn = await self.page.query_selector('button:has-text("Add a note")')
                if add_note_btn:
                    await add_note_btn.click()
                    await self._random_delay(0.5, 1)
                    
                    note_field = await self.page.query_selector('textarea[name="message"]')
                    if note_field:
                        await note_field.fill(note)
                        await self._random_delay(0.5, 1)
            
            # Send connection
            send_btn = await self.page.query_selector('button:has-text("Send")')
            if send_btn:
                await send_btn.click()
                await self._random_delay(1, 2)
                return {"success": True}
            
            return {"success": False, "error": "Send button not found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_message(self, profile_url: str, message: str) -> dict:
        """Send message to connection"""
        try:
            await self.page.goto(profile_url)
            await self._random_delay(2, 4)
            
            # Click Message button
            message_btn = await self.page.query_selector('button:has-text("Message")')
            if not message_btn:
                return {"success": False, "error": "Message button not found (not connected?)"}
            
            await message_btn.click()
            await self._random_delay(1, 2)
            
            # Type message
            message_box = await self.page.query_selector('div[role="textbox"]')
            if message_box:
                await message_box.fill(message)
                await self._random_delay(1, 2)
                
                # Send
                send_btn = await self.page.query_selector('button[type="submit"]')
                if send_btn:
                    await send_btn.click()
                    await self._random_delay(1, 2)
                    return {"success": True}
            
            return {"success": False, "error": "Message box not found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def visit_profile(self, profile_url: str) -> dict:
        """Visit a profile (for engagement/visibility)"""
        try:
            await self.page.goto(profile_url)
            await self._random_delay(3, 6)  # Simulate reading profile
            
            # Scroll down a bit (human-like)
            await self.page.evaluate("window.scrollBy(0, 300)")
            await self._random_delay(1, 2)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()

    async def _random_delay(self, min_sec: float, max_sec: float):
        """Human-like random delay"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
