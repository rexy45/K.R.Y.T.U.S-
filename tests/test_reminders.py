from krytus.reminders import (
    get_all_reminders,
    get_pending_reminders,
    init_database,
    mark_reminder_delivered,
    set_reminder,
)


def test_init_database(temp_dirs):
    init_database()
    reminders = get_all_reminders()
    assert reminders == []


def test_set_and_get_reminder(temp_dirs):
    init_database()
    result = set_reminder(0, "Test reminder")
    assert result["success"] is True
    assert "reminder_id" in result
    
    pending = get_pending_reminders()
    assert len(pending) == 1
    assert pending[0]["message"] == "Test reminder"


def test_mark_delivered_idempotent(temp_dirs):
    init_database()
    result = set_reminder(1, "Test")
    reminder_id = result["reminder_id"]
    
    first = mark_reminder_delivered(reminder_id)
    assert first is True
    
    second = mark_reminder_delivered(reminder_id)
    assert second is False
    
    pending = get_pending_reminders()
    assert len(pending) == 0


def test_get_all_reminders(temp_dirs):
    init_database()
    set_reminder(5, "First")
    set_reminder(10, "Second")
    
    all_reminders = get_all_reminders()
    assert len(all_reminders) == 2
    assert all_reminders[0]["message"] == "First"
    assert all_reminders[1]["message"] == "Second"
    assert "delivered" in all_reminders[0]


def test_pending_reminders_time_filter(temp_dirs):
    init_database()
    set_reminder(0, "Past reminder")
    
    pending = get_pending_reminders()
    assert len(pending) == 1
    assert pending[0]["message"] == "Past reminder"
