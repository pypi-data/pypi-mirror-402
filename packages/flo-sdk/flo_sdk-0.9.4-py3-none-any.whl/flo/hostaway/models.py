"""Hostaway data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class HostawayListing:
    """Represents a Hostaway listing."""
    foreign_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    max_guests: Optional[int] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        result = {
            "foreignId": self.foreign_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
            "propertyType": self.property_type,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "maxGuests": self.max_guests,
            "status": self.status,
            "ownerId": self.owner_id,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
        # Add any extra fields
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_hostaway(cls, hostaway_data: Dict[str, Any]) -> "HostawayListing":
        """Create HostawayListing from Hostaway API response."""
        # Extract common fields
        listing_id = hostaway_data.get("id") or hostaway_data.get("listingId") or hostaway_data.get("_id")
        if listing_id is None:
            raise ValueError("Listing ID not found in response")
        
        # Build result dict with known fields
        result = {
            "foreign_id": str(listing_id),
            "name": hostaway_data.get("name") or hostaway_data.get("title"),
            "address": hostaway_data.get("address"),
            "city": hostaway_data.get("city"),
            "state": hostaway_data.get("state") or hostaway_data.get("stateCode"),
            "zip_code": hostaway_data.get("zipCode") or hostaway_data.get("zip") or hostaway_data.get("postalCode"),
            "country": hostaway_data.get("country") or hostaway_data.get("countryCode"),
            "property_type": hostaway_data.get("propertyType") or hostaway_data.get("type"),
            "bedrooms": hostaway_data.get("bedrooms") or hostaway_data.get("bedroomCount"),
            "bathrooms": hostaway_data.get("bathrooms") or hostaway_data.get("bathroomCount"),
            "max_guests": hostaway_data.get("maxGuests") or hostaway_data.get("maxOccupancy") or hostaway_data.get("accommodates"),
            "status": hostaway_data.get("status"),
            "owner_id": hostaway_data.get("ownerId") or hostaway_data.get("owner_id"),
            "created_at": hostaway_data.get("createdAt") or hostaway_data.get("created_at") or hostaway_data.get("dateCreated"),
            "updated_at": hostaway_data.get("updatedAt") or hostaway_data.get("updated_at") or hostaway_data.get("dateModified"),
        }
        
        # Store any extra fields that aren't in our standard model
        known_fields = {
            "id", "listingId", "_id", "name", "title", "address", "city", "state", "stateCode",
            "zipCode", "zip", "postalCode", "country", "countryCode", "propertyType", "type",
            "bedrooms", "bedroomCount", "bathrooms", "bathroomCount", "maxGuests", "maxOccupancy",
            "accommodates", "status", "ownerId", "owner_id", "createdAt", "created_at",
            "dateCreated", "updatedAt", "updated_at", "dateModified"
        }
        extra_fields = {k: v for k, v in hostaway_data.items() if k not in known_fields}
        result["extra_fields"] = extra_fields
        
        return cls(**result)


@dataclass
class HostawayOwner:
    """Represents a Hostaway owner."""
    foreign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        result = {
            "foreignId": self.foreign_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "companyName": self.company_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
        # Add any extra fields
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_hostaway(cls, hostaway_data: Dict[str, Any]) -> "HostawayOwner":
        """Create HostawayOwner from Hostaway API response."""
        # Extract owner ID
        owner_id = hostaway_data.get("id") or hostaway_data.get("ownerId") or hostaway_data.get("_id")
        if owner_id is None:
            raise ValueError("Owner ID not found in response")
        
        # Handle name fields (could be separate or combined)
        name = hostaway_data.get("name") or hostaway_data.get("fullName")
        first_name = hostaway_data.get("firstName") or hostaway_data.get("first_name")
        last_name = hostaway_data.get("lastName") or hostaway_data.get("last_name")
        
        # If name is combined but first/last are not provided, try to split
        if name and not first_name and not last_name:
            name_parts = name.split(" ", 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        # Build result dict
        result = {
            "foreign_id": str(owner_id),
            "first_name": first_name,
            "last_name": last_name,
            "company_name": hostaway_data.get("companyName") or hostaway_data.get("company_name"),
            "email": hostaway_data.get("email"),
            "phone": hostaway_data.get("phone") or hostaway_data.get("phoneNumber"),
            "address": hostaway_data.get("address"),
            "city": hostaway_data.get("city"),
            "state": hostaway_data.get("state") or hostaway_data.get("stateCode"),
            "zip_code": hostaway_data.get("zipCode") or hostaway_data.get("zip") or hostaway_data.get("postalCode"),
            "country": hostaway_data.get("country") or hostaway_data.get("countryCode"),
            "status": hostaway_data.get("status"),
            "created_at": hostaway_data.get("createdAt") or hostaway_data.get("created_at") or hostaway_data.get("dateCreated"),
            "updated_at": hostaway_data.get("updatedAt") or hostaway_data.get("updated_at") or hostaway_data.get("dateModified"),
        }
        
        # Store any extra fields
        known_fields = {
            "id", "ownerId", "_id", "name", "fullName", "firstName", "first_name",
            "lastName", "last_name", "companyName", "company_name", "email", "phone",
            "phoneNumber", "address", "city", "state", "stateCode", "zipCode", "zip",
            "postalCode", "country", "countryCode", "status", "createdAt", "created_at",
            "dateCreated", "updatedAt", "updated_at", "dateModified"
        }
        extra_fields = {k: v for k, v in hostaway_data.items() if k not in known_fields}
        result["extra_fields"] = extra_fields
        
        return cls(**result)


@dataclass
class HostawayUser:
    """Represents a Hostaway user."""
    foreign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        result = {
            "foreignId": self.foreign_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
        # Add any extra fields
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_hostaway(cls, hostaway_data: Dict[str, Any]) -> "HostawayUser":
        """Create HostawayUser from Hostaway API response."""
        # Extract user ID
        user_id = hostaway_data.get("id") or hostaway_data.get("userId") or hostaway_data.get("_id")
        if user_id is None:
            raise ValueError("User ID not found in response")
        
        # Handle name fields
        name = hostaway_data.get("name") or hostaway_data.get("fullName")
        first_name = hostaway_data.get("firstName") or hostaway_data.get("first_name")
        last_name = hostaway_data.get("lastName") or hostaway_data.get("last_name")
        
        # If name is combined but first/last are not provided, try to split
        if name and not first_name and not last_name:
            name_parts = name.split(" ", 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        # Build result dict
        result = {
            "foreign_id": str(user_id),
            "first_name": first_name,
            "last_name": last_name,
            "email": hostaway_data.get("email"),
            "phone": hostaway_data.get("phone") or hostaway_data.get("phoneNumber"),
            "role": hostaway_data.get("role") or hostaway_data.get("userRole"),
            "status": hostaway_data.get("status"),
            "created_at": hostaway_data.get("createdAt") or hostaway_data.get("created_at") or hostaway_data.get("dateCreated"),
            "updated_at": hostaway_data.get("updatedAt") or hostaway_data.get("updated_at") or hostaway_data.get("dateModified"),
        }
        
        # Store any extra fields
        known_fields = {
            "id", "userId", "_id", "name", "fullName", "firstName", "first_name",
            "lastName", "last_name", "email", "phone", "phoneNumber", "role",
            "userRole", "status", "createdAt", "created_at", "dateCreated",
            "updatedAt", "updated_at", "dateModified"
        }
        extra_fields = {k: v for k, v in hostaway_data.items() if k not in known_fields}
        result["extra_fields"] = extra_fields
        
        return cls(**result)


@dataclass
class HostawayUnit:
    """Represents a Hostaway unit."""
    foreign_id: str
    listing_id: Optional[int] = None
    name: Optional[str] = None
    unit_number: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    max_guests: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dict matching backend format."""
        result = {
            "foreignId": self.foreign_id,
            "listingId": self.listing_id,
            "name": self.name,
            "unitNumber": self.unit_number,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "maxGuests": self.max_guests,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }
        # Add any extra fields
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_hostaway(cls, hostaway_data: Dict[str, Any]) -> "HostawayUnit":
        """Create HostawayUnit from Hostaway API response."""
        # Extract unit ID
        unit_id = hostaway_data.get("id") or hostaway_data.get("unitId") or hostaway_data.get("_id")
        if unit_id is None:
            raise ValueError("Unit ID not found in response")
        
        # Build result dict
        result = {
            "foreign_id": str(unit_id),
            "listing_id": hostaway_data.get("listingId") or hostaway_data.get("listing_id"),
            "name": hostaway_data.get("name") or hostaway_data.get("title"),
            "unit_number": hostaway_data.get("unitNumber") or hostaway_data.get("unit_number"),
            "bedrooms": hostaway_data.get("bedrooms") or hostaway_data.get("bedroomCount"),
            "bathrooms": hostaway_data.get("bathrooms") or hostaway_data.get("bathroomCount"),
            "max_guests": hostaway_data.get("maxGuests") or hostaway_data.get("maxOccupancy") or hostaway_data.get("accommodates"),
            "status": hostaway_data.get("status"),
            "created_at": hostaway_data.get("createdAt") or hostaway_data.get("created_at") or hostaway_data.get("dateCreated"),
            "updated_at": hostaway_data.get("updatedAt") or hostaway_data.get("updated_at") or hostaway_data.get("dateModified"),
        }
        
        # Store any extra fields
        known_fields = {
            "id", "unitId", "_id", "listingId", "listing_id", "name", "title",
            "unitNumber", "unit_number", "bedrooms", "bedroomCount", "bathrooms",
            "bathroomCount", "maxGuests", "maxOccupancy", "accommodates", "status",
            "createdAt", "created_at", "dateCreated", "updatedAt", "updated_at",
            "dateModified"
        }
        extra_fields = {k: v for k, v in hostaway_data.items() if k not in known_fields}
        result["extra_fields"] = extra_fields
        
        return cls(**result)
