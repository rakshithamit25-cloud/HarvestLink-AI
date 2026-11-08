from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import ProduceListing, MatchResult, Order, User

class ImpactService:
    @staticmethod
    def get_metrics(db: Session) -> dict:
        """
        Computes impact metrics strictly from separate database records.
        Does NOT merge matched, paid, and delivered quantities.
        'waste prevented (verified)' strictly corresponds to delivered_quantity.
        """
        # 1. Total listed quantity
        listed_qty = db.query(func.coalesce(func.sum(ProduceListing.quantity), 0.0)).scalar() or 0.0
        
        # 2. Matched quantity (proposed, farmer_approved, buyer_approved, confirmed)
        matched_qty = db.query(
            func.coalesce(func.sum(MatchResult.allocated_quantity), 0.0)
        ).filter(MatchResult.status.in_(["proposed", "farmer_approved", "buyer_approved", "confirmed"])).scalar() or 0.0

        # 3. Confirmed & paid quantity
        confirmed_qty = db.query(
            func.coalesce(func.sum(Order.quantity), 0.0)
        ).filter(Order.payment_status == "completed").scalar() or 0.0

        # 4. Delivered quantity (only after explicit delivery verification)
        delivered_qty = db.query(
            func.coalesce(func.sum(Order.quantity), 0.0)
        ).filter(Order.order_status == "delivered").scalar() or 0.0

        # 5. Remaining unsold inventory
        remaining_unsold = db.query(
            func.coalesce(func.sum(ProduceListing.available_quantity), 0.0)
        ).scalar() or 0.0

        # Counts
        active_farmers = db.query(User).filter(User.role == "farmer").count()
        active_buyers = db.query(User).filter(User.role == "buyer").count()

        # Total transaction value ($ USD)
        total_val = db.query(
            func.coalesce(func.sum(Order.total_amount), 0.0)
        ).filter(Order.payment_status == "completed").scalar() or 0.0

        return {
            "listed_quantity": round(float(listed_qty), 2),
            "matched_quantity": round(float(matched_qty), 2),
            "confirmed_quantity": round(float(confirmed_qty), 2),
            "delivered_quantity": round(float(delivered_qty), 2),
            "remaining_unsold_quantity": round(float(remaining_unsold), 2),
            "waste_prevented_verified_kg": round(float(delivered_qty), 2),
            "is_simulated_demo": True,
            "active_farmers_count": active_farmers,
            "active_buyers_count": active_buyers,
            "total_value_usd": round(float(total_val), 2)
        }
