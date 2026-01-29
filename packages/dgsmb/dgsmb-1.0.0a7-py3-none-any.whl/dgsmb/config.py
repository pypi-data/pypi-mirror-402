from pydantic import BaseModel, Field


class Node(BaseModel):
    path: str = Field(None, description="SMB путь")
    username: str = Field(None, description="Имя пользователя")
    password: str = Field(None, description="Пароль")
    domain: str = Field('group.s7', description="Домен")

    host: str | None = Field(None, description="SMB хост")
    share_path: str | None = Field(None, description="Остальная часть пути")
    service_name: str | None = Field(None, description="Сервис")

    current: bool = Field(False, description="Используется, как текущее")


class MasterNode(Node):
    pass


class BackupNode(Node):
    pass


class SMBConfig(BaseModel):
    master_node: MasterNode = Field(None, description="Конфигурация основного подключения")
    backup_node: BackupNode | None = Field(None, description="Конфигурация запасного подключения")
    reconnect_wait_time: int = Field(5, description="Время ожидания переподключения в секундах")
    reconnect_attempts: int = Field(5, description="Количество попыток переподключения")