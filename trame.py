import folium
import matplotlib.pyplot as plt
from datetime import datetime
import math

# Fonction pour lire les trames NMEA à partir d'un fichier
def lire_trames_nmea(fichier):
    try:
        with open(fichier, 'r') as file:
            lignes = file.readlines()
        
        # Filtrage des trames NMEA, qui contiennent GPGGA ou PGGA
        trames_nmea = [ligne.strip() for ligne in lignes if 'GPGGA' in ligne or 'PGGA' in ligne]
        
        return trames_nmea

    except FileNotFoundError:
        print("Le fichier spécifié est introuvable.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

# Fonction pour calculer la distance entre deux points GPS en kilomètres
def calculer_distance(lat1, lon1, lat2, lon2):
    rayon_terre = 6371.0  # Rayon de la Terre en kilomètres
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = rayon_terre * c
    return distance

# Fonction pour extraire les coordonnées GPS et la vitesse des trames NMEA
def extraire_coordonnees_et_vitesse(trames_nmea):
    coordonnees = []
    vitesses = []
    heures = []
    distances_parcourues = [0]

    for trame in trames_nmea:
        elements = trame.split(',')

        if elements[0] in ('GPGGA', 'PGGA'):
            try:
                lat = float(elements[2][:2]) + float(elements[2][2:]) / 60
                lon = float(elements[4][:3]) + float(elements[4][3:]) / 60

                if elements[3] == 'S':
                    lat = -lat
                if elements[5] == 'W':
                    lon = -lon

                heure_trame = elements[1]
                heures.append(datetime.strptime(heure_trame, "%H%M%S.%f"))
                coordonnees.append((lat, lon))

            except ValueError:
                print("Erreur de conversion pour la trame :", trame)
    
    for i in range(1, len(coordonnees)):
        lat1, lon1 = coordonnees[i - 1]
        lat2, lon2 = coordonnees[i]
        distance = calculer_distance(lat1, lon1, lat2, lon2)
        delta_temps = (heures[i] - heures[i - 1]).total_seconds() / 3600
        
        if delta_temps > 0:
            vitesse = distance / delta_temps
            vitesses.append(vitesse)
        else:
            vitesses.append(0)

        distances_parcourues.append(distances_parcourues[-1] + distance)

    return coordonnees, vitesses, heures, distances_parcourues
    
# Fonction pour calculer l'accélération à partir des vitesses
def calculer_acceleration(vitesses, heures):
    accelerations = [0]  # Initialiser avec 0 pour le premier point

    for i in range(1, len(vitesses)):
        delta_vitesse = vitesses[i] - vitesses[i - 1]
        delta_temps = (heures[i] - heures[i - 1]).total_seconds() / 3600  # Temps en heures
        
        if delta_temps > 0:
            # Calculer l'accélération en km/h²
            acceleration_kmh2 = delta_vitesse / delta_temps
            # Convertir l'accélération en m/s²
            acceleration_ms2 = acceleration_kmh2 / 12960
            accelerations.append(acceleration_ms2)
        else:
            accelerations.append(0)

    return accelerations

    return accelerations
    
# Fonction pour tracer le chemin sur une carte avec la vitesse en km/h dans l'infobulle
def tracer_chemin(coordonnees, vitesses, distances_parcourues, accelerations):
    if not coordonnees:
        print("Aucune coordonnée disponible pour le tracé.")
        return

    carte = folium.Map(location=coordonnees[0], zoom_start=14)

    # Ajouter un marqueur pour chaque point du trajet avec la vitesse, distance et accélération comme infobulle
    for i, coord in enumerate(coordonnees):
        vitesse_kmh = vitesses[i] if i < len(vitesses) else 0  # S'assurer que l'index est valide
        distance_km = distances_parcourues[i]  # Récupérer la distance cumulée
        acceleration = accelerations[i] if i < len(accelerations) else 0  # Récupérer l'accélération

        folium.Marker(
            location=coord,
            popup=f'Vitesse: {vitesse_kmh:.2f} km/h<br>Distance parcourue: {distance_km:.2f} km<br>Accélération: {acceleration:.4f} m/s²',  # Afficher vitesse, distance et accélération
            icon=folium.Icon(color="blue", icon='info-sign')
        ).add_to(carte)

    # Marquer les points de départ et d'arrivée de manière distincte
    folium.Marker(coordonnees[0], popup="Départ", icon=folium.Icon(color="green")).add_to(carte)
    folium.Marker(coordonnees[-1], popup="Arrivée", icon=folium.Icon(color="red")).add_to(carte)

    # Sauvegarder la carte dans un fichier HTML
    carte.save("chemin_voiture_points.html")
    print("Carte générée avec succès : 'chemin_voiture_points.html'")

# Fonction pour afficher les graphiques de la vitesse et de la distance parcourue sur la même figure
def afficher_vitesse_et_distance(vitesses, distances_parcourues, heures):
    if not vitesses or not distances_parcourues:
        print("Aucune donnée disponible.")
        return

    temps_reel = [(heure - heures[0]).total_seconds() for heure in heures[1:]]

    fig, ax = plt.subplots(2, 1, figsize=(10, 12))

    ax[0].plot(temps_reel, vitesses, color='blue', label='Vitesse (km/h)')
    ax[0].set_title("Vitesse de la voiture au fil du temps")
    ax[0].set_xlabel("Temps (secondes depuis la première trame)")
    ax[0].set_ylabel("Vitesse (km/h)")
    ax[0].legend()
    ax[0].grid(True)

    ax[1].plot(temps_reel, distances_parcourues[1:], color='green', label='Distance parcourue (km)')
    ax[1].set_title("Distance parcourue par la voiture au fil du temps")
    ax[1].set_xlabel("Temps (secondes depuis la première trame)")
    ax[1].set_ylabel("Distance parcourue (km)")
    ax[1].legend()
    ax[1].grid(True)

    plt.tight_layout()
    plt.savefig("vitesse_et_distance_voiture.png")
    plt.show()

# Remplacez ici le chemin du fichier par celui de votre fichier cible
fichier = r'C:\Users\CIEL23_admin\Documents\2024-2025\trames\2024-09-20_11-53-59.txt'

# Lire les trames NMEA et extraire les coordonnées et la vitesse
trames = lire_trames_nmea(fichier)
coordonnees, vitesses, heures, distances_parcourues = extraire_coordonnees_et_vitesse(trames)

# Calculer l'accélération
accelerations = calculer_acceleration(vitesses, heures)

# Tracer le chemin sur la carte avec les vitesses, distances et accélérations affichées dans les infobulles
tracer_chemin(coordonnees, vitesses, distances_parcourues, accelerations)

# Afficher les graphiques de la vitesse et de la distance parcourue sur la même figure
afficher_vitesse_et_distance(vitesses, distances_parcourues, heures)