"""Token usage management and capping."""

import logging
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import User

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage information."""
    current_balance: int
    requested: int
    remaining: int
    allowed: int


class TokenCapError(Exception):
    """Raised when token limit exceeded."""
    pass


class TokenManager:
    """Manages token usage and capping."""
    
    # Default limits
    DEFAULT_DAILY_LIMIT = 1000
    DEFAULT_REQUEST_LIMIT = 100
    
    # Request-specific costs
    REQUEST_COSTS = {
        "quiz": 50,
        "exercise": 30,
        "lesson_plan": 40,
        "term_outline": 60,
        "homework": 20,
        "correction": 25,
        "explain": 15,
        "tutor": 10,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_balance(self, user_id: int) -> int:
        """Get user's current token balance."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.token_balance or 0
    
    def check_and_deduct(
        self,
        user_id: int,
        action: str,
        custom_cost: Optional[int] = None,
    ) -> TokenUsage:
        """Check balance and deduct tokens.
        
        Args:
            user_id: User ID
            action: Action type (quiz, exercise, etc.)
            custom_cost: Override default cost
        
        Raises:
            TokenCapError: If insufficient tokens
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise TokenCapError("User not found")
        
        current_balance = user.token_balance or 0
        cost = custom_cost or self.REQUEST_COSTS.get(action, self.DEFAULT_REQUEST_LIMIT)
        
        if current_balance < cost:
            raise TokenCapError(
                f"Insufficient tokens. Have {current_balance}, need {cost}. "
                f"Purchase more tokens to continue."
            )
        
        # Deduct tokens
        user.token_balance = current_balance - cost
        self.db.commit()
        
        return TokenUsage(
            current_balance=user.token_balance,
            requested=cost,
            remaining=user.token_balance,
            allowed=self.DEFAULT_DAILY_LIMIT,
        )
    
    def add_tokens(
        self,
        user_id: int,
        amount: int,
        reason: str = "purchase",
    ) -> int:
        """Add tokens to user balance."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise TokenCapError("User not found")
        
        current = user.token_balance or 0
        user.token_balance = current + amount
        self.db.commit()
        
        logger.info(f"Added {amount} tokens to user {user_id}: {reason}")
        return user.token_balance
    
    def refund_tokens(
        self,
        user_id: int,
        amount: int,
        reason: str = "refund",
    ) -> int:
        """Refund tokens to user (on failure)."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise TokenCapError("User not found")
        
        current = user.token_balance or 0
        user.token_balance = current + amount
        self.db.commit()
        
        logger.info(f"Refunded {amount} tokens to user {user_id}: {reason}")
        return user.token_balance
    
    def get_action_cost(self, action: str) -> int:
        """Get cost for action."""
        return self.REQUEST_COSTS.get(action, self.DEFAULT_REQUEST_LIMIT)


def create_token_manager(db: Session) -> TokenManager:
    """Factory function to create token manager."""
    return TokenManager(db)