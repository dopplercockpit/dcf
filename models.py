from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text, String

from db import Base


class ValuationRun(Base):
    __tablename__ = "valuation_runs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ticker = Column(String(16), nullable=False)
    assumptions_json = Column(Text, nullable=False)
    results_json = Column(Text, nullable=False)
    intrinsic_value_per_share = Column(Float, nullable=True)
    stressed_intrinsic_value_per_share = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    upside_pct = Column(Float, nullable=True)
    esg_total = Column(Float, nullable=True)
    data_quality = Column(String(32), nullable=True)
