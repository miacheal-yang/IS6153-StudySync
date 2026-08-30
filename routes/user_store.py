import json
from pathlib import Path


def user_file(root_path: str) -> Path:
    return Path(root_path) / "LocalStorage" / "ss_user.json"


def ensure_user_storage(root_path: str) -> None:
    file_path = user_file(root_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_root_file = Path(root_path) / "ss_user.json"
    legacy_folder_file = Path(root_path) / "ss_user" / "users.json"
    if not file_path.exists() and legacy_root_file.exists():
        file_path.write_text(legacy_root_file.read_text(encoding="utf-8"), encoding="utf-8")
    elif not file_path.exists() and legacy_folder_file.exists():
        file_path.write_text(legacy_folder_file.read_text(encoding="utf-8"), encoding="utf-8")
    if not file_path.exists():
        file_path.write_text("[]", encoding="utf-8")


def load_users(root_path: str) -> list[dict]:
    ensure_user_storage(root_path)
    file_path = user_file(root_path)
    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, list):
        return data
    return []


def save_users(root_path: str, users: list[dict]) -> None:
    ensure_user_storage(root_path)
    user_file(root_path).write_text(
        json.dumps(users, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def next_user_id(users: list[dict]) -> str:
    max_num = 0
    for user in users:
        raw = str(user.get("id", ""))
        if raw.startswith("u"):
            try:
                max_num = max(max_num, int(raw[1:]))
            except ValueError:
                pass
    return f"u{max_num + 1:03d}"


def find_user_by_email(users: list[dict], email: str) -> dict | None:
    target = email.strip().lower()
    for user in users:
        if str(user.get("email", "")).strip().lower() == target:
            return user
    return None


def find_user_by_id(users: list[dict], user_id: str) -> dict | None:
    for user in users:
        if str(user.get("id")) == str(user_id):
            return user
    return None


def to_public_user(user: dict) -> dict:
    tier = str(user.get("tier", "free")).lower()
    return {
        "id": user.get("id"),
        "full_name": user.get("name", ""),
        "email": user.get("email", ""),
        "major": user.get("major", ""),
        "semester": user.get("semester", ""),
        "avatar_url": user.get("avatarUrl", ""),
        "default_reminder": user.get("defaultReminder", "0"),
        "tier": tier,
        "is_premium": tier == "premium",
    }
