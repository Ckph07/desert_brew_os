"""
Race condition test for concurrent FIFO allocations.

Este test verifica que el locking pesimista funciona correctamente.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.stock import StockBatch
from logic.stock_rotation import allocate_stock_fifo, InsufficientStockError


TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def concurrent_db():
    """Setup database for concurrent testing."""
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    
    # Create initial stock
    session = Session()
    batch = StockBatch(
        sku="MALT-PALE-2ROW",
        batch_number="CONCURRENT-TEST",
        category="MALT",
        initial_quantity=Decimal("100"),
        remaining_quantity=Decimal("100"),
        unit_measure="KG",
        unit_cost=Decimal("18"),
        total_cost=Decimal("1800")
    )
    session.add(batch)
    session.commit()
    session.close()
    
    yield engine, Session
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def allocate_in_thread(session_factory, thread_id):
    """
    Function to run in separate thread.
    Attempts to allocate 30kg.
    """
    session = session_factory()
    try:
        allocations = allocate_stock_fifo(
            sku="MALT-PALE-2ROW",
            amount_needed=Decimal("30"),
            session=session
        )
        session.commit()
        return {
            "thread_id": thread_id,
            "success": True,
            "allocations": allocations
        }
    except InsufficientStockError as e:
        session.rollback()
        return {
            "thread_id": thread_id,
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        session.rollback()
        return {
            "thread_id": thread_id,
            "success": False,
            "error": f"Unexpected: {str(e)}"
        }
    finally:
        session.close()


def test_concurrent_allocations_no_oversell(concurrent_db):
    """
    CRITICAL: Verificar que el locking evita overselling.
    
    Escenario:
    - Stock inicial: 100kg
    - 5 threads intentan asignar 30kg cada uno
    - Solo 3 deben tener éxito (3 * 30 = 90kg)
    - Los otros 2 deben fallar con InsufficientStockError
    
    Sin locking adecuado, podríamos asignar 150kg de un stock de 100kg.
    """
    engine, Session = concurrent_db
    
    # Launch 5 concurrent allocations
    num_threads = 5
    results = []
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(allocate_in_thread, Session, i)
            for i in range(num_threads)
        ]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    # Assertions
    # Exactly 3 should succeed (90kg total)
    assert len(successful) == 3, f"Expected 3 successes, got {len(successful)}"
    
    # The other 2 should fail with insufficient stock
    assert len(failed) == 2, f"Expected 2 failures, got {len(failed)}"
    
    # Verify final database state
    session = Session()
    final_batch = session.query(StockBatch).filter(
        StockBatch.sku == "MALT-PALE-2ROW"
    ).first()
    
    # Should have 10kg remaining (100 - 90)
    assert final_batch.remaining_quantity == Decimal("10"), \
        f"Expected 10kg remaining, got {final_batch.remaining_quantity}"
    
    session.close()
    
    print(f"\n✓ Race condition test passed:")
    print(f"  - Successful allocations: {len(successful)}")
    print(f"  - Failed allocations: {len(failed)}")
    print(f"  - Final remaining: {final_batch.remaining_quantity}kg")
