from typing import Optional
from abc import ABC, abstractmethod


class ConfigurationManagerInterface(ABC):
    @abstractmethod
    def get_config(self, key: str) -> str:
        pass
    
    @abstractmethod
    def get_all_configs(self) -> Optional[dict]:
        pass