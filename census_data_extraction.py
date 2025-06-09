from census import Census
from us import states
from fuzzywuzzy import process
import pandas as pd

def fetch_census_data(place_names, api_key):
    """
    Fetches population, median income, mean income, and education data from the Census API
    for a given list of Illinois place names using fuzzy matching.

    Args:
        place_names (list): List of city or village names as strings.
        api_key (str): Your U.S. Census API key.

    Returns:
        pandas.DataFrame: DataFrame containing the census data for matched places.
    """
    c = Census(api_key)

    # Step 1: Get all place names and GEOIDs in Illinois
    il_places = c.acs5.get(['NAME'], {'for': 'place:*', 'in': f'state:{states.IL.fips}'}, year=2020)
    name_to_geo = {
        entry['NAME'].replace(", Illinois", "").replace(" village", "").replace(" city", ""): entry['place']
        for entry in il_places
    }

    def normalize_name(name):
        return name.lower().replace("village of ", "").replace("city of ", "").replace(",", "").strip()

    # Normalize the lookup dict
    name_to_geo_normalized = {normalize_name(name): geo for name, geo in name_to_geo.items()}

    # Step 2: Fuzzy match input names
    matched = {}
    for name in place_names:
        best_match, score = process.extractOne(normalize_name(name), name_to_geo_normalized.keys())
        if score >= 80:
            matched[name] = name_to_geo_normalized[best_match]

    # Step 3: Define desired ACS variables
    variables = {
        # Population
        "population": "B01003_001E",  # total population
        
        # Income metrics
        "median_income": "B19013_001E",  # median household income
        "aggregate_income": "B19025_001E",  # household income
        "per_capita_income": "B19301_001E",  # per capita income
        # "mean_income": "B19017_001E",  # mean income
        
        # Poverty metrics
        "poverty_status": "B17001_002E",  # total population below poverty level
        "poverty_status_under_18": "B17001_003E",  # under 18 years below poverty level
        "poverty_status_18_to_64": "B17001_007E",  # 18 to 64 years below poverty level
        "poverty_status_65_and_over": "B17001_011E",  # 65 years and over below poverty level
        
        # Employment metrics
        "labor_force": "B23025_002E",  # in labor force
        "employed": "B23025_004E",  # employed
        "unemployed": "B23025_005E",  # unemployed
        "not_in_labor_force": "B23025_007E",  # not in labor force
        
        # Housing metrics
        "median_home_value": "B25077_001E",  # median home value
        "median_gross_rent": "B25064_001E",  # median gross rent
        "owner_occupied_units": "B25003_002E",  # owner-occupied housing units
        "renter_occupied_units": "B25003_003E",  # renter-occupied housing units
        
        # Education metrics
        "education_high_school": "B15003_017E",  # >=25 yrs with high school diploma
        "education_bachelors": "B15003_022E",  # >=25 yrs with bachelor's degree
        "education_masters": "B15003_023E",  # >=25 yrs with master's degree
        "education_doctorate": "B15003_025E",  # >=25 yrs with doctorate degree
        
        # Industry metrics
        "construction_employment": "C24030_003E",  # employed in construction
        "manufacturing_employment": "C24030_004E",  # employed in manufacturing
        "retail_employment": "C24030_006E",  # employed in retail trade
        "professional_employment": "C24030_013E",  # employed in professional services
        
        # Additional economic metrics
        "gini_index": "B19083_001E",  # income inequality (Gini index)
        "public_assistance": "B19057_002E",  # households with public assistance income
        "social_security": "B19055_002E",  # households with social security income
        "retirement_income": "B19059_002E",  # households with retirement income
    }

    # Step 4: Fetch data
    results = []
    for place_name, geoid in matched.items():
        data = c.acs5.state_place(
            list(variables.values()),
            states.IL.fips,
            geoid,
            year=2020
        )[0]
        row = {
            "place": place_name,
            # Population
            "population": data[variables["population"]],
            
            # Income metrics
            "median_income": data[variables["median_income"]],
            "aggregate_income": data[variables["aggregate_income"]],
            "per_capita_income": data[variables["per_capita_income"]],
            # "mean_income": data[variables["mean_income"]],
            
            # Poverty metrics
            "poverty_total": data[variables["poverty_status"]],
            "poverty_under_18": data[variables["poverty_status_under_18"]],
            "poverty_18_to_64": data[variables["poverty_status_18_to_64"]],
            "poverty_65_and_over": data[variables["poverty_status_65_and_over"]],
            
            # Employment metrics
            "labor_force": data[variables["labor_force"]],
            "employed": data[variables["employed"]],
            "unemployed": data[variables["unemployed"]],
            "not_in_labor_force": data[variables["not_in_labor_force"]],
            
            # Housing metrics
            "median_home_value": data[variables["median_home_value"]],
            "median_gross_rent": data[variables["median_gross_rent"]],
            "owner_occupied_units": data[variables["owner_occupied_units"]],
            "renter_occupied_units": data[variables["renter_occupied_units"]],
            
            # Education metrics
            "high_school_grads": data[variables["education_high_school"]],
            "bachelors_grads": data[variables["education_bachelors"]],
            "masters_grads": data[variables["education_masters"]],
            "doctorate_grads": data[variables["education_doctorate"]],
            
            # Industry metrics
            "construction_employment": data[variables["construction_employment"]],
            "manufacturing_employment": data[variables["manufacturing_employment"]],
            "retail_employment": data[variables["retail_employment"]],
            "professional_employment": data[variables["professional_employment"]],
            
            # Additional economic metrics
            "gini_index": data[variables["gini_index"]],
            "public_assistance": data[variables["public_assistance"]],
            "social_security": data[variables["social_security"]],
            "retirement_income": data[variables["retirement_income"]]
        }
        results.append(row)

    return pd.DataFrame(results)


if __name__ == "__main__":
    place_names = [
    "Algonquin", "Alsip", "Bannockburn", "Normal", "Brookfield", "Carbondale", "Countryside", "Decatur",
    "Deer Park", "Downers Grove", "Elgin", "Elk Grove Village", "Evanston", "Geneva", "Grayslake",
    "Hoffman Estates", "La Grange", "Northbrook", "Oak Park", "Peoria", "Schaumburg", "Rolling Meadows",
    "Springfield", "Waukegan", "Wilmette", "Batavia", "Beach Park", "Kane County", "Skokie",
    "Village of Bartlett", "Arlington Heights", "Village of Alsip", "Addison Township", "Village of Chicago Ridge",
    "Village of Crete", "Village of Campton Hills", "City of DeKalb", "DuPage County", "Crystal Lake", "Bellwood",
    "Village of Bensenville", "Calumet City", "City of Batavia", "Carpentersville", "Village of Buffalo Grove",
    "City of Berwyn", "City of Blue Island", "Barrington, Illinois", "Village of Algonquin", "Village of Carol Stream",
    "East Dundee", "Village of Diamond, Illinois", "Village of Deerfield", "Bull Valley", "City of Aurora",
    "City of Chicago Heights", "Village of Elmwood Park", "Cook County", "Cary", "Chicago Region"
    ]

    api_key = 'e8a746a9564827c7ffdf8bbc87f94d1602770a94'
    df = fetch_census_data(place_names, api_key)
    # print(df.head())

    # save data to csv
    df.to_csv("census_data.csv", index=False)


