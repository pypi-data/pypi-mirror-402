# Keble Email

A Python package providing asynchronous email handling capabilities, including sending emails via SMTP and retrieving emails via IMAP.

## Features

- **Async SMTP**: Send emails asynchronously with support for HTML and MJML templates
- **Async IMAP**: Retrieve emails asynchronously with filtering by date
- **Regular IMAP**: Non-async IMAP client for synchronous operations
- **Template Support**: Use HTML or MJML templates with Jinja2 rendering
- **Attachments**: Easily add single or multiple attachments to emails
- **Email Parsing**: Parse email bodies and HTML content
- **Environment Variables**: Configure via environment variables for easy deployment

## Installation

```bash
pip install keble-email
```

Or via Poetry:

```bash
poetry add keble-email
```

## Configuration

Create a settings class that implements the `EmailSettingABC` interface:

```python
from keble_email import EmailSettingABC
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(EmailSettingABC, BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    SMTP_SENDER_EMAIL: str
    SMTP_SENDER_NAME: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_TLS: bool
    SMTP_SSL: bool
    TEST_RECIPIENT_EMAIL: str = "test@example.com"  # For testing purposes

    @property
    def sender_email(self) -> str:
        return self.SMTP_SENDER_EMAIL

    @property
    def sender_name(self) -> str:
        return self.SMTP_SENDER_NAME

    @property
    def smtp_user(self) -> str:
        return self.SMTP_USER

    @property
    def smtp_password(self) -> str:
        return self.SMTP_PASSWORD

    @property
    def smtp_host(self) -> str:
        return self.SMTP_HOST

    @property
    def smtp_port(self) -> int:
        return self.SMTP_PORT

    @property
    def smtp_tls(self) -> bool:
        return self.SMTP_TLS

    @property
    def smtp_ssl(self) -> bool:
        return self.SMTP_SSL

# Create instance
settings = Settings()
```

Example `.env` file:

```
SMTP_TLS=False
SMTP_SSL=True
SMTP_PORT=465
SMTP_HOST=smtp.example.com
SMTP_SENDER_EMAIL=admin@example.com
SMTP_SENDER_NAME=Example Admin
SMTP_USER=your_username
SMTP_PASSWORD=your_password
TEST_RECIPIENT_EMAIL=test@example.com

# Optional IMAP settings
IMAP_HOST=imap.example.com
IMAP_PORT=993
```

## Usage Examples

### Sending Emails with AsyncEmailSender

#### Using HTML Content Directly

```python
import asyncio
from keble_email import AsyncEmailSender

async def send_email_example():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Email</title>
    </head>
    <body>
        <h1>Hello World</h1>
        <p>This is a test email sent from Keble Email.</p>
    </body>
    </html>
    """
    
    result = await AsyncEmailSender.asend(
        subject="Test Email",
        recipient_email="recipient@example.com",
        html=html_content,
        settings=settings,  # Your settings instance
    )
    
    print(f"Email sent successfully: {result['success']}")
    print(f"Status code: {result['status_code']}")

if __name__ == "__main__":
    asyncio.run(send_email_example())
```

#### Using HTML Templates with Jinja2

```python
import asyncio
from pathlib import Path
from keble_email import AsyncEmailSender

async def send_template_email():
    # Path to your HTML template
    template_path = Path("templates/welcome.html")
    
    # Template variables
    environment = {
        "name": "John Doe",
        "verification_url": "https://example.com/verify?token=123456",
        "company_name": "Example Company"
    }
    
    result = await AsyncEmailSender.asend(
        subject="Welcome to Our Service",
        recipient_email="user@example.com",
        html_template=template_path,
        environment=environment,
        settings=settings,
        cc="support@example.com",
    )
    
    print(f"Email sent successfully: {result['success']}")

if __name__ == "__main__":
    asyncio.run(send_template_email())
```

#### Using MJML Templates

```python
import asyncio
from pathlib import Path
from keble_email import AsyncEmailSender

async def send_mjml_email():
    # Path to your MJML template
    template_path = Path("templates/newsletter.mjml")
    
    # Template variables
    environment = {
        "user_name": "Jane Smith",
        "articles": [
            {"title": "New Feature Announcement", "url": "https://example.com/blog/new-feature"},
            {"title": "Tips and Tricks", "url": "https://example.com/blog/tips"}
        ]
    }
    
    result = await AsyncEmailSender.asend(
        subject="This Month's Newsletter",
        recipient_email="subscriber@example.com",
        mjml_template=template_path,
        environment=environment,
        settings=settings,
    )
    
    print(f"Email sent successfully: {result['success']}")

if __name__ == "__main__":
    asyncio.run(send_mjml_email())
```

#### Sending Emails with Attachments

```python
import asyncio
from pathlib import Path
from keble_email import AsyncEmailSender

async def send_email_with_attachments():
    html_content = "<html><body><h1>Please find attached files</h1></body></html>"
    
    # Single attachment
    pdf_path = Path("documents/report.pdf")
    
    # Multiple attachments
    attachment_paths = [
        Path("documents/data.xlsx"),
        Path("documents/image.jpg")
    ]
    
    result = await AsyncEmailSender.asend(
        subject="Monthly Report",
        recipient_email="manager@example.com",
        html=html_content,
        settings=settings,
        attachment_path=pdf_path,  # Main attachment
        attachment_paths=attachment_paths,  # Additional attachments
    )
    
    print(f"Email with attachments sent: {result['success']}")

if __name__ == "__main__":
    asyncio.run(send_email_with_attachments())
```

### Retrieving Emails with AsyncImap

#### Connect and List Folders

```python
import asyncio
from keble_email import AsyncImap

async def list_folders_example():
    # Initialize IMAP client
    imap = AsyncImap(
        host="imap.example.com",  # Your IMAP server
        port=993,                 # Usually 993 for IMAPS
        user="your_username",
        password="your_password",
    )
    
    # Connect to server
    await imap.aconnect()
    
    # List all folders
    folders = await imap.alist_folders()
    print("Available folders:")
    for folder in folders:
        print(f"- {folder}")
    
    # Logout
    if imap.client:
        await imap.client.logout()

if __name__ == "__main__":
    asyncio.run(list_folders_example())
```

#### Fetch Emails from a Specific Folder with Date Filtering

```python
import asyncio
from datetime import date, timedelta
from keble_email import AsyncImap

async def fetch_recent_emails():
    # Initialize IMAP client
    imap = AsyncImap(
        host="imap.example.com",
        port=993,
        user="your_username",
        password="your_password",
    )
    
    # Connect
    await imap.aconnect()
    
    # Get emails from INBOX for the last 7 days
    week_ago = date.today() - timedelta(days=7)
    today = date.today()
    
    msgs_in_folder = await imap.afetch_folder(
        folder="INBOX",
        d=[week_ago, today]  # Date range
    )
    
    print(f"Found {msgs_in_folder.get_total_msgs()} messages in INBOX")
    
    # Process emails
    for i, msg_bytes in enumerate(msgs_in_folder.msgs):
        print(f"Email {i+1} size: {len(msg_bytes)} bytes")
        # Here you would typically parse the email using a library like email.parser
    
    # Logout
    if imap.client:
        await imap.client.logout()

if __name__ == "__main__":
    asyncio.run(fetch_recent_emails())
```

#### Get Emails from All Folders

```python
import asyncio
from datetime import date
from keble_email import AsyncImap

async def get_all_emails_from_today():
    # Initialize IMAP client
    imap = AsyncImap(
        host="imap.example.com",
        port=993,
        user="your_username",
        password="your_password",
    )
    
    # Get emails from all folders from today
    today = date.today()
    all_msgs = await imap.aget_emails(d=today)
    
    print(f"Total folders: {len(all_msgs)}")
    print(f"Total messages: {sum(m.get_total_msgs() for m in all_msgs)}")
    
    # Process each folder
    for folder_msgs in all_msgs:
        folder_name = folder_msgs.folder
        msg_count = folder_msgs.get_total_msgs()
        print(f"Folder '{folder_name}' has {msg_count} messages")

if __name__ == "__main__":
    asyncio.run(get_all_emails_from_today())
```

### Using the Synchronous IMAP Client

```python
from datetime import date, timedelta
from keble_email import Imap

def get_emails_example():
    # Create IMAP config
    imap_config = Imap(
        imap_host="imap.example.com",
        imap_port=993,
        imap_user="your_username",
        imap_password="your_password",
    )
    
    # Get emails from the last 7 days
    week_ago = date.today() - timedelta(days=7)
    today = date.today()
    
    # Get emails within date range
    email_folders = Imap.get_emails_by_dates(
        imap=imap_config, 
        d=[week_ago, today]
    )
    
    # Process results
    total_folders = len(email_folders)
    total_emails = sum(folder.get_total_msgs() for folder in email_folders)
    
    print(f"Found {total_emails} emails in {total_folders} folders")
    
    # Process each email
    for folder in email_folders:
        print(f"Folder: {folder.folder} - {folder.get_total_msgs()} emails")
        for msg in folder.msgs:
            print(f"Subject: {msg.subject}")
            print(f"From: {msg.from_}")
            print(f"Date: {msg.date}")
            print("-" * 50)

if __name__ == "__main__":
    get_emails_example()
```

### Parsing Email Content

```python
from keble_email import parse_email_body, HTMLStripperParser

# Parse email body to separate current email from past forwarded/replied content
def parse_email_example():
    email_text = """
    Hello,
    
    This is my response to your inquiry.
    
    Best regards,
    John
    
    > On Monday, June 1, 2023, Jane <jane@example.com> wrote:
    > Hello John,
    > I have a question about your product.
    > Regards,
    > Jane
    """
    
    current_email, past_emails = parse_email_body(email_text)
    print("Current email content:")
    print(current_email)
    print("\nPast email content:")
    for line in past_emails:
        print(line)
    
    # Strip HTML from an email body
    html_content = "<html><body><h1>Hello</h1><p>This is a test</p></body></html>"
    parser = HTMLStripperParser()
    parser.feed(html_content)
    plain_text = parser.get_content()
    print("\nHTML stripped content:")
    print(plain_text)

if __name__ == "__main__":
    parse_email_example()
```

## Testing

Run tests using pytest:

```bash
pip install pytest pytest-asyncio
pytest -xvs tests/
```

Make sure to set up a proper `.env` file with test credentials before running the tests.

## License

MIT
