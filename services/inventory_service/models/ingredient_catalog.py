"""
Ingredient catalog model for raw material master data.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from database import Base


class IngredientCatalogItem(Base):
    """
    Master catalog for raw materials/ingredients.

    This table stores the canonical SKU, display name, category and
    default unit used by the Receive Stock flow.
    """

    __tablename__ = "ingredient_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    category = Column(String(20), nullable=False)
    default_unit = Column(String(10), nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<IngredientCatalogItem(id={self.id}, sku='{self.sku}', "
            f"name='{self.name}', category='{self.category}')>"
        )
