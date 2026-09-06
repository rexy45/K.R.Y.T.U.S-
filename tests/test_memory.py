from krytus.memory import get_recent_memories, recall_memory, save_memory


def test_save_and_recall_memory(temp_dirs):
    result = save_memory("architecture", "We decided to use PostgreSQL for the analytics DB")
    assert result["success"] is True
    
    result = recall_memory("PostgreSQL analytics", n_results=3)
    assert result["success"] is True
    assert len(result["memories"]) == 1
    assert "PostgreSQL" in result["memories"][0]["content"]
    assert result["memories"][0]["topic"] == "architecture"


def test_recall_empty(temp_dirs):
    result = recall_memory("nonexistent topic")
    assert result["success"] is True
    assert result["memories"] == []


def test_multiple_memories(temp_dirs):
    save_memory("bug-fix", "Fixed memory leak in worker process")
    save_memory("decision", "Switched from Redis to Dragonfly for caching")
    save_memory("architecture", "Adopted event-driven architecture for notifications")
    
    result = recall_memory("caching", n_results=2)
    assert result["success"] is True
    assert len(result["memories"]) == 1
    assert "caching" in result["memories"][0]["content"].lower()


def test_get_recent_memories(temp_dirs):
    save_memory("topic1", "Note 1")
    save_memory("topic2", "Note 2")
    save_memory("topic3", "Note 3")
    
    result = get_recent_memories(5)
    assert result["success"] is True
    assert len(result["memories"]) == 3
    assert result["memories"][0]["topic"] == "topic3"
    assert result["memories"][2]["topic"] == "topic1"
