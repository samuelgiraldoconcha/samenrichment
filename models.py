from datetime import datetime
import pydantic
from pydantic import Basemodel, PositiveInt

class Prospect(Basemodel):
    id: int
    vc_firm: str
    startup: str
    additional_info: str
    enriched: bool
    enrichment_data: dict[str,str]

class Enrichment_target(Basemodel):
    id: int
    name: str
    main_link: str
    scrape_link: str
    scrape_fields: dict[str, str]

class Enrichment(Basemodel):
    id: int
    date: str
    prospects: List[Prospect]
    enrichment_targets: List[Enrichment_target]
    enriched_data: dict[Prospect, dict[str,str]]


print(pydantic.__version__)