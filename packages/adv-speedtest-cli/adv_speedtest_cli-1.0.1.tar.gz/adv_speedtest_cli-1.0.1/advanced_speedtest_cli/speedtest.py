#!/usr/bin/env python3
"""
Advanced Speedtest CLI - A cross-platform speedtest utility
Version: 1.0.0
Author: Shakil Ahmed
Email: shakilofficial0@gmail.com
"""

import os
import sys
import json
import requests
import asyncio
import websockets
import time
import random
import re
import uuid
import hashlib
import threading
import concurrent.futures
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from colorama import Fore, Style, init
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class Config:
    """Configuration constants"""
    VERSION = "1.0.1"
    AUTHOR = "Shakil Ahmed"
    GITHUB_REPO_LINK = "https://github.com/shakilofficial0/adv-speedtest-cli"
    EMAIL = "shakilofficial0@gmail.com"
    BANNER =  """
░█▀▀░█▀█░█▀▀░█▀▀░█▀▄░▀█▀░█▀▀░█▀▀░▀█▀░░░░░█▀▀░█░░░▀█▀
░▀▀█░█▀▀░█▀▀░█▀▀░█░█░░█░░█▀▀░▀▀█░░█░░▄▄▄░█░░░█░░░░█░
░▀▀▀░▀░░░▀▀▀░▀▀▀░▀▀░░░▀░░▀▀▀░▀▀▀░░▀░░░░░░▀▀▀░▀▀▀░▀▀▀
"""
    # API endpoints
    SPEEDTEST_LOGIN_API = "https://api.speedtest.net/user-login.php"
    
    @staticmethod
    def get_cookies_file_path() -> Path:
        """Get cross-platform cookies storage path"""
        if os.name == 'nt':  # Windows
            app_data = os.getenv('APPDATA') or os.path.expanduser('~')
            cookies_dir = Path(app_data) / 'adv-speedtest-cli'
        else:  # macOS and Linux
            cookies_dir = Path.home() / '.adv-speedtest-cli'
        
        cookies_dir.mkdir(parents=True, exist_ok=True)
        return cookies_dir / 'cookies.json'


class CookieManager:
    """Manage authentication cookies for speedtest.net"""
    
    @staticmethod
    def save_cookies(email: str, cookies: dict, expiration: Optional[str] = None) -> None:
        """Save cookies to file for a specific email
        
        Args:
            email: User email
            cookies: Dictionary of cookies to store
            expiration: Expiration timestamp (from response headers), if available
        """
        cookies_file = Config.get_cookies_file_path()
        
        try:
            # Load existing cookies
            if cookies_file.exists():
                with open(cookies_file, 'r') as f:
                    all_cookies = json.load(f)
            else:
                all_cookies = {}
            
            # Calculate expiration time if not provided
            if not expiration and cookies:
                # Look for expiration in cookies
                for key, value in cookies.items():
                    if isinstance(value, dict) and 'expires' in value:
                        expiration = value['expires']
                        break
            
            # Store cookies with metadata
            all_cookies[email] = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'expires_at': expiration or None
            }
            
            # Save to file
            with open(cookies_file, 'w') as f:
                json.dump(all_cookies, f, indent=2)
            
        except Exception as e:
            print(f"✗ Error saving cookies: {str(e)}")
    
    @staticmethod
    def load_cookies(email: str) -> Optional[dict]:
        """Load cookies for a specific email"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return None
            
            with open(cookies_file, 'r') as f:
                all_cookies = json.load(f)
            
            user_data = all_cookies.get(email)
            if user_data and isinstance(user_data, dict):
                # Handle both old format (direct cookies) and new format (with metadata)
                if 'cookies' in user_data:
                    return user_data['cookies']
                else:
                    return user_data
            
            return None
        
        except Exception as e:
            print(f"✗ Error loading cookies: {str(e)}")
            return None
    
    @staticmethod
    def save_user_data(email: str, user_data: dict) -> None:
        """Save user profile data to cache
        
        Args:
            email: User email
            user_data: User profile data from window.OOKLA.globals
        """
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if cookies_file.exists():
                with open(cookies_file, 'r') as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            
            if email not in all_data:
                all_data[email] = {}
            
            user_entry = all_data[email]
            if isinstance(user_entry, dict):
                user_entry['user_data'] = user_data
                user_entry['user_data_saved_at'] = datetime.now().isoformat()
            
            with open(cookies_file, 'w') as f:
                json.dump(all_data, f, indent=2)
        
        except Exception as e:
            print(f"✗ Error saving user data: {str(e)}")
    
    @staticmethod
    def load_user_data(email: str) -> Optional[dict]:
        """Load user profile data from cache
        
        Args:
            email: User email
            
        Returns:
            User profile data dict or None if not found
        """
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return None
            
            with open(cookies_file, 'r') as f:
                all_data = json.load(f)
            
            user_entry = all_data.get(email)
            if user_entry and isinstance(user_entry, dict):
                return user_entry.get('user_data')
            
            return None
        
        except Exception as e:
            print(f"✗ Error loading user data: {str(e)}")
            return None
    
    @staticmethod
    def is_cookie_expired(email: str) -> bool:
        """Check if stored cookies have expired"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return True
            
            with open(cookies_file, 'r') as f:
                all_cookies = json.load(f)
            
            user_data = all_cookies.get(email)
            if not user_data:
                return True
            
            # If new format with metadata
            if isinstance(user_data, dict) and 'expires_at' in user_data:
                expires_at = user_data.get('expires_at')
                if expires_at:
                    try:
                        expiry_datetime = datetime.fromisoformat(expires_at)
                        return datetime.now() > expiry_datetime
                    except ValueError:
                        # If we can't parse the date, assume not expired
                        return False
                return False
            
            # If old format (direct cookies), assume not expired
            return False
        
        except Exception as e:
            print(f"✗ Error checking cookie expiration: {str(e)}")
            return True
    
    @staticmethod
    def get_cookie_expiration(email: str) -> Optional[str]:
        """Get expiration date string for a user's cookies"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return None
            
            with open(cookies_file, 'r') as f:
                all_cookies = json.load(f)
            
            user_data = all_cookies.get(email)
            if isinstance(user_data, dict) and 'expires_at' in user_data:
                return user_data.get('expires_at')
            
            return None
        
        except Exception as e:
            print(f"✗ Error getting cookie expiration: {str(e)}")
            return None
    
    @staticmethod
    def delete_cookies(email: str) -> None:
        """Delete cookies for a specific email"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return
            
            with open(cookies_file, 'r') as f:
                all_cookies = json.load(f)
            
            if email in all_cookies:
                del all_cookies[email]
                
                with open(cookies_file, 'w') as f:
                    json.dump(all_cookies, f, indent=2)
        
        except Exception as e:
            print(f"✗ Error deleting cookies: {str(e)}")
    
    @staticmethod
    def get_cached_users() -> list:
        """Get list of all cached/previously logged-in users"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if not cookies_file.exists():
                return []
            
            with open(cookies_file, 'r') as f:
                all_cookies = json.load(f)
            
            return list(all_cookies.keys())
        
        except Exception as e:
            print(f"✗ Error reading cached users: {str(e)}")
            return []


class LoginManager:
    """Handle speedtest.net authentication and login"""
    
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    @staticmethod
    def fetch_session_cookie() -> Optional[dict]:
        """Fetch initial session cookie from speedtest.net"""
        try:
            headers = {
                'User-Agent': LoginManager.USER_AGENT,
                'Referer': 'https://api.speedtest.net/user-login.php'
            }
            
            response = requests.get(
                Config.SPEEDTEST_LOGIN_API,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            
            # Extract cookies from response
            if response.cookies:
                return dict(response.cookies)
            
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching session: {str(e)}")
            return None
    
    @staticmethod
    def verify_cached_login(email: str) -> bool:
        """Verify if cached login is still valid and fetch user details"""
        cookies = CookieManager.load_cookies(email)
        
        if not cookies:
            return False
        
        try:
            headers = {
                'User-Agent': LoginManager.USER_AGENT,
                'Referer': 'https://api.speedtest.net/user-login.php'
            }
            
            # Verify cached cookies by making a GET request
            response = requests.get(
                Config.SPEEDTEST_LOGIN_API,
                headers=headers,
                cookies=cookies,
                timeout=10,
                allow_redirects=False
            )
            
            # If cookies are valid and user is authenticated, we should get a redirect or success
            if response.status_code in [200, 302]:
                # Fetch user details for cached login
                user_data = LoginManager.fetch_user_details(email)
                return user_data is not None
            
            return False
        
        except requests.exceptions.RequestException:
            return False
    
    @staticmethod
    def login_with_credentials(email: str, password: str) -> Optional[str]:
        """Login with email and password
        
        Returns email if successful (status 302), None if failed (status 200)
        """
        try:
            # Step 1: Fetch initial session cookie
            print("Fetching session...")
            session_cookies = LoginManager.fetch_session_cookie()
            
            if not session_cookies:
                print("✗ Failed to fetch session")
                return None
            
            # Step 2: Login with credentials
            print("Authenticating...")
            headers = {
                'User-Agent': LoginManager.USER_AGENT,
                'Origin': 'https://api.speedtest.net',
                'Referer': 'https://api.speedtest.net/user-login.php',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            login_data = {
                'action': 'login',
                'email': email,
                'password': password,
                'remember-me': 'on'
            }
            
            response = requests.post(
                Config.SPEEDTEST_LOGIN_API,
                data=login_data,
                headers=headers,
                cookies=session_cookies,
                timeout=10,
                allow_redirects=False
            )
            
            # Status 302 means redirect (successful login)
            if response.status_code == 302:
                # Merge new cookies with session cookies
                all_cookies = {**session_cookies}
                if response.cookies:
                    all_cookies.update(dict(response.cookies))
                
                # Extract expiration time from Set-Cookie headers
                expiration = None
                if 'set-cookie' in response.headers:
                    # Parse Set-Cookie header for Max-Age or expires
                    cookie_header = response.headers['set-cookie']
                    if 'Max-Age=' in cookie_header:
                        try:
                            max_age_str = cookie_header.split('Max-Age=')[1].split(';')[0]
                            max_age = int(max_age_str)
                            expiration_datetime = datetime.now()
                            from datetime import timedelta
                            expiration_datetime += timedelta(seconds=max_age)
                            expiration = expiration_datetime.isoformat()
                        except (ValueError, IndexError):
                            pass
                
                CookieManager.save_cookies(email, all_cookies, expiration)
                print(f"✓ Login successful!")
                
                # Fetch user details from speedtest homepage
                user_data = LoginManager.fetch_user_details(email)
                if user_data:
                    print(f"✓ User data cached: {user_data.get('userName', 'Unknown')}")
                
                return email
            # Status 200 means failed login
            elif response.status_code == 200:
                print("✗ Invalid credentials")
                return None
            else:
                print(f"✗ Unexpected response status: {response.status_code}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Login failed: {str(e)}")
            return None
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def fetch_user_details(email: str) -> Optional[dict]:
        """Fetch user details from https://www.speedtest.net/
        
        Extracts window.OOKLA.globals data from the page HTML.
        Returns the user data if logged in, None otherwise.
        """
        try:
            cookies = CookieManager.load_cookies(email)
            
            if not cookies:
                print("✗ No cookies found for user")
                return None
            
            print("Fetching user details...")
            headers = {
                'User-Agent': LoginManager.USER_AGENT,
                'Referer': 'https://www.speedtest.net/'
            }
            
            response = requests.get(
                'https://www.speedtest.net/',
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"✗ Failed to fetch user details (Status: {response.status_code})")
                return None
            
            # Extract window.OOKLA.globals from HTML
            html_content = response.text
            
            # Find the script tag containing window.OOKLA.globals
            import re
            pattern = r'window\.OOKLA\.globals\s*=\s*({.*?});\s*window\.OOKLA\.isBlocked'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if not match:
                print("✗ Could not find user data in page")
                return None
            
            try:
                globals_json_str = match.group(1)
                user_data = json.loads(globals_json_str)
                
                # Check if user is logged in
                if user_data.get('userName'):
                    print(f"✓ User details fetched for {user_data.get('userName')}")
                    # Save user data to cache
                    CookieManager.save_user_data(email, user_data)
                    return user_data
                else:
                    print("✗ User not logged in")
                    return None
            
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse user data: {str(e)}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching user details: {str(e)}")
            return None
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def logout_with_cookies(email: str) -> bool:
        """Logout using stored cookies
        
        Sends GET request to logout endpoint. Returns True regardless of status code.
        """
        try:
            cookies = CookieManager.load_cookies(email)
            
            if not cookies:
                print("✗ No cached cookies found")
                return False
            
            print("Logging out...")
            headers = {
                'User-Agent': LoginManager.USER_AGENT,
                'Referer': 'https://api.speedtest.net/user-logout.php'
            }
            
            response = requests.get(
                'https://api.speedtest.net/user-logout.php',
                headers=headers,
                cookies=cookies,
                timeout=10,
                allow_redirects=False
            )
            
            # Status 302 or 200 both mean logout successful
            if response.status_code in [200, 302]:
                print("✓ Logout successful!")
                return True
            else:
                print(f"✗ Logout failed with status {response.status_code}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Logout error: {str(e)}")
            return False
        except KeyboardInterrupt:
            raise


class ServerManager:
    """Handle speedtest server operations"""
    
    CONFIG_API = "https://www.speedtest.net/api/js/config-sdk?engine=js&limit=10&https_functional=true"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    
    @staticmethod
    def get_or_create_anonymous_user() -> str:
        """Get or create anonymous user for non-logged-in users"""
        anonymous_email = "anonymous_user"
        
        # Check if anonymous user already has cookies
        existing_cookies = CookieManager.load_cookies(anonymous_email)
        if existing_cookies:
            return anonymous_email
        
        # Create anonymous user with empty cookies
        CookieManager.save_cookies(anonymous_email, {})
        return anonymous_email
    
    @staticmethod
    def fetch_server_config(user_email: Optional[str] = None) -> Optional[dict]:
        """Fetch server configuration from speedtest API
        
        Args:
            user_email: User email to use cookies from. If None, uses anonymous user.
            
        Returns:
            dict with config data including servers, or None if failed
        """
        try:
            # Use anonymous user if no email provided
            if not user_email:
                user_email = ServerManager.get_or_create_anonymous_user()
            
            # Load cookies for user
            cookies = CookieManager.load_cookies(user_email)
            if not cookies:
                cookies = {}
            
            print("Fetching server configuration...")
            headers = {
                'User-Agent': ServerManager.USER_AGENT,
                'Referer': 'https://www.speedtest.net/'
            }
            
            response = requests.get(
                ServerManager.CONFIG_API,
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                config_data = response.json()
                
                # Store token and guid in user data
                if 'clientAuth' in config_data and 'token' in config_data['clientAuth']:
                    ServerManager._save_client_auth(user_email, config_data['clientAuth'], config_data.get('guid'))
                
                print(f"✓ Server configuration fetched successfully!")
                return config_data
            else:
                print(f"✗ Failed to fetch config (Status: {response.status_code})")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching server config: {str(e)}")
            return None
        except ValueError as e:
            print(f"✗ Invalid response format: {str(e)}")
            return None
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def _save_client_auth(user_email: str, client_auth: dict, guid: Optional[str]) -> None:
        """Save client auth token and guid to user data"""
        cookies_file = Config.get_cookies_file_path()
        
        try:
            if cookies_file.exists():
                with open(cookies_file, 'r') as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            
            if user_email not in all_data:
                all_data[user_email] = {}
            
            user_data = all_data[user_email]
            if isinstance(user_data, dict):
                user_data['client_auth'] = client_auth
                if guid:
                    user_data['guid'] = guid
            
            with open(cookies_file, 'w') as f:
                json.dump(all_data, f, indent=2)
        
        except Exception as e:
            print(f"✗ Error saving client auth: {str(e)}")
    
    @staticmethod
    def pick_random_server(servers: list) -> Optional[dict]:
        """Pick a random server from the list
        
        Args:
            servers: List of server dictionaries
            
        Returns:
            Random server dict or None if list is empty
        """
        if not servers:
            return None
        
        import random
        return random.choice(servers)
    
    @staticmethod
    def fetch_search_results(search_query: str, user_email: Optional[str] = None) -> Optional[dict]:
        """Fetch servers matching search criteria
        
        Args:
            search_query: Search query (ISP, server name, or location)
            user_email: User email to use cookies from. If None, uses anonymous user.
            
        Returns:
            dict with config data including filtered servers, or None if failed
        """
        try:
            # Use anonymous user if no email provided
            if not user_email:
                user_email = ServerManager.get_or_create_anonymous_user()
            
            # Load cookies for user
            cookies = CookieManager.load_cookies(user_email)
            if not cookies:
                cookies = {}
            
            # URL encode the search query
            from urllib.parse import quote
            encoded_query = quote(search_query)
            
            search_api = f"https://www.speedtest.net/api/js/config-sdk?engine=js&limit=30&https_functional=true&search={encoded_query}"
            
            print(f"Searching for servers matching '{search_query}'...")
            headers = {
                'User-Agent': ServerManager.USER_AGENT,
                'Referer': 'https://www.speedtest.net/'
            }
            
            response = requests.get(
                search_api,
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                config_data = response.json()
                
                # Store token and guid in user data
                if 'clientAuth' in config_data and 'token' in config_data['clientAuth']:
                    ServerManager._save_client_auth(user_email, config_data['clientAuth'], config_data.get('guid'))
                
                if 'servers' in config_data and config_data['servers']:
                    print(f"✓ Found {len(config_data['servers'])} server(s) matching your search!")
                else:
                    print("✗ No servers found matching your search criteria.")
                
                return config_data
            else:
                print(f"✗ Failed to search servers (Status: {response.status_code})")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error searching servers: {str(e)}")
            return None
        except ValueError as e:
            print(f"✗ Invalid response format: {str(e)}")
            return None
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def get_distance_color(distance: float) -> str:
        """Get color code based on distance
        
        Distance ranges:
        0-100km: Green
        100-500km: Cyan
        500-1000km: Yellow
        1000-2000km: Magenta
        2000+km: Red
        """
        if distance <= 100:
            return Fore.GREEN
        elif distance <= 500:
            return Fore.CYAN
        elif distance <= 1000:
            return Fore.YELLOW
        elif distance <= 2000:
            return Fore.MAGENTA
        else:
            return Fore.RED
    
    @staticmethod
    def get_server_display_name(server: dict) -> str:
        """Get formatted display name for a server with color-coded distance"""
        sponsor = server.get('sponsor', 'Unknown')
        name = server.get('name', 'Unknown')
        distance = server.get('distance', 0)
        country = server.get('country', 'Unknown')
        
        distance_color = ServerManager.get_distance_color(distance)
        distance_str = f"{distance_color}{distance}km{Style.RESET_ALL}"
        
        return f"{sponsor} - {name}, {country} ({distance_str})"


class State:
    """Application state management"""
    def __init__(self):
        self.is_logged_in = False
        self.current_user = None
        self.selected_server = None  # Store full server dict
        self.speedtest_mode = "multiple"  # 'multiple' or 'single'
        self.parallel_connections = 8  # Default number of parallel connections
    
    def login(self, username: str):
        """Set user as logged in"""
        self.is_logged_in = True
        self.current_user = username
    
    def logout(self):
        """Logout user"""
        self.is_logged_in = False
        self.current_user = None
    
    def set_server(self, server_dict: Optional[dict]):
        """Set selected server
        
        Args:
            server_dict: Server dictionary from API or None for auto-pick
        """
        self.selected_server = server_dict
    
    def get_server_display(self) -> str:
        """Get server display text"""
        if self.selected_server is None:
            return "Auto Pick"
        
        # If it's a dict, get the display name
        if isinstance(self.selected_server, dict):
            return ServerManager.get_server_display_name(self.selected_server)
        
        # Fallback for string (legacy)
        return str(self.selected_server)


class Display:
    """Handle all display and UI related functions"""
    
    @staticmethod
    def clear_screen():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_banner(banner_text: str):
        """Print ASCII art banner"""
        print(banner_text)
    
    @staticmethod
    def print_header() -> None:
        """Print header with banner and author details"""
        Display.clear_screen()
        Display.print_banner(Config.BANNER)
        print("=" * 50)
        print(f"Version: {Config.VERSION}")
        print(f"GitHub: {Config.GITHUB_REPO_LINK}")
        print(f"Author: {Config.AUTHOR}")
        print(f"Email: {Config.EMAIL}")
        print("=" * 50)
        print()
    
    @staticmethod
    def print_menu(state: State) -> None:
        """Display main menu"""
        Display.print_header()
        
        # Build menu
        menu_items = []
        menu_number = 1
        
        # Login/Logout option
        if not state.is_logged_in:
            menu_items.append((menu_number, "Login"))
            menu_number += 1
        
        # Server selection with color coding
        server_display = state.get_server_display()
        if server_display == "Auto Pick":
            colored_server = f"{Fore.YELLOW}{server_display}{Style.RESET_ALL}"
        else:
            colored_server = f"{Fore.GREEN}{server_display}{Style.RESET_ALL}"
        
        menu_items.append((menu_number, f"Select Server ({colored_server})"))
        menu_number += 1
        
        # Speed test options
        menu_items.append((menu_number, "Run SpeedTest"))
        menu_number += 1
        
        menu_items.append((menu_number, "Run SpeedTest and Share"))
        menu_number += 1
        
        # Settings option
        menu_items.append((menu_number, "Settings"))
        menu_number += 1
        
        # Logout option (only if logged in)
        if state.is_logged_in:
            menu_items.append((menu_number, f"Logout ({state.current_user})"))
            menu_number += 1
        
        # Display menu items
        print("MENU")
        print("=" * 50)
        for num, item in menu_items:
            print(f"{num}. {item}")
        print("0. Exit")
        print("=" * 50)
        print()
        
        return menu_items
    
    @staticmethod
    def print_footer() -> None:
        """Print author credits and version"""
        print()
        print("=" * 50)
        print(f"Version: {Config.VERSION}")
        print(f"GitHub: {Config.GITHUB_REPO_LINK}")
        print(f"Author: {Config.AUTHOR}")
        print(f"Email: {Config.EMAIL}")
        print("=" * 50)


class AuthManager:
    """Handle authentication operations - UI layer"""
    
    @staticmethod
    def login() -> Optional[str]:
        """Handle user login with UI"""
        try:
            Display.print_header()
            print("LOGIN")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            # Get cached users (excluding anonymous_user)
            all_cached_users = CookieManager.get_cached_users()
            cached_users = [u for u in all_cached_users if u != "anonymous_user"]
            
            if cached_users:
                print("Previously logged-in users:")
                print("-" * 50)
                for idx, user_email in enumerate(cached_users, 1):
                    # Check if cookie is expired
                    is_expired = CookieManager.is_cookie_expired(user_email)
                    expiration_str = CookieManager.get_cookie_expiration(user_email)
                    
                    if is_expired:
                        print(f"{idx}. {user_email} {Fore.RED}[EXPIRED]{Style.RESET_ALL}")
                    elif expiration_str:
                        print(f"{idx}. {user_email} (Expires: {expiration_str})")
                    else:
                        print(f"{idx}. {user_email}")
                
                print(f"{len(cached_users) + 1}. New Login")
                print("-" * 50)
                print()
                
                try:
                    choice = input("Select user or enter new login (number): ").strip()
                    choice_num = int(choice)
                    
                    # Check if user selected a cached user
                    if 1 <= choice_num <= len(cached_users):
                        selected_email = cached_users[choice_num - 1]
                        
                        # Check if cookies are expired
                        if CookieManager.is_cookie_expired(selected_email):
                            print("\n✗ Cached login expired. Please enter password.")
                            password = input("Enter password: ").strip()
                            result = LoginManager.login_with_credentials(selected_email, password)
                            if result:
                                print(f"✓ Login successful! Welcome {selected_email}")
                                input("Press Enter to continue...")
                                return result
                            else:
                                input("Press Enter to continue...")
                                return None
                        
                        # Verify cached login
                        print("\nVerifying cached login...")
                        if LoginManager.verify_cached_login(selected_email):
                            print(f"✓ Login successful! Welcome {selected_email}")
                            input("Press Enter to continue...")
                            return selected_email
                        else:
                            print("✗ Cached login verification failed. Please enter password.")
                            password = input("Enter password: ").strip()
                            result = LoginManager.login_with_credentials(selected_email, password)
                            if result:
                                print(f"✓ Login successful! Welcome {selected_email}")
                                input("Press Enter to continue...")
                                return result
                            else:
                                input("Press Enter to continue...")
                                return None
                    # User chose "New Login"
                    elif choice_num == len(cached_users) + 1:
                        email = input("Enter email: ").strip()
                        password = input("Enter password: ").strip()
                        
                        result = LoginManager.login_with_credentials(email, password)
                        
                        if result:
                            print(f"✓ Login successful! Welcome {email}")
                            input("Press Enter to continue...")
                            return result
                        else:
                            input("Press Enter to continue...")
                            return None
                    else:
                        print("✗ Invalid selection")
                        input("Press Enter to continue...")
                        return None
                
                except ValueError:
                    print("✗ Invalid input. Please enter a number.")
                    input("Press Enter to continue...")
                    return None
            
            else:
                # No cached users, proceed with new login
                email = input("Enter email: ").strip()
                password = input("Enter password: ").strip()
                
                result = LoginManager.login_with_credentials(email, password)
                
                if result:
                    print(f"✓ Login successful! Welcome {email}")
                    input("Press Enter to continue...")
                    return result
                else:
                    input("Press Enter to continue...")
                    return None
        
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by the menu handler
    
    @staticmethod
    def logout(email: str) -> None:
        """Handle user logout with UI"""
        try:
            Display.print_header()
            print("LOGOUT")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            confirm = input(f"Logout from {email}? (y/n): ").strip().lower()
            if confirm == 'y':
                # Send logout request to API
                logout_success = LoginManager.logout_with_cookies(email)
                
                # Remove cached cookies regardless of logout response
                CookieManager.delete_cookies(email)
                
                if logout_success:
                    print(f"✓ Logged out successfully")
                else:
                    print(f"✓ Cookies cleared locally")
            else:
                print("✗ Logout cancelled")
            
            input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by the menu handler


class ServerSelectionUI:
    """Handle server selection UI - wrapper around ServerManager"""
    
    @staticmethod
    def search_server(current_user: Optional[str] = None) -> Optional[dict]:
        """Handle server search functionality
        
        Args:
            current_user: Currently logged-in user email
            
        Returns:
            Selected server dict or None if cancelled
        """
        try:
            Display.print_header()
            print("SEARCH SERVER")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            search_query = input("Enter search criteria (ISP/Server/Location): ").strip()
            
            if not search_query:
                print("✗ Search query cannot be empty")
                input("Press Enter to continue...")
                return None
            
            print()
            # Fetch search results
            config = ServerManager.fetch_search_results(search_query, current_user)
            
            if not config or 'servers' not in config or not config['servers']:
                print("✗ No servers found")
                input("Press Enter to continue...")
                return None
            
            servers = config['servers']
            
            print()
            for idx, server in enumerate(servers, 1):
                display_name = ServerManager.get_server_display_name(server)
                print(f"{idx}. {display_name}")
            
            print("=" * 50)
            print()
            
            choice = int(input("Select server number: ").strip())
            
            if 1 <= choice <= len(servers):
                selected_server = servers[choice - 1]
                display_name = ServerManager.get_server_display_name(selected_server)
                print(f"✓ Server selected: {display_name}")
                input("Press Enter to continue...")
                return selected_server
            else:
                print("✗ Invalid selection")
                input("Press Enter to continue...")
                return None
        
        except ValueError:
            print("✗ Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            return None
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def select_server(current_user: Optional[str] = None) -> Optional[dict]:
        """Handle server selection UI
        
        Args:
            current_user: Currently logged-in user email
            
        Returns:
            Selected server dict or None for auto-pick
        """
        try:
            Display.print_header()
            print("SELECT SERVER")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            # Fetch server configuration
            config = ServerManager.fetch_server_config(current_user)
            
            if not config or 'servers' not in config:
                print("✗ Failed to load servers")
                input("Press Enter to continue...")
                return None
            
            servers = config['servers']
            
            print("\n0. Auto Pick (Nearest Server)")
            for idx, server in enumerate(servers, 1):
                display_name = ServerManager.get_server_display_name(server)
                print(f"{idx}. {display_name}")
            
            total_options = len(servers) + 1  # +1 for search option
            print(f"{total_options}. Search Server")
            print("=" * 50)
            print()
            
            choice = int(input("Select server number: ").strip())
            
            if choice == 0:
                # Auto pick - choose random server
                selected_server = ServerManager.pick_random_server(servers)
                if selected_server:
                    display_name = ServerManager.get_server_display_name(selected_server)
                    print(f"✓ Server set to: {display_name} (Auto Pick)")
                    input("Press Enter to continue...")
                    return selected_server
                else:
                    print("✗ No servers available")
                    input("Press Enter to continue...")
                    return None
            
            elif 1 <= choice <= len(servers):
                selected_server = servers[choice - 1]
                display_name = ServerManager.get_server_display_name(selected_server)
                print(f"✓ Server selected: {display_name}")
                input("Press Enter to continue...")
                return selected_server
            
            elif choice == total_options:
                # Call search server
                return ServerSelectionUI.search_server(current_user)
            
            else:
                print("✗ Invalid selection")
                input("Press Enter to continue...")
                return None
        
        except ValueError:
            print("✗ Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            return None
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by the menu handler


class DownloadTest:
    """Handle download speed test with concurrent ping monitoring"""
    
    @staticmethod
    async def concurrent_ping_monitor(server: dict, duration: float, ping_queue: asyncio.Queue = None) -> List[float]:
        """Run continuous ping test during download
        
        Args:
            server: Server dictionary with 'host' key
            duration: How long to monitor pings (seconds)
            ping_queue: Optional asyncio.Queue to share pings in real-time
            
        Returns:
            List of ping times in milliseconds
        """
        ping_times = []
        
        try:
            host = server.get('host')
            if not host:
                return ping_times
            
            ws_url = f"wss://{host}/ws?"
            
            try:
                async with websockets.connect(ws_url, ping_interval=None) as websocket:
                    start_time = time.time()
                    ping_count = 0
                    
                    while time.time() - start_time < duration:
                        try:
                            # Send PING with timestamp
                            ping_timestamp = int(time.time() * 1000)
                            ping_message = f"PING {ping_timestamp}\t{ping_count}\t"
                            
                            send_time = time.time()
                            await asyncio.wait_for(websocket.send(ping_message), timeout=2.0)
                            
                            # Wait for PONG response
                            pong_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            
                            receive_time = time.time()
                            
                            # Calculate latency in milliseconds
                            latency_ms = (receive_time - send_time) * 1000
                            ping_times.append(latency_ms)
                            ping_count += 1
                            
                            # Share ping in real-time via queue
                            if ping_queue:
                                await ping_queue.put(latency_ms)
                            
                            # Small delay between pings
                            await asyncio.sleep(0.2)
                        
                        except (asyncio.TimeoutError, Exception):
                            # Continue monitoring even if a ping fails
                            ping_count += 1
                            await asyncio.sleep(0.2)
                
            except (websockets.exceptions.WebSocketException, OSError):
                pass
            
        except Exception:
            pass
        
        
        return ping_times
    
    @staticmethod
    def time_based_download(url: str, test_duration: int, pbar: tqdm = None) -> tuple:
        """Download data for a fixed time period with speed tracking
        
        Args:
            url: Download URL
            test_duration: How long to download in seconds
            pbar: Progress bar object to update
            
        Returns:
            Tuple of (total_bytes, speed_samples) where speed_samples are instantaneous speeds
        """
        bytes_downloaded = 0
        start_time = time.time()
        speed_samples = []
        last_update_time = start_time
        last_update_bytes = 0
        
        try:
            response = requests.get(url, stream=True, timeout=60, allow_redirects=True)
            
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=10240):
                    if chunk:
                        bytes_downloaded += len(chunk)
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        # Calculate instantaneous speed every 0.1 seconds
                        time_since_last = current_time - last_update_time
                        if time_since_last >= 0.1:
                            bytes_delta = bytes_downloaded - last_update_bytes
                            instant_speed_mbps = (bytes_delta * 8) / (time_since_last * 1_000_000)
                            if instant_speed_mbps > 0:
                                speed_samples.append(instant_speed_mbps)
                            
                            last_update_time = current_time
                            last_update_bytes = bytes_downloaded
                        
                        if pbar:
                            pbar.update(len(chunk))
                        
                        # Check if test duration exceeded
                        if elapsed >= test_duration:
                            break
        
        except Exception as e:
            pass
        
        return bytes_downloaded, speed_samples
    
    @staticmethod
    def is_speed_stable(speed_samples: List[float], threshold: float = 3.0, min_samples: int = 5) -> bool:
        """Check if speed has stabilized using coefficient of variation
        
        Args:
            speed_samples: List of speed measurements in Mbps
            threshold: Coefficient of variation threshold (3% = 0.03)
            min_samples: Minimum samples needed to determine stability
            
        Returns:
            True if speed is stable, False otherwise
        """
        if len(speed_samples) < min_samples:
            return False
        
        # Use last N samples to check recent stability
        recent_samples = speed_samples[-min_samples:]
        
        # Calculate mean and standard deviation
        mean_speed = sum(recent_samples) / len(recent_samples)
        
        if mean_speed == 0:
            return False
        
        # Calculate coefficient of variation (CV = std_dev / mean)
        variance = sum((x - mean_speed) ** 2 for x in recent_samples) / len(recent_samples)
        std_dev = variance ** 0.5
        cv = std_dev / mean_speed
        
        # Stable if CV is low (less than 10% variation)
        return cv < 0.10
    
    @staticmethod
    async def run_download_test(server: dict, state: State, initial_duration: int = 10, 
                               num_connections: int = 1, max_duration: int = 30) -> dict:
        """Run adaptive download speed test with stability detection
        
        Strategy:
        - Start with initial_duration (10s) minimum to get stable readings
        - Continuously monitor speed samples
        - When speed stabilizes (CV < 10%), can stop early
        - Use multiple connections to stabilize network
        - Never exceed max_duration (30s)
        - Calculate final speed using overall bytes/time for accuracy
        
        Args:
            server: Server dictionary with host, id, etc.
            state: Application state
            initial_duration: Initial probe duration in seconds
            num_connections: Number of parallel connections
            max_duration: Maximum test duration in seconds
            
        Returns:
            Dictionary with download statistics
        """
        try:
            host = server.get('host', '')
            
            if not host:
                return {
                    'speed': 0,
                    'bytes': 0,
                    'duration': 0,
                    'latency': {},
                    'error': 'No host available'
                }
            
            # Generate cache buster
            cache_buster = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            
            # Construct download URL
            download_url = f"https://{host}/download?nocache={cache_buster}&size=250000000"
            
            print(f"Downloading from: {host}")
            print()
            
            # Start concurrent ping monitor with shared queue
            ping_queue = asyncio.Queue()
            monitor_task = asyncio.create_task(DownloadTest.concurrent_ping_monitor(server, max_duration + 2, ping_queue))
            
            total_bytes = 0
            all_speed_samples = []
            
            # Unified download logic for both single and multi-connection
            if num_connections == 1:
                print("Starting download (single connection)...")
                desc = "Download"
            else:
                print(f"Starting {num_connections} parallel downloads...")
                desc = "Downloading"
            
            progress_data = {
                'bytes': 0,
                'speed_samples': [],
                'stop': False,
                'active_connections': num_connections,
                'connection_status': {i: True for i in range(num_connections)}
            }
            progress_lock = threading.Lock()
            
            def download_worker(conn_id):
                """Download from a connection with health tracking"""
                bytes_dl = 0
                local_samples = []
                start = time.time()
                last_update = start
                last_bytes = 0
                
                try:
                    response = requests.get(download_url, stream=True, timeout=60, allow_redirects=True)
                    
                    if response.status_code == 200:
                        while not progress_data['stop'] and time.time() - start < max_duration:
                            try:
                                chunk_data = response.raw.read(10240)
                                if not chunk_data:
                                    # Connection ended early - mark as unhealthy
                                    if num_connections > 1:
                                        with progress_lock:
                                            progress_data['connection_status'][conn_id] = False
                                            progress_data['stop'] = True
                                    break
                                
                                bytes_dl += len(chunk_data)
                                current_time = time.time()
                                
                                # Calculate instantaneous speed every 0.1 seconds
                                time_delta = current_time - last_update
                                if time_delta >= 0.1:
                                    bytes_delta = bytes_dl - last_bytes
                                    instant_speed = (bytes_delta * 8) / (time_delta * 1_000_000)
                                    if instant_speed > 0:
                                        local_samples.append(instant_speed)
                                    
                                    with progress_lock:
                                        progress_data['bytes'] += bytes_delta
                                        progress_data['speed_samples'].extend(local_samples[-1:])
                                    
                                    last_update = current_time
                                    last_bytes = bytes_dl
                            
                            except Exception:
                                # Connection error - mark as unhealthy
                                if num_connections > 1:
                                    with progress_lock:
                                        progress_data['connection_status'][conn_id] = False
                                        progress_data['stop'] = True
                                break
                    else:
                        # Bad status code
                        if num_connections > 1:
                            with progress_lock:
                                progress_data['connection_status'][conn_id] = False
                                progress_data['stop'] = True
                
                except Exception:
                    # Connection failed
                    if num_connections > 1:
                        with progress_lock:
                            progress_data['connection_status'][conn_id] = False
                            progress_data['stop'] = True
                
                return bytes_dl, local_samples
            
            start_time = time.time()
            skip_duration = 3  # Skip first 3 seconds (connection ramp-up)
            
            with tqdm(unit='B', unit_scale=True, desc=desc, bar_format='{desc}: {n_fmt} bytes, Speed: {rate_fmt}') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_connections) as executor:
                    futures = [executor.submit(download_worker, i) for i in range(num_connections)]
                    
                    last_bytes = 0
                    
                    while any(not f.done() for f in futures):
                        with progress_lock:
                            current_bytes = progress_data['bytes']
                            current_samples = progress_data['speed_samples'].copy()
                            all_healthy = all(progress_data['connection_status'].values())
                        
                        if current_bytes > last_bytes:
                            pbar.update(current_bytes - last_bytes)
                            last_bytes = current_bytes
                        
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        # Check connection health (only for multi-connection)
                        if num_connections > 1 and not all_healthy:
                            with progress_lock:
                                progress_data['stop'] = True
                            break
                        
                        # Check max duration
                        if elapsed >= max_duration:
                            with progress_lock:
                                progress_data['stop'] = True
                            break
                        
                        # Use asyncio.sleep to allow event loop to run
                        await asyncio.sleep(0.1)
                    
                    # Final update
                    with progress_lock:
                        final_bytes = progress_data['bytes']
                        all_speed_samples = progress_data['speed_samples'].copy()
                        progress_data['stop'] = True
                    
                    if final_bytes > last_bytes:
                        pbar.update(final_bytes - last_bytes)
                    
                    # Collect all results
                    for future in futures:
                        try:
                            conn_bytes, conn_samples = future.result(timeout=1)
                            total_bytes += conn_bytes
                        except Exception:
                            pass
            
            # Remove first 3 seconds of samples (connection ramp-up)
            filtered_samples = [s for i, s in enumerate(all_speed_samples) if i >= skip_duration]
            all_speed_samples = filtered_samples if filtered_samples else all_speed_samples
            
            total_duration = time.time() - start_time - 0.5  # 0.5 second buffer for connection cleanup
            
            # Wait for ping monitoring to complete
            ping_times = []
            
            try:
                # First, collect any pings already in the queue
                while not ping_queue.empty():
                    try:
                        ping = ping_queue.get_nowait()
                        ping_times.append(ping)
                    except asyncio.QueueEmpty:
                        break
                
                # Wait a bit for any remaining pings
                wait_start = time.time()
                while time.time() - wait_start < 1.0:
                    try:
                        ping = ping_queue.get_nowait()
                        ping_times.append(ping)
                    except asyncio.QueueEmpty:
                        await asyncio.sleep(0.05)
                
            except Exception:
                pass
            
            # Cancel the monitor task since we got what we need
            if not monitor_task.done():
                monitor_task.cancel()
            
            # Calculate final speed using overall bytes/time method
            overall_speed = (total_bytes * 8) / (total_duration * 1_000_000) if total_duration > 0 else 0
            speed_mbps = overall_speed
            
            # Calculate latency statistics
            latency_stats = {}
            if ping_times and ping_times != [0]:
                latency_stats = {
                    'min': min(ping_times),
                    'max': max(ping_times),
                    'avg': sum(ping_times) / len(ping_times),
                    'median': sorted(ping_times)[len(ping_times) // 2],
                    'count': len(ping_times)
                }
            
            print()
            print(f"✓ Download Complete!")
            print(f"  Speed: {speed_mbps:.2f} Mbps")
            print(f"  Duration: {total_duration:.2f}s")
            print(f"  Downloaded: {total_bytes / (1024*1024):.2f} MB")
            
            # Wait for latency stats if not available
            if not latency_stats and not monitor_task.done():
                retry_count = 0
                while not latency_stats and retry_count < 5 and not monitor_task.done():
                    try:
                        await asyncio.sleep(0.1)
                        if monitor_task.done():
                            ping_times = monitor_task.result()
                            if ping_times:
                                latency_stats = {
                                    'min': min(ping_times),
                                    'max': max(ping_times),
                                    'avg': sum(ping_times) / len(ping_times),
                                    'median': sorted(ping_times)[len(ping_times) // 2],
                                    'count': len(ping_times)
                                }
                            break
                        retry_count += 1
                    except Exception:
                        break
            
            if latency_stats:
                print(f"  Avg Ping: {PingTest.get_ping_color(latency_stats['avg'])}")
            
            return {
                'speed': speed_mbps,
                'bytes': total_bytes,
                'duration': total_duration,
                'latency': latency_stats,
                'samples': len(ping_times),
                'speed_samples_count': len(all_speed_samples)
            }
        
        except Exception as e:
            print(f"✗ Download test error: {str(e)}")
            return {
                'speed': 0,
                'bytes': 0,
                'duration': 0,
                'latency': {},
                'error': str(e)
            }
    
    @staticmethod
    async def run_upload_test(server: dict, state: State, test_duration: int = 15, 
                              num_connections: int = 1) -> dict:
        """Run time-based upload speed test
        
        Strategy:
        - Upload for fixed 15 seconds total
        - Skip first 3 seconds (connection ramp-up)
        - Measure speed only from second 3-12
        - Stop immediately at 12 seconds, close all connections
        - Calculate speed using bytes collected in the 3-12 second window
        
        Args:
            server: Server dictionary with host, id, etc.
            state: Application state
            test_duration: Total test duration in seconds (15s)
            num_connections: Number of parallel connections
            
        Returns:
            Dictionary with upload statistics
        """
        try:
            host = server.get('host', '')
            
            if not host:
                return {
                    'speed': 0,
                    'bytes': 0,
                    'duration': 0,
                    'latency': {},
                    'error': 'No host available'
                }
            
            # Generate cache buster
            cache_buster = hashlib.md5(str(time.time()).encode()).hexdigest()
            
            # Construct upload URL
            upload_url = f"https://{host}/upload?nocache={cache_buster}"
            
            print(f"Uploading to: {host}")
            print()
            
            # Start concurrent ping monitor with shared queue
            ping_queue = asyncio.Queue()
            monitor_task = asyncio.create_task(DownloadTest.concurrent_ping_monitor(server, test_duration + 2, ping_queue))
            
            total_bytes = 0
            all_speed_samples = []
            
            # Generate unlimited random data (will stop at 12 seconds)
            chunk_size = 10240  # 10KB chunks
            
            # Unified upload logic for both single and multi-connection
            if num_connections == 1:
                print("Starting upload (single connection)...")
                desc = "Upload"
            else:
                print(f"Starting {num_connections} parallel uploads...")
                desc = "Uploading"
            
            progress_data = {
                'bytes': 0,
                'speed_samples': [],
                'stop': False,
                'start_time': time.time(),
                'measurement_start': 3,  # Start measuring at 3 seconds
                'measurement_end': 12,   # Stop measuring at 12 seconds
                'active_connections': num_connections,
                'connection_status': {i: True for i in range(num_connections)}
            }
            progress_lock = threading.Lock()
            
            def upload_worker(conn_id):
                """Upload random data for fixed duration"""
                response = None
                
                try:
                    # Create a file-like object that tracks upload progress
                    class ProgressTracker:
                        def __init__(self, lock, progress_data, test_duration, conn_id):
                            self.chunk_size = 10240
                            self.bytes_sent = 0
                            self.lock = lock
                            self.progress_data = progress_data
                            self.test_duration = test_duration
                            self.conn_id = conn_id
                            self.last_update = time.time()
                            self.last_bytes = 0
                            self.base_time = progress_data['start_time']
                        
                        def read(self, size=-1):
                            current_time = time.time()
                            elapsed = current_time - self.base_time
                            
                            # Stop at 12 seconds - measurement end time
                            if elapsed >= self.progress_data['measurement_end']:
                                return b''
                            
                            # Check stop signal
                            if self.progress_data['stop']:
                                return b''
                            
                            # Generate random data chunk
                            data = os.urandom(self.chunk_size)
                            self.bytes_sent += len(data)
                            
                            # Update speed samples only during measurement window (3-12 seconds)
                            time_delta = current_time - self.last_update
                            
                            if time_delta >= 0.1:
                                bytes_delta = self.bytes_sent - self.last_bytes
                                instant_speed = (bytes_delta * 8) / (time_delta * 1_000_000)
                                
                                with self.lock:
                                    # Only update shared pool and samples during measurement window
                                    if elapsed >= self.progress_data['measurement_start'] and elapsed < self.progress_data['measurement_end']:
                                        self.progress_data['bytes'] += bytes_delta
                                        if instant_speed > 0:
                                            self.progress_data['speed_samples'].append(instant_speed)
                                
                                self.last_update = current_time
                                self.last_bytes = self.bytes_sent
                            
                            return data
                        
                        def __len__(self):
                            return 0xFFFFFFFF  # Unlimited size
                    
                    # Create progress tracker
                    tracker = ProgressTracker(progress_lock, progress_data, test_duration, conn_id)
                    
                    # Use a session with shorter timeout
                    session = requests.Session()
                    
                    try:
                        response = session.post(
                            upload_url,
                            data=tracker,
                            timeout=5,
                            allow_redirects=True,
                            stream=False
                        )
                    
                    except requests.exceptions.Timeout:
                        # Expected when we stop sending data - ignore
                        pass
                    
                    except Exception:
                        # Connection error - ignore
                        pass
                    
                    finally:
                        # Close the session immediately
                        session.close()
                
                except Exception:
                    pass
                
                return progress_data['bytes'], []
            
            start_time = time.time()
            
            with tqdm(unit='B', unit_scale=True, desc=desc, bar_format='{desc}: {n_fmt} bytes, Speed: {rate_fmt}') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_connections) as executor:
                    futures = [executor.submit(upload_worker, i) for i in range(num_connections)]
                    
                    last_bytes = 0
                    
                    # Monitor for test_duration + 2 seconds
                    while time.time() - start_time < test_duration + 2:
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        with progress_lock:
                            current_bytes = progress_data['bytes']
                        
                        if current_bytes > last_bytes:
                            pbar.update(current_bytes - last_bytes)
                            last_bytes = current_bytes
                        
                        # Check if we've reached measurement end time (12 seconds)
                        if elapsed >= 12:  # measurement_end time
                            with progress_lock:
                                progress_data['stop'] = True
                            break
                        
                        await asyncio.sleep(0.1)
                    
                    # Signal all workers to stop
                    with progress_lock:
                        progress_data['stop'] = True
                    
                    # Final update
                    with progress_lock:
                        final_bytes = progress_data['bytes']
                        all_speed_samples = progress_data['speed_samples'].copy()
                    
                    if final_bytes > last_bytes:
                        pbar.update(final_bytes - last_bytes)
                    
                    total_bytes = final_bytes
            
            # Measurement window is 3-12 seconds = 9 seconds
            # Speed = bytes_in_window / 9_seconds
            measurement_window = 9  # 12 - 3 seconds
            
            total_duration = measurement_window
            
            # Wait for ping monitoring to complete
            ping_times = []
            
            try:
                # First, collect any pings already in the queue
                while not ping_queue.empty():
                    try:
                        ping = ping_queue.get_nowait()
                        ping_times.append(ping)
                    except asyncio.QueueEmpty:
                        break
                
                # Wait a bit for any remaining pings
                wait_start = time.time()
                while time.time() - wait_start < 1.0:
                    try:
                        ping = ping_queue.get_nowait()
                        ping_times.append(ping)
                    except asyncio.QueueEmpty:
                        await asyncio.sleep(0.05)
                
            except Exception:
                pass
            
            # Cancel the monitor task
            if not monitor_task.done():
                monitor_task.cancel()
            
            # Calculate speed using bytes collected in measurement window and 9 second window
            overall_speed = (total_bytes * 8) / (total_duration * 1_000_000) if total_duration > 0 else 0
            speed_mbps = overall_speed
            
            # Calculate latency statistics
            latency_stats = {}
            if ping_times and ping_times != [0]:
                latency_stats = {
                    'min': min(ping_times),
                    'max': max(ping_times),
                    'avg': sum(ping_times) / len(ping_times),
                    'median': sorted(ping_times)[len(ping_times) // 2],
                    'count': len(ping_times)
                }
            
            print()
            print(f"✓ Upload Complete!")
            print(f"  Speed: {speed_mbps:.2f} Mbps")
            print(f"  Uploaded: {total_bytes / (1024*1024):.2f} MB")
            
            if latency_stats:
                print(f"  Avg Ping: {PingTest.get_ping_color(latency_stats['avg'])}")
            
            return {
                'speed': speed_mbps,
                'bytes': total_bytes,
                'duration': total_duration,
                'latency': latency_stats,
                'samples': len(ping_times),
                'speed_samples_count': len(all_speed_samples)
            }
        
        except Exception as e:
            print(f"✗ Upload test error: {str(e)}")
            return {
                'speed': 0,
                'bytes': 0,
                'duration': 0,
                'latency': {},
                'error': str(e)
            }


class PingTest:
    """Handle WebSocket ping test for latency measurement"""
    
    @staticmethod
    async def run_ping_test(server: dict, num_pings: int = 10) -> Optional[List[float]]:
        """Run ping test via WebSocket with tqdm progress and color coding
        
        Args:
            server: Server dictionary with 'host' key
            num_pings: Number of ping packets to send (max 10)
            
        Returns:
            List of ping times in milliseconds, or None if failed
        """
        try:
            host = server.get('host')
            if not host:
                print("✗ Server does not have a host URL")
                return None
            
            # Construct WebSocket URL
            ws_url = f"wss://{host}/ws?"
            
            ping_times = []
            
            
            try:
                async with websockets.connect(ws_url, ping_interval=None) as websocket:
                    print(f"✓ Connected to {host}")
                    
                    with tqdm(total=num_pings, desc="Ping Test", unit="pings", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                        for i in range(num_pings):
                            try:
                                # Send PING with timestamp
                                ping_timestamp = int(time.time() * 1000)
                                ping_message = f"PING {ping_timestamp}\t{i}\t"
                                
                                send_time = time.time()
                                await asyncio.wait_for(websocket.send(ping_message), timeout=5.0)
                                
                                # Wait for PONG response
                                pong_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                
                                receive_time = time.time()
                                
                                # Calculate latency in milliseconds
                                latency_ms = (receive_time - send_time) * 1000
                                ping_times.append(latency_ms)
                                
                                # Color code based on ping value
                                if latency_ms <= 10:
                                    color = Fore.GREEN
                                    status = "Very Good"
                                elif latency_ms <= 60:
                                    color = Fore.CYAN
                                    status = "Good"
                                elif latency_ms <= 120:
                                    color = Fore.YELLOW
                                    status = "Not Good"
                                else:
                                    color = Fore.RED
                                    status = "Bad"
                                
                                # Update progress bar
                                pbar.update(1)
                                pbar.set_description(f"{color}Ping Test: {latency_ms:.2f}ms ({status}){Style.RESET_ALL}")
                                
                                # Small delay between pings
                                await asyncio.sleep(0.1)
                            
                            except asyncio.TimeoutError:
                                pbar.update(1)
                                pbar.set_description(f"{Fore.RED}Ping Test: Timeout{Style.RESET_ALL}")
                            except Exception as e:
                                pbar.update(1)
                                pbar.set_description(f"{Fore.RED}Ping Test: Error{Style.RESET_ALL}")
                    
                    print()
                    
            except (websockets.exceptions.WebSocketException, OSError) as e:
                print(f"✗ WebSocket connection failed: {str(e)}")
                return None
            
            if not ping_times:
                print("✗ No successful pings received")
                return None
            
            return ping_times
        
        except Exception as e:
            print(f"✗ Ping test error: {str(e)}")
            return None
    
    @staticmethod
    def get_ping_color(ping_ms: float) -> str:
        """Get color code based on ping value
        
        Args:
            ping_ms: Ping time in milliseconds
            
        Returns:
            Colored ping value string
        """
        if ping_ms <= 10:
            color = Fore.GREEN
            status = "Very Good"
        elif ping_ms <= 60:
            color = Fore.CYAN
            status = "Good"
        elif ping_ms <= 120:
            color = Fore.YELLOW
            status = "Not Good"
        else:
            color = Fore.RED
            status = "Bad"
        
        return f"{color}{ping_ms:.2f} ms ({status}){Style.RESET_ALL}"
    
    @staticmethod
    def calculate_ping_stats(ping_times: List[float]) -> dict:
        """Calculate ping statistics
        
        Args:
            ping_times: List of ping times in milliseconds
            
        Returns:
            Dictionary with ping statistics
        """
        if not ping_times:
            return {}
        
        ping_times_sorted = sorted(ping_times)
        avg = sum(ping_times) / len(ping_times)
        
        return {
            'min': min(ping_times),
            'max': max(ping_times),
            'avg': avg,
            'median': ping_times_sorted[len(ping_times_sorted) // 2],
            'stddev': (sum((x - avg) ** 2 for x in ping_times) / len(ping_times)) ** 0.5,
            'count': len(ping_times)
        }


class SpeedTest:
    """Handle speed test operations"""
    
    @staticmethod
    def run_test(state: State = None) -> dict:
        """Run speed test with server and user details
        
        Args:
            state: Application state containing user and server information
        """
        try:
            Display.print_header()
            print("RUNNING SPEED TEST")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            # Show User Information
            if state and state.current_user:
                print("USER INFORMATION")
                print("-" * 50)
                print(f"Username: {state.current_user}")
                
                # Try to load and display user data
                user_data = CookieManager.load_user_data(state.current_user)
                if user_data:
                    print(f"Email: {user_data.get('email', 'N/A')}")
                    print(f"ISP: {user_data.get('isp', 'N/A')}")
                    location = user_data.get('location', {})
                    if location:
                        print(f"Location: {location.get('countryName', 'N/A')}")
                        print(f"Coordinates: {location.get('latitude', 0)}, {location.get('longitude', 0)}")
                print()
            
            # Show Server Information
            # Auto-fetch and select server if not already selected
            server = state.selected_server if state else None
            
            if not server and state:
                print("Fetching server list...")
                config = ServerManager.fetch_server_config(state.current_user)
                
                # Check if server fetch failed
                if not config:
                    print()
                    print("=" * 50)
                    print(f"{Fore.RED}✗ ERROR{Style.RESET_ALL}")
                    print("=" * 50)
                    print("Failed to fetch server list.")
                    print("This usually means:")
                    print("  • No internet connection")
                    print("  • Speedtest server is unavailable")
                    print("  • Network is blocked")
                    print("=" * 50)
                    input("Press Enter to go back to main menu...")
                    return {
                        "ping": 0,
                        "download": 0,
                        "upload": 0,
                        "server": "N/A",
                        "error": "Server fetch failed"
                    }
                
                if 'servers' in config:
                    servers = config['servers']
                    if servers:
                        server = ServerManager.pick_random_server(servers)
                        state.set_server(server)
                        print("✓ Server auto-selected\n")
                    else:
                        print()
                        print("=" * 50)
                        print(f"{Fore.RED}✗ ERROR{Style.RESET_ALL}")
                        print("=" * 50)
                        print("No servers available in the response.")
                        print("=" * 50)
                        input("Press Enter to go back to main menu...")
                        return {
                            "ping": 0,
                            "download": 0,
                            "upload": 0,
                            "server": "N/A",
                            "error": "No servers available"
                        }
            
            if server:
                print("SERVER INFORMATION")
                print("-" * 50)
                print(f"Sponsor: {server.get('sponsor', 'N/A')}")
                print(f"Server: {server.get('name', 'N/A')}")
                print(f"Country: {server.get('country', 'N/A')}")
                distance_color = ServerManager.get_distance_color(server.get('distance', 0))
                print(f"Distance: {distance_color}{server.get('distance', 0)}km{Style.RESET_ALL}")
                print(f"Host: {server.get('host', 'N/A')}")
                print(f"ID: {server.get('id', 'N/A')}")
                print()
            
            # Show Speedtest Mode
            if state:
                print("TEST CONFIGURATION")
                print("-" * 50)
                mode_display = "Multiple Connection" if state.speedtest_mode == "multiple" else "Single Connection"
                mode_color = Fore.GREEN if state.speedtest_mode == "multiple" else Fore.CYAN
                print(f"Mode: {mode_color}{mode_display}{Style.RESET_ALL}")
                print()
            
            # Ping Test
            print("STEP 1: PING TEST")
            print("-" * 50)
            print("Measuring latency...\n")
            
            ping_stats = {}
            if server:
                try:
                    # Run actual WebSocket ping test
                    ping_times = asyncio.run(PingTest.run_ping_test(server, num_pings=10))
                    
                    if ping_times:
                        ping_stats = PingTest.calculate_ping_stats(ping_times)
                        print(f"\n✓ Ping Test Complete!")
                        print(f"  Min: {PingTest.get_ping_color(ping_stats['min'])}")
                        print(f"  Max: {PingTest.get_ping_color(ping_stats['max'])}")
                        print(f"  Avg: {PingTest.get_ping_color(ping_stats['avg'])}")
                        print(f"  Median: {PingTest.get_ping_color(ping_stats['median'])}")
                        print(f"  Samples: {ping_stats['count']}")
                    else:
                        print("✗ Ping test failed")
                        # Fallback to demo data
                        demo_ping_times = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        ping_stats = PingTest.calculate_ping_stats(demo_ping_times)
                except Exception as e:
                    print(f"✗ Error during ping test: {str(e)}")
                    # Fallback to demo data
                    demo_ping_times = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ping_stats = PingTest.calculate_ping_stats(demo_ping_times)
            else:
                # No server available, use demo data
                demo_ping_times = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                ping_stats = PingTest.calculate_ping_stats(demo_ping_times)
            
            print()
            
            # Download Test
            print("STEP 2: DOWNLOAD TEST")
            print("-" * 50)
            
            download_stats = {}
            download_latency = {}
            
            if server:
                try:
                    # Determine number of connections based on speedtest mode and user settings
                    num_connections = state.parallel_connections if state and state.speedtest_mode == "multiple" else 1
                    
                    # Run adaptive download test with dynamic duration
                    download_result = asyncio.run(DownloadTest.run_download_test(
                        server, 
                        state, 
                        initial_duration=10,  # Minimum 10 seconds for accurate reading
                        num_connections=num_connections,
                        max_duration=30  # Never exceed 30 seconds
                    ))
                    
                    if download_result and 'error' not in download_result:
                        download_stats = {
                            'speed': download_result['speed'],
                            'bytes': download_result['bytes'],
                            'duration': download_result['duration'],
                            'samples': download_result.get('samples', 0)
                        }
                        download_latency = download_result.get('latency', {})
                    else:
                        print("✗ Download test failed")
                        download_stats = {
                            'speed': 0,
                            'bytes': 0,
                            'duration': 0,
                            'samples': 0
                        }
                
                except Exception as e:
                    print(f"✗ Error during download test: {str(e)}")
                    download_stats = {
                        'speed': 0,
                        'bytes': 0,
                        'duration': 0,
                        'samples': 0
                    }
            else:
                # No server available
                download_stats = {
                    'speed': 0,
                    'bytes': 0,
                    'duration': 0,
                    'samples': 0
                }
            
            print()
            
            # Upload Test
            print("STEP 3: UPLOAD TEST")
            print("-" * 50)
            
            upload_stats = {}
            upload_latency = {}
            
            if server:
                try:
                    # Determine number of connections based on speedtest mode and user settings
                    num_connections = state.parallel_connections if state and state.speedtest_mode == "multiple" else 1
                    
                    # Run upload test with fixed 15 second duration, measuring 3-12 seconds
                    upload_result = asyncio.run(DownloadTest.run_upload_test(
                        server, 
                        state, 
                        test_duration=15,  # Fixed 15 second total duration
                        num_connections=num_connections
                    ))
                    
                    if upload_result and 'error' not in upload_result:
                        upload_stats = {
                            'speed': upload_result['speed'],
                            'bytes': upload_result['bytes'],
                            'duration': upload_result['duration'],
                            'samples': upload_result.get('samples', 0)
                        }
                        upload_latency = upload_result.get('latency', {})
                    else:
                        print("✗ Upload test failed")
                        upload_stats = {
                            'speed': 0,
                            'bytes': 0,
                            'duration': 0,
                            'samples': 0
                        }
                
                except Exception as e:
                    print(f"✗ Error during upload test: {str(e)}")
                    upload_stats = {
                        'speed': 0,
                        'bytes': 0,
                        'duration': 0,
                        'samples': 0
                    }
            else:
                # No server available
                upload_stats = {
                    'speed': 0,
                    'bytes': 0,
                    'duration': 0,
                    'samples': 0
                }
            
            print()
            
            print("✓ Test Complete!")
            print("Press Enter to see final results...")
            input()
            
            # Build result with all test data
            return {
                "ping": ping_stats.get('avg', 0),
                "download": download_stats.get('speed', 0),
                "upload": upload_stats.get('speed', 0),
                "server": server.get('name', 'Unknown') if server else "N/A",
                "download_latency": download_latency,
                "upload_latency": upload_latency,
                "download_speeds": {
                    "combined": download_stats.get('speed', 0),
                    "average": download_stats.get('speed', 0)
                },
                "upload_speeds": {
                    "combined": upload_stats.get('speed', 0),
                    "average": upload_stats.get('speed', 0)
                }
            }
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by the menu handler
    
    @staticmethod
    def run_test_and_share(state: State = None) -> dict:
        """Run speed test and prepare for sharing
        
        Args:
            state: Application state containing user and server information
        """
        try:
            Display.print_header()
            print("RUNNING SPEED TEST AND SHARE")
            print("=" * 50)
            print("(Press Ctrl+C to go back to main menu)")
            print("=" * 50)
            print()
            
            # Call the standard run_test to get base results
            result = SpeedTest.run_test(state)
            
            # Check if there was an error in the test
            if "error" in result:
                # Error was already displayed by run_test, return as-is
                return {
                    "ping": result.get("ping", 0),
                    "download": result.get("download", 0),
                    "upload": result.get("upload", 0),
                    "server": result.get("server", "N/A"),
                    "share_link": "N/A",
                    "error": result.get("error", "Test failed")
                }
            
           
            
            # Generate a unique share link (placeholder implementation)
            test_data = f"{result['ping']}{result['download']}{result['upload']}{datetime.now()}"
            share_id = hashlib.md5(test_data.encode()).hexdigest()[:8].upper()
            share_link = f"https://speedtest.example.com/results/{share_id}"
            
            
            # Add share_link to result and return
            result["share_link"] = share_link
            return result
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by the menu handler


class SettingsManager:
    """Handle application settings"""
    
    @staticmethod
    def show_settings(state: State) -> None:
        """Display and handle settings menu"""
        while True:
            try:
                Display.print_header()
                print("SETTINGS")
                print("=" * 50)
                print("(Press Ctrl+C to go back to main menu)")
                print("=" * 50)
                print()
                
                # Display current speedtest mode
                mode_display = "Multiple Connection" if state.speedtest_mode == "multiple" else "Single Connection"
                colored_mode = f"{Fore.GREEN}{mode_display}{Style.RESET_ALL}" if state.speedtest_mode == "multiple" else mode_display
                
                print("1. Select Speedtest Mode (Current: {})".format(colored_mode))
                print("2. Parallel Connections (Current: {})".format(Fore.CYAN + str(state.parallel_connections) + Style.RESET_ALL))
                print("=" * 50)
                print()
                
                choice = input("Select option (1-2 to continue, 0 to go back): ").strip()
                
                if choice == "0":
                    return
                elif choice == "1":
                    SettingsManager.select_speedtest_mode(state)
                elif choice == "2":
                    SettingsManager.set_parallel_connections(state)
                else:
                    print("✗ Invalid selection")
                    input("Press Enter to continue...")
            
            except KeyboardInterrupt:
                raise
    
    @staticmethod
    def select_speedtest_mode(state: State) -> None:
        """Select speedtest connection mode"""
        try:
            Display.print_header()
            print("SELECT SPEEDTEST MODE")
            print("=" * 50)
            print("(Press Ctrl+C to go back to settings)")
            print("=" * 50)
            print()
            
            # Display options with color coding
            multiple_color = f"{Fore.GREEN}(Default){Style.RESET_ALL}" if state.speedtest_mode == "multiple" else ""
            single_color = f"{Fore.GREEN}(Current){Style.RESET_ALL}" if state.speedtest_mode == "single" else ""
            
            print("1. Multiple Connection {}".format(multiple_color))
            print("2. Single Connection {}".format(single_color))
            print("=" * 50)
            print()
            
            choice = input("Select option: ").strip()
            
            if choice == "1":
                state.speedtest_mode = "multiple"
                print(f"\n✓ Speedtest mode set to: {Fore.GREEN}Multiple Connection{Style.RESET_ALL}")
                input("Press Enter to continue...")
            elif choice == "2":
                state.speedtest_mode = "single"
                print(f"\n✓ Speedtest mode set to: Single Connection")
                input("Press Enter to continue...")
            else:
                print("✗ Invalid selection")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            raise
    
    @staticmethod
    def set_parallel_connections(state: State) -> None:
        """Set number of parallel connections for multi-connection mode"""
        try:
            Display.print_header()
            print("SET PARALLEL CONNECTIONS")
            print("=" * 50)
            print("(Press Ctrl+C to go back to settings)")
            print("=" * 50)
            print()
            print(f"Current value: {Fore.CYAN}{state.parallel_connections}{Style.RESET_ALL}")
            print(f"Default value: {Fore.GREEN}8{Style.RESET_ALL}")
            print("Recommended: 4-16 connections")
            print()
            
            while True:
                try:
                    user_input = input("Enter number of parallel connections (1-64): ").strip()
                    
                    # If empty, use default
                    if not user_input:
                        user_input = "8"
                    
                    connections = int(user_input)
                    
                    if 1 <= connections <= 64:
                        state.parallel_connections = connections
                        print(f"\n✓ Parallel connections set to: {Fore.CYAN}{connections}{Style.RESET_ALL}")
                        input("Press Enter to continue...")
                        return
                    else:
                        print("✗ Please enter a number between 1 and 64")
                
                except ValueError:
                    print("✗ Invalid input. Please enter a valid number.")
        
        except KeyboardInterrupt:
            raise


class MenuHandler:
    """Handle menu navigation and selection"""
    
    def __init__(self, state: State):
        self.state = state
    
    def handle_menu_choice(self, menu_items: list, choice: str) -> bool:
        """
        Handle user menu choice
        Returns: False if user wants to exit, True to continue
        """
        try:
            choice_num = int(choice.strip())
            
            # Exit option
            if choice_num == 0:
                return False
            
            # Find the corresponding menu item
            for menu_num, menu_text in menu_items:
                if menu_num == choice_num:
                    return self._execute_menu_action(menu_text)
            
            print("✗ Invalid selection. Please try again.")
            input("Press Enter to continue...")
            return True
            
        except ValueError:
            print("✗ Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            return True
    
    def _execute_menu_action(self, action: str) -> bool:
        """Execute menu action based on selection"""
        
        try:
            if "Login" in action:
                username = AuthManager.login()
                if username:
                    self.state.login(username)
                return True
            
            elif "Select Server" in action:
                server = ServerSelectionUI.select_server(self.state.current_user)
                # server can be None (auto-pick) or a dict (selected server)
                self.state.set_server(server)
                return True
            
            elif "Run SpeedTest and Share" in action:
                result = SpeedTest.run_test_and_share(self.state)
                Display.print_header()
                print("SPEED TEST RESULTS")
                print("=" * 50)
                print(f"  Ping: {result['ping']:.2f} ms")
                print(f"  Download: {result['download']:.2f} Mbps")
                print(f"  Upload: {result['upload']:.2f} Mbps")
                print(f"  Share Link: {result.get('share_link', 'N/A')}")
                print("=" * 50)
                input("Press Enter to continue...")
                return True
            
            elif "Run SpeedTest" in action:
                result = SpeedTest.run_test(self.state)
                Display.print_header()
                print("SPEED TEST RESULTS")
                print("=" * 50)
                print(f"  Ping: {result['ping']:.2f} ms")
                print(f"  Download: {result['download']:.2f} Mbps")
                print(f"  Upload: {result['upload']:.2f} Mbps")
                print("=" * 50)
                input("Press Enter to continue...")
                return True
            
            elif "Settings" in action:
                SettingsManager.show_settings(self.state)
                return True
            
            elif "Logout" in action:
                AuthManager.logout(self.state.current_user)
                self.state.logout()
                return True
            
            return True
        
        except KeyboardInterrupt:
            # User pressed Ctrl+C during an action, return to main menu
            return True


class Application:
    """Main application class"""
    
    def __init__(self):
        self.state = State()
        self.menu_handler = MenuHandler(self.state)
    
    def run(self):
        """Main application loop"""
        while True:
            try:
                menu_items = Display.print_menu(self.state)
                choice = input("Select option: ")
                should_continue = self.menu_handler.handle_menu_choice(menu_items, choice)
                
                if not should_continue:
                    raise KeyboardInterrupt  # Trigger exit
            except KeyboardInterrupt:
                raise  # Re-raise to main to exit application


def main():
    """Entry point of the application"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Advanced Speedtest CLI', add_help=False)
    parser.add_argument('--q', action='store_true', help='Quick run - run speedtest with default values')
    args, unknown = parser.parse_known_args()
    
    # If --q flag is present, run quick speedtest
    if args.q:
        Display.clear_screen()
        Display.print_banner(Config.BANNER)
        print("=" * 50)
        print("Quick Speedtest Mode - Anonymous User")
        print("=" * 50)
        print()
        
        state = State()
        # Use anonymous user
        state.login("anonymous_user")
        # Auto-pick server
        state.set_server(None)
        # Run speedtest with default settings
        result = SpeedTest.run_test(state)
        
        # Display results
        Display.print_header()
        print("SPEED TEST RESULTS")
        print("=" * 50)
        print(f"✓ Test Complete!")
        print(f"  Ping: {result['ping']:.2f} ms")
        print(f"  Download: {result['download']:.2f} Mbps")
        print(f"  Upload: {result['upload']:.2f} Mbps")
        print("=" * 50)
        sys.exit(0)
    
    app = Application()
    try:
        app.run()
    except KeyboardInterrupt:
        # Only close if user presses Ctrl+C from main menu
        print("\n\n" + "=" * 50)
        print("Thank you for using Advanced Speedtest CLI!")
        print("=" * 50)
        print(f"Version: {Config.VERSION}")
        print(f"GitHub: {Config.GITHUB_REPO_LINK}")
        print(f"Author: {Config.AUTHOR}")
        print(f"Email: {Config.EMAIL}")
        print("=" * 50)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
