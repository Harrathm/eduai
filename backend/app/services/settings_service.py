"""Platform Settings Service with in-memory cache and immediate invalidation."""

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SettingsCache:
    """Thread-safe in-memory cache for platform settings with immediate invalidation."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, str]] = {}  # school_id -> {key: value}

    def get(self, school_id: int, key: str, db: Session) -> Optional[str]:
        cache_key = str(school_id)
        with self._lock:
            if cache_key in self._cache and key in self._cache[cache_key]:
                return self._cache[cache_key][key]

        value = self._load_from_db(school_id, key, db)
        with self._lock:
            self._cache.setdefault(cache_key, {})[key] = value
        return value

    def get_all(self, school_id: int, db: Session) -> dict[str, str]:
        cache_key = str(school_id)
        with self._lock:
            if cache_key in self._cache:
                return dict(self._cache[cache_key])

        settings = self._load_all_from_db(school_id, db)
        with self._lock:
            self._cache[cache_key] = dict(settings)
        return dict(settings)

    def set(self, school_id: int, key: str, value: str, db: Session) -> None:
        from app.models import PlatformSetting
        setting = db.query(PlatformSetting).filter(
            PlatformSetting.school_id == school_id,
            PlatformSetting.key == key,
        ).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.now(timezone.utc)
        else:
            setting = PlatformSetting(
                school_id=school_id,
                key=key,
                value=value,
            )
            db.add(setting)
        db.commit()

        cache_key = str(school_id)
        with self._lock:
            self._cache.setdefault(cache_key, {})[key] = value

    def delete(self, school_id: int, key: str, db: Session) -> None:
        from app.models import PlatformSetting
        db.query(PlatformSetting).filter(
            PlatformSetting.school_id == school_id,
            PlatformSetting.key == key,
        ).delete()
        db.commit()

        cache_key = str(school_id)
        with self._lock:
            if cache_key in self._cache:
                self._cache[cache_key].pop(key, None)

    def invalidate(self, school_id: int) -> None:
        with self._lock:
            self._cache.pop(str(school_id), None)

    def invalidate_all(self) -> None:
        with self._lock:
            self._cache.clear()

    def get_bool(self, school_id: int, key: str, db: Session, default: bool = False) -> bool:
        val = self.get(school_id, key, db)
        if val is None:
            return default
        return val.lower() in ("true", "1", "yes")

    def get_int(self, school_id: int, key: str, db: Session, default: int = 0) -> int:
        val = self.get(school_id, key, db)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def get_json(self, school_id: int, key: str, db: Session, default: Any = None) -> Any:
        val = self.get(school_id, key, db)
        if val is None:
            return default
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default

    def _load_from_db(self, school_id: int, key: str, db: Session) -> Optional[str]:
        from app.models import PlatformSetting
        setting = db.query(PlatformSetting).filter(
            PlatformSetting.school_id == school_id,
            PlatformSetting.key == key,
        ).first()
        return setting.value if setting else None

    def _load_all_from_db(self, school_id: int, db: Session) -> dict[str, str]:
        from app.models import PlatformSetting
        settings = db.query(PlatformSetting).filter(
            PlatformSetting.school_id == school_id,
        ).all()
        return {s.key: s.value for s in settings if s.value is not None}


# Singleton instance
settings_cache = SettingsCache()
