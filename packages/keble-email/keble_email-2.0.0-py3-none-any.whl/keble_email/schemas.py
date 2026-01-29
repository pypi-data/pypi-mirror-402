from abc import ABC, abstractmethod


class EmailSettingABC(ABC):
    @property
    @abstractmethod
    def sender_email(self) -> str: ...

    @property
    @abstractmethod
    def sender_name(self) -> str: ...

    @property
    @abstractmethod
    def smtp_user(self) -> str: ...

    @property
    @abstractmethod
    def smtp_password(self) -> str: ...

    @property
    @abstractmethod
    def smtp_host(self) -> str: ...

    @property
    @abstractmethod
    def smtp_port(self) -> int: ...

    @property
    @abstractmethod
    def smtp_tls(self) -> bool: ...

    @property
    @abstractmethod
    def smtp_ssl(self) -> bool: ...
