# -*- coding: utf-8 -*-
"""Seed Python course - fixes lesson_type, quiz linking, images, documents."""
import sys, json
sys.path.insert(0, ".")

from app.db import get_db
from app.models import Module, Lesson, Quiz, QuizQuestion, QuizOption, ContentType
from sqlalchemy import text

db = next(get_db())
COURSE_ID = 36
SCHOOL_ID = 1
TEACHER_ID = 6

# Clean old data
db.execute(text("DELETE FROM quiz_options WHERE question_id IN (SELECT qq.id FROM quiz_questions qq JOIN quizzes q ON qq.quiz_id = q.id WHERE q.title LIKE 'Quiz :%')"))
db.execute(text("DELETE FROM quiz_questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE title LIKE 'Quiz :%')"))
db.execute(text("DELETE FROM quizzes WHERE title LIKE 'Quiz :%'"))
db.execute(text("DELETE FROM lessons WHERE module_id IN (SELECT id FROM modules WHERE course_id = 36)"))
db.execute(text("DELETE FROM modules WHERE course_id = 36"))
db.commit()
print("Cleaned old data")

modules_data = [
    {
        "title": "Introduction et Installation de Python",
        "desc": "Decouvrez Python, ses avantages, et configurez votre environnement.",
        "order": 1,
        "lessons": [
            {
                "title": "Qu'est-ce que Python ?",
                "desc": "Histoire et philosophie de Python",
                "lesson_type": "video",
                "content_text": "# Qu'est-ce que Python ?\n\nPython est un langage interprete, cree par Guido van Rossum en 1991.\n\nAvantages :\n- Syntaxe claire et lisible\n- Typage dynamique\n- Bibliotheque standard riche\n- Multi-paradigme\n\nDomaines : Web, Data Science, IA, Scripting, Jeux",
                "video_url": "https://www.youtube.com/embed/rfscVS0vtbw",
                "video_duration_seconds": 900,
                "duration_minutes": 15,
                "image_urls": '["https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"]',
            },
            {
                "title": "Installation de Python",
                "desc": "Installation sur Windows, Mac, Linux",
                "lesson_type": "video",
                "content_text": "# Installation de Python\n\n## Windows\n1. Telecharger python.org/downloads\n2. Cocher Add Python to PATH\n3. Install Now\n\n## Mac\nbrew install python3\n\n## Ubuntu\nsudo apt install python3 python3-pip\n\n## Verification\npython3 --version\n\n## IDE recommandes\n- **VS Code** avec extension Python\n- **PyCharm** Community\n- **Jupyter Notebook** pour l'exploration interactive",
                "video_url": "https://www.youtube.com/embed/YYXdXT2l-Gg",
                "video_duration_seconds": 600,
                "duration_minutes": 10,
                "document_url": "https://www.python.org/downloads/",
                "document_type": "Lien officiel",
            },
            {
                "title": "Premier programme",
                "desc": "Hello World et exercice pratique",
                "lesson_type": "text",
                "content_text": "# Premier Programme\n\n```python\nprint('Bonjour, le monde !')\n```\n\n## Variables et input\n```python\nnom = input('Votre nom ? ')\nprint(f'Bonjour {nom} !')\n```\n\n## Exercice : Calculatrice simple\n1. Demandez deux nombres a l'utilisateur\n2. Affichez la somme, la difference, le produit et le quotient",
                "duration_minutes": 15,
            },
        ],
        "quiz": {
            "title": "Quiz : Introduction et Installation de Python",
            "desc": "Testez vos connaissances sur l'introduction a Python",
            "questions": [
                ("En quelle annee Python a-t-il ete cree ?", "1991", ["1989", "1991", "1995", "2000"]),
                ("Qui est le createur de Python ?", "Guido van Rossum", ["James Gosling", "Guido van Rossum", "Bjarne Stroustrup", "Dennis Ritchie"]),
                ("Quelle extension pour un script Python ?", ".py", [".java", ".py", ".js", ".rb"]),
            ],
        },
    },
    {
        "title": "Types de donnees et Variables",
        "desc": "Entiers, flottants, chaines, booleens et listes.",
        "order": 2,
        "lessons": [
            {
                "title": "Variables et affectation",
                "desc": "Creer et manipuler des variables",
                "lesson_type": "text",
                "content_text": "# Variables et affectation\n\n```python\nnom = 'Alice'\nage = 25\ntaille = 1.75\nest_etudiant = True\n```\n\n## Regles\n- Commencer par lettre ou `_`\n- Pas d'espace dans le nom\n- `type(age)` -> `<class 'int'>`\n\n## Conversions\n```python\nstr(42)       # '42'\nint('42')     # 42\nfloat('3.14') # 3.14\n```",
                "duration_minutes": 12,
                "image_urls": '["https://miro.medium.com/max/1400/1*JAWxNM4mKUfIkLrpFOxhGA.png"]',
            },
            {
                "title": "Nombres et operateurs",
                "desc": "Arithmetique et comparaison",
                "lesson_type": "video",
                "content_text": "# Nombres et operateurs\n\n## Arithmetiques\n`+` `-` `*` `/` `//` (division entiere) `%` (modulo) `**` (puissance)\n\n## Comparaison\n`==` `!=` `>` `<` `>=` `<=`\n\n## Logiques\n`and` `or` `not`\n\n## Exemples\n```python\n10 // 3   # 3\n10 % 3    # 1\n2 ** 10   # 1024\n```",
                "video_url": "https://www.youtube.com/embed/kqtD5dpn9C8",
                "video_duration_seconds": 1080,
                "duration_minutes": 18,
            },
            {
                "title": "Chaines de caracteres",
                "desc": "Manipulation des strings",
                "lesson_type": "text",
                "content_text": "# Chaines de caracteres\n\n```python\ns = 'Python'\ns[0]     # 'P'\ns[-1]    # 'n'\ns[0:3]   # 'Pyt'\n```\n\n## Methodes utiles\n- `.upper()`, `.lower()`, `.title()`\n- `.strip()` - supprime espaces\n- `.split(',')` - decoupe en liste\n- `', '.join(liste)` - joint\n- `.replace('a', 'b')` - remplace\n\n## F-strings (formatage)\n```python\nprenom = 'Alice'\nage = 25\nprint(f'{prenom} a {age} ans')\n```",
                "duration_minutes": 15,
            },
            {
                "title": "Listes et tuples",
                "desc": "Structures de donnees ordonnees",
                "lesson_type": "text",
                "content_text": "# Listes et tuples\n\n## Listes (mutables)\n```python\nfruits = ['pomme', 'banane', 'cerise']\nfruits.append('datte')\nfruits.remove('pomme')\nlen(fruits)\n```\n\n## List comprehension\n```python\ncubes = [x**3 for x in range(10)]\npairs = [x for x in range(20) if x % 2 == 0]\n```\n\n## Tuples (immuables)\n```python\ncoord = (10, 20)\nx, y = coord\nprint(x)  # 10\n```\n\n- **Liste** : `[]` — mutable, modifiable\n- **Tuple** : `()` — immutable, plus rapide",
                "duration_minutes": 20,
                "image_urls": '["https://miro.medium.com/max/1400/1*YhMhXcY8Hw5iK3k0eK5h3A.png"]',
            },
        ],
        "quiz": {
            "title": "Quiz : Types de donnees et Variables",
            "desc": "Testez vos connaissances sur les types de donnees",
            "questions": [
                ("Quel est le type de 3.14 ?", "float", ["int", "float", "str", "bool"]),
                ("Quelle methode convertit en minuscules ?", ".lower()", [".lower()", ".down()", ".small()", ".min()"]),
                ("Longueur de 'Python' ?", "6", ["5", "6", "7", "4"]),
            ],
        },
    },
    {
        "title": "Structures de controle",
        "desc": "Conditions, boucles et flux d'execution.",
        "order": 3,
        "lessons": [
            {
                "title": "Conditions if/elif/else",
                "desc": "Branchements conditionnels",
                "lesson_type": "video",
                "content_text": "# Conditions\n\n```python\nage = 18\nif age >= 18:\n    print('Majeur')\nelif age >= 16:\n    print('Presque majeur')\nelse:\n    print('Mineur')\n```\n\n## Ternaire\n```python\nstatut = 'actif' if age >= 18 else 'inactif'\n```\n\n## Operateur `in`\n```python\nfruits = ['pomme', 'banane']\nif 'pomme' in fruits:\n    print('Trouve!')\n```",
                "video_url": "https://www.youtube.com/embed/Zp5MuPOtsSY",
                "video_duration_seconds": 840,
                "duration_minutes": 14,
            },
            {
                "title": "Boucles for et while",
                "desc": "Iterations et parcours",
                "lesson_type": "video",
                "content_text": "# Boucles\n\n## for\n```python\nfor fruit in ['pomme', 'banane', 'cerise']:\n    print(fruit)\n\nfor i in range(5):\n    print(i)  # 0, 1, 2, 3, 4\n\nfor i in range(2, 10, 2):\n    print(i)  # 2, 4, 6, 8\n```\n\n## while\n```python\ncompteur = 0\nwhile compteur < 5:\n    print(compteur)\n    compteur += 1\n```\n\n## break et continue\n- `break` arrete la boucle\n- `continue` saute l'iteration courante",
                "video_url": "https://www.youtube.com/embed/9OeznAkyQz4",
                "video_duration_seconds": 1080,
                "duration_minutes": 18,
            },
            {
                "title": "Exercice : Mini-jeu de devinette",
                "desc": "Jeu de devinette avec les conditions",
                "lesson_type": "text",
                "content_text": "# Exercice : Jeu de Devinette\n\n```python\nimport random\n\nsecret = random.randint(1, 100)\ntentatives = 0\nmax_tentatives = 7\n\nprint('Devinez un nombre entre 1 et 100!')\n\nwhile tentatives < max_tentatives:\n    guess = int(input('Votre proposition : '))\n    tentatives += 1\n    \n    if guess == secret:\n        print(f'Bravo! Trouve en {tentatives} tentatives!')\n        break\n    elif guess < secret:\n        print('Trop petit!')\n    else:\n        print('Trop grand!')\nelse:\n    print(f'Desole, le nombre etait {secret}')\n```\n\n## A vous de jouer!\n1. Creez ce fichier `devinette.py`\n2. Lancez-le avec `python devinette.py`\n3. Essayez de gagner en moins de 7 tentatives",
                "duration_minutes": 25,
            },
        ],
        "quiz": {
            "title": "Quiz : Structures de controle",
            "desc": "Conditions et boucles",
            "questions": [
                ("Que fait elif ?", "Teste une condition alternative", ["Termine le programme", "Teste une condition alternative", "Repete une boucle", "Declare une variable"]),
                ("Quelle boucle itere sur une sequence ?", "for", ["while", "for", "loop", "repeat"]),
                ("Que fait break ?", "Arrete la boucle", ["Sauter l'iteration", "Arrete la boucle", "Redemarre", "Rien"]),
            ],
        },
    },
    {
        "title": "Fonctions",
        "desc": "Creer, parametrer et reutiliser du code.",
        "order": 4,
        "lessons": [
            {
                "title": "Definition et appels de fonctions",
                "desc": "Creer des fonctions avec def",
                "lesson_type": "video",
                "content_text": "# Fonctions\n\n```python\ndef saluer(nom):\n    return f'Bonjour {nom} !'\n\nmessage = saluer('Alice')\nprint(message)\n```\n\n## Parametres par defaut\n```python\ndef pres(nom, age, ville='Paris'):\n    print(f'{nom}, {age} ans, a {ville}')\n\npres('Alice', 25)\npres('Bob', 30, 'Lyon')\n```\n\n## Retour multiple\n```python\ndef calc(a, b):\n    return a + b, a * b\n\nsomme, produit = calc(3, 4)\n```",
                "video_url": "https://www.youtube.com/embed/9Os0o3wzS_I",
                "video_duration_seconds": 960,
                "duration_minutes": 16,
            },
            {
                "title": "Portee et fonctions lambda",
                "desc": "Scope et fonctions anonymes",
                "lesson_type": "text",
                "content_text": "# Portee et Lambda\n\n## Portee (Scope)\n```python\nx = 'global'\n\ndef ma_fct():\n    x = 'local'\n    print(x)  # local\n\nma_fct()\nprint(x)  # global\n```\n\n## Lambda (fonctions anonymes)\n```python\ndoubler = lambda x: x * 2\nadd = lambda a, b: a + b\n\nprint(doubler(5))  # 10\nprint(add(3, 4))   # 7\n```\n\n## Utilise avec sorted, map, filter\n```python\nnoms = ['Alice', 'Bob', 'Charlie']\nnoms.sort(key=lambda x: len(x))\n# ['Bob', 'Alice', 'Charlie']\n\ncarres = list(map(lambda x: x**2, range(5)))\n# [0, 1, 4, 9, 16]\n```\n\n## Decorateurs\n```python\ndef timer(f):\n    def wrapper(*args):\n        import time\n        start = time.time()\n        result = f(*args)\n        print(f'{f.__name__} execute en {time.time()-start:.2f}s')\n        return result\n    return wrapper\n```",
                "duration_minutes": 14,
                "image_urls": '["https://miro.medium.com/max/1400/1*VJtX7z7dK4d3Y3Y3Y3Y3YQ.png"]',
            },
        ],
        "quiz": {
            "title": "Quiz : Fonctions",
            "desc": "Testez vos connaissances sur les fonctions",
            "questions": [
                ("Quel mot-cle definit une fonction ?", "def", ["func", "def", "function", "define"]),
                ("Qu'est-ce qu'une lambda ?", "Fonction anonyme", ["Fonction avec decorateur", "Fonction anonyme", "Une variable", "Un module"]),
                ("Que retourne return a, b ?", "Un tuple", ["Une liste", "Un tuple", "Deux valeurs", "Rien"]),
            ],
        },
    },
    {
        "title": "Dictionnaires, Sets et Collections",
        "desc": "Structures de donnees avancees.",
        "order": 5,
        "lessons": [
            {
                "title": "Dictionnaires",
                "desc": "Paires cle-valeur",
                "lesson_type": "video",
                "content_text": "# Dictionnaires\n\n```python\nstudent = {'nom': 'Alice', 'age': 22, 'filiere': 'Info'}\nprint(student['nom'])  # Alice\nstudent.get('age')     # 22\nstudent.get('ville', 'N/A')  # N/A (defaut)\n```\n\n## Iteration\n```python\nfor cle, val in student.items():\n    print(f'{cle}: {val}')\n\nfor cle in student.keys():\n    print(cle)\n\nfor val in student.values():\n    print(val)\n```\n\n## Dict comprehension\n```python\ncarres = {x: x**2 for x in range(6)}\n# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25}\n```\n\n## Dictionnaires imbriques\n```python\npersonne = {\n    'nom': 'Alice',\n    'adresses': [\n        {'type': 'domicile', 'rue': '123 Rue A'},\n        {'type': 'bureau', 'rue': '456 Rue B'}\n    ]\n}\n```",
                "video_url": "https://www.youtube.com/embed/daefaLgNkw0",
                "video_duration_seconds": 960,
                "duration_minutes": 16,
            },
            {
                "title": "Sets et collections avancees",
                "desc": "Ensembles et outils de collections",
                "lesson_type": "text",
                "content_text": "# Sets et Collections Avancees\n\n## Sets (enssemble sans doublons)\n```python\na = {1, 2, 3}\nb = {3, 4, 5}\n\na | b   # union: {1, 2, 3, 4, 5}\na & b   # intersection: {3}\na - b   # difference: {1, 2}\na ^ b   # difference symetrique: {1, 2, 4, 5}\n```\n\n## Counter\n```python\nfrom collections import Counter\n\ntexte = 'bonjour le monde'\nc = Counter(texte)\nprint(c.most_common(3))\n# [('o', 3), ('n', 2), (' ', 2)]\n```\n\n## defaultdict\n```python\nfrom collections import defaultdict\n\nd = defaultdict(list)\nd['fruits'].append('pomme')\nd['fruits'].append('banane')\n# {'fruits': ['pomme', 'banane']}\n```\n\n## namedtuple\n```python\nfrom collections import namedtuple\n\nPoint = namedtuple('Point', ['x', 'y'])\np = Point(10, 20)\nprint(p.x, p.y)  # 10 20\n```",
                "duration_minutes": 14,
            },
        ],
        "quiz": {
            "title": "Quiz : Dictionnaires et Sets",
            "desc": "Structures de donnees avancees",
            "questions": [
                ("Comment acceder a une valeur du dict ?", "dict.get()", ["dict.get()", "dict[]", "dict.value()", "dict.access()"]),
                ("Un set ne contient pas de...", "Doublons", ["Elements", "Doublons", "Cles", "Valeurs"]),
            ],
        },
    },
    {
        "title": "Programmation Objet (POO)",
        "desc": "Classes, objets, heritage et polymorphisme.",
        "order": 6,
        "lessons": [
            {
                "title": "Classes et objets",
                "desc": "Instances, attributs, methodes",
                "lesson_type": "video",
                "content_text": "# Classes et Objets\n\n```python\nclass Voiture:\n    def __init__(self, marque, vitesse=0):\n        self.marque = marque\n        self.vitesse = vitesse\n    \n    def accelerer(self, inc=10):\n        self.vitesse += inc\n        return self\n    \n    def freiner(self, dec=10):\n        self.vitesse = max(0, self.vitesse - dec)\n        return self\n    \n    def __str__(self):\n        return f'{self.marque} a {self.vitesse} km/h'\n\n# Utilisation\nv = Voiture('Toyota')\nv.accelerer(50)\nprint(v)  # Toyota a 50 km/h\n```\n\n## Proprietes\n```python\nclass Cercle:\n    def __init__(self, rayon):\n        self._rayon = rayon\n    \n    @property\n    def aire(self):\n        return 3.14159 * self._rayon ** 2\n\nc = Cercle(5)\nprint(f'Aire: {c.aire}')  # 78.54\n```",
                "video_url": "https://www.youtube.com/embed/ZDa-Z5JzLYM",
                "video_duration_seconds": 1200,
                "duration_minutes": 20,
                "image_urls": '["https://miro.medium.com/max/1400/1*5E3Y3Y3Y3Y3Y3Y3Y3Y3YQ.png"]',
            },
            {
                "title": "Heritage et polymorphisme",
                "desc": "Classes parentes et enfants",
                "lesson_type": "video",
                "content_text": "# Heritage et Polymorphisme\n\n```python\nclass Animal:\n    def parler(self):\n        raise NotImplementedError\n    \n    def __str__(self):\n        return self.__class__.__name__\n\nclass Chien(Animal):\n    def parler(self):\n        return 'Wouf !'\n    \n    def caresser(self):\n        return 'Le chien remue la queue'\n\nclass Chat(Animal):\n    def parler(self):\n        return 'Miaou !'\n    \n    def caresser(self):\n        return 'Le chat ronronne'\n\n# Polymorphisme\nanimaux = [Chien(), Chat()]\nfor a in animaux:\n    print(f'{a}: {a.parler()}')\n\n# Verifier le type\nchien = Chien()\nisinstance(chien, Animal)  # True\nisinstance(chien, Chien)   # True\n```\n\n## Methode super()\n```python\nclass Employe(Personne):\n    def __init__(self, nom, salaire):\n        super().__init__(nom)\n        self.salaire = salaire\n```",
                "video_url": "https://www.youtube.com/embed/3ohzBxnf2Ys",
                "video_duration_seconds": 1080,
                "duration_minutes": 18,
            },
            {
                "title": "Projet : Systeme de Bibliotheque",
                "desc": "Creez un petit systeme de gestion de bibliotheque",
                "lesson_type": "text",
                "content_text": "# Projet : Systeme de Bibliotheque\n\n## Livre\n```python\nclass Livre:\n    def __init__(self, titre, auteur, isbn):\n        self.titre = titre\n        self.auteur = auteur\n        self.isbn = isbn\n        self.disponible = True\n    \n    def emprunter(self):\n        if self.disponible:\n            self.disponible = False\n            return True\n        return False\n    \n    def retourner(self):\n        self.disponible = True\n    \n    def __str__(self):\n        statut = 'Disponible' if self.disponible else 'Emprunte'\n        return f'{self.titre} par {self.auteur} [{statut}]'\n```\n\n## Bibliotheque\n```python\nclass Bibliotheque:\n    def __init__(self, nom):\n        self.nom = nom\n        self.livres = []\n    \n    def ajouter(self, livre):\n        self.livres.append(livre)\n    \n    def chercher(self, titre):\n        return [l for l in self.livres if titre.lower() in l.titre.lower()]\n    \n    def cataloguer(self):\n        print(f'=== Catalogue : {self.nom} ===')\n        for l in self.livres:\n            print(f'  {l}')\n```\n\n## A vous de jouer!\n1. Creez les classes ci-dessus\n2. Ajoutez 3 livres a la bibliotheque\n3. Testez emprunt et retour\n4. Ajoutez une methode `rechercher_par_auteur(auteur)`\n5. Ajoutez un compteur d'emprunts",
                "duration_minutes": 30,
                "image_urls": '["https://upload.wikimedia.org/wikipedia/commons/6/65/Circle-icons-book.svg"]',
                "document_url": "https://docs.python.org/3/tutorial/classes.html",
                "document_type": "Lien",
            },
        ],
        "quiz": {
            "title": "Quiz : Programmation Objet",
            "desc": "POO en Python",
            "questions": [
                ("Premier parametre d'une methode ?", "self", ["this", "self", "cls", "moi"]),
                ("Mot-cle du constructeur ?", "__init__", ["__init__", "__new__", "__start__", "__create__"]),
                ("L'heritage permet de...", "Reutiliser le code parent", ["Creer des variables", "Reutiliser le code parent", "Supprimer des methodes", "Acceder a la BDD"]),
                ("Qu'est-ce que le polymorphisme ?", "Meme interface, comportements differents", ["Suppression", "Meme interface, comportements differents", "Tuples", "Encapsulation"]),
                ("Role de super() ?", "Appeler la classe parente", ["Creer un objet", "Appeler la classe parente", "Supprimer", "Import"]),
            ],
        },
    },
]

lesson_id_counter = 0
for mod_data in modules_data:
    mod = Module(course_id=COURSE_ID, title=mod_data["title"], description=mod_data["desc"], order=mod_data["order"])
    db.add(mod)
    db.flush()
    print(f"Module {mod.order}: {mod.title}")

    last_lesson_id = None
    for i, ld in enumerate(mod_data["lessons"]):
        ct = ContentType.VIDEO if ld["lesson_type"] == "video" else ContentType.TEXT
        lesson = Lesson(
            module_id=mod.id, school_id=SCHOOL_ID, teacher_id=TEACHER_ID,
            title=ld["title"], description=ld["desc"],
            lesson_type=ld["lesson_type"],  # FIX: set lesson_type correctly
            content_type=ct,
            content_text=ld["content_text"],
            video_url=ld.get("video_url"),
            video_duration_seconds=ld.get("video_duration_seconds"),
            pdf_url=ld.get("pdf_url"),
            document_url=ld.get("document_url"),
            document_type=ld.get("document_type"),
            image_urls=ld.get("image_urls"),
            duration_minutes=ld.get("duration_minutes", 10),
            order=i + 1,
        )
        db.add(lesson)
        db.flush()
        last_lesson_id = lesson.id
        lesson_id_counter += 1
        print(f"  Lesson {i+1}: [{ld['lesson_type']}] {ld['title']}")

    # Create quiz and link it to the LAST lesson of the module
    qd = mod_data["quiz"]
    quiz = Quiz(
        lesson_id=last_lesson_id,  # FIX: link quiz to lesson
        title=qd["title"], description=qd["desc"],
        passing_score_percent=70, total_points=len(qd["questions"]),
    )
    db.add(quiz)
    db.flush()
    print(f"  Quiz: {len(qd['questions'])} questions -> linked to lesson {last_lesson_id}")

    for qi, (q_text, correct, opts) in enumerate(qd["questions"]):
        qq = QuizQuestion(quiz_id=quiz.id, question_text=q_text, question_type="mcq", points=1, order_index=qi)
        db.add(qq)
        db.flush()
        for oi, opt in enumerate(opts):
            db.add(QuizOption(question_id=qq.id, option_text=opt, is_correct=(opt == correct), order_index=oi))
    db.flush()

# Update course stats
db.execute(text("UPDATE courses SET total_modules = 6, total_lessons = :nl, is_published = true, status = 'PUBLISHED' WHERE id = 36"), {"nl": lesson_id_counter})
db.commit()
print(f"\nDone! Course 36 seeded: {len(modules_data)} modules, {lesson_id_counter} lessons, {len(modules_data)} quizzes")
