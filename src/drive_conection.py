import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from PyPDF2 import PdfReader
from pathlib import Path
import spacy
import re
import fitz
import requests

nlp = spacy.load("en_core_web_sm")


def initialize_drive_connection():
    """
    Authenticates with Google Drive and returns the drive object.
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  
    drive = GoogleDrive(gauth)  
    return drive

def extract_doi_from_pdf(file_path, filename):
    """
    Extracts the DOI of the given PDF file and associates it with the original file name.

    param file_path: Path of the PDF file.
    :param filename: Original filename of the file.
    :return: DOI found in the PDF and the filename.
    """
    try:
        doc = fitz.open(file_path)
        doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
        for page_num in range(min(5, len(doc))): 
            page = doc.load_page(page_num)
            text = page.get_text()
            doi_match = re.search(doi_pattern, text, re.IGNORECASE)
            if doi_match:
                return doi_match.group(0), filename  
        doc.close()
    except Exception as e:
        print(f"Error al extraer DOI del archivo '{filename}': {e}")
    return None, filename

def get_article_metadata(doi, filename):
    """
    Gets the article metadata from the DOI and appends the file name.

    param doi: DOI of the article.
    param filename: Original name of the file.
    :return: Dictionary with the metadata of the article and the filename.
    """
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        message = data.get('message', {})
        
        title = message.get('title', ['N/A'])[0]
        authors = message.get('author', [])
        authors_names = [f"{author.get('given', '')} {author.get('family', '')}" for author in authors]
        authors_concatenated = ', '.join(authors_names)
        keywords = message.get('subject', ['N/A'])
        keywords_concatenated = ', '.join(keywords)

        year = message.get('issued', {}).get('date-parts', [[None]])[0][0]
        abstract = message.get('abstract', '')

        if abstract:
            abstract = re.sub('<[^<]+?>', '', abstract).strip()

        study_area = extract_study_area_from_abstract(abstract)

        publisher = message.get('publisher', 'N/A')

        return {
            'DOI': doi,
            'Title': title,
            'Authors': authors_concatenated,
            'Abstract': abstract if abstract else 'N/A',  
            'Keywords': keywords_concatenated,
            'Year': year,
            'Study Area': study_area,
            'Publisher': publisher,
            'Filename': filename  
        }
    else:
        print(f"Error al recuperar DOI {doi}: {response.status_code}")
        return None


def extract_study_area_from_abstract(abstract):
    doc = nlp(abstract)
    locations = []
    for ent in doc.ents:
        if ent.label_ == "GPE":
            locations.append(ent.text)
    return ', '.join(set(locations)) if locations else 'N/A'


def process_doi_list(doi_list, filename_list):
    """
    Procesa una lista de DOIs y crea un DataFrame con la metadata y el nombre del archivo original.

    :param doi_list: Lista de DOIs.
    :param filename_list: Lista de nombres de archivos correspondientes a los DOIs.
    :return: DataFrame con la metadata del artículo y el nombre del archivo.
    """
    records = []
    for doi, filename in zip(doi_list, filename_list):
        metadata = get_article_metadata(doi, filename)
        if metadata:
            records.append(metadata)
    return pd.DataFrame(records)

def process_pdfs_in_drive_folder(drive, folder_id):
    """
    Procesa todos los PDFs en una carpeta de Google Drive y retorna un DataFrame con la metadata.

    :param folder_id: ID de la carpeta en Google Drive.
    :return: DataFrame con la metadata de todos los PDFs en la carpeta.
    """
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    doi_list = []
    filename_list = []  
    for file in file_list:
        if file['mimeType'] == 'application/pdf':  # Solo procesar PDFs
            print(f"Procesando archivo PDF: {file['title']}")
            file.GetContentFile(file['title'])

            doi, filename = extract_doi_from_pdf(file['title'], file['title'])
            if doi:
                doi_list.append(doi)
                filename_list.append(filename)

            os.remove(file['title'])

    df = process_doi_list(doi_list, filename_list)
    return df

