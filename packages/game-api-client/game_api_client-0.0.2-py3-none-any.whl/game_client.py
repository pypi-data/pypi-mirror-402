"""
Simple GAME API Client

A minimal client for the GAME trading API.
"""
import time
import logging
from typing import List, Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class GameAPIError(Exception):
    """Base exception for GAME API errors"""
    pass


class GameAPI:
    """
    Simple GAME API client
    
    Example:
        api = GameAPI(
            token="your_authentik_token",
            base_url="https://your-game-api-url.com"
        )
        status = await api.get_status()
        trades = await api.get_trades()
    """
    
    def __init__(
        self,
        token: str,
        base_url: str,
        verify_ssl: bool = False,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.personal_token = token
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
        if not token:
            raise GameAPIError("Personal token is required")
    
    async def _get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        if self._is_token_valid():
            return self._access_token
        
        await self._refresh_token()
        return self._access_token
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self._access_token or not self._token_expires_at:
            return False
        return time.time() < (self._token_expires_at - 60)
    
    async def _refresh_token(self) -> None:
        """Refresh the access token using personal token"""
        url = f"{self.base_url}/api/v1/auth/token"
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"token": self.personal_token},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    raise GameAPIError(
                        f"Token exchange failed: {response.status_code} - {response.text}"
                    )
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                self._token_expires_at = time.time() + token_data.get("expires_in", 3600)
                
        except httpx.RequestError as e:
            raise GameAPIError(f"Network error during token refresh: {e}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Any:
        """Make an authenticated request to the API"""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        # Get fresh access token
        access_token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=self.timeout,
                follow_redirects=True  # Follow redirects
            ) as client:
                
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers
                )
                
                if response.status_code >= 400:
                    error_msg = f"API request failed: {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text}"
                    raise GameAPIError(error_msg)
                
                return response.json()
                
        except httpx.RequestError as e:
            raise GameAPIError(f"Network error: {e}")
    
    # Status endpoints
    async def get_status(self) -> Dict[str, Any]:
        """Get API status"""
        return await self._make_request("GET", "/status")
    
    # Trades endpoints
    async def get_trades(self, direction: Optional[str] = None, duration: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trades with optional filtering"""
        params = {}
        if direction:
            params["direction"] = direction
        if duration:
            params["duration"] = duration
        return await self._make_request("GET", "/trades", params=params)
    
    # Orders endpoints
    async def get_orders(self, direction: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders with optional filtering"""
        params = {}
        if direction:
            params["direction"] = direction
        return await self._make_request("GET", "/orders", params=params)
    
    async def find_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a specific order by its ID (string or numeric)
        
        Args:
            order_id: Order ID to search for
            
        Returns:
            Order data if found, None otherwise
        """
        try:
            orders = await self.get_orders()
            for order in orders:
                # Check both string ID and possible numeric representations
                if (order.get('order_id') == order_id or 
                    str(order.get('order_id', '')) == str(order_id) or
                    str(order.get('id', '')) == str(order_id)):
                    return order
            return None
        except Exception as e:
            logger.error(f"Error finding order {order_id}: {e}")
            return None
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order
        
        Args:
            order_data: Order data (for single order) or {"orders": [...]} (for bulk)
            
        Returns:
            Created order data
        """
        # Validate order data
        if not order_data:
            raise GameAPIError("Order data cannot be empty")
        
        # Check if this is a bulk order
        if "orders" in order_data:
            # Validate bulk order
            orders = order_data["orders"]
            if not isinstance(orders, list) or len(orders) == 0:
                raise GameAPIError("Bulk orders must be a non-empty list")
            
            # Validate each order in bulk
            for i, order in enumerate(orders):
                self._validate_single_order(order, f"Bulk order {i+1}")
            
            return await self._make_request("POST", "/orders/create-bulk", json_data=order_data)
        else:
            # Validate single order
            self._validate_single_order(order_data, "Single order")
            return await self._make_request("POST", "/orders", json_data=order_data)
    
    def _validate_single_order(self, order: Dict[str, Any], context: str) -> None:
        """Validate a single order's required fields"""
        required_fields = ["side", "price", "volume", "date", "start_time", "end_time"]
        
        for field in required_fields:
            if field not in order or order[field] is None:
                raise GameAPIError(f"{context}: Missing required field '{field}'")
        
        # Validate field values
        if order["side"] not in ["buy", "sell"]:
            raise GameAPIError(f"{context}: Invalid side '{order['side']}'. Must be 'buy' or 'sell'")
        
        try:
            price = float(order["price"])
            if price <= 0:
                raise GameAPIError(f"{context}: Price must be positive, got {price}")
        except (ValueError, TypeError):
            raise GameAPIError(f"{context}: Invalid price format '{order['price']}'")
        
        try:
            volume = float(order["volume"])
            if volume <= 0:
                raise GameAPIError(f"{context}: Volume must be positive, got {volume}")
        except (ValueError, TypeError):
            raise GameAPIError(f"{context}: Invalid volume format '{order['volume']}'")
    
    async def delete_order(self, order_id: str) -> Dict[str, Any]:
        """
        Delete an order by ID
        
        Args:
            order_id: Order ID (string like 'ord_123' or numeric string like '1001')
            
        Returns:
            Deletion result
        """
        # Extract numeric ID if it's in format 'ord_123'
        if isinstance(order_id, str) and order_id.startswith('ord_'):
            # For string IDs, we need to find the corresponding numeric ID
            # Try to get all orders and find the matching one
            try:
                orders = await self.get_orders()
                matching_order = None
                
                for order in orders:
                    # Check multiple possible ID fields
                    if (order.get('order_id') == order_id or 
                        str(order.get('order_id', '')) == str(order_id)):
                        matching_order = order
                        break
                
                if matching_order:
                    # Try different ways to get the numeric ID
                    numeric_id = None
                    
                    # Method 1: Check for explicit numeric ID field
                    if 'id' in matching_order and matching_order['id']:
                        numeric_id = str(matching_order['id'])
                    # Method 2: Check order_id_numeric field
                    elif 'order_id_numeric' in matching_order:
                        numeric_id = str(matching_order['order_id_numeric'])
                    # Method 3: Extract from order_id if it's numeric
                    elif matching_order.get('order_id') and str(matching_order['order_id']).isdigit():
                        numeric_id = str(matching_order['order_id'])
                    # Method 4: Try to extract digits from string ID
                    else:
                        import re
                        digits = re.findall(r'\d+', order_id)
                        if digits:
                            numeric_id = digits[0]
                        else:
                            raise GameAPIError(f"Cannot extract numeric ID from {order_id}")
                    
                    logger.info(f"Deleting order {order_id} using numeric ID {numeric_id}")
                    return await self._make_request("DELETE", f"/orders/{numeric_id}")
                
                else:
                    # Order not found in list, try fallback approach
                    logger.warning(f"Order {order_id} not found in current orders, trying fallback")
                    numeric_id = order_id.replace('ord_', '')
                    return await self._make_request("DELETE", f"/orders/{numeric_id}")
                    
            except Exception as e:
                if "Cannot extract numeric ID" in str(e):
                    raise
                # If we can't find the order, try the original approach as fallback
                logger.warning(f"Error finding order {order_id}, using fallback: {e}")
                numeric_id = order_id.replace('ord_', '')
                return await self._make_request("DELETE", f"/orders/{numeric_id}")
        else:
            # Already numeric
            numeric_id = str(order_id)
            return await self._make_request("DELETE", f"/orders/{numeric_id}")
    
    # Market endpoints
    async def get_market_data(self) -> List[Dict[str, Any]]:
        """Get market data"""
        return await self._make_request("GET", "/market")
    
    # Spot endpoints
    async def get_spot_data(self) -> List[Dict[str, Any]]:
        """Get spot data"""
        return await self._make_request("GET", "/spot")
    
    async def get_spot_status(self) -> Dict[str, Any]:
        """Get spot API status"""
        return await self._make_request("GET", "/spot/status")
    
    # Helper methods
    async def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            await self.get_status()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
