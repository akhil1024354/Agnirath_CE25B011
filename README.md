# Agnirath_CE25B011
THE FINAL CHALLENGE:
Question 1: Phase 1: The Cartographer (Data Pipeline)
1) The Route API 
 I have utilized both OSRM and Open Elevation to map the route from Sasolburg to Zeerust. The OSRM gives us the route data from Sasolburg to Zeerust using the gps (lat, lon) of both the cities, then after gathering the gps data using OSRM i have used Open Elevation to get the altitude data of of all these gps data points.
I initially tried to take a resolution of 50 metres which gives us a data set of 6667 points, but when I tried doing this due to the large number of requests the server was blocking my request halfway. So i routed to taking a resolution of 250 m from the OSRM and the Open Elevation and then upscaled it locally on my system. This created no problem in the data because, Open Elevation however does not provide 50 metre resolution, it also upscaled 90 metre resolution to give us 50 m resolution. 
The obvious thing here is 90m vs 250 m resolution, but it doesn't matter much as the roads anywhere in this world are designed to have a gradual slope increase if there is a hill ahead, hence it is very rarely that we observe a slove variation in 90m that we weren't able to using 250m.
2)The solar model
The solar prediction model we have built is a purely mathematical prediction with the assumption that there is no effect of weather on the solar irradiance. It only takes into consideration the maximum solar irradiance and the angle between the panel and the sun.
This prediction uses the formula 

here, : The solar irradiance at a specific time  (measured in ).
: The maximum peak irradiance hitting the panels at solar noon ().
: The current time of day in seconds.
 (Mean Time): The exact time of solar noon, which centers the peak of the curve ( seconds, or 12:00 PM).
 (Standard Deviation): standard deviation of spread of width of say light
Phase 2: 
I have used the SLSQP optimiser as it is the most easy optimiser to implement that is also effective in our use case.
The objective of our optimiser i first took was to save on energy, the result for this objective was that the car was taking the absolute limit of the time it is being given to cover the distance i.e. 9 hrs, and the charge it stored in the battery was 297%, this obvious error was due to the battery and velocity limits being soft constraints.
After that i changed up my code and converted the battery cap to 100 percent, now again the problem was that it was taking up as much time as it was given to complete the race, the car was running at more or less 60kmph throughout the race to save on energy.
Then after this i ended up realizing that our objective is not to minimise the energy but to minimise the time after which i changed the objective to find good results, the car was completing the race in 3 smg hours. The problem with this though is that the final battery percentage is barely above 20 % so any unexpected factors such as a sudden gush of wind can make our car fail.
I could not run a proper simulation with initial velocity 0 as the optimiser then easily going out of bounds of the velocity limits even when not necessary.
My plan to make the optimiser better is to implement a soft constrain not at 20 percent but at 30 such that even if any unexpected factors interfere with the car, our car wont be disqualified.
