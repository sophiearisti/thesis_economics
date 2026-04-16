import numpy as np
import pandas as pd
from esda.moran import Moran_Rate
from esda.smoothing import Empirical_Bayes

# Sample data: Events (deaths) and Population at risk
events = np.array([1, 50, 9, 100, 2])
population = np.array([10, 1000, 100, 2000, 5])

# Initialize the Empirical Bayes smoother
eb = Empirical_Bayes(events, population)

# The smoothed rates are stored in the .r attribute
smoothed_rates = eb.r

print("Original Rates:", events / population)
print("EB Smoothed Rates:", smoothed_rates)