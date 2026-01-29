"""Async IMAP client module for handling email interactions using aioimaplib."""

import re
from datetime import date, timedelta
from typing import List, Optional, Union

from aioimaplib import aioimaplib
from pydantic import BaseModel, ConfigDict


class BytesMsgsInFolder(BaseModel):
    """Model representing messages in a folder."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    msgs: List[bytes]  # raw message bytes
    folder: str

    def get_total_msgs(self) -> int:
        """Return the total number of messages in this folder."""
        return len(self.msgs)


class AsyncImap:
    """Async IMAP client using aioimaplib.

    This class provides an asynchronous interface to IMAP operations.

    # Example usage
    # async def main():
    #     imap = AsyncImap(
    #         host="imap.example.com",
    #         port=993,
    #         user="user@example.com",
    #         password="secret",
    #     )
    #     # fetch emails from today
    #     today = datetime.utcnow().date()
    #     all_msgs = await imap.get_emails(d=today)
    #     print("Total folders:", len(all_msgs))
    #     print("Total messages:", sum(m.get_total_msgs() for m in all_msgs))
    """

    def __init__(self, host: str, port: int, user: str, password: str):
        """Initialize the AsyncImap client.

        Args:
            host: IMAP server hostname
            port: IMAP server port
            user: Username for authentication
            password: Password for authentication
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.client: Optional[aioimaplib.IMAP4_SSL] = None

    async def aconnect(self) -> None:
        """Connect to the IMAP server and authenticate."""
        self.client = aioimaplib.IMAP4_SSL(host=self.host, port=self.port)
        # wait for server greet
        await self.client.wait_hello_from_server()
        await self.client.login(self.user, self.password)

    async def alist_folders(self) -> List[str]:
        """List all available folders in the IMAP account."""
        # Compile a regex pattern for matching any string
        assert self.client is not None
        all_pattern = re.compile(".*")
        resp = await self.client.list(reference_name="", mailbox_pattern=all_pattern)
        # responses come back like: ('*', 'LIST', '(\HasNoChildren)', '"/"','INBOX')
        return [
            line[-1].decode().strip('"')
            for line in resp.lines
            if isinstance(line, tuple)
        ]

    def _date_criteria(self, d: Union[date, List[date]]) -> str:
        """Create IMAP search criteria for date range.

        Args:
            d: Either a single date or a list of two dates representing a range

        Returns:
            String with formatted IMAP date search criteria
        """
        if isinstance(d, list):
            lo, hi = sorted(d)
            hi += timedelta(days=1)
            return f"(SINCE {lo:%d-%b-%Y} BEFORE {hi:%d-%b-%Y})"
        # No else needed as we're returning in the if block
        return f"(ON {d:%d-%b-%Y})"

    async def afetch_folder(
        self,
        folder: str,
        d: Optional[Union[date, List[date]]] = None,
    ) -> BytesMsgsInFolder:
        """Fetch messages from a specific folder.

        Args:
            folder: The folder name to fetch messages from
            d: Optional date or date range to filter messages

        Returns:
            MsgsInFolder object containing the messages and folder name

        Raises:
            RuntimeError: If search fails in the folder
        """
        # SELECT folder
        assert self.client is not None
        await self.client.select(
            folder
        )  # Remove readonly parameter as it's not supported
        # build search criteria
        crit = self._date_criteria(d) if d else "ALL"
        typ, data = await self.client.search(crit)
        if typ != "OK":  # Use string 'OK' instead of responses.OK
            raise RuntimeError(f"Search failed in {folder}: {typ}")
        uids = b" ".join(data).split()
        msgs = []
        for uid in uids:
            _typ, fetched = await self.client.fetch(uid.decode(), "(RFC822)")
            if _typ == "OK":  # Use string 'OK' instead of responses.OK
                # fetched is list of tuples: [(b'1 (RFC822 {1234}', b'...raw msg...', b')')]
                for part in fetched:
                    if isinstance(part, tuple):
                        msgs.append(part[1])
        return BytesMsgsInFolder(msgs=msgs, folder=folder)

    async def aget_emails(
        self, d: Optional[Union[date, List[date]]] = None
    ) -> List[BytesMsgsInFolder]:
        """Connect, list folders, and fetch messages per folder.

        Args:
            d: Optional date or date range to filter messages

        Returns:
            List of MsgsInFolder objects containing messages from all folders
        """
        assert self.client is not None
        await self.aconnect()
        folders = await self.alist_folders()
        results = []
        for f in folders:
            try:
                mf = await self.afetch_folder(f, d)
                results.append(mf)
            except (RuntimeError, aioimaplib.Error) as e:
                # log & continue
                print(f"Error processing folder {f}: {str(e)}")
                continue
        await self.client.logout()
        return results
