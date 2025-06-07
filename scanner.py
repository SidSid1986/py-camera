import configparser

class ScannerConfig:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config = configparser.ConfigParser()
        self.reload()

    def reload(self):
        self.config.read(self.file_path, encoding="utf-8")

    def get_ip(self):
        return self.config.get("device", "ip", fallback="127.0.0.1")

    def get_port(self):
        return self.config.getint("device", "port", fallback=32001)

    def get_dll_path(self):
        return self.config.get("paths", "dll", fallback="EthernetScanner.dll")