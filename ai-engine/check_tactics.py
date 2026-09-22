import json 
f = open('models/saved/robustness_report.json') 
r = json.load(f) 
for tactic, stats in r['detection_rate_by_tactic'].items(): 
    print(tactic, stats['rate'], stats['n']) 
