import datetime
import unittest
from unittest import mock

import pytest

from transiter import models, exceptions
from transiter.data.dams import feeddam, systemdam
from transiter.services import feedservice, views
from .. import testutil

SYSTEM_ID = "1"
FEED_ONE_ID = "2"
FEED_ONE_PK = 3
FEED_ONE_AUTO_UPDATE_PERIOD = 500
FEED_TWO_AUTO_UPDATE_PERIOD = -1
FEED_TWO_ID = "4"


@pytest.fixture
def system():
    return models.System(id=SYSTEM_ID)


@pytest.fixture
def feed_1(system):
    return models.Feed(
        id=FEED_ONE_ID, auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD, system=system
    )


@pytest.fixture
def feed_2(system):
    return models.Feed(
        id=FEED_TWO_ID, auto_update_period=FEED_TWO_AUTO_UPDATE_PERIOD, system=system
    )


def test_list_all_auto_updating(monkeypatch, feed_1):
    monkeypatch.setattr(feeddam, "list_all_auto_updating", lambda: [feed_1])

    expected = [feedservice.Feed(SYSTEM_ID, FEED_ONE_ID, FEED_ONE_AUTO_UPDATE_PERIOD)]

    actual = feedservice.list_all_auto_updating()

    assert expected == actual


def test_list_all_in_system__no_such_system(monkeypatch):
    monkeypatch.setattr(systemdam, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.list_all_in_system(SYSTEM_ID)


def test_list_all_in_system(monkeypatch, system, feed_1, feed_2):
    monkeypatch.setattr(systemdam, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(feeddam, "list_all_in_system", lambda *args: [feed_1, feed_2])

    expected = [
        views.Feed(
            id=FEED_ONE_ID,
            auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD,
            _system_id=SYSTEM_ID,
        ),
        views.Feed(
            id=FEED_TWO_ID,
            auto_update_period=FEED_TWO_AUTO_UPDATE_PERIOD,
            _system_id=SYSTEM_ID,
        ),
    ]

    actual = feedservice.list_all_in_system(SYSTEM_ID)

    assert actual == expected


def test_get_in_system_by_id(monkeypatch, feed_1):
    monkeypatch.setattr(feeddam, "get_in_system_by_id", lambda *args: feed_1)

    expected = views.FeedLarge(
        id=FEED_ONE_ID,
        auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD,
        _system_id=SYSTEM_ID,
        updates=views.UpdatesInFeedLink(_feed_id=FEED_ONE_ID, _system_id=SYSTEM_ID),
    )

    actual = feedservice.get_in_system_by_id(SYSTEM_ID, FEED_ONE_ID)

    assert expected == actual


def test_get_in_system_by_id__no_such_feed(monkeypatch):
    monkeypatch.setattr(feeddam, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.get_in_system_by_id(SYSTEM_ID, FEED_ONE_ID),


class TestFeedService(testutil.TestCase(feedservice), unittest.TestCase):

    SYSTEM_ID = "1"
    FEED_ONE_ID = "2"
    FEED_ONE_PK = 3
    FEED_ONE_AUTO_UPDATE_PERIOD = 500
    FEED_TWO_AUTO_UPDATE_PERIOD = -1
    FEED_TWO_ID = "4"

    def setUp(self):
        self.feeddam = self.mockImportedModule(feedservice.feeddam)
        self.systemdam = self.mockImportedModule(feedservice.systemdam)
        self.updatemanager = self.mockImportedModule(feedservice.updatemanager)

        self.system = models.System()
        self.system.id = self.SYSTEM_ID

        self.feed_one = models.Feed()
        self.feed_one.pk = self.FEED_ONE_PK
        self.feed_one.id = self.FEED_ONE_ID
        self.feed_one.system = self.system

        self.feed_two = models.Feed()
        self.feed_two.id = self.FEED_TWO_ID
        self.feed_two.system = self.system

        self.feed_update_one = models.FeedUpdate(feed=self.feed_one)
        self.feed_update_two = models.FeedUpdate(feed=self.feed_one)

    def test_create_feed_update(self):
        """[Feed service] Create a feed update"""
        self.updatemanager.create_feed_update.return_value = 3

        expected = 3

        actual = feedservice.create_and_execute_feed_update(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )

        self.assertEqual(actual, expected)

    def test_create_feed_update__no_such_feed(self):
        """[Feed service] Create a feed update - no such feed"""
        self.updatemanager.create_feed_update.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.create_and_execute_feed_update(
                self.SYSTEM_ID, self.FEED_ONE_ID
            ),
        )

    def test_list_updates_in_feed(self):
        """[Feed service] List updates in a feed"""
        self.feeddam.get_in_system_by_id.return_value = self.feed_one
        self.feeddam.list_updates_in_feed.return_value = [
            self.feed_update_one,
            self.feed_update_two,
        ]

        expected = [
            self.feed_update_one.to_dict(),
            self.feed_update_two.to_dict(),
        ]

        actual = feedservice.list_updates_in_feed(self.SYSTEM_ID, self.FEED_ONE_ID)

        self.assertListEqual(actual, expected)

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )
        self.feeddam.list_updates_in_feed.assert_called_once_with(self.FEED_ONE_PK)

    def test_list_updates_in_feed__no_such_feed(self):
        """[Feed service] List updates in a feed - no such feed"""
        self.feeddam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.list_updates_in_feed(self.SYSTEM_ID, self.FEED_ONE_ID),
        )

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )


@pytest.mark.parametrize(
    "feed_pks", [pytest.param([]), pytest.param([1]), pytest.param([1, 2])],
)
def test_trip_feed_updates(monkeypatch, datetime_now, feed_pks):

    before_datetime = datetime.datetime(
        year=datetime_now.year,
        month=datetime_now.month,
        day=datetime_now.day,
        hour=datetime_now.hour - 1,
        minute=datetime_now.minute,
        second=0,
        microsecond=0,
    )

    dam_trip_feed_updates = mock.Mock()
    monkeypatch.setattr(feeddam, "list_all_feed_pks", lambda: feed_pks)
    monkeypatch.setattr(feeddam, "trim_feed_updates", dam_trip_feed_updates)

    feedservice.trim_feed_updates()

    if len(feed_pks) == 0:
        dam_trip_feed_updates.assert_not_called()
    else:
        dam_trip_feed_updates.assert_has_calls(
            [mock.call(feed_pk, before_datetime) for feed_pk in feed_pks]
        )
