import asyncio
import json
import math
from app.db.database import AsyncSessionLocal
from app.api.crud import get_matches

async def test():
    async with AsyncSessionLocal() as session:
        matches = await get_matches(session)
        print(f"Total matches: {len(matches)}")
        for i, match in enumerate(matches):
            try:
                # Try to serialize each match individually
                json_str = json.dumps(match, default=str)
            except (ValueError, TypeError) as e:
                print(f"Error at match index {i}, match id {match.get('id')}: {e}")
                print("Match data:", match)
                # Inspect each key
                for key, val in match.items():
                    if isinstance(val, float):
                        if math.isnan(val) or math.isinf(val):
                            print(f"  {key}: {val} (problematic)")
                    try:
                        json.dumps({key: val}, default=str)
                    except (ValueError, TypeError) as e2:
                        print(f"  Key {key} value {val} causes error: {e2}")
                raise
        print("All matches serializable")

if __name__ == "__main__":
    asyncio.run(test())