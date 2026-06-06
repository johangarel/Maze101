# **MAZE101**

***---------------------------------------------------------------------------------------------------------------------------***

### ***ENGLISH :***

***---------------------------------------------------------------------------------------------------------------------------***

###### My first "official" python project. A maze game with pygame.

###### This is an alpha version of the game that has a pretty basic setup.



##### **How to play:**

* Open Project1.exe

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

* First, create on levels/ a new .txt file where you will have to make a grid of the level.



&#x09;Legend :

&#x09;W = Wall

&#x09;P = Player Spawn

&#x09;T = Trap

&#x09;S = Special teleporter (to load another map)

&#x09;E = Enemy

&#x09;lower case letter = Key

&#x09;Other upper case letter = Door (ex. Key "a" opens Door "A")

&#x09;Number = Teleporter

&#x09;Space = Nothing



* Then, open `levels/levels\\\\\\\\\\\\\\\_config.json` and add a new entry for the level. Use existing levels as examples.

Example entry:

```json
"6": {
  "files": \\\\\\\\\\\\\\\["level6.txt"],
  "meta": "level6\\\\\\\\\\\\\\\_meta.json"
}
```

* Create the meta file in `levels/`, for example `level6\\\\\\\\\\\\\\\_meta.json`.
Important fields:

  * `name`: display name for the level
  * `color`: RGB list like `\\\\\\\\\\\\\\\[255, 128, 0]`
  * `reward`: number of stars for completion
  * `tps`: teleporter mapping, using `null` for unused portals
  * `fow`: `true` or `false`
  * `submap\\\\\\\\\\\\\\\_routes`: optional routes between maps when using multiple files

Example meta file:

```json
{
  "name": "Hidden Vault",
  "color": \\\\\\\\\\\\\\\[255, 128, 0],
  "reward": 2,
  "tps": \\\\\\\\\\\\\\\[1, 0, 5, 4, null, null],
  "fow": false,
  "submap\\\\\\\\\\\\\\\_routes": {
    "0": {
      "0": { "target\\\\\\\\\\\\\\\_map": 1, "spawn\\\\\\\\\\\\\\\_pos": \\\\\\\\\\\\\\\[1, 1] }
    },
    "1": {
      "0": { "target\\\\\\\\\\\\\\\_map": 0, "spawn\\\\\\\\\\\\\\\_pos": \\\\\\\\\\\\\\\[1, 1] }
    }
  }
}
```

* If the level uses multiple maps, add several filenames to `files` and configure `submap\\\\\\\\\\\\\\\_routes` in the meta file.







***---------------------------------------------------------------------------------------------------------------------------***

### ***FRANCAIS :***

***---------------------------------------------------------------------------------------------------------------------------***

###### Mon premier projet Python « officiel ». Un jeu de labyrinthe avec Pygame.

###### Il s'agit d'une version alpha du jeu avec une configuration de base assez limitée.



##### **Comment jouer :**

* Ouvrir Project1.exe

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

* Créez d'abord un fichier .txt dans le répertoire levels/ où vous définirez la grille du niveau.

&#x09;

&#x09;Légende :

&#x09;W = Mur

&#x09;P = Point d'apparition du joueur

&#x09;T = Piège

&#x09;S = Téléporteur spécial (charger une autre carte)

&#x09;E = Enemi

&#x09;Lettre minuscule = Clé

&#x09;Autre lettre majuscule = Porte (ex. : la clé "a" ouvre la porte "A")

&#x09;Chiffre = Téléporteur

&#x09;Espace = Rien



* Ensuite, ouvrez `levels/levels\\\\\\\\\\\\\\\_config.json` et ajoutez une entrée pour le nouveau niveau. Inspirez-vous des niveaux existants.

Exemple d'entrée :

```json
"6": {
  "files": \\\\\\\\\\\\\\\["level6.txt"],
  "meta": "level6\\\\\\\\\\\\\\\_meta.json"
}
```

* Créez ensuite le fichier méta dans `levels/`, par exemple `level6\\\\\\\\\\\\\\\_meta.json`.
Champs importants :

  * `name` : nom affiché du niveau
  * `color` : couleur RGB sous forme de liste `\\\\\\\\\\\\\\\[255, 128, 0]`
  * `reward` : nombre d'étoiles obtenues
  * `tps` : configuration des téléporteurs, `null` pour les portails non utilisés
  * `fow` : `true` ou `false`
  * `submap\\\\\\\\\\\\\\\_routes` : optionnel, pour relier plusieurs cartes

Exemple de fichier méta :

```json
{
  "name": "Coffre caché",
  "color": \\\\\\\\\\\\\\\[255, 128, 0],
  "reward": 2,
  "tps": \\\\\\\\\\\\\\\[1, 0, 5, 4, null, null],
  "fow": false,
  "submap\\\\\\\\\\\\\\\_routes": {
    "0": {
      "0": { "target\\\\\\\\\\\\\\\_map": 1, "spawn\\\\\\\\\\\\\\\_pos": \\\\\\\\\\\\\\\[1, 1] }
    },
    "1": {
      "0": { "target\\\\\\\\\\\\\\\_map": 0, "spawn\\\\\\\\\\\\\\\_pos": \\\\\\\\\\\\\\\[1, 1] }
    }
  }
}
```

* Si le niveau utilise plusieurs fichiers de carte, ajoutez plusieurs noms dans `files` et configurez `submap\\\\\\\\\\\\\\\_routes` dans le fichier méta.





&#x20;

