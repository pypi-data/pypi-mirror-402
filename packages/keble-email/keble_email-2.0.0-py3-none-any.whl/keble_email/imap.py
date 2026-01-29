# Group emails: https://support.google.com/mail/answer/5900?hl=en&co=GENIE.Platform%3DDesktop#:~:text=Emails%20are%20grouped%20if%20each,IDs%20as%20a%20previous%20message
import datetime
import re
import traceback
from html.parser import HTMLParser  # python 3
from ssl import SSLError
from typing import Any, List, Optional, Tuple, Union

import keble_helpers
from imap_tools.errors import UnexpectedCommandStatusError
from imap_tools.folder import FolderInfo
from imap_tools.mailbox import MailBox
from imap_tools.message import MailMessage
from imap_tools.query import A
from pydantic import BaseModel, ConfigDict


class MsgsInFolder(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    msgs: List[MailMessage]
    folder: str

    def get_total_msgs(self) -> int:
        return len(self.msgs)

    @classmethod
    def get_total_msgs_in_list(cls, folders: List["MsgsInFolder"]) -> int:
        c = 0
        for f in folders:
            c += f.get_total_msgs()
        return c


class Imap(BaseModel):
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str

    @classmethod
    def get_emails_by_dates(
        cls, imap: "Imap", d: Union[datetime.date, List[datetime.date]]
    ) -> List[MsgsInFolder]:
        return cls.get_emails(imap=imap, query=cls.query_builder(d=d, imap=imap))

    @classmethod
    def get_alltime_emails(cls, imap: "Imap") -> List[MsgsInFolder]:
        return cls.get_emails(imap=imap)

    @classmethod
    def get_mailbox(cls, imap: "Imap"):
        mb = MailBox(imap.imap_host, imap.imap_port)
        if "163.com" in imap.imap_host or "126.com" in imap.imap_host:
            # if the host is 163 or 126, send this ID to the server before login
            # otherwise, will have unsafe login error
            # https://blog.csdn.net/jony_online/article/details/108638571
            # https://comp.lang.python.narkive.com/oQ37YrgI/how-to-send-a-non-standard-imap-command
            args = (
                "name",
                imap.imap_user,
                "contact",
                imap.imap_user,
                "version",
                "1.0.0",
                "vendor",
                "myclient",
            )
            mb.client.xatom("ID", '("' + '" "'.join(args) + '")')  # noqa
        return mb

    @classmethod
    def get_emails(cls, *, imap: "Imap", query: Any = None) -> List[MsgsInFolder]:
        # Get date, subject and body len of all emails from INBOX folder
        emails: List[MsgsInFolder] = []
        # threads = [] # all threads are Different Query or Folder
        # threads_joined = 0

        with cls.get_mailbox(imap).login(imap.imap_user, imap.imap_password) as mailbox:
            for folder in cls.get_all_folders(mailbox):
                print(
                    f"Checking email {imap.imap_user} with query {query}  (host: {imap.imap_host}) folder {folder.name}"
                )
                try:
                    emails.append(cls.get_folder_emails(mailbox, folder.name, query))
                except Exception as e:
                    traceback.print_exc()
                    print(
                        f"[Exception on Email Folder] Failed to lookup on email {imap.imap_user} (host: {imap.imap_host}) folder {folder.name} with query {query} due to {e}"
                    )
        return emails

    @classmethod
    def get_folder_emails(cls, mailbox, folder: str, query: Any = None) -> MsgsInFolder:
        # change the folder
        mailbox.folder.set(folder, readonly=True)
        # fetch emails inside the folder
        msgs = []
        for msg in mailbox.fetch(query):
            msgs.append(msg)
        return MsgsInFolder(msgs=msgs, folder=folder)

    @classmethod
    def get_all_folders(cls, mailbox) -> List[FolderInfo]:
        return mailbox.folder.list()

    @classmethod
    def query_builder(
        cls,
        *,
        d: Union[
            datetime.date | datetime.datetime, List[datetime.date | datetime.datetime]
        ],
        imap: Optional["Imap"] = None,
    ):
        # if d is a list, provide a query range,
        if isinstance(d, list):
            max_d = max(d)
            min_d = min(d)
            if isinstance(max_d, datetime.datetime):
                max_d = keble_helpers.datetime_to_date(max_d)
            if isinstance(min_d, datetime.datetime):
                min_d = keble_helpers.datetime_to_date(min_d)
            since_d = min_d
            before_d = max_d + datetime.timedelta(days=1)  # include the max date
            same_date = max_d == min_d  # it still can be the same date
        else:
            same_date = True
            if isinstance(d, datetime.datetime):
                d = keble_helpers.datetime_to_date(d)
            since_d = d
            before_d = d

        # ensure is date
        # _d = helpers.datetime_to_date(d)
        # before_d = _d + datetime.timedelta(days=1)
        since_s = since_d.strftime("%d-%b-%Y")
        before_s = before_d.strftime("%d-%b-%Y")
        byte_date = f"SINCE {since_s} BEFORE {before_s}".encode("utf-8")  # str.encode()
        # SOME IMAP does not implement the 'ON' query, you can only use SINCE and BEFORE
        if imap is not None and "qq.com" in imap.imap_host:
            # imap.qq.com
            # imap.exmail.qq.com
            return byte_date
        if same_date:
            return A(date=since_d)  # since_d is fine if the dates are same
        else:
            return A(date_gte=since_d, date_lt=before_d)

    @classmethod
    def validate_imap(
        cls, *, imap_host: str, imap_user: str, imap_port: int, imap_password: str
    ) -> "Imap":
        imap = Imap(
            imap_host=imap_host.strip(),
            imap_user=imap_user.strip(),
            imap_port=imap_port,
            imap_password=imap_password.strip(),
        )
        try:
            Imap.get_mailbox(imap=imap).login(imap.imap_user, imap.imap_password)
        except Exception as e:
            failed_reason = e
            if isinstance(e, UnexpectedCommandStatusError):
                failed_reason = e.command_result[1][0].decode().lower()
            elif isinstance(e, SSLError):
                failed_reason = e.reason.lower()
            raise ValueError(f"{failed_reason}")
        return imap


_ALL_PAST_EMAILS_PREFIX = [">", "-"]


def parse_email_body(
    email_texts: Union[List[str], str], parsed_email: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Return string + list of string
    current email text, trimmed past email texts
    """
    rows: List[str] = (
        email_texts.strip("\n\t ").split("\n")
        if isinstance(email_texts, str)
        else email_texts
    )
    parsed = parsed_email if parsed_email is not None else ""
    first_seen_token = None
    past_emails_rows = []
    for r in range(len(rows)):
        row = rows[r].strip(" ")
        first_char = row[0] if len(row) > 0 else None
        if first_char is None:
            continue

        if first_seen_token is None and first_char in _ALL_PAST_EMAILS_PREFIX:
            first_seen_token = first_char
        if first_seen_token is None:
            # not entering the past emails footer
            # continue directly
            parsed += f"{rows[r]}\n"  # use the ORIGINAL rows[r] data, DO NOT USE the strip one
            continue
        if first_seen_token == first_char:
            # it is a row for past email
            trim = row.strip(f"{first_char} \t")  # strip char and spaces
            # some past email row is empty, therefore, check length
            if len(trim) > 0:
                past_emails_rows.append(trim)
            continue
        if first_seen_token != first_char:
            # the consecutive break
            rest_rows = rows[r + 1 :]
            if len(rest_rows) > 0:
                # restart the consecutive
                _parsed, _email_texts = parse_email_body(rest_rows)
                return f"{parsed}\n{_parsed}".strip("\n "), _email_texts
            # or break the loop
            break

    return parsed.strip("\n "), past_emails_rows


class HTMLStripperParser(HTMLParser):
    """Simple, stupid parser to remove all HTML tags from
    a document. The point is to just get a the data.
    >>> parser = HTMLStripperParser()
    >>> parser.feed(string_with_html)
    >>> parser.get_content()
    """

    def get_content(self):
        "Ignores all consecutive whitespace"
        return re.sub("\s+", " ", self.content)

    def handle_data(self, data):
        if hasattr(self, "content"):
            self.content += data
        else:
            self.content = data


class HTMLAttributeStripper(HTMLParser):
    """A parser that strips out all element attributes.
    Usage:
        >>> html = open('index.html').read()
        >>> parser = HTMLAttributeStripper()
        >>> parser.feed(html)
        >>> parser.write('new_file.html')
    If you want to leave some tags as-is (say <a> elements), you can specify
    the `keep_tags` argument:
        >>> parser = HTMLAttributeStripper(keep_tags=['a'])
    If you want to keep some attributes, specify them with the `keep_attrs`
    argument:
        >>> parser = HTMLAttributeStripper(keep_attrs=['href'])
    If you want to completely exclude some elements from the document's body,
    you can specify those with `omit_tags`:
        >>> parser = HTMLAttributeStripper(omit_tags=['span'])
    The above example will remove all <span> elements from the document.
    """

    def __init__(self, *args, **kwargs):
        self.elements = []
        self.keep_attrs = kwargs.pop("keep_attrs", [])
        self.keep_tags = kwargs.pop("keep_tags", [])
        self.omit_tags = kwargs.pop("omit_tags", [])
        super().__init__(*args, **kwargs)

    def handle_endtag(self, tag):
        if tag not in self.omit_tags:
            self.elements.append("</{0}>".format(tag))

    def _attrstring(self, attrs):
        """given a list of [(attr, value), ...], return a string of the
        format: attr="value".
        """
        attrs = ['{0}="{1}"'.format(attr, val) for attr, val in attrs]
        return " ".join(attrs)

    def handle_starttag(self, tag, attrs):
        if tag in self.keep_tags:
            # we want to keep this on as-is
            self.elements.append("<{0} {1}>".format(tag, self._attrstring(attrs)))

        if tag not in self.omit_tags:
            items = []  # attributes we plan to keep
            for attr, value in attrs:
                if attr in self.keep_attrs:
                    items.append((attr, value))
            if items:
                self.elements.append("<{0} {1}>".format(tag, self._attrstring(items)))
            else:
                self.elements.append("<{0}>".format(tag))

    def handle_data(self, data):
        if data:
            self.elements.append(data.strip())

    @property
    def cleaned_content(self):
        return "\n".join(self.elements)

    def write(self, filename):
        with open(filename, "w+") as f:
            f.write(self.cleaned_content)
