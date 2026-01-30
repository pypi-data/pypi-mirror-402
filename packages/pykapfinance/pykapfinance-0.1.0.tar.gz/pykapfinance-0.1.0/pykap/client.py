"""
KAP API Client
Main client for interacting with KAP API endpoints.
"""

import requests
import base64
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from requests.auth import HTTPBasicAuth

from .models import (
    DisclosureInfo,
    DisclosureDetail,
    MemberInfo,
    FundInfo,
    BlockedDisclosure,
    CAProcessStatus,
    MemberSecuritiesResponse
)
from .exceptions import (
    KAPAuthenticationError,
    KAPAPIError,
    KAPValidationError
)


class KAPClient:
    """
    KAP (Kamuyu Aydınlatma Platformu) API Client
    
    This client provides access to all KAP API endpoints including:
    - Token generation
    - Disclosure operations
    - Member (company) information
    - Fund information
    - Corporate actions
    """
    
    # API Endpoints
    BASE_URL_PROD = "https://apigw.mkk.com.tr"
    BASE_URL_TEST = "https://apigwdev.mkk.com.tr"
    DEFAULT_API_KEY = "29223dec-32bc-49fb-919f-51405d110ab2"
    DEFAULT_API_SECRET = None
    
    # Disclosure classes
    DISCLOSURE_CLASS_FR = "FR"  # Finansal Rapor
    DISCLOSURE_CLASS_ODA = "ODA"  # Özel Durum Açıklaması
    DISCLOSURE_CLASS_DG = "DG"  # Diğer Bildirim
    DISCLOSURE_CLASS_DUY = "DUY"  # Düzenleyici Kurum Bildirimi
    
    # Disclosure types
    DISCLOSURE_TYPE_FR = "FR"  # Finansal Rapor
    DISCLOSURE_TYPE_ODA = "ODA"  # Özel Durum Açıklaması
    DISCLOSURE_TYPE_DG = "DG"  # Diğer Bildirim
    DISCLOSURE_TYPE_DUY = "DUY"  # Düzenleyici Kurum
    DISCLOSURE_TYPE_FON = "FON"  # Fon Bildirimi
    DISCLOSURE_TYPE_CA = "CA"  # Hak Kullanım
    
    def __init__(self, test_mode: bool = True, auto_refresh_token: bool = True,
                 api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize KAP API Client
        
        Args:
            test_mode: Use test environment (default: True)
            auto_refresh_token: Automatically refresh token when expired (default: True)
            api_key: API key for authentication (optional, uses default if not provided)
            api_secret: API secret for authentication (optional)
        """
        self.test_mode = test_mode
        self.base_url = self.BASE_URL_TEST if test_mode else self.BASE_URL_PROD
        self.auto_refresh_token = auto_refresh_token
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.api_secret = api_secret or self.DEFAULT_API_SECRET
        self.token = None
        self.token_expiry = None
        self.session = requests.Session()
        
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if include_auth:
            if self.test_mode:
                # Test ortamında Basic Auth kullan (API_KEY:API_SECRET)
                credentials = f"{self.api_key}:{self.api_secret if self.api_secret else ''}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
            else:
                # Production ortamında Bearer token kullan
                if self.auto_refresh_token and self._is_token_expired():
                    self.generate_token()
                
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                
        return headers
    
    def _is_token_expired(self) -> bool:
        """Check if token is expired"""
        if not self.token or not self.token_expiry:
            return True
        return datetime.now() >= self.token_expiry
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        include_auth: bool = True
    ) -> Any:
        """
        Make HTTP request to KAP API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            include_auth: Include authentication header
            
        Returns:
            Response data
            
        Raises:
            KAPAPIError: API request failed
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            # Handle error responses
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise KAPAPIError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    error_code=error_data.get("code"),
                    error_message=error_data.get("message")
                )
            
            # Return response
            if response.content:
                return response.json()
            return None
            
        except requests.exceptions.RequestException as e:
            raise KAPAPIError(f"Request failed: {str(e)}")
    
    def generate_token(self) -> str:
        """
        Generate authentication token (Production only)
        Token is valid for 24 hours.
        
        Returns:
            Token string
            
        Raises:
            KAPAuthenticationError: Token generation failed
        """
        if self.test_mode:
            # Test mode doesn't require token
            return ""
        
        try:
            endpoint = f"/auth/generateToken?apiKey={self.api_key}"
            response = self._make_request("GET", endpoint, include_auth=False)
            
            self.token = response.get("token")
            # Token expires in 24 hours
            self.token_expiry = datetime.now() + timedelta(hours=24)
            
            return self.token
            
        except Exception as e:
            raise KAPAuthenticationError(f"Token generation failed: {str(e)}")
    
    def get_disclosures(
        self,
        disclosure_index: int,
        disclosure_type: Optional[str] = None,
        disclosure_class: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> List[DisclosureInfo]:
        """
        Get list of disclosures (Bildirim Listesi Servisi)
        Returns first 50 disclosures starting from disclosure_index.
        
        Args:
            disclosure_index: Starting disclosure index (must be >= 538004)
            disclosure_type: Disclosure type filter (FR, ODA, DG, DUY, FON, CA)
            disclosure_class: Disclosure class filter (FR, ODA, DG, DUY)
            company_id: Company ID filter
            
        Returns:
            List of DisclosureInfo objects
            
        Raises:
            KAPValidationError: Invalid parameters
            KAPAPIError: API request failed
        """
        if disclosure_index < 538004:
            raise KAPValidationError("disclosure_index must be >= 538004")
        
        params = {"disclosureIndex": disclosure_index}
        
        if disclosure_type:
            params["disclosureTypes"] = disclosure_type
        if disclosure_class:
            params["disclosureClass"] = disclosure_class
        if company_id:
            params["companyId"] = company_id
        
        endpoint = "/api/vyk/disclosures"
        response = self._make_request("GET", endpoint, params=params)
        
        return [DisclosureInfo.from_dict(item) for item in response]
    
    def get_disclosure_detail(
        self,
        disclosure_index: int,
        file_type: str = "data",
        sub_report_list: Optional[str] = None
    ) -> DisclosureDetail:
        """
        Get disclosure details (Bildirim Detay Servisi)
        
        Args:
            disclosure_index: Disclosure index number
            file_type: File type ('html' or 'data', default: 'data')
            sub_report_list: Sub-report IDs (comma-separated)
            
        Returns:
            DisclosureDetail object
            
        Raises:
            KAPValidationError: Invalid parameters
            KAPAPIError: API request failed
        """
        if file_type not in ["html", "data"]:
            raise KAPValidationError("file_type must be 'html' or 'data'")
        
        params = {"fileType": file_type}
        if sub_report_list:
            params["subReportList"] = sub_report_list
        
        endpoint = f"/api/vyk/disclosureDetail/{disclosure_index}"
        response = self._make_request("GET", endpoint, params=params)
        
        return DisclosureDetail.from_dict(response)
    
    def download_attachment(self, attachment_id: str) -> bytes:
        """
        Download disclosure attachment (Bildirim Ekleri İndirme Servisi)
        
        Args:
            attachment_id: Attachment ID from disclosure detail
            
        Returns:
            File content as bytes
            
        Raises:
            KAPAPIError: Download failed
        """
        endpoint = f"/api/vyk/downloadAttachment/{attachment_id}"
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = self.session.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise KAPAPIError(f"Attachment download failed: {str(e)}")
    
    def get_last_disclosure_index(self) -> int:
        """
        Get last published disclosure index (Yayınlanmış Son Bildirim Id Servisi)
        
        Returns:
            Last disclosure index number
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = "/api/vyk/lastDisclosureIndex"
        response = self._make_request("GET", endpoint)
        return int(response.get("lastDisclosureIndex", 0))
    
    def get_members(self) -> List[MemberInfo]:
        """
        Get list of all KAP member companies (Şirket Listesi Servisi)
        
        Returns:
            List of MemberInfo objects
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = "/api/vyk/members"
        response = self._make_request("GET", endpoint)
        return [MemberInfo.from_dict(item) for item in response]
    
    def get_member_detail(self, member_id: str) -> Dict[str, Any]:
        """
        Get company details (Şirket Detay Servisi)
        
        Args:
            member_id: Company ID
            
        Returns:
            Company detail data
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = f"/api/vyk/memberDetail/{member_id}"
        return self._make_request("GET", endpoint)
    
    def get_member_securities(self) -> List[MemberSecuritiesResponse]:
        """
        Get securities information for all IGS companies 
        (Şirket Menkul Kıymet Bilgileri Servisi)
        
        Returns:
            List of MemberSecuritiesResponse objects
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = "/api/vyk/memberSecurities"
        response = self._make_request("GET", endpoint)
        return [MemberSecuritiesResponse.from_dict(item) for item in response]
    
    def get_funds(
        self,
        fund_state: Optional[List[str]] = None,
        fund_class: Optional[List[str]] = None,
        fund_type: Optional[List[str]] = None
    ) -> List[FundInfo]:
        """
        Get list of funds (Fon Listesi Servisi)
        
        Args:
            fund_state: Fund state filter (Y=active, N=passive, T=liquidation)
            fund_class: Fund class filter
            fund_type: Fund type filter
            
        Returns:
            List of FundInfo objects
            
        Raises:
            KAPAPIError: API request failed
        """
        params = {}
        if fund_state:
            params["fundState"] = fund_state
        if fund_class:
            params["fundClass"] = fund_class
        if fund_type:
            params["fundType"] = fund_type
        
        endpoint = "/api/vyk/funds"
        response = self._make_request("GET", endpoint, params=params)
        return [FundInfo.from_dict(item) for item in response]
    
    def get_fund_detail(self, fund_id: int) -> Dict[str, Any]:
        """
        Get fund details (Fon Detay Servisi)
        
        Args:
            fund_id: Fund ID
            
        Returns:
            Fund detail data
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = f"/api/vyk/fundDetail/{fund_id}"
        return self._make_request("GET", endpoint)
    
    def get_blocked_disclosures(self) -> List[BlockedDisclosure]:
        """
        Get list of blocked/removed disclosures (Bloklanmış Bildirimler Servisi)
        
        Returns:
            List of BlockedDisclosure objects
            
        Raises:
            KAPAPIError: API request failed
        """
        endpoint = "/api/vyk/blockedDisclosures"
        response = self._make_request("GET", endpoint)
        return [BlockedDisclosure.from_dict(item) for item in response]
    
    def get_ca_event_status(self, process_ref_ids: List[int]) -> List[CAProcessStatus]:
        """
        Get corporate action process status (Hak Kullanım Süreç Durum Servisi)
        
        Args:
            process_ref_ids: List of process reference IDs
            
        Returns:
            List of CAProcessStatus objects
            
        Raises:
            KAPAPIError: API request failed
        """
        if not process_ref_ids:
            raise KAPValidationError("process_ref_ids cannot be empty")
        
        params = {"processRefId": ",".join(map(str, process_ref_ids))}
        endpoint = "/api/vyk/caEventStatus"
        response = self._make_request("GET", endpoint, params=params)
        return [CAProcessStatus.from_dict(item) for item in response]
    
    def search_disclosures_by_company(
        self,
        company_id: str,
        start_index: Optional[int] = None,
        disclosure_type: Optional[str] = None
    ) -> List[DisclosureInfo]:
        """
        Search disclosures for a specific company
        
        Args:
            company_id: Company ID
            start_index: Starting disclosure index (if None, uses last index)
            disclosure_type: Filter by disclosure type
            
        Returns:
            List of DisclosureInfo objects
        """
        if start_index is None:
            start_index = self.get_last_disclosure_index()
        
        return self.get_disclosures(
            disclosure_index=start_index,
            company_id=company_id,
            disclosure_type=disclosure_type
        )
    
    def get_company_by_stock_code(self, stock_code: str) -> Optional[MemberInfo]:
        """
        Find company by stock code
        
        Args:
            stock_code: Stock code (e.g., 'THYAO')
            
        Returns:
            MemberInfo object or None if not found
        """
        members = self.get_members()
        for member in members:
            if member.stock_code and stock_code.upper() in member.stock_code.upper():
                return member
        return None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.session.close()
