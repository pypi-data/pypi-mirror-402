"""QuickBooks data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class Vendor:
    """Represents a QuickBooks vendor."""
    foreign_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    default_currency: str = "USD"
    contact_name: Optional[str] = None
    modified_date: Optional[str] = None
    platform_id: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    tax_number: Optional[str] = None
    addresses: List[Dict[str, Any]] = field(default_factory=list)
    subsidiaries: List[Dict[str, Any]] = field(default_factory=list)
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "defaultCurrency": self.default_currency,
            "contactName": self.contact_name,
            "modifiedDate": self.modified_date,
            "platformId": self.platform_id,
            "website": self.website,
            "registrationNumber": self.registration_number,
            "taxNumber": self.tax_number,
            "addresses": self.addresses,
            "subsidiaries": self.subsidiaries,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_rutter(cls, rutter_data: Dict[str, Any]) -> "Vendor":
        """Create Vendor from Rutter API response."""
        return cls(
            foreign_id=rutter_data.get("id", ""),
            name=rutter_data.get("vendor_name", ""),
            email=rutter_data.get("email"),
            phone=rutter_data.get("phone"),
            status=rutter_data.get("status", "active"),
            default_currency=rutter_data.get("currency_code", "USD"),
            contact_name=rutter_data.get("contact_name"),
            modified_date=rutter_data.get("updated_at"),
            platform_id=rutter_data.get("platform_id"),
            website=rutter_data.get("website"),
            registration_number=rutter_data.get("registration_number"),
            tax_number=rutter_data.get("tax_number"),
            addresses=rutter_data.get("addresses", []),
            subsidiaries=rutter_data.get("subsidiaries", []),
            platform_data=rutter_data.get("platform_data"),
        )


@dataclass
class Customer:
    """Represents a QuickBooks customer."""
    foreign_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    currency_code: Optional[str] = None
    tax_number: Optional[str] = None
    registration_number: Optional[str] = None
    status: Optional[str] = None
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "contactName": self.contact_name,
            "currencyCode": self.currency_code,
            "taxNumber": self.tax_number,
            "registrationNumber": self.registration_number,
            "status": self.status,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_rutter(cls, rutter_data: Dict[str, Any]) -> "Customer":
        """Create Customer from Rutter API response."""
        return cls(
            foreign_id=rutter_data.get("id", ""),
            name=rutter_data.get("customer_name") or rutter_data.get("name", ""),
            email=rutter_data.get("email"),
            phone=rutter_data.get("phone"),
            contact_name=rutter_data.get("contact_name"),
            currency_code=rutter_data.get("currency_code"),
            tax_number=rutter_data.get("tax_number"),
            registration_number=rutter_data.get("registration_number"),
            status=rutter_data.get("status"),
            platform_data=rutter_data.get("platform_data"),
        )


@dataclass
class Account:
    """Represents a QuickBooks chart of accounts entry."""
    foreign_id: str
    name: Optional[str] = None
    account_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    nominal_code: Optional[str] = None
    parent_id: Optional[str] = None
    platform_id: Optional[str] = None
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "accountType": self.account_type,
            "category": self.category,
            "status": self.status,
            "nominalCode": self.nominal_code,
            "parentId": self.parent_id,
            "platformId": self.platform_id,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_rutter(cls, rutter_data: Dict[str, Any]) -> "Account":
        """Create Account from Rutter API response."""
        return cls(
            foreign_id=rutter_data.get("id", ""),
            name=rutter_data.get("name"),
            account_type=rutter_data.get("account_type"),
            category=rutter_data.get("category"),
            status=rutter_data.get("status"),
            nominal_code=rutter_data.get("nominal_code"),
            parent_id=rutter_data.get("parent_id"),
            platform_id=rutter_data.get("platform_id"),
            platform_data=rutter_data.get("platform_data"),
        )


@dataclass
class Invoice:
    """Represents a QuickBooks invoice."""
    foreign_id: str
    document_number: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    currency_code: Optional[str] = None
    status: Optional[str] = None
    total_discount: Optional[float] = None
    sub_total: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    amount_due: Optional[float] = None
    memo: Optional[str] = None
    account_id: Optional[str] = None
    customer_id: Optional[str] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "documentNumber": self.document_number,
            "issueDate": self.issue_date,
            "dueDate": self.due_date,
            "currencyCode": self.currency_code,
            "status": self.status,
            "totalDiscount": self.total_discount,
            "subTotal": self.sub_total,
            "taxAmount": self.tax_amount,
            "totalAmount": self.total_amount,
            "amountDue": self.amount_due,
            "memo": self.memo,
            "accountId": self.account_id,
            "customerId": self.customer_id,
            "lineItems": self.line_items,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_rutter(cls, rutter_data: Dict[str, Any]) -> "Invoice":
        """Create Invoice from Rutter API response."""
        return cls(
            foreign_id=rutter_data.get("id", ""),
            document_number=rutter_data.get("document_number"),
            issue_date=rutter_data.get("issue_date"),
            due_date=rutter_data.get("due_date"),
            currency_code=rutter_data.get("currency_code"),
            status=rutter_data.get("status"),
            total_discount=rutter_data.get("total_discount"),
            sub_total=rutter_data.get("sub_total"),
            tax_amount=rutter_data.get("tax_amount"),
            total_amount=rutter_data.get("total_amount"),
            amount_due=rutter_data.get("amount_due"),
            memo=rutter_data.get("memo"),
            account_id=rutter_data.get("account_id"),
            customer_id=rutter_data.get("customer_id"),
            line_items=rutter_data.get("line_items", []),
            platform_data=rutter_data.get("platform_data"),
        )


@dataclass
class Expense:
    """Represents a QuickBooks expense."""
    foreign_id: str
    platform_id: Optional[str] = None
    expense_date: Optional[str] = None
    memo: Optional[str] = None
    vendor_id: Optional[str] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "platformId": self.platform_id,
            "expenseDate": self.expense_date,
            "memo": self.memo,
            "vendorId": self.vendor_id,
            "lineItems": self.line_items,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_rutter(cls, rutter_data: Dict[str, Any]) -> "Expense":
        """Create Expense from Rutter API response."""
        return cls(
            foreign_id=rutter_data.get("id", ""),
            platform_id=rutter_data.get("platform_id"),
            expense_date=rutter_data.get("expense_date"),
            memo=rutter_data.get("memo"),
            vendor_id=rutter_data.get("vendor_id"),
            line_items=rutter_data.get("line_items", []),
            platform_data=rutter_data.get("platform_data"),
        )

