import pandas as pd
from scholarly import scholarly
from habanero import Crossref
import re

# Crear una instancia de Crossref para buscar DOIs
cr = Crossref()

def search_and_extract_articles(combined_search_term, max_results=100):
    """
    Performs a search in Google Scholar using terms combined with Boolean connectors,
    extracts the relevant information and returns a list of results.
    
    Args:
        search_terms (list): combined search terms.
        max_results (int): max number to extract.
    
    Returns:
        results (list): list.
    """


    search_query = scholarly.search_pubs(combined_search_term)
    
    results = []

    for _ in range(max_results):
        try:
            result = next(search_query)

            # important information
            title = result['bib'].get('title', 'N/A')
            authors = result['bib'].get('author', 'N/A')
            year = result['bib'].get('pub_year', 'N/A')
            venue = result['bib'].get('venue', 'N/A')
            
            # DOI
            pub_url = result.get('pub_url', '')
            doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', pub_url, re.I)
            doi = doi_match.group(0) if doi_match else 'N/A'
            
            if doi == 'N/A':
                doi = get_doi_from_crossref(title)

            abstract = result.get('abstract', 'N/A')


            results.append({
                'Title': title,
                'Authors': authors,
                'Year': year,
                'Venue': venue,
                'DOI': doi,
                'Abstract': abstract
            })
        except StopIteration:
            break
    df = pd.DataFrame(results)
    return df

def get_doi_from_crossref(title):
    """
    Consulting doi

    Args:
        title (str): paper title.

    Returns:
        str: DOI or 'N/A'.
    """
    try:
        result = cr.works(query_title=title, select=["DOI"], limit=1)
        if result['message']['items']:
            return result['message']['items'][0]['DOI']
    except Exception as e:
        print(f"Error DOI for {title}: {e}")
    return 'N/A'



