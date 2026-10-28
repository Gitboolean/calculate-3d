"""catalog tables — mirror migrations 20261028_2232/_2233 (SQL there is the source of truth).

The FK to `plastics` only guards integrity; catalog code never reads that table (ADR 0005).
"""

from sqlalchemy import Column, ForeignKey, Index, Integer, Table, Text

from calculate3d.core.db import created_at_column, metadata

items = Table(
    "items",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("name_key", Text, nullable=False),
    Column("print_time_s", Integer, nullable=False),
    created_at_column(),
    Index("uq_items_name_key", "name_key", unique=True),
)

item_plastics = Table(
    "item_plastics",
    metadata,
    Column("item_id", Text, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("plastic_id", Text, ForeignKey("plastics.id", ondelete="RESTRICT"), primary_key=True),
    Column("usage_cg", Integer, nullable=False),
    created_at_column(),
    Index("idx_item_plastics_plastic_id", "plastic_id"),
)
