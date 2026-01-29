from smb.base import NotConnectedError


def check_connection(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        
        # Если отключено автоматическое переключение узлов
        if not self.automate_switch_node:
            # Переподключаемся только к текущему узлу
            if self.cfg.master_node.current:
                if not self._check_connection_node(self.cfg.master_node):
                    if self._reconnect_node(self.cfg.master_node):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            elif self.cfg.backup_node and self.cfg.backup_node.current:
                if not self._check_connection_node(self.cfg.backup_node):
                    if self._reconnect_node(self.cfg.backup_node):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            raise NotConnectedError("not available connection")
        
        # Если автоматическое переключение разрешено
        if self.cfg.master_node.current:
            # Подключены к master - сначала пробуем переподключиться к нему
            if not self._check_connection_node(self.cfg.master_node):
                if self._reconnect_node(self.cfg.master_node):
                    return func(*args, **kwargs)
                # Если не удалось переподключиться к master, пробуем backup
                elif self.cfg.backup_node is not None:
                    if self._reconnect_node(self.cfg.backup_node):
                        return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        elif self.cfg.backup_node and self.cfg.backup_node.current:
            # Подключены к backup - проверяем доступность master
            if self._check_connection_node(self.cfg.master_node):
                # Master доступен - переподключаемся к нему
                if self._reconnect_node(self.cfg.master_node):
                    return func(*args, **kwargs)
            # Master недоступен - проверяем текущее подключение к backup
            if not self._check_connection_node(self.cfg.backup_node):
                if self._reconnect_node(self.cfg.backup_node):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        raise NotConnectedError("not available connection")
    return wrapper
