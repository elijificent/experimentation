# pylint: disable=missing-docstring
import uuid

from src.app import DbClient, User
from src.env import EnvStage

client = DbClient(EnvStage.TESTING)


def test_user_initialization():
    user = User(
        username="test_user", hashed_password="123456", random_salt="pepper", db=client
    )

    assert user.username == "test_user"
    assert user.hashed_password == "123456"
    assert user.random_salt == "pepper"
    assert user.user_uuid is not None
    assert user.db is not None


def test_user_creation_and_read():
    user_uuid = User.create(username="test_user", password="123456", db=client)

    user = User.read(user_uuid, db=client)

    assert user.username == "test_user"
    assert user.hashed_password is not None
    assert user.random_salt is not None
    assert user.user_uuid is not None
    assert user.db == client


def test_user_update():
    user_uuid = User.create(username="test_user", password="123456", db=client)

    updated = User.update(user_uuid, username="new_user", db=client)

    assert updated

    user = User.read(user_uuid, db=client)

    assert user.username == "new_user"

    not_a_user = User.update(uuid.uuid4(), username="new_user", db=client)
    assert not not_a_user


def test_user_delete():
    user_uuid = User.create(username="test_user", password="123456", db=client)

    deleted = User.delete(user_uuid, db=client)
    assert deleted

    user = User.read(user_uuid, db=client)

    assert user is None


def test_user_login():
    user_uuid = User.create(username="test_user", password="123456", db=client)

    bad_pass = User.authenticate(user_uuid=user_uuid, password="invalid", db=client)

    assert not bad_pass

    good_pass = User.authenticate(user_uuid=user_uuid, password="123456", db=client)

    assert good_pass
