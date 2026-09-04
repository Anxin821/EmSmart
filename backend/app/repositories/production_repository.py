from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.crud import (
    batch_import_weekly,
    create_monthly_production,
    create_weekly_production,
    delete_monthly_production,
    delete_weekly_production,
    generate_monthly_from_weekly,
    get_monthly_production_paginated,
    get_monthly_summary_stats,
    get_monthly_trend,
    get_weekly_production_by_id,
    get_weekly_production_paginated,
    update_monthly_production,
    update_weekly_production,
)


__all__ = [
    "get_weekly_production_paginated",
    "get_weekly_production_by_id",
    "create_weekly_production",
    "update_weekly_production",
    "delete_weekly_production",
    "get_monthly_production_paginated",
    "get_monthly_summary_stats",
    "get_monthly_trend",
    "create_monthly_production",
    "update_monthly_production",
    "delete_monthly_production",
    "generate_monthly_from_weekly",
    "batch_import_weekly",
]


# Thin repository wrapper: keep current CRUD logic in core.crud and expose a module
# that matches the new service/repository boundary.
