import soccerdata as sd
import soccerdata.fbref
import traceback

# Patch headers
soccerdata.fbref.FBREF_HEADERS.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

print("Testing FBref with patched headers")
try:
    fbref = sd.FBref(leagues="ITA-Serie A", seasons="2425")
    print("FBref created")
    schedule = fbref.read_schedule()
    print("Schedule shape:", schedule.shape)
    print("Columns:", schedule.columns.tolist())
except Exception as e:
    print("Error:", e)
    traceback.print_exc()