from typing import Union, List, Dict

# Type aliases for clarity
TenantId = Union[str, int]
TenantInfo = Dict[str, Union[str, List[TenantId]]]
Tenants = Union[List[TenantId], List[TenantInfo]]

def extract_tenant_ids(tenants: Tenants) -> List[TenantId]:
    """
    Extract tenant IDs from the tenants parameter, which can be either a list of IDs
    or a list of tenant info dictionaries.
    
    Args:
        tenants: Either a list of tenant IDs (strings/integers) or a list of tenant info dictionaries
        
    Returns:
        List of tenant IDs
        
    Raises:
        ValueError: If the tenants parameter format is invalid
    """
    if not tenants:
        raise ValueError("Invalid format for tenants: empty list")

    first_tenant = tenants[0]
    
    if isinstance(first_tenant, (str, int)):
        return tenants  # type: ignore
    elif isinstance(first_tenant, dict) and "tenantIds" in first_tenant:
        # TODO: support multiple tenants in future
        return first_tenant["tenantIds"]
    else:
        raise ValueError("Invalid format for tenants")

def extract_tenant_field(tenants: Tenants, dashboard_owner: str) -> str:
    """
    Extract tenant field from the tenants parameter, falling back to dashboard_owner
    if tenants is a simple list of IDs.
    
    Args:
        tenants: Either a list of tenant IDs (strings/integers) or a list of tenant info dictionaries
        dashboard_owner: The default tenant field to use if tenants is a simple list
        
    Returns:
        The tenant field string
        
    Raises:
        ValueError: If the tenants parameter format is invalid
    """
    if not tenants:
        raise ValueError("Invalid format for tenants: empty list")

    first_tenant = tenants[0]
    
    if isinstance(first_tenant, (str, int)):
        return dashboard_owner
    elif isinstance(first_tenant, dict) and "tenantField" in first_tenant:
        return first_tenant["tenantField"]
    else:
        raise ValueError("Invalid format for tenants") 