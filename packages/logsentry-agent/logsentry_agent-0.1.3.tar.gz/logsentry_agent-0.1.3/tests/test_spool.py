from pathlib import Path

from logsentry_agent.spool import SpoolQueue


def test_spool_enqueue_and_dequeue(tmp_path: Path):
    spool = SpoolQueue(tmp_path / "spool.db", max_mb=1)
    payload = {"events": [{"source": "test"}]}
    spool.enqueue(payload)

    batch = spool.dequeue_batch(10)
    assert len(batch) == 1
    row_id, stored = batch[0]
    assert stored == payload

    spool.delete([row_id])
    assert spool.pending_count() == 0
