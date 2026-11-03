"""pricing tables — mirror migrations 20261028_2230/_2231 (SQL there is the source of truth)."""

from sqlalchemy import Column, Index, Integer, Table, Text

from calculate3d.core.db import created_at_column, metadata

plastics = Table(
    "plastics",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("name_key", Text, nullable=False),
    Column("price_per_kg_kop", Integer, nullable=False),
    created_at_column(),
    Index("uq_plastics_name_key", "name_key", unique=True),
)

# Singleton: no row = «not set» (AC-09); the app always writes SETTINGS_ID.
price_settings = Table(
    "price_settings",
    metadata,
    Column("id", Text, primary_key=True),
    Column("tariff_per_kwh_kop", Integer, nullable=False),
    Column("printer_power_w", Integer, nullable=False),
    Column("printer_price_kop", Integer, nullable=False),
    Column("printer_lifetime_h", Integer, nullable=False),
    Column("parts_per_hour_kop", Integer, nullable=False),
    Column("scrap_rate_permille", Integer, nullable=False),
    created_at_column(),
)
