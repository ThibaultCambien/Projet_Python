import os
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time

# Configuration du logger pour afficher les messages d'information et d'erreur
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def charger_flux(filepath):
    """
    Lit un fichier contenant des URLs de flux RSS et retourne une liste.

    Args:
        filepath (str): Chemin vers le fichier contenant les URLs.

    Returns:
        list: Une liste d'URLs (chaque ligne du fichier correspond à une URL).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # On enlève les lignes vides et les espaces inutiles
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Fichier introuvable : {filepath}")
        return []

def charger_mots_cles(filepath):
    """
    Charge une liste de mots-clés à partir d'un fichier texte.

    Args:
        filepath (str): Chemin vers le fichier contenant les mots-clés.

    Returns:
        list: Une liste de mots-clés en minuscules.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # On convertit tout en minuscules pour éviter les problèmes de casse
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Fichier introuvable : {filepath}")
        return []

def article_match(entry, keywords):
    """
    Vérifie si un article contient un des mots-clés.

    Args:
        entry (dict): Article du flux RSS (dictionnaire contenant les infos).
        keywords (list): Liste des mots-clés à rechercher.

    Returns:
        str: Le mot-clé trouvé dans l'article, ou None si aucun mot-clé ne correspond.
    """
    # On combine le titre et la description pour maximiser les chances de correspondance
    content = (entry.title + " " + entry.get("description", "")).lower()
    for keyword in keywords:
        if keyword in content:
            return keyword
    return None

def analyse_flux(url, keywords):
    """
    Analyse un flux RSS et retourne les articles correspondant aux mots-clés.

    Args:
        url (str): URL du flux RSS.
        keywords (list): Liste des mots-clés.

    Returns:
        list: Une liste d'articles correspondant aux mots-clés.
    """
    try:
        feed = feedparser.parse(url)
        matched = []
        for entry in feed.entries:
            if not hasattr(entry, 'title'):
                # Si l'article n'a pas de titre, on passe
                continue
            keyword = article_match(entry, keywords)
            if keyword:
                # On ajoute les infos importantes de l'article
                matched.append({
                    "title": entry.title,
                    "published": entry.get("published", "Date inconnue"),
                    "link": entry.link,
                    "keyword": keyword
                })
        return matched
    except Exception as e:
        # Petite astuce : on loggue l'erreur mais on continue
        logging.warning(f"Erreur lors du traitement de {url} : {e}")
        return []

def main():
    """
    Fonction principale du script. Elle charge les données, traite les flux RSS
    et sauvegarde les résultats dans un fichier.
    """
    # Mesure du temps de démarrage
    start_time = time.time()

    # Chargement des fichiers d'entrée
    rss_urls = charger_flux("rss_list.txt")
    keywords = charger_mots_cles("mots_cles.txt")

    # Vérification des données d'entrée
    if not rss_urls or not keywords:
        logging.error("Les fichiers d'entrée sont manquants ou vides.")
        return

    logging.info(f"{len(rss_urls)} flux à scanner.")
    logging.info(f"Mots-clés utilisés : {keywords}")

    results = []
    # Utilisation de ThreadPoolExecutor pour le traitement parallèle
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(analyse_flux, url, keywords) for url in rss_urls]
        for future in as_completed(futures):
            try:
                articles = future.result()
                results.extend(articles)
            except Exception as e:
                logging.warning(f"Erreur dans un thread : {e}")

    for article in results:
        print(f"[{article['keyword']}] {article['title']} ({article['published']})\n{article['link']}\n")

    with open("resultat.txt", "w", encoding="utf-8") as f:
        for article in results:
            f.write(f"{article['title']} | {article['published']} | {article['link']} | {article['keyword']}\n")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Temps total d'exécution : {elapsed_time:.2f} secondes.")

if __name__ == "__main__":
    main()