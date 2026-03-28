from __future__ import annotations

import logging
import threading
import time

from app.db.session import SessionLocal
from app.db.models import Image
from app.db.repo import Repository
from app.pipeline.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _recover_stuck():
    session = SessionLocal()
    try:
        repo = Repository(session, Image)
        stuck = repo.list(limit=1000, processing_status="processing")
        for img in stuck:
            img.processing_status = "pending"
        if stuck:
            session.commit()
            logger.info(f"Recovered {len(stuck)} stuck images back to pending")
    except Exception as e:
        logger.warning(f"Recovery failed: {e}")
    finally:
        session.close()


def _process_pending():
    _recover_stuck()
    orchestrator = get_orchestrator()

    logger.info("Worker started (sequential images, parallel pipeline steps)")

    idle_rounds = 0
    while not _stop_event.is_set():
        session = SessionLocal()
        try:
            repo = Repository(session, Image)

            faces_pending = repo.list(limit=1, processing_status="faces_pending")
            if faces_pending:
                idle_rounds = 0
                image = faces_pending[0]
                logger.info(f"Re-detecting faces: {image.file_path}")
                image.processing_status = "processing"
                session.commit()
                try:
                    orchestrator.reprocess_faces(session, image.id, image.file_path)
                    image.processing_status = "completed"
                    session.commit()
                except Exception as e:
                    logger.warning(f"Face reprocess failed for {image.file_path}: {e}")
                    image.processing_status = "completed"
                    try:
                        session.commit()
                    except Exception:
                        session.rollback()
                session.close()
                continue

            pending = repo.list(limit=1, processing_status="pending")
            if not pending:
                session.close()
                idle_rounds += 1
                wait = min(5 * idle_rounds, 30)
                _stop_event.wait(timeout=wait)
                if idle_rounds >= 12:
                    logger.info("Worker idle for 60s+, stopping")
                    break
                continue

            idle_rounds = 0
            image = pending[0]
            logger.info(f"Processing: {image.file_path}")
            image.processing_status = "processing"
            session.commit()

            try:
                orchestrator.process_image(session, image.file_path)
            except Exception as e:
                logger.exception(f"Processing failed for {image.file_path}: {e}")
                image.processing_status = "failed"
                try:
                    session.commit()
                except Exception:
                    session.rollback()

        except Exception as e:
            logger.exception(f"Worker error: {e}")
            time.sleep(2)
        finally:
            session.close()


def start_worker():
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    _stop_event.clear()
    _worker_thread = threading.Thread(target=_process_pending, daemon=True, name="pipeline-worker")
    _worker_thread.start()
    logger.info("Background processing worker started")


def stop_worker():
    _stop_event.set()
    if _worker_thread:
        _worker_thread.join(timeout=10)
    logger.info("Background processing worker stopped")


def is_worker_running() -> bool:
    return _worker_thread is not None and _worker_thread.is_alive()
