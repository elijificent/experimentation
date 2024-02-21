# pylint: disable=missing-docstring

import random
import uuid

import pytest

from src.database.models import User
from src.database.repository import UserRepository
from src.services import AuthService


def random_string(length: int) -> str:
    letters = [chr(random.randint(97, 122)) for i in range(length)]
    return "".join(letters)


def test_validate_password():
    assert AuthService.validate_password("password") is False
    assert AuthService.validate_password("password123") is True
    assert AuthService.validate_password("password123!") is True
    assert AuthService.validate_password("password123!@") is True
    assert AuthService.validate_password("short1") is False


def test_validate_username():
    assert AuthService.validate_username("username") is True
    assert AuthService.validate_username("username123") is True
    assert AuthService.validate_username("name987!") is True
    assert AuthService.validate_username("username123!{}") is False
    assert AuthService.validate_username("short1") is True
    assert AuthService.validate_username("shor") is False
    assert AuthService.validate_username("*" * 51) is False


def test_get_user():
    current_user = UserRepository.get_user_by_username("marvelous_ms")
    if current_user is not None:
        UserRepository.delete(current_user.user_uuid)

    test_pass = "password123!"
    test_name = "marvelous_ms"
    user: User = AuthService.create_user(test_name, test_pass)

    assert AuthService.get_user(user.user_uuid) == user
    assert AuthService.get_user(uuid.uuid4()) is None


def test_create_user():
    current_user = UserRepository.get_user_by_username("marvelous_mx")
    if current_user is not None:
        UserRepository.delete(current_user.user_uuid)

    test_pass = "other_password!"
    test_name = "marvelous_mx"
    user: User = AuthService.create_user(test_name, test_pass)

    assert user.username == test_name
    assert user.hashed_password != test_pass
    assert user.random_salt is not None
    assert AuthService.validate_auth(user.user_uuid, test_name, test_pass)

    with pytest.raises(Exception) as e_info:
        AuthService.create_user(random_string(51), test_pass)
    assert "Username does not meet requirements" in str(e_info.value)

    with pytest.raises(Exception) as e_info:
        AuthService.create_user("a_good_username", "badpas")
    assert "Password does not meet requirements" in str(e_info.value)


def test_update_username():
    old_name = random_string(10)
    new_user = AuthService.create_user(
        username=old_name,
        password="password123!",
    )

    new_name = random_string(10)
    assert new_user.username != new_name

    updated_user = AuthService.update_username(new_user.user_uuid, new_name)
    assert updated_user

    assert AuthService.get_user(new_user.user_uuid).username == new_name
