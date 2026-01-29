"""Plaid data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class Account:
    """Represents a Plaid bank account."""
    account_id: str
    name: str
    mask: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    balance: Optional[float] = None
    currency_code: Optional[str] = None
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "accountId": self.account_id,
            "name": self.name,
            "mask": self.mask,
            "type": self.type,
            "subtype": self.subtype,
            "balance": self.balance,
            "currencyCode": self.currency_code,
            "institutionId": self.institution_id,
            "institutionName": self.institution_name,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_plaid(cls, plaid_data: Dict[str, Any], institution_id: Optional[str] = None, institution_name: Optional[str] = None) -> "Account":
        """Create Account from Plaid API response."""
        # Extract balance from balances object if present
        balance = None
        if "balances" in plaid_data:
            balances = plaid_data["balances"]
            balance = balances.get("available") or balances.get("current")
        
        return cls(
            account_id=plaid_data.get("account_id", ""),
            name=plaid_data.get("name", ""),
            mask=plaid_data.get("mask"),
            type=plaid_data.get("type"),
            subtype=plaid_data.get("subtype"),
            balance=balance,
            currency_code=plaid_data.get("iso_currency_code") or plaid_data.get("unofficial_currency_code"),
            institution_id=institution_id,
            institution_name=institution_name,
            platform_data=plaid_data,
        )


@dataclass
class Transaction:
    """Represents a Plaid transaction."""
    transaction_id: str
    account_id: str
    amount: Optional[float] = None
    date: Optional[str] = None
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    pending: Optional[bool] = None
    currency_code: Optional[str] = None
    authorized_date: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    payment_meta: Optional[Dict[str, Any]] = None
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "transactionId": self.transaction_id,
            "accountId": self.account_id,
            "amount": self.amount,
            "date": self.date,
            "name": self.name,
            "merchantName": self.merchant_name,
            "category": self.category,
            "pending": self.pending,
            "currencyCode": self.currency_code,
            "authorizedDate": self.authorized_date,
            "location": self.location,
            "paymentMeta": self.payment_meta,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_plaid(cls, plaid_data: Dict[str, Any]) -> "Transaction":
        """Create Transaction from Plaid API response."""
        return cls(
            transaction_id=plaid_data.get("transaction_id", ""),
            account_id=plaid_data.get("account_id", ""),
            amount=plaid_data.get("amount"),
            date=plaid_data.get("date"),
            name=plaid_data.get("name"),
            merchant_name=plaid_data.get("merchant_name"),
            category=plaid_data.get("category"),
            pending=plaid_data.get("pending"),
            currency_code=plaid_data.get("iso_currency_code") or plaid_data.get("unofficial_currency_code"),
            authorized_date=plaid_data.get("authorized_date"),
            location=plaid_data.get("location"),
            payment_meta=plaid_data.get("payment_meta"),
            platform_data=plaid_data,
        )


@dataclass
class Institution:
    """Represents a Plaid financial institution."""
    institution_id: str
    name: str
    logo: Optional[str] = None
    url: Optional[str] = None
    primary_color: Optional[str] = None
    country_codes: Optional[List[str]] = None
    products: Optional[List[str]] = None
    platform_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "institutionId": self.institution_id,
            "name": self.name,
            "logo": self.logo,
            "url": self.url,
            "primaryColor": self.primary_color,
            "countryCodes": self.country_codes,
            "products": self.products,
            "platformData": self.platform_data,
        }
    
    @classmethod
    def from_plaid(cls, plaid_data: Dict[str, Any]) -> "Institution":
        """Create Institution from Plaid API response."""
        return cls(
            institution_id=plaid_data.get("institution_id", ""),
            name=plaid_data.get("name", ""),
            logo=plaid_data.get("logo"),
            url=plaid_data.get("url"),
            primary_color=plaid_data.get("primary_color"),
            country_codes=plaid_data.get("country_codes"),
            products=plaid_data.get("products"),
            platform_data=plaid_data,
        )

