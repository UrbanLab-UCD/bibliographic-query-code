import json
import pandas as pd
import requests
import json

def query_wos(api_key, query, count=3000, first_record=1, retries=3, delay=1.0):
    """
    Performs a query on the Web of Science API and extracts relevant information from each record.
    
    Args:
        api_key (str): Web of Science API Key.
        query (str): Query in Web of Science search format.
        count (int, optional): Number of results to return (default 10).
        first_record (int, optional): First record to return (default 1).
        retries (int, optional): Number of retry attempts in case of a throttle error.
        delay (float, optional): Initial delay (in seconds) between retries.
        
    Returns:
        pd.DataFrame: DataFrame with the query results or None if no results were found.
    """
    url = "https://api.clarivate.com/api/wos/"
    headers = {
        'X-ApiKey': api_key,
        'Accept': 'application/json'
    }
    params = {
        'databaseId': 'WOS',
        'usrQuery': query,
        'count': count,
        'firstRecord': first_record
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    print(f"Error al decodificar JSON: {response.text}")
                    return None

                if isinstance(data, dict):
                    print(f"Respuesta de la API: {data}")
                    records_container = data.get('Data', {}).get('Records', {}).get('records', None)

                    if isinstance(records_container, dict):
                        records_data = records_container.get('REC', [])

                        if isinstance(records_data, dict):
                            records_data = [records_data]
                        elif not isinstance(records_data, list):
                            print(f"Warning: formato inesperado de 'REC': {type(records_data)}")
                            return None

                        records = []
                        for record in records_data:
                            static_data = record.get('static_data', {}).get('summary', {})
                            titles_list = static_data.get('titles', {}).get('title', [])
                            title = next((item.get('content') for item in titles_list if item.get('type') == 'item'), 'N/A')
                            authors_list = static_data.get('names', {}).get('name', [])
                            authors = "; ".join([author.get('full_name', 'N/A') for author in authors_list if isinstance(author, dict)])
                            pub_info = static_data.get('pub_info', {})
                            pub_year = pub_info.get('pubyear', 'N/A')
                            source_title = next((item.get('content') for item in titles_list if item.get('type') == 'source'), 'N/A')
                            identifiers = static_data.get('identifiers', {}).get('identifier', [])
                            doi = next((item.get('value') for item in identifiers if item.get('type', '').lower() == 'doi'), 'N/A')
                            abstract = record.get('static_data', {}).get('fullrecord_metadata', {}).get('abstracts', {}).get('abstract', [])
                            abstract_text = " ".join([item.get('content', '') for item in abstract if isinstance(item, dict)])
                            records.append({
                                'Title': title,
                                'Authors': authors,
                                'Year': pub_year,
                                'Source': source_title,
                                'DOI': doi,
                                'Abstract': abstract_text
                            })

                        return pd.DataFrame(records)
                    elif records_container == '':
                        print("No se encontraron registros para esta consulta.")
                        return None
                    else:
                        print(f"Warning: 'records' no es un diccionario. Tipo: {type(records_container)}")
                        return None
                else:
                    print(f"Warning: 'data' no es un diccionario. Tipo: {type(data)}")
                    return None

            elif response.status_code == 429:
                print(f"Throttle error en el intento {attempt + 1}. Retrying in {delay} seconds...")
                time.sleep(delay * (attempt + 1))

            else:
                print(f"Error HTTP {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error en la conexión: {e}")
            return None

    return None


def check_parentheses_balance(query):
    """
    Check if parentheses are balanced in a query.

    Args:
        query (str): The query string.

    Returns:
        bool: True if parentheses are balanced, False otherwise.
    """
    stack = []
    for char in query:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return not stack

import time

def execute_query(api, query, retries=3, delay=2.0):
    """Ejecuta una consulta con reintentos y manejo de errores."""
    for attempt in range(retries):
        try:
            print(f"Executing query: {query}, attempt {attempt + 1}")
            result = query_wos(api, query, count=100, first_record=1, retries=3, delay=1.0)
            return result
        except Exception as e:
            print(f"Error on attempt {attempt + 1} for query: {query}. Error: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    return None

def execute_query_paginated(api, query, delay=1.0, max_records=5000, retries=5):
    all_dfs = []
    first_record = 1
    page_size = 100
    attempts = 0

    while first_record <= max_records:
        try:
            print(f"Getting records from {first_record} to {first_record + page_size - 1}")
            df = query_wos(api, query, count=page_size, first_record=first_record)

            if df is None or df.empty:
                print("No more results or error.")
                break

            all_dfs.append(df)

            if len(df) < page_size:
                break  # Última página

            first_record += page_size
            time.sleep(delay)
            attempts = 0  # reset after success

        except Exception as e:
            print(f"Error en la página {first_record}: {e}")
            attempts += 1
            if attempts >= retries:
                print(f"Falló tras {retries} reintentos.")
                break
            sleep_time = delay * (2 ** attempts)
            print(f"Esperando {sleep_time} segundos antes de reintentar...")
            time.sleep(sleep_time)

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return None