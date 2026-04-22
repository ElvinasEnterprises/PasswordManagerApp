from datetime import datetime


class PasswordEntry:
    """One stored credential: service, username, password, and notes."""

    def __init__(self, service: str, username: str, password: str,
             notes: str = "", id: int | None = None,
             created_at: datetime | None = None, modified_at: datetime | None = None):
        
        if not service:
            raise ValueError("You must enter the service name")
        if not username:
            raise ValueError("You must add a username")
        if not password:
            raise ValueError("You must add a password")
        
        self._id = id
        self._service = service
        self._username = username
        self._password = password
        self._notes = notes
        self._created_at = created_at or datetime.now()
        self._modified_at = modified_at or self._created_at
    
    @property
    def service(self):
        return self._service

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def notes(self):
        return self._notes

    @property
    def created_at(self):
        return self._created_at

    @property
    def modified_at(self):
        return self._modified_at

    @property
    def id(self):
        return self._id
    
    def update_username(self, new_username):
        if not new_username:
            raise ValueError("Username cannot be empty")
        self._username = new_username
        self._modified_at = datetime.now()

    def update_password(self, new_password):
        if not new_password:
            raise ValueError("Password cannot be empty")
        self._password = new_password
        self._modified_at = datetime.now()

    def update_notes(self, new_notes):
        self._notes = new_notes
        self._modified_at = datetime.now()

        