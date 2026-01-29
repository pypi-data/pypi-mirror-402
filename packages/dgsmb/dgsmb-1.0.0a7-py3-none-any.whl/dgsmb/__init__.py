import io
import logging
import traceback

# Необязательный импорт dglog
try:
    import dglog
    DGLOG_AVAILABLE = True
    LoggerType = logging.Logger | dglog.Logger
except ImportError:
    DGLOG_AVAILABLE = False
    LoggerType = logging.Logger

import socket
import time
from tempfile import TemporaryFile
from typing import Optional, Tuple, BinaryIO, List
from smb.SMBConnection import SMBConnection
from smb.base import SharedFile, NotConnectedError, SMBTimeout
from smb.smb_structs import OperationFailure
from .config import SMBConfig, MasterNode, BackupNode, Node
from .decorator import check_connection


class SMBClient:
    def __init__(self, path: str | None = None,
                 username: str | None = None,
                 password: str | None = None,
                 domain: str | None = 'group.s7',
                 cfg: SMBConfig | None = None,
                 logger: LoggerType | None = None,
                 automate_switch_node: bool = True):
        self.path: Optional[str] = path
        self.username: Optional[str] = username
        self.password: Optional[str] = password
        self.domain: Optional[str] = domain
        self.remote_name: Optional[str] = None
        self.service_name: Optional[str] = None
        self.share_path: Optional[str] = None
        self.conn: Optional[SMBConnection] = None
        self.logger = logger or logging.getLogger('dgsmb')
        self.cfg = cfg

        self.automate_switch_node = automate_switch_node

        self._set_master_node_cfg()
        self.cfg.master_node.current = True

        self._prepare_connection_node(self.cfg.master_node)
        if self.cfg.backup_node is not None:
            self._prepare_connection_node(self.cfg.backup_node)

        self.connect()

    def set_path(self, path: str):
        self.path = path

    def set_credentials(self, username: str, password: str, domain='group.s7'):
        assert username, "Empty username isn't allowed"
        assert password, "Empty password isn't allowed"
        self.username = username
        self.password = password
        self.domain = domain

    def _set_master_node_cfg(self):
        if self.cfg is None:
            self.cfg = SMBConfig(
                master_node=MasterNode(
                    path=self.path,
                    username=self.username,
                    password=self.password,
                ),
                backup_node=None,
                reconnect_wait_time=5,
                reconnect_attempts=6,
            )

    @staticmethod
    def _prepare_connection_node(node_cfg: Node):
        path_arr = node_cfg.path.replace('\\', '/').split('/')[2:]
        node_cfg.host = path_arr[0]
        node_cfg.service_name = path_arr[1]
        node_cfg.share_path = '/'.join(path_arr[2:])

    def prepare_connection(self, node_cfg: Node = None):
        path_arr = self.path.replace('\\', '/').split('/')[2:]
        host = path_arr[0] if node_cfg is None else node_cfg.host
        service_name = path_arr[1] if node_cfg is None else node_cfg.service_name
        share_path = '/'.join(path_arr[2:]) if node_cfg is None else node_cfg.share_path
        self.remote_name = host
        self.service_name = service_name
        self.share_path = share_path

    def _switch_current_node_cfg(self, node_cfg: Node):
        if self.cfg.master_node is not None and self.cfg.backup_node is not None:
            if (self.cfg.master_node.current and not isinstance(node_cfg, MasterNode)) or (self.cfg.backup_node.current and not isinstance(node_cfg, BackupNode)):
                self.cfg.master_node.current = not self.cfg.master_node.current
                self.cfg.backup_node.current = not self.cfg.backup_node.current
        else:
            self.cfg.master_node.current = True

    def _connect_node(self, node_cfg: Node):
        """
        Connect to SMB node
        :return: connection status
        """
        try:
            assert node_cfg.username, 'No username provided'
            assert node_cfg.password, 'No password provided'
            self.logger.info(f"Trying to connect to {node_cfg.host}...")
            self.path = node_cfg.path
            self.prepare_connection(node_cfg)
            conn = SMBConnection(
                username=node_cfg.username,
                password=node_cfg.password,
                my_name=socket.gethostname(),
                remote_name=node_cfg.host,
                domain=node_cfg.domain,
                use_ntlm_v2=True,
                is_direct_tcp=True
            )
            assert conn.connect(socket.gethostbyname(node_cfg.host), 445)
            try:
                conn.listPath(node_cfg.service_name, "")
            except Exception as err:
                raise err
            self.conn = conn
            if self.cfg.master_node is not None:
                if self.cfg.backup_node is not None:
                    self._switch_current_node_cfg(node_cfg)
                else:
                    self.cfg.master_node.current = True
            return True
        except OperationFailure as err:
            self.logger.warning(err.message)
            return False
        except Exception as err:
            self.logger.error(err)
            return False

    def _connect(self, node_cfg: Node, attempt):
        if self._connect_node(node_cfg):
            self.logger.info(f"Successfully connected to {node_cfg.host}/{node_cfg.service_name}:{node_cfg.username}")
            return True
        else:
            self.logger.warning(f"[{attempt + 1}/{self.cfg.reconnect_attempts}] Failed to connect to {node_cfg.host}/{node_cfg.service_name}:{node_cfg.username}. try reconnecting...")
            time.sleep(self.cfg.reconnect_wait_time)
            return False

    def connect(self):
        """Connect to SMB server (tries master then backup)."""
        for try_ in range(self.cfg.reconnect_attempts):
            if self._connect(self.cfg.master_node, try_):
                break
        else:
            if self.cfg.backup_node is not None:
                self.logger.warning(f"Failed to connect to {self.cfg.master_node.host}/{self.cfg.master_node.service_name}:{self.cfg.master_node.username} try connect to {self.cfg.backup_node.host}/{self.cfg.backup_node.service_name}:{self.cfg.backup_node.username}")
                for try_ in range(self.cfg.reconnect_attempts):
                    if self._connect(self.cfg.backup_node, try_):
                        break
                else:
                    self.logger.error("Could not connect to both master and backup nodes. Giving up..")
                    raise NotConnectedError
            else:
                self.logger.error("Could not connect to master and backup nodes is not set. Giving up..")
                raise NotConnectedError

    def _reconnect_node(self, node_cfg: Node) -> bool:
        self.logger.info(f"Reconnect to {node_cfg.host}.")
        self.conn = None
        for try_ in range(self.cfg.reconnect_attempts):
            if self._connect(node_cfg, try_):
                break
        return self.conn is not None

    def _check_connection_node(self, node_cfg: Node) -> bool:
        try:
            self.conn.listPath(node_cfg.service_name, "")
            return True
        except (NotConnectedError, OperationFailure, ConnectionResetError, SMBTimeout):
            return False
        except AttributeError:
            return False
        except Exception as err:
            self.logger.error(f"Unexpected error during connection check: {err}. Traceback: {traceback.format_exc()}")
            return False

    def _check_connection(self):
        if self.cfg.master_node.current:
            if not self._check_connection_node(self.cfg.master_node):
                return self._reconnect_node(self.cfg.master_node)
        elif self.cfg.backup_node and self.cfg.backup_node.current:
            if not self._check_connection_node(self.cfg.backup_node):
                return self._reconnect_node(self.cfg.backup_node)
        return False

    def force_switch_node(self):
        assert self.cfg.backup_node, "Backup node is not set. Could not switch"
        self.logger.info("Switching node")
        if self.cfg.master_node.current:
            if self._connect_node(self.cfg.backup_node):
                self.logger.info(f"Successfully connected to {self.cfg.backup_node.host}/{self.cfg.backup_node.service_name}:{self.cfg.backup_node.username}")
                return True
        elif self.cfg.backup_node.current:
            if self._connect_node(self.cfg.master_node):
                self.logger.info(f"Successfully connected to {self.cfg.master_node.host}/{self.cfg.master_node.service_name}:{self.cfg.master_node.username}")
                return True
        return False

    # === SMB operations (единообразно) ===

    @check_connection
    def list_files(self, smb_subdir: str = "", pattern: str = "*") -> List[SharedFile]:
        """List files in directory (without '.'/'..')."""
        self.logger.debug("Connection established")
        return [
            x for x in self.conn.listPath(self.service_name, f'{self.share_path}/{smb_subdir}', pattern=pattern)
            if x.filename not in ('.', '..')
        ]

    @check_connection
    def list_files_full(self, smb_subdir: str = "", pattern: str = "*") -> List[SharedFile]:
        """List all files in directory (with '.'/'..')."""
        self.logger.debug("Connection established")
        return self.conn.listPath(self.service_name, f'{self.share_path}/{smb_subdir}', pattern=pattern)

    def list_file_names(self, smb_subdir: str = "", pattern="*") -> List[str]:
        """List just filenames (without '.'/'..')."""
        return [file.filename for file in self.list_files(smb_subdir, pattern=pattern)]

    def exists_file(self, file_name: str, smb_subdir: str = "") -> bool:
        """Check if file exists in directory."""
        return file_name in self.list_file_names(smb_subdir)

    def download_file(self, filename, local_path='.', smb_subdir: str = None) -> bool:
        """Download file from SMB to local filesystem."""
        try:
            tmp_file, _ = self.download_file_tmp(filename, smb_subdir)
        except NotConnectedError:
            self.logger.error("Not connected to SMB")
            return False
        if not tmp_file:
            return False
        try:
            local_full_path = f'{local_path}/{filename}'
            with open(local_full_path, 'wb') as f:
                f.write(tmp_file.read())
            return True
        except Exception as ex:
            self.logger.error(f"Failed to write file: {ex}")
            return False
        finally:
            tmp_file.close()

    @check_connection
    def upload_file(self, filename: str, local_path: str, smb_subdir: str = None) -> bool:
        """Upload file from local filesystem to SMB."""
        local_full_path = f'{local_path}/{filename}'
        with open(local_full_path, 'rb') as f:
            return self.upload_file_tmp(filename, f, smb_subdir)

    @check_connection
    def download_file_tmp(self, filename: str, smb_subdir: str = None) -> Tuple[TemporaryFile, bool]:
        """Download file as TemporaryFile."""
        file_data = TemporaryFile()
        path = f'{smb_subdir}/{filename}' if smb_subdir else filename
        self.conn.retrieveFile(self.service_name, f"{self.share_path}/{path}", file_data)
        file_data.seek(0)
        if file_data:
            return file_data, True
        return None, False

    @check_connection
    def upload_file_tmp(self, filename: str, payload: io.BytesIO | BinaryIO, smb_subdir: str = None) -> bool:
        """Upload file from file-like object (tmp file) to SMB."""
        path = f'{smb_subdir}/{filename}' if smb_subdir else filename
        self.conn.storeFile(self.service_name, f"{self.share_path}/{path}", payload)
        return True

    @check_connection
    def remove_file(self, filename: str, smb_subdir: str = None) -> bool:
        """Remove file from SMB share."""
        path = f'{smb_subdir}/{filename}' if smb_subdir else filename
        self.conn.deleteFiles(self.service_name, f"{self.share_path}/{path}")
        return True

    # Aliases for maximum discoverability:
    download = download_file
    download_tmp = download_file_tmp
    download_file_as_tmp = download_file_tmp
    upload = upload_file
    upload_tmp = upload_file_tmp
    delete = remove_file
    list = list_files
    ls = list_files
    get_list_files = list_files
    lsf = list_files_full
    ls_names = list_file_names
