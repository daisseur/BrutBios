désolé s'il y a des fautes d'anglais dans le code 😅
# BrutBios
Il existe peut-être des meilleures alternatives mais pourquoi se priver de tant de fun et de manque de sommeil ?

> Pourquoi ne pas brutforce un hash de mot de passe bios ? Pour une question de puissance de calcul ! donc il faudrait pouvoir partager cette puissance de calcul mais pas de manière trop chiante donc tadaaam !
> Bon le code est en anglais mais la page github en français, pas de logique, ça vous étonne ?

## ETAPES
- ### [1] GIT CLONE
  ```sh
  git clone https://github.com/daisseur/BrutBios/
  ```
- ### [2] EXECUTER TEST.PY
  ```sh
  python3 test.py
  ```
  > Le script va tester hashcat en générant des hashs sha256 salted et en les crackant. Mais il va aussi installer des librairies si besoin ou installer hashcat (je l'ai fait pour windows l'installation parce que c'est chiant). Pour linux faites tout seul c'est simple et mac je sais pas.
  
   PAS BESOIN DE DROITS ADMINS
- ### [3] EXECUTER MAIN.PY
    ```sh
  python3 main.py
  ```
  > Un magnifique petit script qui m'aura fait perdre 4 heures de sommeil et m'aura fait loupé mon éval de SVT
  
  > Le but est de gérer efficacement en partionnant la tâche, la première façon de partitionner la tâche est avec les masques donc `?u?u?l?u` par exemple. La deuxième façon est avec les checkpoint de hashcat qui sont ici sauvegardé ce qui permet d'avroir des processus pouvant être interrompu à tout moment

  Niveau interface...
  > Un tentative de menu et une tentative de jolie debug, à vous d'en juger mais ça marche en tout cas ( en principe )
  
  ![image](https://github.com/daisseur/BrutBios/assets/100715068/05aae33e-419a-41b5-a565-efd53f1677d0)
  #### 2 modes
  1)
  > Il ya donc le mode `benchmark` qui vas vous dire à quel point votre pc est mieux que le mien avec le nombre de Khash/s ou Mhash/s ça dépend (il s'agit du nombre de hashs pouvant être testé à la seconde). Vous avez ensuite l'affichage d'un joli texte vous indicant souvant le nombre d'années qu'il vous faudrait pour cracker le mdp du bios que je chercher
  
  2)
  > Et le mode principal `Run MainBrutForce` pour lancer la magnifique classe qui fait de ce programme un code orienté objet
- ### [4] ARRETER LE SCRIPT SANS TOUT CASSER
  > Pour arrêter le script et enregistrer au prochain mask il n'y a qu'à faire `python3 stop.py` sinon taper 'c' ou 'q' sur hashcat une fois lancé
  
## Pour tout problèmes...
 Soit un message sur discord soit une issue si vous êtes déterminé

 Le projet n'est pas fini mais le principal marche à peu près, il manque plus qu'une petite api web pour dire quel mask il faut faire, quel ordi est en train de tourner avec quel checkpoint. Mais aussi de mieux sélectionner quel Mask tester, actuellement c'est avec le json uniquement.


