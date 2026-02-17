# Guide voyage – Consignes par destination

Page statique pour afficher les consignes selon **pays** et **type de voyage** (pro / perso). Les données viennent du fichier Excel **referentiel_données.xlsx** ; un script Python génère la page HTML.

## Utilisation

1. **Mettre à jour l’Excel** : éditer `referentiel_données.xlsx` (colonnes ci‑dessous).
2. **Générer la page** : lancer `python3 build_from_excel.py` depuis le dossier `guide-voyage`.
3. **Ouvrir** `index.html` dans un navigateur et choisir pays + type de voyage.

## Colonnes du fichier Excel

| Colonne | Rôle |
|--------|------|
| **Code** | Code ISO du pays (ex. FR, US) |
| **Name_EN** | Nom du pays en anglais |
| **Name_FR** | Nom du pays en français (affiché dans la page) |
| **Personnal_risk** | Couleur du risque personnes (ex. Red) → déclenche les consignes « prévenir les assistantes » |
| **Blocked_Country IT** | Oui = pays bloqué par défaut (IT) → dérogation, PC/iPhone vierges |
| **Customs_Risk** | Oui = risque à la douane → device clean (pro : IT prête iPhone) |
| **Local_Data_risk** | Oui = risque vol de données (hôtel, compromat, compromission) → cleaning au retour |
| **4G_included** | Oui = pays dans le forfait 4G ; Non = prendre carte SIM Olafly |
| **Comments** | Commentaires pour les autres régions couvertes par le forfait 4G (affichés dans la page) |

Valeurs considérées comme « Oui » : `Yes`, `Oui`, `1`, `true`, `x`, `o` (insensible à la casse).

## Fichiers

- **referentiel_données.xlsx** : référentiel à maintenir (source de vérité).
- **build_from_excel.py** : lit l’Excel et génère `index.html` (aucune dépendance pip : utilise uniquement la bibliothèque standard pour lire le .xlsx).
- **index_template.html** : modèle de page (ne pas éditer à la main ; il contient le placeholder `__PAYS_JSON__` remplacé par le script).
- **index.html** : page générée (données embarquées, pas de serveur ni de data.js).

## Logique d’affichage

- **Risque personnes** : si `Personnal_risk` est renseigné → affichage du niveau + consignes « prévenir les assistantes » (assurance, itinéraire, médecine du voyage, briefing sécurité).
- **Risque données** : pays bloqué IT et/ou risque douane → consignes dérogation / device clean (pro vs perso).
- **Hors forfait** : si `4G_included` = Non → carte SIM Olafly ; les **Comments** sont affichés dans ce bloc s’ils sont renseignés.
- **Au retour** : si `Local_Data_risk` = Oui → cleaning PC/iPhone ; si risque rouge → quarantaine possible.
