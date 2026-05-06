#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from app.db.models import Match
from app.db.database import Base
from sqlalchemy import inspect

print("Match.__table__:", Match.__table__)
print("Columns:", [c.name for c in Match.__table__.c])
print("Primary keys:", [c.name for c in Match.__table__.primary_key])
print("All column objects:", Match.__table__.c)

print("\nInspecting Base.metadata.tables['matches']:")
if 'matches' in Base.metadata.tables:
    table = Base.metadata.tables['matches']
    print("Table columns:", [c.name for c in table.c])
else:
    print("Table not found in metadata")

print("\nChecking mapper:")
from sqlalchemy.orm import class_mapper
try:
    mapper = class_mapper(Match)
    print("Mapper columns:", [c.key for c in mapper.columns])
except Exception as e:
    print("Mapper error:", e)

print("\nChecking if understat_id exists in Match.__dict__:", 'understat_id' in Match.__dict__)
print("Match.__dict__.keys():", list(Match.__dict__.keys()))

# Check if there is another Match class somewhere
import app.db.models as models
print("\nModule models attributes:", [attr for attr in dir(models) if not attr.startswith('_')])