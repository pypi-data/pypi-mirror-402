"""Main TCBS Client implementation"""

import requests
from typing import Optional, Dict, Any, List, Union
from tcbs.auth import TokenManager
from tcbs.exceptions import TCBSAuthError, TCBSAPIError


class TCBSClient:
    """Unified client for TCBS iFlash Open API"""
    
    BASE_URL = "https://openapi.tcbs.com.vn"
    
    def __init__(self, api_key: str):
        """Initialize TCBS client with API key
        
        Args:
            api_key: Your TCBS API key
        """
        self.api_key = api_key
        self.token_manager = TokenManager
        self._session = requests.Session()
    
    def _ensure_authenticated(self) -> None:
        """Ensure valid token exists, prompt for OTP if needed"""
        token = self.token_manager.load_token()
        
        if token is None:
            otp = input("Enter OTP: ")
            self.get_token(otp)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        self._ensure_authenticated()
        token = self.token_manager.load_token()
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{self.BASE_URL}{endpoint}"
        
        if "headers" not in kwargs:
            kwargs["headers"] = self._get_headers()
        
        response = self._session.request(method, url, **kwargs)
        
        if response.status_code != 200:
            raise TCBSAPIError(f"API Error {response.status_code}: {response.text}")
        
        return response.json()
    
    # ===== Group 1: Account & Authentication =====
    
    def get_token(self, otp: str) -> Dict[str, Any]:
        """Exchange API Key + OTP for JWT token
        
        Args:
            otp: One-time password from authentication app
            
        Returns:
            Token response data
        """
        url = f"{self.BASE_URL}/gaia/v1/oauth2/openapi/token"
        
        payload = {
            "apiKey": self.api_key,
            "otp": otp
        }
        
        response = self._session.post(url, json=payload)
        
        if response.status_code != 200:
            raise TCBSAuthError(f"Authentication failed: {response.text}")
        
        data = response.json()
        
        if "token" in data:
            # Token lifetime is 8 hours (28800 seconds) based on JWT exp claim
            self.token_manager.save_token(data["token"], 28800)
        
        return data

    def get_profile(self, custody_code: str, fields: str = "basicInfo,personalInfo,bankSubAccounts,bankAccounts") -> Dict[str, Any]:
        """Lấy thông tin tiểu khoản
        
        Args:
            custody_code: Số tài khoản (e.g., "105C334455")
            fields: Danh sách thông tin cần lấy (comma-separated)
            
        Returns:
            Account information
        """
        endpoint = f"/eros/v2/get-profile/by-username/{custody_code}"
        return self._request("GET", endpoint, params={"fields": fields})
    
    # ===== Group 2: Stock Trading (Normal) =====
    
    def place_order(self, account_no: str, symbol: str, side: str, price: float, 
                   quantity: int, price_type: str = "LO") -> Dict[str, Any]:
        """Đặt lệnh thường
        
        Args:
            account_no: Số tiểu khoản (e.g., "0001170730")
            symbol: Mã chứng khoán (e.g., "FPT")
            side: Loại lệnh - "B" (mua) hoặc "S" (bán)
            price: Giá đặt lệnh
            quantity: Khối lượng
            price_type: Loại giá - "LO" (limit), "MP" (market), "ATO", "ATC"
            
        Returns:
            Order response
        """
        endpoint = f"/akhlys/v1/accounts/{account_no}/orders"
        
        payload = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "priceType": price_type
        }
        
        return self._request("POST", endpoint, json=payload)

    def update_order(self, account_no: str, order_id: str, price: float = None, 
                    quantity: int = None) -> Dict[str, Any]:
        """Sửa lệnh thường
        
        Args:
            account_no: Số tiểu khoản
            order_id: Order ID cần sửa
            price: Giá mới (optional)
            quantity: Khối lượng mới (optional)
            
        Returns:
            Update response
        """
        endpoint = f"/akhlys/v1/accounts/{account_no}/orders/{order_id}"
        
        payload = {}
        if price is not None:
            payload["price"] = price
        if quantity is not None:
            payload["quantity"] = quantity
        
        return self._request("PUT", endpoint, json=payload)
    
    def cancel_order(self, account_no: str, order_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """Huỷ lệnh thường
        
        Args:
            account_no: Số tiểu khoản
            order_ids: Order ID hoặc danh sách Order IDs cần huỷ
            
        Returns:
            Cancel response
        """
        endpoint = f"/akhlys/v1/accounts/{account_no}/cancel-orders"
        
        if isinstance(order_ids, str):
            order_ids = [order_ids]
        
        payload = {"orderIds": order_ids}
        
        return self._request("PUT", endpoint, json=payload)
    
    def get_order_book(self, account_no: str) -> Dict[str, Any]:
        """Lấy sổ lệnh
        
        Args:
            account_no: Số tiểu khoản
            
        Returns:
            Order book data
        """
        endpoint = f"/aion/v1/accounts/{account_no}/orders"
        return self._request("GET", endpoint)

    def get_order_by_id(self, account_no: str, order_id: str) -> Dict[str, Any]:
        """Lấy sổ lệnh theo Order ID
        
        Args:
            account_no: Số tiểu khoản
            order_id: Order ID
            
        Returns:
            Order details
        """
        endpoint = f"/aion/v1/accounts/{account_no}/orders/{order_id}"
        return self._request("GET", endpoint)
    
    def get_matching_details(self, account_no: str) -> Dict[str, Any]:
        """Lấy thông tin khớp lệnh
        
        Args:
            account_no: Số tiểu khoản
            
        Returns:
            Matching details
        """
        endpoint = f"/aion/v1/accounts/{account_no}/matching-details"
        return self._request("GET", endpoint)
    
    def get_purchasing_power(self, account_no: str, symbol: Optional[str] = None, 
                            price: Optional[float] = None) -> Dict[str, Any]:
        """Lấy sức mua (hỗ trợ 3 biến thể: tổng quát, theo mã, theo mã + giá)
        
        Args:
            account_no: Số tiểu khoản
            symbol: Mã chứng khoán (optional)
            price: Giá tính sức mua (optional, requires symbol)
            
        Returns:
            Purchasing power data
        """
        if price is not None and symbol is None:
            raise ValueError("symbol is required when price is provided")
        
        if symbol and price:
            endpoint = f"/aion/v1/accounts/{account_no}/ppse/{symbol}/{price}"
        elif symbol:
            endpoint = f"/aion/v1/accounts/{account_no}/ppse/{symbol}"
        else:
            endpoint = f"/aion/v1/accounts/{account_no}/ppse"
        
        return self._request("GET", endpoint)

    def get_margin_quota(self, custody_id: str) -> List[Dict[str, Any]]:
        """Hạn mức margin
        
        Args:
            custody_id: Số tài khoản
            
        Returns:
            Margin quota information
        """
        endpoint = f"/aion/v1/customers/{custody_id}/accounts"
        return self._request("GET", endpoint)
    
    def get_asset(self, account_no: str) -> Dict[str, Any]:
        """Tra cứu tài sản cổ phiếu theo tiểu khoản
        
        Args:
            account_no: Số tiểu khoản
            
        Returns:
            Stock asset information
        """
        endpoint = f"/aion/v1/accounts/{account_no}/se"
        return self._request("GET", endpoint)
    
    def get_cash_investment(self, account_no: str) -> Dict[str, Any]:
        """Lấy thông tin số dư tiền
        
        Args:
            account_no: Số tiểu khoản
            
        Returns:
            Cash balance information
        """
        endpoint = f"/aion/v1/accounts/{account_no}/cashInvestments"
        return self._request("GET", endpoint)
    
    # ===== Group 3: Derivative Trading =====
    
    def get_derivative_status(self, account_id: str, sub_account_id: str, 
                             get_type: str = "1") -> Dict[str, Any]:
        """Tổng quan tiền, ký quỹ của phái sinh
        
        Args:
            account_id: Số tài khoản lưu kí
            sub_account_id: Tiểu khoản phái sinh
            get_type: "0" (toàn bộ) hoặc "1" (chỉ tiền)
            
        Returns:
            Derivative account status
        """
        endpoint = "/khronos/v1/account/status"
        params = {
            "accountId": account_id,
            "subAccountId": sub_account_id,
            "getType": get_type
        }
        return self._request("GET", endpoint, params=params)

    def place_derivative_order(self, account_id: str, sub_account_id: str, symbol: str,
                              side: str, price: float, volume: int, 
                              price_type: str = "LO") -> Dict[str, Any]:
        """Đặt lệnh thường phái sinh
        
        Args:
            account_id: Số tài khoản lưu kí
            sub_account_id: Tiểu khoản phái sinh
            symbol: Mã hợp đồng (e.g., "VN30F2303")
            side: "B" (Long) hoặc "S" (Short)
            price: Giá đặt lệnh
            volume: Khối lượng
            price_type: Loại giá - "LO", "MP", "ATO", "ATC"
            
        Returns:
            Order response
        """
        endpoint = "/khronos/v1/order/place"
        
        payload = {
            "accountId": account_id,
            "subAccountId": sub_account_id,
            "symbol": symbol,
            "side": side,
            "price": price,
            "volume": volume,
            "priceType": price_type
        }
        
        return self._request("POST", endpoint, json=payload)
    
    def get_derivative_orders(self, account_id: str, page_no: int = 1, 
                             page_size: int = 20, symbol: str = "ALL,ALL",
                             order_type: str = "", status: str = "0") -> Dict[str, Any]:
        """Tra cứu sổ lệnh thường phái sinh
        
        Args:
            account_id: Số tài khoản lưu kí
            page_no: Trang số
            page_size: Số phần tử trong trang
            symbol: Filter theo mã ("ALL,ALL", "VN30F2303,B", "ALL,B")
            order_type: Filter loại lệnh ("", "3", "4", "5", "6")
            status: Filter trạng thái ("0": tất cả, "1": chờ khớp, "2": đã khớp)
            
        Returns:
            Derivative order book
        """
        endpoint = "/khronos/v1/order/in-day"
        params = {
            "accountId": account_id,
            "pageNo": page_no,
            "pageSize": page_size,
            "symbol": symbol,
            "orderType": order_type,
            "status": status
        }
        return self._request("GET", endpoint, params=params)

    # ===== Group 4: Market Data =====
    
    def get_market_info(self, tickers: Optional[str] = None, 
                       index: Optional[str] = None) -> Dict[str, Any]:
        """Lấy thông tin giá cổ phiếu
        
        Args:
            tickers: Danh sách mã chứng khoán (comma-separated)
            index: Chỉ số thị trường
            
        Returns:
            Market information
        """
        endpoint = "/tartarus/v1/tickerCommons"
        params = {}
        if tickers:
            params["tickers"] = tickers
        if index:
            params["index"] = index
        
        return self._request("GET", endpoint, params=params)
    
    def get_price_history(self, ticker: str, page: int = 0, 
                         size: int = 50) -> Dict[str, Any]:
        """Lịch sử khớp lệnh theo mã
        
        Args:
            ticker: Mã chứng khoán
            page: Số trang
            size: Số phần tử
            
        Returns:
            Price history data
        """
        endpoint = f"/nyx/v1/intraday/{ticker}/his/paging"
        params = {"page": page, "size": size}
        return self._request("GET", endpoint, params=params)
    
    def get_foreign_room(self, index: str) -> Dict[str, Any]:
        """Thông tin room nước ngoài
        
        Args:
            index: Chỉ số thị trường (e.g., "VNINDEX", "VN30")
            
        Returns:
            Foreign room information
        """
        endpoint = "/tartarus/v1/tickerSnaps"
        params = {"index": index}
        return self._request("GET", endpoint, params=params)
