from __future__ import annotations

from dto.user_profile import UserProfile, UserResponse
from service.user_profile import build_user_profile, load_user_profile, load_user_profiles

PROFILE_KEYS = {
    "id", "username", "fullname", "email", "phone", "status", "emailVerified", "twoFactorEnabled", "role",
    "permissionId", "permission", "groupId", "group", "lastLoginAt", "createdAt", "updatedAt",
}  # fmt: skip


def test_profile_shape_and_secrets(regular_user, user_permission, groups_repo) -> None:
    group = groups_repo.insert({"name": "Ops"})
    user = {**regular_user, "group_id": group["id"], "two_factor_secret": "S3CRET"}
    profile = build_user_profile(user, user_permission, group)
    dumped = profile.model_dump(mode="json")
    assert set(dumped) == PROFILE_KEYS
    assert dumped["role"] == "user"
    assert dumped["permission"] == {
        "id": user_permission["id"],
        "name": "User",
        "alias": "user",
        "privileges": ["profile:read"],
    }
    assert dumped["group"] == {"id": group["id"], "name": "Ops"}
    text = profile.model_dump_json()
    assert "S3CRET" not in text and "password" not in text.lower()


def test_profile_without_relations(user_factory) -> None:
    profile = build_user_profile(user_factory())
    assert profile.role is None and profile.permission is None and profile.group is None


def test_load_single_and_batch(regular_user, admin_user, permissions_repo, groups_repo) -> None:
    single = load_user_profile(regular_user, permissions_repo, groups_repo)
    assert isinstance(single, UserProfile) and single.role == "user"
    many = load_user_profiles([regular_user, admin_user], permissions_repo, groups_repo)
    assert all(isinstance(p, UserResponse) for p in many)
    assert [p.role for p in many] == ["user", "admin"]
    assert "passwordHash" not in many[0].model_dump(mode="json")
