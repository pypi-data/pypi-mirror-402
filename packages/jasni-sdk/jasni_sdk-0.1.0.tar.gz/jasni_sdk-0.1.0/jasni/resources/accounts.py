"""
Accounts Resource

Resource for managing email accounts.
"""

from typing import TYPE_CHECKING, Optional

from jasni.types import (
    CreateAccountResponse,
    DeleteAccountResponse,
    ListAccountsResponse,
    UpdateAccountResponse,
)

if TYPE_CHECKING:
    from jasni.http import AsyncHttpClient, HttpClient


class AccountsResource:
    """
    Resource for managing email accounts (synchronous).
    
    Example:
        >>> accounts = jasni.accounts.list()
        >>> print(f"You have {accounts.total} accounts")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
    
    def list(self) -> ListAccountsResponse:
        """
        List all email accounts for the authenticated user.
        
        Returns:
            ListAccountsResponse with accounts and total count
        
        Example:
            >>> accounts = jasni.accounts.list()
            >>> for account in accounts.accounts:
            ...     print(f"- {account.email}")
        """
        data = self._http.get("/api/v1/accounts")
        return ListAccountsResponse(**data)
    
    def create(
        self,
        *,
        username: Optional[str] = None,
        name: Optional[str] = None
    ) -> CreateAccountResponse:
        """
        Create a new email account.
        
        Args:
            username: The local part of the email (before @).
                     Auto-generated if not provided.
            name: Display name for the account.
        
        Returns:
            CreateAccountResponse with the new account
        
        Example:
            >>> # Create with custom username
            >>> result = jasni.accounts.create(
            ...     username="myaccount",
            ...     name="My Account"
            ... )
            >>> print(f"Created: {result.account.email}")
            
            >>> # Create with auto-generated username
            >>> result = jasni.accounts.create(name="Random Account")
        """
        data = self._http.post("/api/v1/accounts", body={
            "username": username,
            "name": name,
        })
        return CreateAccountResponse(**data)
    
    def update(self, email: str, *, name: str) -> UpdateAccountResponse:
        """
        Update an email account (e.g., change the display name).
        
        Args:
            email: The email address of the account to update
            name: New display name for the account
        
        Returns:
            UpdateAccountResponse with the updated account
        
        Example:
            >>> result = jasni.accounts.update(
            ...     "myaccount@mail.jasni.ai",
            ...     name="New Display Name"
            ... )
            >>> print(f"Updated: {result.account.name}")
        """
        data = self._http.patch("/api/v1/accounts", body={
            "email": email,
            "name": name,
        })
        return UpdateAccountResponse(**data)
    
    def delete(self, email: str) -> DeleteAccountResponse:
        """
        Delete an email account.
        
        Args:
            email: The email address to delete
        
        Returns:
            DeleteAccountResponse confirming deletion
        
        Example:
            >>> jasni.accounts.delete("myaccount@mail.jasni.ai")
        """
        data = self._http.delete("/api/v1/accounts", query={"email": email})
        return DeleteAccountResponse(**data)


class AsyncAccountsResource:
    """
    Resource for managing email accounts (asynchronous).
    
    Example:
        >>> accounts = await jasni.accounts.list()
        >>> print(f"You have {accounts.total} accounts")
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
    
    async def list(self) -> ListAccountsResponse:
        """
        List all email accounts for the authenticated user.
        
        Returns:
            ListAccountsResponse with accounts and total count
        """
        data = await self._http.get("/api/v1/accounts")
        return ListAccountsResponse(**data)
    
    async def create(
        self,
        *,
        username: Optional[str] = None,
        name: Optional[str] = None
    ) -> CreateAccountResponse:
        """
        Create a new email account.
        
        Args:
            username: The local part of the email (before @).
                     Auto-generated if not provided.
            name: Display name for the account.
        
        Returns:
            CreateAccountResponse with the new account
        """
        data = await self._http.post("/api/v1/accounts", body={
            "username": username,
            "name": name,
        })
        return CreateAccountResponse(**data)
    
    async def update(self, email: str, *, name: str) -> UpdateAccountResponse:
        """
        Update an email account (e.g., change the display name).
        
        Args:
            email: The email address of the account to update
            name: New display name for the account
        
        Returns:
            UpdateAccountResponse with the updated account
        """
        data = await self._http.patch("/api/v1/accounts", body={
            "email": email,
            "name": name,
        })
        return UpdateAccountResponse(**data)
    
    async def delete(self, email: str) -> DeleteAccountResponse:
        """
        Delete an email account.
        
        Args:
            email: The email address to delete
        
        Returns:
            DeleteAccountResponse confirming deletion
        """
        data = await self._http.delete("/api/v1/accounts", query={"email": email})
        return DeleteAccountResponse(**data)
