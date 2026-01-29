"""Buildium data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class BuildiumUser:
    """Represents a Buildium user."""
    foreign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    alternate_email: Optional[str] = None
    phone_numbers: List[Dict[str, Any]] = field(default_factory=list)
    user_types: List[str] = field(default_factory=list)
    is_active: bool = True
    is_company: bool = False
    last_login: Optional[str] = None
    user_role: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "companyName": self.company_name,
            "email": self.email,
            "alternateEmail": self.alternate_email,
            "phoneNumbers": self.phone_numbers,
            "userTypes": self.user_types,
            "isActive": self.is_active,
            "isCompany": self.is_company,
            "lastLogin": self.last_login,
            "userRole": self.user_role,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumUser":
        """Create BuildiumUser from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            first_name=buildium_data.get("FirstName"),
            last_name=buildium_data.get("LastName"),
            company_name=buildium_data.get("CompanyName"),
            email=buildium_data.get("Email"),
            alternate_email=buildium_data.get("AlternateEmail"),
            phone_numbers=buildium_data.get("PhoneNumbers", []),
            user_types=buildium_data.get("UserTypes", []),
            is_active=buildium_data.get("IsActive", True),
            is_company=buildium_data.get("IsCompany", False),
            last_login=buildium_data.get("LastLogin"),
            user_role=buildium_data.get("UserRole"),
        )


@dataclass
class BuildiumVendor:
    """Represents a Buildium vendor."""
    foreign_id: str
    is_company: bool = False
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    primary_email: Optional[str] = None
    alternate_email: Optional[str] = None
    phone_numbers: List[Dict[str, Any]] = field(default_factory=list)
    website: Optional[str] = None
    category: Optional[Dict[str, Any]] = None
    address: Optional[Dict[str, Any]] = None
    vendor_insurance: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    account_number: Optional[str] = None
    expense_gl_account_id: Optional[int] = None
    tax_information: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "isCompany": self.is_company,
            "isActive": self.is_active,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "companyName": self.company_name,
            "primaryEmail": self.primary_email,
            "alternateEmail": self.alternate_email,
            "phoneNumbers": self.phone_numbers,
            "website": self.website,
            "category": self.category,
            "address": self.address,
            "vendorInsurance": self.vendor_insurance,
            "comments": self.comments,
            "accountNumber": self.account_number,
            "expenseGlAccountId": self.expense_gl_account_id,
            "taxInformation": self.tax_information,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumVendor":
        """Create BuildiumVendor from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            is_company=buildium_data.get("IsCompany", False),
            is_active=buildium_data.get("IsActive", True),
            first_name=buildium_data.get("FirstName"),
            last_name=buildium_data.get("LastName"),
            company_name=buildium_data.get("CompanyName"),
            primary_email=buildium_data.get("PrimaryEmail"),
            alternate_email=buildium_data.get("AlternateEmail"),
            phone_numbers=buildium_data.get("PhoneNumbers", []),
            website=buildium_data.get("Website"),
            category=buildium_data.get("Category"),
            address=buildium_data.get("Address"),
            vendor_insurance=buildium_data.get("VendorInsurance"),
            comments=buildium_data.get("Comments"),
            account_number=buildium_data.get("AccountNumber"),
            expense_gl_account_id=buildium_data.get("ExpenseGLAccountId"),
            tax_information=buildium_data.get("TaxInformation"),
        )


@dataclass
class BuildiumGlAccount:
    """Represents a Buildium GL account."""
    foreign_id: str
    account_number: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    account_type: Optional[str] = None
    sub_type: Optional[str] = None
    is_default_gl_account: bool = False
    default_account_name: Optional[str] = None
    is_contra_account: bool = False
    is_bank_account: bool = False
    cash_flow_classification: Optional[str] = None
    exclude_from_cash_balances: bool = False
    is_active: bool = True
    parent_gl_account_id: Optional[int] = None
    sub_accounts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "accountNumber": self.account_number,
            "name": self.name,
            "description": self.description,
            "accountType": self.account_type,
            "subType": self.sub_type,
            "isDefaultGlAccount": self.is_default_gl_account,
            "defaultAccountName": self.default_account_name,
            "isContraAccount": self.is_contra_account,
            "isBankAccount": self.is_bank_account,
            "cashFlowClassification": self.cash_flow_classification,
            "excludeFromCashBalances": self.exclude_from_cash_balances,
            "isActive": self.is_active,
            "parentGlAccountId": self.parent_gl_account_id,
            "subAccounts": self.sub_accounts,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumGlAccount":
        """Create BuildiumGlAccount from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            account_number=buildium_data.get("AccountNumber"),
            name=buildium_data.get("Name"),
            description=buildium_data.get("Description"),
            account_type=buildium_data.get("Type"),
            sub_type=buildium_data.get("SubType"),
            is_default_gl_account=buildium_data.get("IsDefaultGLAccount", False),
            default_account_name=buildium_data.get("DefaultAccountName"),
            is_contra_account=buildium_data.get("IsContraAccount", False),
            is_bank_account=buildium_data.get("IsBankAccount", False),
            cash_flow_classification=buildium_data.get("CashFlowClassification"),
            exclude_from_cash_balances=buildium_data.get("ExcludeFromCashBalances", False),
            is_active=buildium_data.get("IsActive", True),
            parent_gl_account_id=buildium_data.get("ParentGLAccountId"),
            sub_accounts=buildium_data.get("SubAccounts", []),
        )


@dataclass
class BuildiumBill:
    """Represents a Buildium bill."""
    foreign_id: str
    date: Optional[str] = None
    due_date: Optional[str] = None
    paid_date: Optional[str] = None
    memo: Optional[str] = None
    vendor_id: Optional[int] = None
    work_order_id: Optional[int] = None
    reference_number: Optional[str] = None
    approval_status: Optional[str] = None
    lines: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "date": self.date,
            "dueDate": self.due_date,
            "paidDate": self.paid_date,
            "memo": self.memo,
            "vendorId": self.vendor_id,
            "workOrderId": self.work_order_id,
            "referenceNumber": self.reference_number,
            "approvalStatus": self.approval_status,
            "lines": self.lines,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumBill":
        """Create BuildiumBill from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            date=buildium_data.get("Date"),
            due_date=buildium_data.get("DueDate"),
            paid_date=buildium_data.get("PaidDate"),
            memo=buildium_data.get("Memo"),
            vendor_id=buildium_data.get("VendorId"),
            work_order_id=buildium_data.get("WorkOrderId"),
            reference_number=buildium_data.get("ReferenceNumber"),
            approval_status=buildium_data.get("ApprovalStatus"),
            lines=buildium_data.get("Lines", []),
        )


@dataclass
class BuildiumRental:
    """Represents a Buildium rental property."""
    foreign_id: str
    name: Optional[str] = None
    structure_description: Optional[str] = None
    number_units: Optional[int] = None
    is_active: bool = True
    operating_bank_account_id: Optional[int] = None
    reserve: Optional[float] = None
    address: Optional[Dict[str, Any]] = None
    year_built: Optional[int] = None
    rental_type: Optional[str] = None
    rental_sub_type: Optional[str] = None
    rental_manager: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "structureDescription": self.structure_description,
            "numberUnits": self.number_units,
            "isActive": self.is_active,
            "operatingBankAccountId": self.operating_bank_account_id,
            "reserve": self.reserve,
            "address": self.address,
            "yearBuilt": self.year_built,
            "rentalType": self.rental_type,
            "rentalSubType": self.rental_sub_type,
            "rentalManager": self.rental_manager,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumRental":
        """Create BuildiumRental from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            name=buildium_data.get("Name"),
            structure_description=buildium_data.get("StructureDescription"),
            number_units=buildium_data.get("NumberUnits"),
            is_active=buildium_data.get("IsActive", True),
            operating_bank_account_id=buildium_data.get("OperatingBankAccountId"),
            reserve=buildium_data.get("Reserve"),
            address=buildium_data.get("Address"),
            year_built=buildium_data.get("YearBuilt"),
            rental_type=buildium_data.get("RentalType"),
            rental_sub_type=buildium_data.get("RentalSubType"),
            rental_manager=buildium_data.get("RentalManager"),
        )


@dataclass
class BuildiumRentalOwner:
    """Represents a Buildium rental owner."""
    foreign_id: str
    is_company: bool = False
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    alternate_email: Optional[str] = None
    phone_numbers: List[Dict[str, Any]] = field(default_factory=list)
    comment: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    management_agreement_start_date: Optional[str] = None
    management_agreement_end_date: Optional[str] = None
    property_ids: List[int] = field(default_factory=list)
    tax_information: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "isCompany": self.is_company,
            "isActive": self.is_active,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "companyName": self.company_name,
            "email": self.email,
            "alternateEmail": self.alternate_email,
            "phoneNumbers": self.phone_numbers,
            "comment": self.comment,
            "address": self.address,
            "managementAgreementStartDate": self.management_agreement_start_date,
            "managementAgreementEndDate": self.management_agreement_end_date,
            "propertyIds": self.property_ids,
            "taxInformation": self.tax_information,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumRentalOwner":
        """Create BuildiumRentalOwner from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            is_company=buildium_data.get("IsCompany", False),
            is_active=buildium_data.get("IsActive", True),
            first_name=buildium_data.get("FirstName"),
            last_name=buildium_data.get("LastName"),
            company_name=buildium_data.get("CompanyName"),
            email=buildium_data.get("Email"),
            alternate_email=buildium_data.get("AlternateEmail"),
            phone_numbers=buildium_data.get("PhoneNumbers", []),
            comment=buildium_data.get("Comment"),
            address=buildium_data.get("Address"),
            management_agreement_start_date=buildium_data.get("ManagementAgreementStartDate"),
            management_agreement_end_date=buildium_data.get("ManagementAgreementEndDate"),
            property_ids=buildium_data.get("PropertyIds", []),
            tax_information=buildium_data.get("TaxInformation"),
        )


@dataclass
class BuildiumRentalUnit:
    """Represents a Buildium rental unit."""
    foreign_id: str
    property_id: Optional[int] = None
    building_name: Optional[str] = None
    unit_number: Optional[str] = None
    description: Optional[str] = None
    market_rent: Optional[float] = None
    address: Optional[Dict[str, Any]] = None
    unit_bedrooms: Optional[str] = None
    unit_bathrooms: Optional[str] = None
    unit_size: Optional[float] = None
    is_unit_listed: bool = False
    is_unit_occupied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "propertyId": self.property_id,
            "buildingName": self.building_name,
            "unitNumber": self.unit_number,
            "description": self.description,
            "marketRent": self.market_rent,
            "address": self.address,
            "unitBedrooms": self.unit_bedrooms,
            "unitBathrooms": self.unit_bathrooms,
            "unitSize": self.unit_size,
            "isUnitListed": self.is_unit_listed,
            "isUnitOccupied": self.is_unit_occupied,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumRentalUnit":
        """Create BuildiumRentalUnit from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            property_id=buildium_data.get("PropertyId"),
            building_name=buildium_data.get("BuildingName"),
            unit_number=buildium_data.get("UnitNumber"),
            description=buildium_data.get("Description"),
            market_rent=buildium_data.get("MarketRent"),
            address=buildium_data.get("Address"),
            unit_bedrooms=buildium_data.get("UnitBedrooms"),
            unit_bathrooms=buildium_data.get("UnitBathrooms"),
            unit_size=buildium_data.get("UnitSize"),
            is_unit_listed=buildium_data.get("IsUnitListed", False),
            is_unit_occupied=buildium_data.get("IsUnitOccupied", False),
        )


@dataclass
class BuildiumAssociation:
    """Represents a Buildium association."""
    foreign_id: str
    name: Optional[str] = None
    is_active: bool = True
    reserve: Optional[float] = None
    description: Optional[str] = None
    year_built: Optional[int] = None
    operating_bank_account: Optional[str] = None
    operating_bank_account_id: Optional[int] = None
    address: Optional[Dict[str, Any]] = None
    association_manager: Optional[Dict[str, Any]] = None
    fiscal_year_end_day: Optional[int] = None
    fiscal_year_end_month: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "name": self.name,
            "isActive": self.is_active,
            "reserve": self.reserve,
            "description": self.description,
            "yearBuilt": self.year_built,
            "operatingBankAccount": self.operating_bank_account,
            "operatingBankAccountId": self.operating_bank_account_id,
            "address": self.address,
            "associationManager": self.association_manager,
            "fiscalYearEndDay": self.fiscal_year_end_day,
            "fiscalYearEndMonth": self.fiscal_year_end_month,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumAssociation":
        """Create BuildiumAssociation from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            name=buildium_data.get("Name"),
            is_active=buildium_data.get("IsActive", True),
            reserve=buildium_data.get("Reserve"),
            description=buildium_data.get("Description"),
            year_built=buildium_data.get("YearBuilt"),
            operating_bank_account=buildium_data.get("OperatingBankAccount"),
            operating_bank_account_id=buildium_data.get("OperatingBankAccountId"),
            address=buildium_data.get("Address"),
            association_manager=buildium_data.get("AssociationManager"),
            fiscal_year_end_day=buildium_data.get("FiscalYearEndDay"),
            fiscal_year_end_month=buildium_data.get("FiscalYearEndMonth"),
        )


@dataclass
class BuildiumAssociationOwner:
    """Represents a Buildium association owner."""
    foreign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    alternate_email: Optional[str] = None
    phone_numbers: List[Dict[str, Any]] = field(default_factory=list)
    primary_address: Optional[Dict[str, Any]] = None
    alternate_address: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    ownership_accounts: List[Dict[str, Any]] = field(default_factory=list)
    mailing_preference: Optional[str] = None
    vehicles: List[Dict[str, Any]] = field(default_factory=list)
    occupies_unit: bool = False
    board_member_terms: List[Dict[str, Any]] = field(default_factory=list)
    created_date_time: Optional[str] = None
    tax_id: Optional[str] = None
    delinquency_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "alternateEmail": self.alternate_email,
            "phoneNumbers": self.phone_numbers,
            "primaryAddress": self.primary_address,
            "alternateAddress": self.alternate_address,
            "comment": self.comment,
            "emergencyContact": self.emergency_contact,
            "ownershipAccounts": self.ownership_accounts,
            "mailingPreference": self.mailing_preference,
            "vehicles": self.vehicles,
            "occupiesUnit": self.occupies_unit,
            "boardMemberTerms": self.board_member_terms,
            "createdDateTime": self.created_date_time,
            "taxId": self.tax_id,
            "delinquencyStatus": self.delinquency_status,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumAssociationOwner":
        """Create BuildiumAssociationOwner from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            first_name=buildium_data.get("FirstName"),
            last_name=buildium_data.get("LastName"),
            email=buildium_data.get("Email"),
            alternate_email=buildium_data.get("AlternateEmail"),
            phone_numbers=buildium_data.get("PhoneNumbers", []),
            primary_address=buildium_data.get("PrimaryAddress"),
            alternate_address=buildium_data.get("AlternateAddress"),
            comment=buildium_data.get("Comment"),
            emergency_contact=buildium_data.get("EmergencyContact"),
            ownership_accounts=buildium_data.get("OwnershipAccounts", []),
            mailing_preference=buildium_data.get("MailingPreference"),
            vehicles=buildium_data.get("Vehicles", []),
            occupies_unit=buildium_data.get("OccupiesUnit", False),
            board_member_terms=buildium_data.get("BoardMemberTerms", []),
            created_date_time=buildium_data.get("CreatedDateTime"),
            tax_id=buildium_data.get("TaxId"),
            delinquency_status=buildium_data.get("DelinquencyStatus"),
        )


@dataclass
class BuildiumAssociationUnit:
    """Represents a Buildium association unit."""
    foreign_id: str
    association_id: Optional[int] = None
    association_name: Optional[str] = None
    unit_number: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    unit_bedrooms: Optional[str] = None
    unit_bathrooms: Optional[str] = None
    unit_size: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "associationId": self.association_id,
            "associationName": self.association_name,
            "unitNumber": self.unit_number,
            "address": self.address,
            "unitBedrooms": self.unit_bedrooms,
            "unitBathrooms": self.unit_bathrooms,
            "unitSize": self.unit_size,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumAssociationUnit":
        """Create BuildiumAssociationUnit from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            association_id=buildium_data.get("AssociationId"),
            association_name=buildium_data.get("AssociationName"),
            unit_number=buildium_data.get("UnitNumber"),
            address=buildium_data.get("Address"),
            unit_bedrooms=buildium_data.get("UnitBedrooms"),
            unit_bathrooms=buildium_data.get("UnitBathrooms"),
            unit_size=buildium_data.get("UnitSize"),
        )


@dataclass
class BuildiumWorkOrder:
    """Represents a Buildium work order."""
    foreign_id: str
    task: Optional[Dict[str, Any]] = None
    work_details: Optional[str] = None
    invoice_number: Optional[str] = None
    chargeable_to: Optional[str] = None
    entry_allowed: Optional[str] = None
    entry_notes: Optional[str] = None
    vendor_id: Optional[int] = None
    vendor_notes: Optional[str] = None
    entry_contact: Optional[Dict[str, Any]] = None
    bill_transaction_id: Optional[int] = None
    amount: Optional[float] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        return {
            "foreignId": self.foreign_id,
            "task": self.task,
            "workDetails": self.work_details,
            "invoiceNumber": self.invoice_number,
            "chargeableTo": self.chargeable_to,
            "entryAllowed": self.entry_allowed,
            "entryNotes": self.entry_notes,
            "vendorId": self.vendor_id,
            "vendorNotes": self.vendor_notes,
            "entryContact": self.entry_contact,
            "billTransactionId": self.bill_transaction_id,
            "amount": self.amount,
            "lineItems": self.line_items,
        }

    @classmethod
    def from_buildium(cls, buildium_data: Dict[str, Any]) -> "BuildiumWorkOrder":
        """Create BuildiumWorkOrder from Buildium API response."""
        return cls(
            foreign_id=str(buildium_data.get("Id", "")),
            task=buildium_data.get("Task"),
            work_details=buildium_data.get("WorkDetails"),
            invoice_number=buildium_data.get("InvoiceNumber"),
            chargeable_to=buildium_data.get("ChargeableTo"),
            entry_allowed=buildium_data.get("EntryAllowed"),
            entry_notes=buildium_data.get("EntryNotes"),
            vendor_id=buildium_data.get("VendorId"),
            vendor_notes=buildium_data.get("VendorNotes"),
            entry_contact=buildium_data.get("EntryContact"),
            bill_transaction_id=buildium_data.get("BillTransactionId"),
            amount=buildium_data.get("Amount"),
            line_items=buildium_data.get("LineItems", []),
        )
