You will need to install selenium and pandas.

### How I use this repository:
1. I paste a list of startups in `template.csv`.
2. I run main.py.
3. I copy the results in a `search_results.csv` output file that I use to make the outreach the LinkedIn profiles of the founders of the startups. We ask them for intros to VCs.
4. Sometimes I have to clean the output data using `clean_csv.py`.

### Cases: 
1. Whole info neeeded. Most of the times I need all the info I could get (LinkedIn profile of the founder, Website of the Startup and funding info from Crunchbase). In this case, I use `Utils_fundingStage.py` inside the `main.py`function.
2. Just funding Info. In some cases, I only need the funding info, because the VC's portfolio page is actually great and they include Founders' names. In this case, I use `Only_crunchbase.py` inside the `main.py`function.
3. Please don't bully me, I know there is a long way to not sucking. Bitch*.

### Workflow: https://miro.com/app/board/uXjVKlbx8eY=/?shareablePresentation=1
