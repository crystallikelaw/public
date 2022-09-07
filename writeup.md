# Disentangling Traffic:Data Driven Approaches to Road Safety
###  Kapilan Mahalingam, September 2022

## Abstract
The goal of the project is to identify trends in traffic accidents to identify locations and features that correlate with higher accident rates/severity. A week's worth of data from [kaggle](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) was used to determine the most accident prone states and cities, as well as locations with anomalously high pedestrian crossing accidents.

### Design
I'm limiting observations to cities/zip codes with at least 7 accidents in the week of January 1st, 2021 (to limit the variance of per capita figures). I also only use cities/towns with population reported in the 2021 census.

### Data
I used the above data, as well as population data from the 2021 census [from here](https://www.kaggle.com/datasets/darinhawley/us-2021-census-cities-populations-coordinates) to determine per capita figures.

### Tools
I used Excel for EDA and to stitch the population figures with the rest of the data. I did the rest in Tableau. I used python to extract the data from the initial dataset, as it was too large to load in Excel.

### Communication
I've attached my Tableau dashboard

### Results
I identified a few locations of interest, which might be beneficial to explore. Other than that, a fixed effects model would be a good first step forward, rather than just exploring the data visually. Additionally, using more data is rather important, preliminary regressions were terrible due to the paucity of observations, the numerous cities with 0 or 1 accident means city/state/roadway/point-of-interest level fixed effects were remarkably imprecise.
