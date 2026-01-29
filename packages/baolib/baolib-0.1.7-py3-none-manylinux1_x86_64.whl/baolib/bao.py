import os
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .baod import e8, j8, Data
from .baob import lib, consume


def set_bao_log_level(level: str):
    """Set the Bao log level (trace|debug|info|warn|error|fatal|panic)."""
    return consume(lib.bao_setLogLevel(e8(level)))


PrivateID = str
PublicID = str


def newPrivateID() -> PrivateID:
    return consume(lib.bao_security_newPrivateID())

def publicID(private_id: PrivateID) -> PublicID:
    return consume(lib.bao_security_publicID(e8(private_id)))

def decodeID(id_str: str) -> Dict[str, Any]:
    '''
    Docstring for decodeID
    
    :param id_str: Description
    :type id_str: str
    :return: Description
    :rtype: Dict[str, Any]
    '''
    return consume(lib.bao_security_decodeID(e8(id_str)))

class Access:
    read = 1
    write = 2
    admin = 4
    read_write = read | write


class Groups:
    users = "users"
    admins = "admins"
    public = "public"
    blockchain = "#blockchain"
    cleanup = "#cleanup"


@dataclass
class AccessChange:
    group: str
    access: int
    userId: PublicID


@dataclass
class Message:
    subject: str
    body: str = ""
    attachments: List[str] = None
    fileInfo: Dict[str, Any] = None

    def __post_init__(self):
        self.attachments = self.attachments or []
        self.fileInfo = self.fileInfo or {}

    def toJson(self) -> str:
        return json.dumps(asdict(self))


class DB:
    def __init__(self, handle: int):
        self.hnd = handle

    @staticmethod
    def open(driver: str, path: str, ddl: str = "") -> "DB":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        r = lib.bao_db_open(e8(driver), e8(path), e8(ddl))
        consume(r)
        return DB(r.hnd)

    @staticmethod
    def default() -> "DB":
        home = os.path.expanduser("~")
        db_path = os.path.join(home, ".config", "bao.db")
        return DB.open("sqlite3", db_path)

    def close(self):
        if getattr(self, "hnd", 0):
            consume(lib.bao_db_close(self.hnd))
            self.hnd = 0

    def exec(self, query: str, args: Dict[str, Any]):
        r = lib.bao_db_exec(self.hnd, e8(query), j8(args))
        return consume(r)

    def fetch(self, query: str, args: Dict[str, Any], max_rows: int = 100000):
        r = lib.bao_db_fetch(self.hnd, e8(query), j8(args), max_rows)
        return consume(r)

    def fetch_one(self, query: str, args: Dict[str, Any]):
        r = lib.bao_db_fetch_one(self.hnd, e8(query), j8(args))
        return consume(r)

    def __del__(self):
        self.close()


def _file_url(path: str) -> str:
    if path.startswith("file://"):
        return path
    p = Path(path).expanduser().absolute()
    return p.as_uri()

def local_store(id: str, path: str) -> Dict[str, Any]:
    base = _file_url(path)
    return {
        "id": id,
        "type": "local",
        "local": {"base": base},
    }

def s3_store(
    id: str,
    endpoint: str,
    bucket: str,
    access_key_id: str,
    secret_access_key: str,
    region: str = "",
    prefix: str = "",
    verbose: int = 0,
    proxy: str = "",
) -> Dict[str, Any]:
    return {
        "id": id,
        "type": "s3",
        "s3": {
            "endpoint": endpoint,
            "region": region,
            "bucket": bucket,
            "prefix": prefix,
            "auth": {
                "accessKeyId": access_key_id,
                "secretAccessKey": secret_access_key,
            },
            "verbose": verbose,
            "proxy": proxy,
        },
    }

def azure_store(
    id: str,
    account_name: str,
    account_key: str,
    share: str,
    base_path: str = "",
    verbose: int = 0,
) -> Dict[str, Any]:
    return {
        "id": id,
        "type": "azure",
        "azure": {
            "accountName": account_name,
            "accountKey": account_key,
            "share": share,
            "basePath": base_path,
            "verbose": verbose,
        },
    }

def webdav_store(
    id: str,
    host: str,
    username: str,
    password: str,
    base_path: str = "",
    port: int = 0,
    https: bool = False,
    verbose: int = 0,
) -> Dict[str, Any]:
    return {
        "id": id,
        "type": "webdav",
        "webdav": {
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "basePath": base_path,
            "verbose": verbose,
            "https": https,
        },
    }

def sftp_store(
    id: str,
    host: str,
    username: str,
    password: str = "",
    port: int = 0,
    key_file: str = "",
    base_path: str = "",
    verbose: int = 0,
) -> Dict[str, Any]:
    return {
        "id": id,
        "type": "sftp",
        "sftp": {
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "keyFile": key_file,
            "basePath": base_path,
            "verbose": verbose,
        },
    }

class Vault:
    def __init__(self):
        self.hnd: int = 0
        self.id: str = ""
        self.userId: str = ""
        self.userPublicId: str = ""
        self.store_config: Dict[str, Any] = {}
        self.author: str = ""
        self.config: Dict[str, Any] = {}

    @staticmethod
    def _from_result(r) -> "Vault":
        info = consume(r) or {}
        s = Vault()
        s.hnd = r.hnd
        s.id = info.get("id", "")
        s.userId = info.get("userId", "")
        s.userPublicId = info.get("userPublicId", "")
        s.store_config = info.get("storeConfig", {})
        s.author = info.get("author", "")
        s.config = info.get("config", {})
        return s

    @staticmethod
    def create(db: DB, identity: PrivateID, store_config: Dict[str, Any], settings: Dict[str, Any] = None) -> "Vault":
        settings = settings or {}
        r = lib.bao_vault_create(db.hnd, e8(identity), j8(store_config), j8(settings))
        return Vault._from_result(r)

    @staticmethod
    def open(db: DB, identity: PrivateID, store_config: Dict[str, Any], author: PublicID) -> "Vault":
        r = lib.bao_vault_open(db.hnd, e8(identity), j8(store_config), e8(author))
        return Vault._from_result(r)

    def close(self):
        if getattr(self, "hnd", 0):
            consume(lib.bao_vault_close(self.hnd))
            self.hnd = 0

    def sync_access(self, changes: List[AccessChange] = None, options: int = 0):
        '''
        Sync access changes from the remote store and optionaly apply new changes.
        
        :param self: Bao instance
        :param changes: List of access changes to apply
        :type changes: List[AccessChange]
        :param options: Options for syncing access
        :type options: int
        :return: Result of the sync operation
        :rtype: Any
        '''
        payload = [] if not changes else [asdict(c) for c in changes]
        return consume(lib.bao_vault_syncAccess(self.hnd, options, j8(payload)))

    def get_access(self, group: str):
        '''
        returns the users and their access levels for the specified group.
        
        :param self: Bao instance
        :param group: Group name
        :type group: str
        :return: map of user IDs to access levels
        :rtype: Any
        '''
        return consume(lib.bao_vault_getAccess(self.hnd, e8(group)))

    def get_groups(self, user: PublicID):
        return consume(lib.bao_vault_getGroups(self.hnd, e8(user)))

    def wait_files(self, file_ids: Optional[List[int]] = None):
        '''
        Wait for the specified files to be fully written/synced.
        
        :param self: Bao instance
        :param file_ids: List of file IDs to wait for
        :type file_ids: Optional[List[int]]
        :return: Result of the wait operation
        :rtype: Any
        '''
        payload = None if file_ids is None else j8(file_ids)
        return consume(lib.bao_vault_waitFiles(self.hnd, payload))

    def list_groups(self):
        '''
        The return the list of groups in the Bao store 
        
        :param self: Bao instance
        '''
        return consume(lib.bao_listGroups(self.hnd))

    def sync(self, groups: List[str] = [Groups.users]):
        '''
        Update the files in the specified groups from the remote store.
        
        :param self: Bao instance
        :param groups: Groups to sync, default is Groups.users
        :type groups: List[str]
        '''
        if len(groups) == 0:
            raise ValueError("groups must be a non-empty list of group names")
        payload = None if groups is None else j8(groups)
        return consume(lib.bao_vault_sync(self.hnd, payload))

    def set_attribute(self, name: str, value: str, options: int = 0):
        return consume(lib.bao_vault_setAttribute(self.hnd, options, e8(name), e8(value)))

    def get_attribute(self, name: str, author: PublicID):
        return consume(lib.bao_vault_getAttribute(self.hnd, e8(name), e8(author)))

    def get_attributes(self, author: PublicID):
        return consume(lib.bao_vault_getAttributes(self.hnd, e8(author)))

    def read_dir(self, dir: str, since: Optional[datetime] = None, from_id: int = 0, limit: int = 0):
        since_sec = 0 if since is None else int(since.timestamp())
        return consume(lib.bao_vault_readDir(self.hnd, e8(dir), since_sec, from_id, limit))

    def stat(self, name: str):
        return consume(lib.bao_vault_stat(self.hnd, e8(name)))

    def read(self, name: str, dest: str, options: int = 0):
        return consume(lib.bao_vault_read(self.hnd, e8(name), e8(dest), options))

    def write(self, dest: str, group: str, src: str = "", attrs: bytes = b"", options: int = 0):
        attrs = attrs or b""
        data = Data.from_byte_array(attrs)
        r = lib.bao_vault_write(self.hnd, e8(dest), e8(src), e8(group), data, options)
        return consume(r)

    def delete(self, name: str, options: int = 0):
        return consume(lib.bao_vault_delete(self.hnd, e8(name), options))

    def allocated_size(self) -> int:
        r = lib.bao_vault_allocatedSize(self.hnd)
        return consume(r)

    def baoql(self, group: str, db: DB) -> "Replica":
        r = lib.bao_replica_open(self.hnd, e8(group), db.hnd)
        consume(r)
        return Replica(r.hnd)

    def send(self, dir: str, group: str, message: Message):
        return consume(lib.bao_mailbox_send(self.hnd, e8(dir), e8(group), e8(message.toJson())))

    def receive(self, dir: str, since: int = 0, from_id: int = 0) -> List[Message]:
        res = consume(lib.bao_mailbox_receive(self.hnd, e8(dir), since, from_id)) or []
        return [Message(**m) for m in res]

    def download(self, dir: str, message: Dict[str, Any], attachment: int, dest: str):
        return consume(lib.bao_mailbox_download(self.hnd, e8(dir), j8(message), attachment, e8(dest)))

    def __del__(self):
        self.close()

    def __repr__(self) -> str:
        return self.store_config.get("id", "") or self.id


class Rows:
    def __init__(self, hnd: int):
        self.hnd = hnd

    def next(self) -> bool:
        return bool(consume(lib.bao_replica_next(self.hnd)))

    def current(self):
        return consume(lib.bao_replica_current(self.hnd))

    def close(self):
        consume(lib.bao_replica_closeRows(self.hnd))
        self.hnd = 0


class Replica:
    def __init__(self, hnd: int):
        self.hnd = hnd

    def exec(self, query: str, args: Dict[str, Any]):
        return consume(lib.bao_replica_exec(self.hnd, e8(query), j8(args)))

    def query(self, query: str, args: Dict[str, Any]) -> Rows:
        r = lib.bao_replica_query(self.hnd, e8(query), j8(args))
        consume(r)
        return Rows(r.hnd)

    def fetch(self, query: str, args: Dict[str, Any], max_rows: int = 100000):
        return consume(lib.bao_replica_fetch(self.hnd, e8(query), j8(args), max_rows))

    def fetch_one(self, query: str, args: Dict[str, Any]):
        return consume(lib.bao_replica_fetchOne(self.hnd, e8(query), j8(args)))

    def sync(self) -> int:
        r = lib.bao_replica_sync(self.hnd)
        return consume(r)

    def cancel(self):
        return consume(lib.bao_replica_cancel(self.hnd))

class Mailbox:
    def __init__(self, hnd: int):
        self.hnd = hnd
        
    def send(self, dir: str, group: str, message: Message):
        return consume(lib.bao_mailbox_send(self.hnd, e8(dir), e8(group), e8(message.toJson())))
    
    def receive(self, dir: str, since: int = 0, from_id: int = 0) -> List[Message]:
        res = consume(lib.bao_mailbox_receive(self.hnd, e8(dir), since, from_id)) or []
        return [Message(**m) for m in res]
    
    def download(self, dir: str, message: Dict[str, Any], attachment: int, dest: str):
        return consume(lib.bao_mailbox_download(self.hnd, e8(dir), j8(message), attachment, e8(dest)))  
    