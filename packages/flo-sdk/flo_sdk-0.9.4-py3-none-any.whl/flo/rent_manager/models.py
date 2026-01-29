"""Rent Manager data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class RentManagerUser:
    """Represents a Rent Manager user."""
    foreign_id: str
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_address: Optional[str] = None
    is_active: bool = True
    user_type: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "userName": self.user_name,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "emailAddress": self.email_address,
            "isActive": self.is_active,
            "userType": self.user_type,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerUser":
        """Create RentManagerUser from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("UserID", "")),
            user_name=rm_data.get("UserName"),
            first_name=rm_data.get("FirstName"),
            last_name=rm_data.get("LastName"),
            email_address=rm_data.get("EmailAddress"),
            is_active=rm_data.get("IsActive", True),
            user_type=rm_data.get("UserType"),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerOwner:
    """Represents a Rent Manager owner."""
    foreign_id: str
    name: Optional[str] = None
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "displayName": self.display_name,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "companyName": self.company_name,
            "emailAddress": self.email_address,
            "phoneNumber": self.phone_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerOwner":
        """Create RentManagerOwner from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("OwnerID", "")),
            name=rm_data.get("Name"),
            display_name=rm_data.get("DisplayName"),
            first_name=rm_data.get("FirstName"),
            last_name=rm_data.get("LastName"),
            company_name=rm_data.get("CompanyName"),
            email_address=rm_data.get("EmailAddress"),
            phone_number=rm_data.get("PhoneNumber"),
            address=rm_data.get("Address"),
            city=rm_data.get("City"),
            state=rm_data.get("State"),
            postal_code=rm_data.get("PostalCode"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerProperty:
    """Represents a Rent Manager property."""
    foreign_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    property_type: Optional[str] = None
    primary_owner_id: Optional[int] = None
    default_bank_id: Optional[int] = None
    is_active: bool = True
    comment: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "propertyType": self.property_type,
            "primaryOwnerId": self.primary_owner_id,
            "defaultBankId": self.default_bank_id,
            "isActive": self.is_active,
            "comment": self.comment,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerProperty":
        """Create RentManagerProperty from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("PropertyID", "")),
            name=rm_data.get("Name"),
            address=rm_data.get("Address"),
            city=rm_data.get("City"),
            state=rm_data.get("State"),
            postal_code=rm_data.get("PostalCode"),
            property_type=rm_data.get("PropertyType"),
            primary_owner_id=rm_data.get("PrimaryOwnerID"),
            default_bank_id=rm_data.get("DefaultBankID"),
            is_active=rm_data.get("IsActive", True),
            comment=rm_data.get("Comment"),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerUnit:
    """Represents a Rent Manager unit."""
    foreign_id: str
    property_id: Optional[int] = None
    unit_number: Optional[str] = None
    unit_type: Optional[str] = None
    square_feet: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    market_rent: Optional[float] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "propertyId": self.property_id,
            "unitNumber": self.unit_number,
            "unitType": self.unit_type,
            "squareFeet": self.square_feet,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "marketRent": self.market_rent,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerUnit":
        """Create RentManagerUnit from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("UnitID", "")),
            property_id=rm_data.get("PropertyID"),
            unit_number=rm_data.get("UnitNumber"),
            unit_type=rm_data.get("UnitType"),
            square_feet=rm_data.get("SquareFeet"),
            bedrooms=rm_data.get("Bedrooms"),
            bathrooms=rm_data.get("Bathrooms"),
            market_rent=rm_data.get("MarketRent"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerJob:
    """Represents a Rent Manager job."""
    foreign_id: str
    property_id: Optional[int] = None
    job_number: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "propertyId": self.property_id,
            "jobNumber": self.job_number,
            "description": self.description,
            "jobType": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "estimatedCost": self.estimated_cost,
            "actualCost": self.actual_cost,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerJob":
        """Create RentManagerJob from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("JobID", "")),
            property_id=rm_data.get("PropertyID"),
            job_number=rm_data.get("JobNumber"),
            description=rm_data.get("Description"),
            job_type=rm_data.get("JobType"),
            status=rm_data.get("Status"),
            priority=rm_data.get("Priority"),
            estimated_cost=rm_data.get("EstimatedCost"),
            actual_cost=rm_data.get("ActualCost"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerCreditCard:
    """Represents a Rent Manager credit card."""
    foreign_id: str
    card_name: Optional[str] = None
    card_number: Optional[str] = None
    expiration_date: Optional[str] = None
    card_type: Optional[str] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "cardName": self.card_name,
            "cardNumber": self.card_number,
            "expirationDate": self.expiration_date,
            "cardType": self.card_type,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerCreditCard":
        """Create RentManagerCreditCard from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("CreditCardID", "")),
            card_name=rm_data.get("CardName"),
            card_number=rm_data.get("CardNumber"),
            expiration_date=rm_data.get("ExpirationDate"),
            card_type=rm_data.get("CardType"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerIssue:
    """Represents a Rent Manager issue."""
    foreign_id: str
    property_id: Optional[int] = None
    issue_number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_to: Optional[str] = None
    reported_by: Optional[str] = None
    is_active: bool = True
    create_date: Optional[str] = None
    modified_date: Optional[str] = None
    properties: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "propertyId": self.property_id,
            "issueNumber": self.issue_number,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
            "assignedTo": self.assigned_to,
            "reportedBy": self.reported_by,
            "isActive": self.is_active,
            "createDate": self.create_date,
            "modifiedDate": self.modified_date,
            "properties": self.properties,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerIssue":
        """Create RentManagerIssue from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("IssueID", "")),
            property_id=rm_data.get("PropertyID"),
            issue_number=rm_data.get("IssueNumber"),
            description=rm_data.get("Description"),
            status=rm_data.get("Status"),
            priority=rm_data.get("Priority"),
            category=rm_data.get("Category"),
            assigned_to=rm_data.get("AssignedTo"),
            reported_by=rm_data.get("ReportedBy"),
            is_active=rm_data.get("IsActive", True),
            create_date=rm_data.get("CreateDate"),
            modified_date=rm_data.get("ModifiedDate"),
            properties=rm_data.get("Properties", []),
        )


@dataclass
class RentManagerGlAccount:
    """Represents a Rent Manager GL account."""
    foreign_id: str
    reference: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    gl_account_type: Optional[str] = None
    parent_gl_account_id: Optional[int] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "reference": self.reference,
            "name": self.name,
            "description": self.description,
            "glAccountType": self.gl_account_type,
            "parentGlAccountId": self.parent_gl_account_id,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerGlAccount":
        """Create RentManagerGlAccount from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("GLAccountID", "")),
            reference=rm_data.get("Reference"),
            name=rm_data.get("Name"),
            description=rm_data.get("Description"),
            gl_account_type=rm_data.get("GLAccountType"),
            parent_gl_account_id=rm_data.get("ParentGLAccountID"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
        )


@dataclass
class RentManagerVendor:
    """Represents a Rent Manager vendor."""
    foreign_id: str
    name: Optional[str] = None
    payee: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    default_account_id: Optional[int] = None
    tax_id: Optional[str] = None
    is_active: bool = True
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    properties: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "payee": self.payee,
            "companyName": self.company_name,
            "contactName": self.contact_name,
            "emailAddress": self.email_address,
            "phoneNumber": self.phone_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "defaultAccountId": self.default_account_id,
            "taxId": self.tax_id,
            "isActive": self.is_active,
            "createdDate": self.created_date,
            "modifiedDate": self.modified_date,
            "properties": self.properties,
        }

    @classmethod
    def from_rent_manager(cls, rm_data: Dict[str, Any]) -> "RentManagerVendor":
        """Create RentManagerVendor from Rent Manager API response."""
        return cls(
            foreign_id=str(rm_data.get("VendorID", "")),
            name=rm_data.get("Name"),
            payee=rm_data.get("Payee"),
            company_name=rm_data.get("CompanyName"),
            contact_name=rm_data.get("ContactName"),
            email_address=rm_data.get("EmailAddress"),
            phone_number=rm_data.get("PhoneNumber"),
            address=rm_data.get("Address"),
            city=rm_data.get("City"),
            state=rm_data.get("State"),
            postal_code=rm_data.get("PostalCode"),
            default_account_id=rm_data.get("DefaultAccountID"),
            tax_id=rm_data.get("TaxID"),
            is_active=rm_data.get("IsActive", True),
            created_date=rm_data.get("CreatedDate"),
            modified_date=rm_data.get("ModifiedDate"),
            properties=rm_data.get("Properties", []),
        )
