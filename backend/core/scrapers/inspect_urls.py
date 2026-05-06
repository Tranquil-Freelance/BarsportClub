import understat
print(understat.MATCH_URL if hasattr(understat, 'MATCH_URL') else 'No MATCH_URL')
import understat.utils
print(understat.utils.PATTERN if hasattr(understat.utils, 'PATTERN') else 'No PATTERN')