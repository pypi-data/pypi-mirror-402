
from typing import Optional

class User:
        """Represents a user entity."""
        def __init__(self, user_id: str, email: str, display_name: str, first_name: str, last_name: str, avatar: Optional[str]):
            self.user_id = user_id
            self.email = email
            self.display_name = display_name
            self.first_name = first_name
            self.last_name = last_name
            self.avatar = avatar
        def __repr__(self):
            return f"<User id={self.user_id} email={self.email} name={self.display_name}>"

class Group:
        """Represents a group entity."""
        def __init__(self, groupid: int, creation_date: str, uuid: str, display_name: str):
            self.groupid = groupid
            self.creation_date = creation_date
            self.uuid = uuid
            self.display_name = display_name
            self.creation_date = creation_date
        def __repr__(self):
            return f"<Group id={self.groupid} name={self.display_name} uuid={self.uuid}>"
        

