import concurrent.futures
from app.models import ProduceListing, User
from app.services.inventory_service import InventoryService, InsufficientStockException
from tests.conftest import TestingSessionLocal

def attempt_reserve(listing_id: int, qty: float):
    db = TestingSessionLocal()
    success = False
    try:
        InventoryService.reserve_stock(db, listing_id, qty)
        success = True
    except InsufficientStockException:
        success = False
    finally:
        db.close()
    return success

def test_simultaneous_allocation_never_exceeds_stock(db_session):
    kumar = db_session.query(User).filter(User.role == "farmer").first()
    
    # Create listing with exactly 100 kg
    listing = ProduceListing(
        farmer_id=kumar.id,
        crop_name="Tomato",
        quantity=100.0,
        available_quantity=100.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    listing_id = listing.id

    # 5 concurrent threads each attempt to reserve 30 kg (Total attempted = 150 kg, Available = 100 kg)
    # At most 3 can succeed (3 * 30 = 90 kg), 2 MUST fail.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(attempt_reserve, listing_id, 30.0) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    successes = [r for r in results if r is True]
    failures = [r for r in results if r is False]

    assert len(successes) == 3, f"Expected exactly 3 successful allocations, got {len(successes)}"
    assert len(failures) == 2, f"Expected 2 rejections due to atomic bounds, got {len(failures)}"

    db_session.refresh(listing)
    assert listing.available_quantity == 10.0, f"Expected remaining stock 10.0 kg, got {listing.available_quantity}"
    assert listing.available_quantity >= 0, "Inventory must never drop below zero!"
