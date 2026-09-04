from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.core.crud import (
    get_servers_paginated, create_server, update_server, delete_server,
    get_aging_racks_paginated, create_aging_rack, update_aging_rack, delete_aging_rack,
    get_wifi_aps_paginated, create_wifi_ap, update_wifi_ap, delete_wifi_ap,
)

__all__ = [
    "get_servers_paginated",
    "create_server",
    "update_server",
    "delete_server",
    "get_aging_racks_paginated",
    "create_aging_rack",
    "update_aging_rack",
    "delete_aging_rack",
    "get_wifi_aps_paginated",
    "create_wifi_ap",
    "update_wifi_ap",
    "delete_wifi_ap",
]

def list_servers(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    return get_servers_paginated(db, page, page_size, keyword, production_line, status)

def create_server_repo(db: Session, data: dict):
    return create_server(db, data)

def update_server_repo(db: Session, server_id: str, data: dict):
    return update_server(db, server_id, data)

def delete_server_repo(db: Session, server_id: str):
    return delete_server(db, server_id)

# aging racks
def list_aging_racks(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    return get_aging_racks_paginated(db, page, page_size, keyword, production_line, status)

def create_aging_rack_repo(db: Session, data: dict):
    return create_aging_rack(db, data)

def update_aging_rack_repo(db: Session, rack_id: str, data: dict):
    return update_aging_rack(db, rack_id, data)

def delete_aging_rack_repo(db: Session, rack_id: str):
    return delete_aging_rack(db, rack_id)

# wifi aps
def list_wifi_aps(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    return get_wifi_aps_paginated(db, page, page_size, keyword, production_line, status)

def create_wifi_ap_repo(db: Session, data: dict):
    return create_wifi_ap(db, data)

def update_wifi_ap_repo(db: Session, ap_id: str, data: dict):
    return update_wifi_ap(db, ap_id, data)

def delete_wifi_ap_repo(db: Session, ap_id: str):
    return delete_wifi_ap(db, ap_id)
