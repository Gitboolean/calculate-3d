"""importing tables — mirror migration 20261110_2110 (SQL there is the source of truth).

The FK to `plastics` only guards integrity and cascades the delete (AC-11); importing never reads
that table (ADR 0005).
"""

from sqlalchemy import Column, ForeignKey, Index, Table, Text

from calculate3d.core.db import created_at_column, metadata

filament_mappings = Table(
    "filament_mappings",
    metadata,
    Column("id", Text, primary_key=True),
    Column("filament_name", Text, nullable=False),
    Column("filament_color", Text, nullable=False),
    Column("plastic_id", Text, ForeignKey("plastics.id", ondelete="CASCADE"), nullable=False),
    created_at_column(),
    Index("uq_filament_mappings_name_color", "filament_name", "filament_color", unique=True),
    Index("idx_filament_mappings_plastic_id", "plastic_id"),
)
