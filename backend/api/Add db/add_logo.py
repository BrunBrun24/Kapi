import requests
import os
import re
import sys
import django
from django.core.files import File
from django.conf import settings

# Ajouter le chemin au répertoire src pour accéder correctement aux modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Définir les paramètres de l'environnement pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Company

import os

def download_logos_for_all_companies(directory: str, name_directory):
    """
    Fonction qui parcourt toutes les entreprises dans la base de données,
    extrait le ticker de l'URL de leur site web, télécharge le logo et l'enregistre.
    Vérifie si le dossier name_directory existe, sinon il le crée.
    """
    # Vérifier si le répertoire existe, sinon le créer
    logo_ticker_directory = os.path.join(directory, name_directory)
    if not os.path.exists(logo_ticker_directory):
        os.makedirs(logo_ticker_directory)
        print(f"Le répertoire {logo_ticker_directory} a été créé.")
    else:
        print(f"Le répertoire {logo_ticker_directory} existe déjà.")
    
    # Récupérer toutes les entreprises dans la base de données
    companies = Company.objects.all()
    
    # Itérer sur chaque entreprise
    for company in companies:
        website_url = company.website
        if website_url:
            download_logo_from_website(logo_ticker_directory, website_url, company)
        else:
            print(f"Pas de site web pour l'entreprise {company.name}")

def download_logo_from_website(directory: str, website_url: str, company: Company):
    """
    Fonction qui récupère le ticker de l'entreprise à partir de son site web,
    télécharge le logo et l'enregistre dans la base de données de l'entreprise.

    Paramètres :
    - website_url (str) : L'URL du site web de l'entreprise (par exemple 'https://www.apple.com').
    - company (Company) : L'instance de l'entreprise pour laquelle le logo est téléchargé.
    """
    
    # Extraire le ticker à partir de l'URL
    # ticker_match = re.search(r'https://www\.([a-zA-Z0-9\-]+)\.com', website_url)
    ticker_match = re.search(r'https?://(?:[a-zA-Z0-9\-]+\.)*([a-zA-Z0-9\-]+)\.com', website_url)
    
    if ticker_match:
        ticker = ticker_match.group(1).upper()  # Extraire et convertir le ticker en majuscules
        
        # Création de l'URL du logo basée sur le ticker
        logo_url = f"https://img.logo.dev/{ticker.lower()}.com?token=pk_dwWxbPa7QQuJ4hxyKO3sow"
        
        # Vérifier si le fichier existe déjà dans le répertoire
        file_path = os.path.join(directory, f"{company.ticker}.png")
        if os.path.exists(file_path):
            return  # Passer à l'entreprise suivante si le logo existe déjà
        
        try:
            # Effectuer la requête pour télécharger l'image
            response = requests.get(logo_url)

            # Vérification du statut de la réponse (200 signifie succès)
            if response.status_code == 200:
                # Créer le répertoire de sauvegarde si nécessaire
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Enregistrer l'image dans un fichier
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                
                # Attacher l'image à l'entreprise via un champ ImageField (si tu as un champ ImageField dans ton modèle)
                company.logo = os.path.relpath(file_path, settings.MEDIA_ROOT)  # Chemin relatif à MEDIA_ROOT
                company.save()
            else:
                print(f"Erreur lors du téléchargement du logo pour {ticker}. Status code: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération du logo pour {ticker}: {e}")
    
    else:
        print(f"Impossible d'extraire le ticker de l'URL : '{website_url}' ({company.ticker})")

def download_logo_from_ticker(directory: str, ticker: str, name: str, extention="com"):
    """
    Fonction qui récupère le ticker de l'entreprise à partir de son site web,
    télécharge le logo et l'enregistre dans la base de données de l'entreprise.

    Paramètres :
    - website_url (str) : L'URL du site web de l'entreprise (par exemple 'https://www.apple.com').
    - company (Company) : L'instance de l'entreprise pour laquelle le logo est téléchargé.
    """
        
    # Création de l'URL du logo basée sur le name
    logo_url = f"https://img.logo.dev/{name.lower()}.{extention.lower()}?token=pk_dwWxbPa7QQuJ4hxyKO3sow"
    
    # Vérifier si le fichier existe déjà dans le répertoire
    file_path = os.path.join(directory, f"{ticker}.png")
    
    try:
        # Effectuer la requête pour télécharger l'image
        response = requests.get(logo_url)

        # Vérification du statut de la réponse (200 signifie succès)
        if response.status_code == 200:
            # Créer le répertoire de sauvegarde si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Enregistrer l'image dans un fichier
            with open(file_path, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Erreur lors du téléchargement du logo pour {ticker}. Status code: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du logo pour {name}: {e}")


# download_logos_for_all_companies("api/static/logo/", "logo_ticker")

download_logo_from_ticker("api/static/logo/", "SW.PA", "Sodexo")
