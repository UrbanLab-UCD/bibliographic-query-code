import os
from pybliometrics.scopus import ScopusSearch
import pandas as pd



def scopus_to_dataframe(query, max_results=20):
    """
    Search in Scopus and stores the results in a pd Dataframe
    
    Args:
        query (str): search query.
        max_results (int): Maximum number of results to extract (default 20).
    
    Returns:
        pd.DataFrame: DataFrame with the search results, including title, authors, year, source and DOI.
    """

    search = ScopusSearch(query, view="COMPLETE", count=max_results)
    

    records = []
    for result in search.results[:max_results]:  
        record = {
            'Title': result.title,
            'Authors': result.author_names,
            'Year': result.coverDate.split('-')[0] if result.coverDate else 'N/A',
            'Source': result.publicationName,
            'DOI': result.doi if result.doi else 'N/A',
            'Abstract': result.description,
            'Keywords': result.authkeywords
        }
        records.append(record)

    df = pd.DataFrame(records)
    return df