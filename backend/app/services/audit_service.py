import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import AuditLog, User

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        actor_id: int,
        actor_role: str,
        consent_method: Optional[str] = None,
        farmer_name: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            consent_method=consent_method,
            farmer_name=farmer_name,
            details=details,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def verify_and_log_operator_consent(
        db: Session,
        operator_user: User,
        farmer_name: str,
        consent_method: str,
        action: str,
        details: Optional[str] = None
    ) -> AuditLog:
        """
        Enforces strict FPO operator consent recording.
        consent_method must be 'verbal' or 'written'.
        farmer_name must not be empty.
        Raises HTTP 400 if validation fails.
        """
        if operator_user.role != "operator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only certified FPO operators may perform proxy actions."
            )
            
        if not consent_method or consent_method.lower() not in ["verbal", "written"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit farmer consent is required. consent_method must be 'verbal' or 'written'."
            )
            
        if not farmer_name or not farmer_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farmer name is required to record operator proxy consent."
            )

        return AuditService.log_action(
            db=db,
            action=f"OPERATOR_PROXY_{action}",
            actor_id=operator_user.id,
            actor_role=operator_user.role,
            consent_method=consent_method.lower(),
            farmer_name=farmer_name.strip(),
            details=details
        )
