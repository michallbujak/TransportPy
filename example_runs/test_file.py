import pandas as pd

nyc = pd.read_csv(r"C:\Users\szmat\Documents\GitHub\TransportPy\data\vehicles\NYC\NYC_100.csv")
nyc["speed"] = 6

nyc.to_csv(r"C:\Users\szmat\Documents\GitHub\TransportPy\data\vehicles\NYC\NYC_100.csv")
