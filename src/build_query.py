import re
import requests


def build_search_query(where=None, what=None, when=None):
    """
    Building the search query
    
    Args:
        where (list): location
        what (list): topics
        when (tuple): years
        
    Returns:
        str: query
    """
    # add quotes
    def add_quotes(term):
        if "*" in term:  # if '*', no quotes
            return term
        else:
            return f'"{term}"'

    def format_terms(terms):
        return [add_quotes(term) for term in terms]

    where_clause = f"({' OR '.join(format_terms(where))})" if where else ""
    what_clause = f"({' OR '.join(format_terms(what))})" if what else ""

    if when:
        start_year, end_year = when
        when_clause = f'PUBYEAR AFT {start_year} AND PUBYEAR BEF {end_year}'
    else:
        when_clause = ""
    
    query_clauses = [where_clause, what_clause]
    combined_query = " AND ".join([clause for clause in query_clauses if clause])

    return f'{combined_query.strip()} {when_clause}'



def convert_query_for_database(combined_query, database):
    """ 
    Converts a combined query into the format required by each database (Google Scholar, Web of Science, Scopus).
    
    Args:
        combined_query (str): combined query with Boolean operators and quotes.
        database (str): Name of the database to which the query will be converted ('google_scholar', 'wos', 'scopus').
        
    Returns:
        str: Query adapted to the specified database format.
    """
    if database.lower() == 'google_scholar':
        scholar_query = combined_query.replace(" AND ", " ").replace(" OR ", " ")
        scholar_query = remove_year_clause(scholar_query)
        return scholar_query.strip()
    
    elif database.lower() == 'wos':
        term_query = extract_term_query(combined_query)  
        year_query = extract_year_query_wos(combined_query)  
        term_query = clean_boolean_query(term_query) if term_query else ''
        year_query = clean_boolean_query(year_query) if year_query else ''


        if term_query and year_query:
            wos_query = f'{term_query} AND {year_query}'
        elif term_query:
            wos_query = term_query
        elif year_query:
            wos_query = year_query
        else:
            wos_query = ''  
        wos_query = clean_boolean_query(wos_query)
        return wos_query
        
    elif database.lower() == 'scopus':
        scopus_query = combined_query
        scopus_query = replace_years_with_scopus_format(scopus_query)
        return scopus_query
    
    else:
        raise ValueError(f"La base de datos '{database}' no está soportada. Usa 'google_scholar', 'wos' o 'scopus'.")

def remove_year_clause(query):
    """
    Removes any year clauses (such as 'PUBYEAR AFT x AND PUBYEAR BEF y') from the query.
    
    Args:
        query (str): query with possible year clauses.
        
    Returns:
        str: Query without year clause
    """
    pattern = r'\bPUBYEAR (AFT \d+|BEF \d+|=\d+)( AND PUBYEAR (AFT \d+|BEF \d+|=\d+))?\b'
    return re.sub(pattern, '', query).strip()

def extract_term_query(query):
    """
    Extracts the part of the query containing the subject terms (for Web of Science).
    
    Args:
        query (str): query with terms and years.
        
    Returns:
        str: Query with thematic terms formatted for TS in Web of Science.
    """
    term_query = remove_year_clause(query)
    return clean_boolean_query(f'TS=({term_query})')

def extract_year_query_wos(query):
    """
    Extracts the years clause in the correct format for Web of Science.
Converts 'PUBYEAR AFT x AND PUBYEAR BEF y' to 'PY=x-y'.
    
    Args:
        query (str): query with years clauses.
        
    Returns:
        str: Query with years clause in Web of Science forma
    """
    pattern = r'PUBYEAR AFT (\d+) AND PUBYEAR BEF (\d+)'
    match = re.search(pattern, query)
    if match:
        start_year, end_year = match.groups()
        return f'PY={start_year}-{end_year}'
    return None

def clean_boolean_query(query):
    """
    Clean up the query to remove unnecessary boolean operators ('AND', 'OR') at the end.
    
    Args:
        query (str): query with possible operators at the end.
        
    Returns:
        str: Query without unnecessary boolean operators at the end.
    """
    # Eliminar cualquier 'AND' o 'OR' que quede al final de la consulta
    query = query.strip()
    query = re.sub(r'( AND | OR )+$', '', query)
    return query

def replace_years_with_scopus_format(query):
    """
    Replace the years clause in the query with the Scopus format.
    Converts 'PUBYEAR AFT x AND PUBYEAR BEF y' to 'PUBYEAR > x AND PUBYEAR < y'.
    
    Args:
        query (str): query with year clauses.
        
    Returns:
        str: Query with years clause in Scopus format.
    """
    pattern = r'PUBYEAR AFT (\d+) AND PUBYEAR BEF (\d+)'
    match = re.search(pattern, query)
    if match:
        start_year, end_year = match.groups()
        year_clause = f'AND PUBYEAR > {start_year} AND PUBYEAR < {end_year}'
        query = re.sub(pattern, year_clause, query)
    return query



def get_doi_from_crossref(title, authors):
    """
    Looking for the DOI using CrossRef.

    Args:
        title (str): Title.
        authors (list): Authors.

    Returns:
        str: DOI  or  a warning message.
    """
    base_url = "https://api.crossref.org/works"
    
    query = f"title:{title}"
    if authors:
        author_query = " ".join(authors)
        query += f" author:{author_query}"
    
    params = {"query": query, "rows": 1}  #
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data["message"]["items"]:
            print(data)
            return data["message"]["items"][0].get("DOI", "No DOI found")
        else:
            return "No results found"
    except Exception as e:
        return f"Error in CrossRef: {e}"