# **MAZE101**

***---------------------------------------------------------------------------------------------------------------------------***

### ***ENGLISH :***

***---------------------------------------------------------------------------------------------------------------------------***

###### My first "official" python project. A maze game with pygame.

###### This is an alpha version of the game that has a pretty basic setup.



##### **How to play:**

* Install `pygame`
* Run `main.py`

\---------------------------------------------------------------------------------------------------------------------------

##### **Features:**

* 5 different mazes
* Teleporters
* Traps
* Keyed doors
* Fog of war and light system
* Sub map system
* Timer and record time
* Star system progression
* A tutorial menu to help with the controls

\---------------------------------------------------------------------------------------------------------------------------

##### **How to create a new level :**

* First, create a new `.txt` file in `levels/` and define the level grid.



Legend:

`W` = Wall

`P` = Player Spawn

`T` = Trap

`S` = Special teleporter (to load another map)

`E` = Enemy

Lowercase letter = Key

Other uppercase letter = Door (ex. Key `a` opens Door `A`)

Number = Teleporter

Space = Nothing





* Then, open `levels/levels_config.json` and add a new entry for the level. Use existing levels as examples.

Example entry:

```json
"6": {
  "files": ["level6.txt"],
  "meta": "level6_meta.json"
}
```

* Create the meta file in `levels/`, for example `level6_meta.json`.
Important fields:

  * `name`: display name for the level
  * `color`: RGB list like `[255, 128, 0]`
  * `reward`: number of stars for completion
  * `tps`: teleporter mapping, using `null` for unused portals
  * `fow`: `true` or `false`
  * `submap_routes`: optional routes between maps when using multiple files

Example meta file:

```json
{
  "name": "Hidden Vault",
  "color": [255, 128, 0],
  "reward": 2,
  "tps": [1, 0, 5, 4, null, null],
  "fow": false,
  "submap_routes": {
    "0": {
      "0": { "target_map": 1, "spawn_pos": [1, 1] }
    },
    "1": {
      "0": { "target_map": 0, "spawn_pos": [1, 1] }
    }
  }
}
```

* If the level uses multiple maps, add several filenames to `files` and configure `submap_routes` in the meta file.







***---------------------------------------------------------------------------------------------------------------------------***

### ***FRANCAIS :***

***---------------------------------------------------------------------------------------------------------------------------***

###### Mon premier projet Python « officiel ». Un jeu de labyrinthe avec Pygame.

###### Il s'agit d'une version alpha du jeu avec une configuration de base assez limitée.



##### **Comment jouer :**

* Installer `pygame`
* Exécuter `main.py`

\---------------------------------------------------------------------------------------------------------------------------

##### **Fonctionnalités :**

* 5 labyrinthes différents
* Téléporteurs
* Pièges
* Portes à clés
* Un système de sous-cartes
* Un système fog of war et de lumière
* Chronomètre et temps record
* Progression par système d'étoiles
* Un menu tutoriel pour aider sur les touches

\---------------------------------------------------------------------------------------------------------------------------

##### **Comment créer un nouveau niveau :**

* Créez d'abord un fichier `.txt` dans le répertoire `levels/` où vous définirez la grille du niveau.

Légende :

* `W` = Mur
* `P` = Point d'apparition du joueur
* `T` = Piège
* `S` = Téléporteur spécial (charge une autre carte)
* `E` = Ennemi
* Lettre minuscule = Clé
* Autre lettre majuscule = Porte (ex. : la clé `a` ouvre la porte `A`)
* Chiffre = Téléporteur
* Espace = Rien



* Ensuite, ouvrez `levels/levels_config.json` et ajoutez une entrée pour le nouveau niveau. Inspirez-vous des niveaux existants.

Exemple d'entrée :

```json
"6": {
  "files": ["level6.txt"],
  "meta": "level6_meta.json"
}
```

* Créez ensuite le fichier méta dans `levels/`, par exemple `level6_meta.json`.
Champs importants :

  * `name` : nom affiché du niveau
  * `color` : couleur RGB sous forme de liste `[255, 128, 0]`
  * `reward` : nombre d'étoiles obtenues
  * `tps` : configuration des téléporteurs, `null` pour les portails non utilisés
  * `fow` : `true` ou `false`
  * `submap_routes` : optionnel, pour relier plusieurs cartes
Exemple de fichier méta :

```json
{
  "name": "Coffre caché",
  "color": [255, 128, 0],
  "reward": 2,
  "tps": [1, 0, 5, 4, null, null],
  "fow": false,
  "submap_routes": {
    "0": {
      "0": { "target_map": 1, "spawn_pos": [1, 1] }
    },
    "1": {
      "0": { "target_map": 0, "spawn_pos": [1, 1] }
    }
  }
}
```

* Si le niveau utilise plusieurs fichiers de carte, ajoutez plusieurs noms dans `files` et configurez `submap_routes` dans le fichier méta.




&#x20;



