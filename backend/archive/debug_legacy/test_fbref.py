import soccerdata as sd
import traceback

try:
    print("Testing FBref with ITA-Serie A season 2425")
    fbref = sd.FBref(leagues="ITA-Serie A", seasons="2425")
    print("FBref created")
    schedule = fbref.read_schedule()
    print("Schedule shape:", schedule.shape)
    print("Columns:", schedule.columns.tolist())
except Exception as e:
    print("Error:", e)
    traceback.print_exc()