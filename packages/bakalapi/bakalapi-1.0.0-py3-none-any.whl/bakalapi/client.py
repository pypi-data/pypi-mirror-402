"""
Main client for accessing the Bakalapi timetable API.
"""

import requests
from typing import Optional
from urllib.parse import quote

from .models import TimetableResponse


class BakalapiError(Exception):
    """Base exception for Bakalapi errors."""
    pass


class BakalapiAPIError(BakalapiError):
    """Exception raised when the API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class BakalapiClient:
    """
    Client for accessing the Bakalapi timetable API.
    
    This client allows you to query timetable information by:
    - Teacher name
    - Room index
    - Class name
    
    Note: Parameters cannot be combined - you can only query by one type at a time.
    
    Example:
        >>> client = BakalapiClient()
        >>> timetable = client.get_teacher_timetable("Mgr. Hana Jaitnerová")
        >>> print(timetable.timetable[0].subject)
    """
    
    BASE_URL = "https://bakalapi-production.up.railway.app/api/timetable"
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize the Bakalapi client.
        
        Args:
            base_url: Optional custom base URL for the API. 
                     Defaults to the production URL.
            timeout: Request timeout in seconds. Defaults to 10.
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "bakalapi-python/1.0.0"
        })
    
    def _make_request(self, endpoint: str) -> dict:
        """
        Make a request to the API and return the JSON response.
        
        Args:
            endpoint: The API endpoint to query.
            
        Returns:
            The JSON response as a dictionary.
            
        Raises:
            BakalapiAPIError: If the API request fails.
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise BakalapiAPIError(f"Request to {url} timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            raise BakalapiAPIError(
                f"API request failed: {e}",
                status_code=status_code
            )
        except requests.exceptions.RequestException as e:
            raise BakalapiAPIError(f"Request failed: {e}")
        except ValueError as e:
            raise BakalapiAPIError(f"Invalid JSON response: {e}")
    
    def get_teacher_timetable(self, teacher_name: str) -> TimetableResponse:
        """
        Get the timetable for a specific teacher.
        
        Args:
            teacher_name: The name of the teacher (e.g., "Mgr. Hana Jaitnerová").
            
        Returns:
            A TimetableResponse object containing the teacher's timetable.
            
        Raises:
            BakalapiAPIError: If the API request fails.
            
        Example:
            >>> client = BakalapiClient()
            >>> timetable = client.get_teacher_timetable("Mgr. Hana Jaitnerová")
        """
        if not teacher_name:
            raise ValueError("teacher_name cannot be empty")
        
        # URL encode the teacher name
        encoded_name = quote(teacher_name)
        endpoint = f"teachers/{encoded_name}"
        
        data = self._make_request(endpoint)
        return TimetableResponse.from_dict(data)
    
    def get_room_timetable(self, room_index: str) -> TimetableResponse:
        """
        Get the timetable for a specific room.
        
        Args:
            room_index: The room index/identifier (e.g., "a1").
            
        Returns:
            A TimetableResponse object containing the room's timetable.
            
        Raises:
            BakalapiAPIError: If the API request fails.
            
        Example:
            >>> client = BakalapiClient()
            >>> timetable = client.get_room_timetable("a1")
        """
        if not room_index:
            raise ValueError("room_index cannot be empty")
        
        # URL encode the room index
        encoded_room = quote(room_index)
        endpoint = f"room/{encoded_room}"
        
        data = self._make_request(endpoint)
        return TimetableResponse.from_dict(data)
    
    def get_class_timetable(self, class_name: str) -> TimetableResponse:
        """
        Get the timetable for a specific class.
        
        Args:
            class_name: The name of the class (e.g., "4.B Sk1" or "1.O Sk1").
            
        Returns:
            A TimetableResponse object containing the class's timetable.
            
        Raises:
            BakalapiAPIError: If the API request fails.
            
        Example:
            >>> client = BakalapiClient()
            >>> timetable = client.get_class_timetable("4.B Sk1")
        """
        if not class_name:
            raise ValueError("class_name cannot be empty")
        
        # URL encode the class name
        encoded_class = quote(class_name)
        endpoint = f"class/{encoded_class}"
        
        data = self._make_request(endpoint)
        return TimetableResponse.from_dict(data)
    
    def close(self):
        """Close the session and release resources."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
