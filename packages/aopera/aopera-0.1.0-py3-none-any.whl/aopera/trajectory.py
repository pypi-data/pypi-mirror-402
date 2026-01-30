
import numpy as np

def satellite_trajectory(altitude, max_elevation, npoints=4000, debut=0, fin=0, signe_debut=-1, signe_fin=1):
    """
    Compute satellite trajectory.
    
    Authors
    -------
    Pierre-Louis Mayeur (ONERA), adapted from Cyril Petit (ONERA).
    """
    # Constantes
    Rt = 6378.15e3  # Rayon de la Terre en mètres
    Cste_grav = 6.6743e-11  # Constante gravitationnelle
    Mt = 5.97e24  # Masse de la Terre
    c = 299792458  # Vitesse de la lumière

    # Calculs préliminaires
    Rs = Rt + altitude
    vsat = np.sqrt(Cste_grav * Mt / Rs)  # Vitesse du satellite
    thetapoint = vsat /Rs
    # beta_max =  np.degrees(np.arccos(Rt/Rs))
    
    beta = np.arccos(Rt/Rs*np.cos(np.radians(max_elevation))) -np.radians(max_elevation) # au signe pres evidemment mais on s'en fiche
    theta_max = np.arccos(Rt/(Rs*np.cos(beta))) # angle max de visibilité
    theta_full = np.linspace(-theta_max, theta_max, npoints+1) # angle rotation satellite 
    
    #temps écoulé en seconde
    time_full = (theta_full - np.min(theta_full)) / thetapoint
    
    #distance à la cible. formule validée par rapport à la litterature.
    distance_full = np.sqrt(Rs**2 + Rt**2 - 2 * Rs * Rt * np.cos(theta_full) * np.cos(beta))
    
    # elevation check formule.
    value = (Rs * np.cos(theta_full) * np.cos(beta) - Rt) / distance_full
    clipped_value = np.clip(value, -1., 1.)  # Assure la valeur est dans [-1, 1]
    elev_full = np.arcsin(clipped_value)
    
    
    # ici on se laisse la possibilité de voir une trajectoire seulement à la montée ou descente.
    if signe_debut == -1:
        # Trouve les indices où la condition est vraie pour les valeurs négatives de theta_full
        idx_theta_neg = np.where(np.sign(theta_full) == signe_debut)[0]
        
        # Trouve les indices où l'élévation est supérieure ou égale au debut (en radians)
        idx_elev_sup_debut = np.where(elev_full[idx_theta_neg] >= debut * np.pi / 180)[0]
        
        # Si des indices sont trouvés, calcule indice_debut
        if len(idx_elev_sup_debut) > 0:
            indice_debut = idx_theta_neg[np.min(idx_elev_sup_debut)] + np.min(np.where(np.sign(theta_full) == signe_debut)[0])
        else:
            print("Erreur elevation de debut jamais atteinte : sortie")
    else:
        # Trouve les indices où la condition est vraie pour les valeurs positives de theta_full
        idx_theta_pos = np.where(np.sign(theta_full) == signe_debut)[0]
        
        # Trouve les indices où l'élévation est supérieure ou égale au debut (en radians)
        idx_elev_sup_debut = np.where(elev_full[idx_theta_pos] >= debut * np.pi / 180)[0]
        
        # Si des indices sont trouvés, calcule indice_debut
        if len(idx_elev_sup_debut) > 0:
            indice_debut = idx_theta_pos[np.max(idx_elev_sup_debut)] + np.min(np.where(np.sign(theta_full) == signe_debut)[0])
        else:
            print("Erreur elevation de debut jamais atteinte : sortie")
            
    if signe_fin == -1:
        # Trouve les indices où la condition est vraie pour les valeurs négatives de theta_full
        idx_theta_neg = np.where(np.sign(theta_full) == signe_fin)[0]
        
        # Trouve les indices où l'élévation est supérieure ou égale à la fin (en radians)
        idx_elev_sup_fin = np.where(elev_full[idx_theta_neg] >= fin * np.pi / 180)[0]
        
        # Si des indices sont trouvés, calcule indice_fin
        if len(idx_elev_sup_fin) > 0:
            indice_fin = idx_theta_neg[np.min(idx_elev_sup_fin)] + np.min(np.where(np.sign(theta_full) == signe_fin)[0])
        else:
            print("Erreur elevation de fin jamais atteinte : sortie")
    else:
        # Trouve les indices où la condition est vraie pour les valeurs positives de theta_full
        idx_theta_pos = np.where(np.sign(theta_full) == signe_fin)[0]
        
        # Trouve les indices où l'élévation est supérieure ou égale à la fin (en radians)
        idx_elev_sup_fin = np.where(elev_full[idx_theta_pos] >= fin * np.pi / 180)[0]
        
        # Si des indices sont trouvés, calcule indice_fin
        if len(idx_elev_sup_fin) > 0:
            indice_fin = idx_theta_pos[np.max(idx_elev_sup_fin)] + np.min(np.where(np.sign(theta_full) == signe_fin)[0])
        else:
            print("Erreur elevation de fin jamais atteinte : sortie")
            
    if indice_fin < indice_debut:
        print("Problème: la position de fin est avant la position début : sortie")
        
    time = time_full[indice_debut:indice_fin+1]
    elevation = elev_full[indice_debut:indice_fin+1]
    theta = theta_full[indice_debut:indice_fin+1]
    distance = distance_full[indice_debut:indice_fin+1]
    npoints = len(time)
    
    azim = np.arccos(np.sin(beta) / np.sqrt(np.sin(beta)**2 + (np.sin(theta)**2) * (np.cos(beta)**2))) * np.sign(theta)
    if beta == 0:
        test = np.where(theta == 0)[0]
        if len(test) > 0:
            azim[test] = 0.0

    Vpar = -vsat / distance * Rt * np.sin(theta) * np.cos(beta)
    Vorth = vsat * np.sqrt(1.0 - (Rt * np.sin(theta) * np.cos(beta) / distance)**2)
    # norm_v = np.sqrt(Vpar**2 + Vorth**2)  
    slew_rate = Vorth / distance
    
    vazim = vsat * (np.sin(theta) * np.sin(beta)*np.sin(azim) + np.cos(theta)*np.cos(azim) + np.sin(theta)*np.cos(beta)*0)
    velev = vsat * (np.sin(theta) * np.sin(beta)*np.sin(elevation)*np.cos(azim) - np.cos(theta)*np.sin(elevation)*np.sin(azim) - np.sin(theta)*np.cos(beta)*np.cos(elevation))
    slew_rate_elev = velev / distance
    slew_rate_azim = vazim / (distance * np.cos(elevation)) 
    
    paa = np.zeros((2, len(velev)))  # Crée un tableau de zéros avec la bonne forme
    paa[0, :] = 2 * distance * slew_rate / c * vazim / Vorth
    paa[1, :] = 2 * distance * slew_rate / c * velev / Vorth

    return  time, distance, elevation, azim, Vpar, Vorth, slew_rate_elev,slew_rate_azim, velev,vazim, paa
