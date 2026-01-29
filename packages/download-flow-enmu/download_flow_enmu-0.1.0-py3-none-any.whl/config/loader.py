"""
配置加载工具，支持从环境变量替换配置值
"""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv


class ConfigLoader:
    """配置加载器，支持环境变量替换"""
    
    def __init__(self, env_file: Path = None):
        if env_file is None:
            # 默认在项目根目录查找 .env
            env_file = Path(__file__).parent.parent / ".env"
        
        # 加载 .env 文件
        if env_file.exists():
            load_dotenv(env_file)
    
    def _replace_env_vars(self, value: Any) -> Any:
        if isinstance(value, str):
            # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replacer, value)
        
        elif isinstance(value, dict):
            return {k: self._replace_env_vars(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._replace_env_vars(item) for item in value]
        
        else:
            return value
    
    def load_json(self, config_path: Path) -> Dict[str, Any]:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return self._replace_env_vars(config)


# 便捷函数
def load_config(config_path: Path = None) -> Dict[str, Any]: 
    if config_path is None:
        config_path = Path.home() / ".flow" / "config.json"
    
    loader = ConfigLoader()
    return loader.load_json(config_path)
