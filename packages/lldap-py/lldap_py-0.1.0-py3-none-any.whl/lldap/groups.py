"""Group management operations."""

from typing import List, Dict, Any, Optional, Union
from .client import LLDAPClient
from .exceptions import ValidationError
from .models import Group, User

# BASE_GROUP_ATTRIBUTES = ["groupid", "creationDate", "uuid", "displayName"]



class GroupManager:
    """Manages group operations."""
    
    def __init__(self, client: LLDAPClient):
        """Initialize group manager.
        
        Args:
            client: LLDAP client instance
        """
        self.client = client
    
    def list_groups(self) -> List[Group]:
        """Get list of all groups.
        
        Returns:
            List of group objects
        """
        query = "{groups{id creationDate uuid displayName}}"
        result = self.client.query(query)
        groups = []
        for grp in result.get("data", {}).get("groups", []):
            groups.append(Group(
                groupid=grp["id"],
                creation_date=grp["creationDate"],
                uuid=grp["uuid"],
                display_name=grp["displayName"],
            ))
        return groups
    
    def create_group(self, name: str) -> Dict[str, Any]:
        """Create a new group.
        
        Args:
            name: Group display name
            
        Returns:
            Created group data
        """
        query = """
        mutation createGroup($group:String!){
            createGroup(name:$group){id}
        }
        """
        variables = {"group": name}
        result = self.client.query(query, variables)
        # return created group data
        return result.get("data", {}).get("createGroup", {})
    
    def fetch_group_by_id(self, group_id: int) -> Optional[Group]:
        for group in self.list_groups():
            if group.groupid == group_id:
                return group
        return None

    
    def get_group_id(self, name: str) -> Optional[int]:
        """Get group ID by display name.
        
        Args:
            name: Group display name
            
        Returns:
            Group ID or None if not found
        """
        groups = self.list_groups()
        for group in groups:
            if group.display_name == name:
                return group.groupid
        return None
    
    def _resolve_group_id(self, group_identifier: Union[str, int]) -> int:
        """Resolve group name or ID to group ID.
        
        Args:
            group_identifier: Either group name (str) or group ID (int)
            
        Returns:
            Group ID
            
        Raises:
            ValidationError: If group not found or invalid type
        """
        if isinstance(group_identifier, int):
            return group_identifier
        elif isinstance(group_identifier, str):
            group_id = self.get_group_id(group_identifier)
            if group_id is None:
                raise ValidationError(f"Group not found: {group_identifier}")
            return group_id
        else:
            raise ValidationError(f"Group identifier must be str (name) or int (id), got {type(group_identifier).__name__}")
    
    def delete_group(self, group_identifier: Union[str, int]) -> bool:
        """Delete a group by name or ID.
        
        Args:
            group_identifier: Group name (str) or group ID (int)
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If group not found
        """
        group_id = self._resolve_group_id(group_identifier)
        
        query = """
        mutation deleteGroup($id:Int!){
            deleteGroup(groupId:$id){ok}
        }
        """
        variables = {"id": group_id}
        result = self.client.query(query, variables)
        return result.get("data", {}).get("deleteGroup", {}).get("ok", False)
    
    def list_group_users(self, group_identifier: Union[str, int]) -> List[User]:
        """List users in a group by name or ID.
        
        Args:
            group_identifier: Group name (str) or group ID (int)
            
        Returns:
            List of User objects
            
        Raises:
            ValidationError: If group not found
        """
        group_id = self._resolve_group_id(group_identifier)
        
        query = """
        query listUsersByGroupName($id:Int!){
            group:group(groupId:$id){users{id email displayName firstName lastName avatar}}
        }
        """
        variables = {"id": group_id}
        result = self.client.query(query, variables)
        users_data = result.get("data", {}).get("group", {}).get("users", [])

        return [User(
            user_id=user["id"],
            email=user["email"],
            display_name=user["displayName"],
            first_name=user["firstName"],
            last_name=user["lastName"],
            avatar=user.get("avatar")
        ) for user in users_data]

    
    