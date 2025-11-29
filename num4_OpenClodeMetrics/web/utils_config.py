"""
Configuration utilities - Đọc từ .env file
"""

import os
from pathlib import Path
from typing import Dict, Any

# Tìm file .env ở root project (D:\GIT\Fintech\fintech\.env)
def find_env_file() -> Path:
    """Tìm file .env từ thư mục hiện tại lên đến root project."""
    current = Path(__file__).resolve()
    
    # Đi lên từ web/ -> num4_OpenClodeMetrics/ -> fintech/
    for parent in current.parents:
        env_file = parent / '.env'
        if env_file.exists():
            return env_file
    
    # Nếu không tìm thấy, thử root project
    root_env = Path('D:/GIT/Fintech/fintech/.env')
    if root_env.exists():
        return root_env
    
    return None


def load_env_file() -> Dict[str, str]:
    """Load .env file và return dict."""
    env_file = find_env_file()
    env_vars = {}
    
    if env_file and env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
    
    return env_vars


def get_config() -> Dict[str, Any]:
    """
    Get configuration từ .env file hoặc environment variables.
    Priority: .env file > environment variables > defaults
    
    Logic:
    - Local: có thể dùng localhost hoặc 0.0.0.0 (0.0.0.0 cho phép access từ network)
    - Server: nên dùng 0.0.0.0 để expose ra ngoài
    """
    env_vars = load_env_file()
    
    # API Server Config - Hard code trong code, không đọc từ .env
    api_host = '0.0.0.0'  # Bind tất cả interfaces
    api_port = 30017  # Port backend chạy (num4_OpenClodeMetrics)
    
    # BASE_URL_SERVER - Chỉ IP hoặc domain, không có port
    base_url_server = env_vars.get('BASE_URL_SERVER') or os.getenv('BASE_URL_SERVER')
    
    # Build API Production URL từ BASE_URL_SERVER + port
    if base_url_server:
        # Nếu BASE_URL_SERVER đã có http:// hoặc https://, giữ nguyên
        if base_url_server.startswith('http://') or base_url_server.startswith('https://'):
            api_production_url = f'{base_url_server}:{api_port}'
        else:
            # Nếu không có protocol, thêm http://
            api_production_url = f'http://{base_url_server}:{api_port}'
    else:
        # Nếu không có BASE_URL_SERVER, dùng localhost (development mode)
        import warnings
        warnings.warn(
            "BASE_URL_SERVER not found in .env. Using localhost for development. "
            "Please set BASE_URL_SERVER in .env file for production.",
            UserWarning
        )
        api_production_url = f'http://localhost:{api_port}'
    
    # Detect environment
    # Nếu có ENVIRONMENT variable, dùng nó; không thì auto-detect
    environment = env_vars.get('ENVIRONMENT') or os.getenv('ENVIRONMENT', 'auto')
    
    # Auto-detect: nếu BASE_URL_SERVER có và không phải localhost → production
    if environment == 'auto':
        if base_url_server and 'localhost' not in base_url_server and '127.0.0.1' not in base_url_server:
            environment = 'production'
        else:
            environment = 'local'
    
    # Database Config (có thể override từ .env)
    db_host = env_vars.get('DB_HOST') or os.getenv('DB_HOST')
    db_port = env_vars.get('DB_PORT') or os.getenv('DB_PORT')
    db_name = env_vars.get('DB_NAME') or os.getenv('DB_NAME')
    db_user = env_vars.get('DB_USER') or os.getenv('DB_USER')
    db_password = env_vars.get('DB_PASSWORD') or os.getenv('DB_PASSWORD')
    
    return {
        'api': {
            'host': api_host,
            'port': api_port,
            'production_url': api_production_url,
            'environment': environment
        },
        'database': {
            'host': db_host,
            'port': db_port,
            'name': db_name,
            'user': db_user,
            'password': db_password
        }
    }


# Get config for frontend (chỉ expose những gì cần thiết)
def get_frontend_config() -> Dict[str, Any]:
    """
    Get config để expose cho frontend.
    
    Logic:
    - Local: frontend nên dùng localhost (không dùng 0.0.0.0 vì browser không hiểu)
    - Server: frontend dùng production_url (IP public hoặc domain)
    """
    config = get_config()
    api_config = config['api']
    
    # Local URL: luôn dùng localhost (không dùng 0.0.0.0)
    api_local_url = f"http://localhost:{api_config['port']}"
    
    # Production URL: từ config hoặc detect từ host
    api_production_url = api_config['production_url']
    
    return {
        'api_base_url': api_production_url,
        'api_local_url': api_local_url,
        'environment': api_config.get('environment', 'auto'),
        'note': 'Frontend nên dùng api_local_url khi chạy local, api_base_url khi chạy production'
    }

