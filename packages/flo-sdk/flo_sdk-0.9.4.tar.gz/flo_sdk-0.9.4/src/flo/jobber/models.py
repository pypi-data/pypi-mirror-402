"""Jobber data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class JobberUser:
    """Jobber user model."""
    foreign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    is_account_admin: bool = False
    is_account_owner: bool = False

    @classmethod
    def from_jobber(cls, data: Dict[str, Any]) -> "JobberUser":
        """Create JobberUser from Jobber API response."""
        name = data.get("name", {})
        email = data.get("email", {})
        phone = data.get("phone", {})
        
        return cls(
            foreign_id=data.get("id", ""),
            first_name=name.get("first"),
            last_name=name.get("last"),
            email=email.get("raw") if email else None,
            phone=phone.get("raw") if phone else None,
            status=data.get("status"),
            is_account_admin=data.get("isAccountAdmin", False),
            is_account_owner=data.get("isAccountOwner", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dictionary."""
        return {
            "foreignId": self.foreign_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "isAccountAdmin": self.is_account_admin,
            "isAccountOwner": self.is_account_owner,
        }


@dataclass
class JobberClient:
    """Jobber client model."""
    foreign_id: str
    name: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)

    @classmethod
    def from_jobber(cls, data: Dict[str, Any]) -> "JobberClient":
        """Create JobberClient from Jobber API response."""
        emails = data.get("emails", [])
        phones = data.get("phones", [])
        
        return cls(
            foreign_id=data.get("id", ""),
            name=data.get("name"),
            emails=[e.get("address") for e in emails if e.get("address")],
            phones=[p.get("number") for p in phones if p.get("number")],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dictionary."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "emails": self.emails,
            "phones": self.phones,
        }


@dataclass
class JobberJob:
    """Jobber job model."""
    foreign_id: str
    job_number: Optional[str] = None
    title: Optional[str] = None
    instructions: Optional[str] = None
    job_status: Optional[str] = None
    total: Optional[float] = None
    created_at: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    client_id: Optional[str] = None

    @classmethod
    def from_jobber(cls, data: Dict[str, Any]) -> "JobberJob":
        """Create JobberJob from Jobber API response."""
        client = data.get("client", {})
        
        return cls(
            foreign_id=data.get("id", ""),
            job_number=data.get("jobNumber"),
            title=data.get("title"),
            instructions=data.get("instructions"),
            job_status=data.get("jobStatus"),
            total=data.get("total"),
            created_at=data.get("createdAt"),
            start_at=data.get("startAt"),
            end_at=data.get("endAt"),
            client_id=client.get("id") if client else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dictionary."""
        return {
            "foreignId": self.foreign_id,
            "jobNumber": self.job_number,
            "title": self.title,
            "instructions": self.instructions,
            "jobStatus": self.job_status,
            "total": self.total,
            "createdAt": self.created_at,
            "startAt": self.start_at,
            "endAt": self.end_at,
            "clientId": self.client_id,
        }


@dataclass
class JobberExpense:
    """Jobber expense model."""
    foreign_id: str
    title: Optional[str] = None
    total: Optional[float] = None
    description: Optional[str] = None
    date: Optional[str] = None
    linked_job_id: Optional[str] = None
    receipt_url: Optional[str] = None
    reimbursable_to_id: Optional[str] = None
    accounting_code_id: Optional[str] = None

    @classmethod
    def from_jobber(cls, data: Dict[str, Any]) -> "JobberExpense":
        """Create JobberExpense from Jobber API response."""
        linked_job = data.get("linkedJob", {})
        
        return cls(
            foreign_id=data.get("id", ""),
            title=data.get("title"),
            total=data.get("total"),
            description=data.get("description"),
            date=data.get("date"),
            linked_job_id=linked_job.get("id") if linked_job else None,
            receipt_url=data.get("receiptUrl"),
            reimbursable_to_id=data.get("reimbursableToId"),
            accounting_code_id=data.get("accountingCodeId"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dictionary."""
        return {
            "foreignId": self.foreign_id,
            "title": self.title,
            "total": self.total,
            "description": self.description,
            "date": self.date,
            "linkedJobId": self.linked_job_id,
            "receiptUrl": self.receipt_url,
            "reimbursableToId": self.reimbursable_to_id,
            "accountingCodeId": self.accounting_code_id,
        }

