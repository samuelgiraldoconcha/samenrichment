You will need to pip install:
- Selenium
- Pandas
- Pygame

### How to use this repository:
1. Paste a list of startups in `template.csv`.
2. Run `python3 -m samenrichment_package.main`.
3. Select option 'E' to start enrichment.
4. If results in `output_files/search_results.csv` have noise, clean them byt running `python3 -m samenrichment_package.main` again, but selectin option 'C'.
5. Copy clean results from `output_files/cleaned_search_results.csv`.
6. Paste that info in the outreach spreadheet we use. 

### TODOs: 
1. Data models. We are creating an app in order to handle different enrichment cases. Models are going to be:
- Prospects.
- Enrichment_targets.
- Scrapes.

2. Frontend.

Please don't bully me, I know there is a long way to not sucking. Bitch*.

### This is a tool I use inside this whole workflow: https://miro.com/app/board/uXjVKlbx8eY=/?shareablePresentation=1
