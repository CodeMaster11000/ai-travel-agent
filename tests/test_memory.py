import app.tools.memory as memory


def test_memory_save_update_read_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DB_FILE", tmp_path / "memory.db")

    assert memory.save_memory("user1", "preferred_category", "Fort")["success"]
    assert memory.save_memory("user1", "PREFERRED_CATEGORY", "Museum")["success"]

    records = memory.get_memories("user1")
    assert len(records) == 1
    assert records[0]["memory_key"] == "preferred_category"
    assert records[0]["memory_value"] == "Museum"

    assert memory.delete_memory("user1", "preferred_category")["success"]
    assert memory.get_memories("user1") == []


def test_memory_rejects_empty_values():
    import pytest
    import app.tools.memory as memory_module

    with pytest.raises(ValueError):
        memory_module.save_memory("", "key", "value")
