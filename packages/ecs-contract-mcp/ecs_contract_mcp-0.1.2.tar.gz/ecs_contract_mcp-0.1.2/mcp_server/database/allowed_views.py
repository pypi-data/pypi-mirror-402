"""View whitelist definition - Single source of truth for allowed views"""

import re

# List of allowed views that can be queried through MCP
# All views must be in the 'view' schema
# Stored in normalized format: schema.table (without brackets)
ALLOWED_VIEWS: list[str] = [
    # Contract core
    "view.Contract",
    "view.ContractAttachment",
    "view.ContractHistory",
    "view.ContractPartner",
    "view.ContractExaminer",
    "view.ContractExtendInfo",
    "view.ContractPriority",
    "view.ContractFlowStageView",
    # Partners and organizations
    "view.Partner",
    "view.Department",
    "view.DepartmentTreeLevel",
    # Users and permissions
    "view.User",
    "view.UserAuthority",
    "view.UserContractAuthority",
    "view.Role",
    "view.RoleAuthority",
    # Review and workflow
    "view.OtherExaminer",
    "view.ExamStatus",
    # Delegation
    "view.Acting",
    "view.ActingAgent",
    "view.ActingContract",
    "view.ActingEntry",
    "view.AllActing",
    # Relations and events
    "view.RelatedContract",
    "view.Event",
    "view.EventAttachment",
    "view.EventContract",
    "view.AlertMailList",
    # Others
    "view.Project",
    "view.SignRequirement",
    "view.UrgentLevel",
    "view.MainContractType",
    "view.SubContractType",
    "view.Attachment",
    "view.LatestAttachment",
    "view.FileType",
    "view.CombinedField",
]

# Convert to set for O(1) lookup
ALLOWED_VIEWS_SET: frozenset[str] = frozenset(ALLOWED_VIEWS)


def normalize_table_name(table_name: str) -> str:
    """Normalize table name by removing brackets and converting to lowercase for comparison

    Handles formats:
    - view.Contract -> view.Contract
    - [view].[Contract] -> view.Contract
    - [view].Contract -> view.Contract

    Args:
        table_name: The table name to normalize

    Returns:
        Normalized table name without brackets
    """
    # Remove brackets: [schema].[table] -> schema.table
    normalized = re.sub(r"\[([^\]]+)\]", r"\1", table_name)
    return normalized


def is_view_allowed(view_name: str) -> bool:
    """Check if a view is in the whitelist

    Handles both bracketed and unbracketed formats:
    - view.Contract
    - [view].[Contract]

    Args:
        view_name: The view name to check

    Returns:
        True if the view is allowed, False otherwise
    """
    normalized = normalize_table_name(view_name)
    return normalized in ALLOWED_VIEWS_SET


def get_allowed_views() -> list[str]:
    """Get list of all allowed views

    Returns:
        List of allowed view names in normalized format
    """
    return ALLOWED_VIEWS.copy()


def get_allowed_views_bracketed() -> list[str]:
    """Get list of all allowed views in SQL Server bracket format

    Returns:
        List of allowed view names with brackets (e.g., [view].[Contract])
    """
    result = []
    for view in ALLOWED_VIEWS:
        parts = view.split(".")
        if len(parts) == 2:
            result.append(f"[{parts[0]}].[{parts[1]}]")
        else:
            result.append(f"[{view}]")
    return result
