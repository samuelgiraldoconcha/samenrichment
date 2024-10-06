from uuid import uuid4
import pandas as pd
from datetime import datetime
import pydantic
from pydantic import BaseModel, PositiveInt, Field

class Prospect(BaseModel):
    id: int = Field(default_factory=lambda: uuid4().hex)
    vc_firm: str = ""
    startup: str = ""
    industry: str = ""
    enriched: bool = False
     #List of primary keys of enrichment
    last_enrichment_id: int = None
    enrichment_data: dict[str,str] = {}

    class Config:
        arbitrary_types_allowed=True

class Enrichment_target(BaseModel):
    id: int
    name: str = ""
    main_link: str = ""
    scrape_link: str = ""
    scrape_fields: dict[str, str]

class Enrichment(BaseModel):
    id: int
    date: str
    pool : str
    #List of primary keys of enrichment targets
    enrichment_targets_ids: list[Prospect] = []
    #Dictionary[Primery key of prospect, dict[primary key of enrichment target, value scraped]]
    enriched_data: dict[Prospect, dict[str,str]] = []

prospecto1 = Prospect(
    vc_firm = "LifeX",
    startup = "Servimarket",
    additional_info = "Retail", 
)

enrichment_targeto1 = Enrichment_target(
    id = 1,
    name = "Octubre 3, 2024",
    main_link = "linkedin.com",
    scrape_link = "/financials",
    scrape_fields = {"funding_data" : "a=sujk"}
)

print(prospecto1)

def parse_csv(csv_path: str):
    # Load the CSV file
    df = pd.read_csv(csv_path)
    # Replace NaN with empty strings
    df.fillna('', inplace=True)

    prospects = []
    
    for index, row in df.iterrows():
            startup_row = row['Startup']
            industry_row = row['Industry']
            prospects.append(Prospect(
                startup = startup_row,
                industry = industry_row
            ))
    
    return prospects      

print(parse_csv("template.csv"))