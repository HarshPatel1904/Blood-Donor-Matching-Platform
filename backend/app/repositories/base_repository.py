from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseRepository(ABC):
    """Abstract Base Class specifying all data access operations."""

    # ---------------- USER OPERATIONS ---------------- #
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_user_status(self, user_id: str, is_active: int) -> bool:
        pass

    # ---------------- DONOR OPERATIONS ---------------- #
    @abstractmethod
    def create_donor(self, donor_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_donor_by_id(self, donor_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_donor_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_donor_profile(self, donor_id: str, updates: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def update_donor_availability(self, donor_id: str, is_available: int) -> bool:
        pass

    @abstractmethod
    def list_donors(
        self,
        blood_group: Optional[str] = None,
        is_available: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        pass

    # ---------------- HOSPITAL OPERATIONS ---------------- #
    @abstractmethod
    def create_hospital(self, hospital_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_hospital_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_hospital_verification(
        self,
        hospital_id: str,
        status: str,
        verified_at: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    def list_hospitals(self, verification_status: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    # ---------------- BLOOD REQUEST OPERATIONS ---------------- #
    @abstractmethod
    def create_blood_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_blood_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_request_verification(
        self,
        request_id: str,
        verification_status: str
    ) -> bool:
        pass

    @abstractmethod
    def update_request_lifecycle(
        self,
        request_id: str,
        request_status: str
    ) -> bool:
        pass

    @abstractmethod
    def list_blood_requests(
        self,
        requester_user_id: Optional[str] = None,
        verification_status: Optional[str] = None,
        request_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

    # ---------------- DONOR RESPONSE OPERATIONS ---------------- #
    @abstractmethod
    def save_donor_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_donor_response(self, request_id: str, donor_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_responses_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_responses_for_donor(self, donor_id: str) -> List[Dict[str, Any]]:
        pass

    # ---------------- NOTIFICATION OPERATIONS ---------------- #
    @abstractmethod
    def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_notifications(
        self,
        recipient_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

    # ---------------- AUDIT LOG OPERATIONS ---------------- #
    @abstractmethod
    def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        pass