"""User management operations."""

import re
from typing import List, Dict, Any, Optional
from .client import LLDAPClient
from .exceptions import ValidationError
from .models import User, Group

class UserManager:
    """Manages user operations."""
    
    def __init__(self, client: LLDAPClient):
        """Initialize user manager.
        
        Args:
            client: LLDAP client instance
        """
        self.client = client
    
    def list_users(self) -> List[User]:
        """Get list of all users.
        
        Returns:
            List of user objects
        """
        query = "{users{id creationDate uuid email displayName firstName lastName, avatar}}"
        result = self.client.query(query)
        users = []
        for usr in result.get("data", {}).get("users", []):
            users.append(User(
                user_id=usr["id"],
                email=usr["email"],
                display_name=usr["displayName"],
                first_name=usr["firstName"],
                last_name=usr["lastName"],
                avatar=usr.get("avatar"),
            ))
        return users
    
    
    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID from email address.
        
        Args:
            email: Email address
            
        Returns:
            User ID or None if not found
        """
        query = "{users{id email}}"
        result = self.client.query(query)
        users = self.list_users()
        
        for user in users:
            if user.email == email:
                return user.user_id
        
        return None
    

    
    def create_user(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new user.
        
        Args:
            user_id: User ID
            email: Email address
            display_name: Display name
            first_name: First name
            last_name: Last name
            avatar_path: Path to avatar image file (JPEG)
            
        Returns:
            Created user data
        """
        query = """
        mutation createUser($user:CreateUserInput!){
            createUser(user:$user){id email displayName firstName lastName avatar}
        }
        """
        
        variables = {
            "user": {
                "id": user_id,
                "email": email,
                "displayName": display_name or "",
                "firstName": first_name or "",
                "lastName": last_name or "",
                "avatar": None,
            }
        }
        
        
        result = self.client.query(query, variables)
        return result.get("data", {}).get("createUser", {})
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        query = """
        mutation deleteUser($userId:String!){
            deleteUser(userId:$userId){ok}
        }
        """
        variables = {"userId": user_id}
        result = self.client.query(query, variables)
        return result.get("data", {}).get("deleteUser", {}).get("ok", False)
    
    def list_user_attributes(self, user_id: str) -> List[str]:
        """List attributes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of attribute names
        """
        query = """
        query getUserInfo($id:String!){
            user(userId:$id){attributes{name}}
        }
        """
        variables = {"id": user_id}
        result = self.client.query(query, variables)
        attributes = result.get("data", {}).get("user", {}).get("attributes", [])
        names = [attr["name"] for attr in attributes]
        return sorted(names)
    
    
    
    def list_user_groups(self, user_id: str) -> List[str]:
        """List groups that a user belongs to.
        
        Args:
            user_id: User ID
            
        Returns:
            List of group display names
        """
        query = """
        query listGroupsByUserId($id:String!){
            user(userId:$id){groups{displayName}}
        }
        """
        variables = {"id": user_id}
        result = self.client.query(query, variables)
        groups = result.get("data", {}).get("user", {}).get("groups", [])
        return [group["displayName"] for group in groups]
    
    def add_user_to_group(self, user_id: str, group_id: int) -> bool:
        """Add user to a group.
        
        Args:
            user_id: User ID
            group_id: Group ID (integer)
            
        Returns:
            True if successful
        """
        query = """
        mutation addUserToGroup($userId:String!,$groupId:Int!){
            addUserToGroup(userId:$userId,groupId:$groupId){ok}
        }
        """
        variables = {"userId": user_id, "groupId": group_id}
        result = self.client.query(query, variables)
        return result.get("data", {}).get("addUserToGroup", {}).get("ok", False)
    
    def remove_user_from_group(self, user_id: str, group_id: int) -> bool:
        """Remove user from a group.
        
        Args:
            user_id: User ID
            group_id: Group ID (integer)
            
        Returns:
            True if successful
        """
        query = """
        mutation removeUserFromGroup($userId:String!,$groupId:Int!){
            removeUserFromGroup(userId:$userId,groupId:$groupId){ok}
        }
        """
        variables = {"userId": user_id, "groupId": group_id}
        result = self.client.query(query, variables)
        return result.get("data", {}).get("removeUserFromGroup", {}).get("ok", False)
    
 
    
    

