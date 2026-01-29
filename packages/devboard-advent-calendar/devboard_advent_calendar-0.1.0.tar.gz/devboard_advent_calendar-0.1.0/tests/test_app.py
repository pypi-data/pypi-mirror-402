import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from haxmas_day_9_Hasona57.main import DeveloperAdventApp, DEV_CHALLENGES
import datetime

def test_dev_challenges_length():
    assert len(DEV_CHALLENGES) == 24

def test_start_date_type():
    assert isinstance(DeveloperAdventApp.START_DATE, datetime.date)

def test_day_challenges_content():
    for key, value in DEV_CHALLENGES.items():
        assert len(value) == 3
