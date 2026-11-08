from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import ProduceListing

class InsufficientStockException(Exception):
    pass

class InventoryService:
    @staticmethod
    def reserve_stock(db: Session, listing_id: int, quantity_to_reserve: float) -> bool:
        """
        Atomically decrements available_quantity using a conditional UPDATE query.
        Works identically on SQLite and PostgreSQL.
        Guarantees that allocated quantity never exceeds available inventory.
        """
        if quantity_to_reserve <= 0:
            return False

        # Execute conditional atomic update checking row count
        stmt = text(
            "UPDATE produce_listings "
            "SET available_quantity = available_quantity - :q "
            "WHERE id = :id AND available_quantity >= :q"
        )
        result = db.execute(stmt, {"q": quantity_to_reserve, "id": listing_id})
        
        # In both SQLite and PostgreSQL, rowcount is 1 if condition was satisfied, 0 otherwise
        if result.rowcount == 1:
            # Update listing status if fully reserved
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
            if listing:
                if listing.available_quantity <= 0.001:
                    listing.listing_status = "fully_matched"
                else:
                    listing.listing_status = "partially_matched"
            db.commit()
            return True
        else:
            db.rollback()
            raise InsufficientStockException(
                f"Cannot allocate {quantity_to_reserve} kg: insufficient stock on listing {listing_id}."
            )

    @staticmethod
    def release_stock(db: Session, listing_id: int, quantity_to_release: float) -> bool:
        """
        Atomically restores stock if a match or reservation is cancelled or rejected.
        """
        if quantity_to_release <= 0:
            return False

        stmt = text(
            "UPDATE produce_listings "
            "SET available_quantity = available_quantity + :q "
            "WHERE id = :id"
        )
        result = db.execute(stmt, {"q": quantity_to_release, "id": listing_id})
        if result.rowcount == 1:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
            if listing:
                if listing.available_quantity >= listing.quantity:
                    listing.listing_status = "active"
                else:
                    listing.listing_status = "partially_matched"
            db.commit()
            return True
        else:
            db.rollback()
            return False
