"""
Seed script: 120+ elements pedagogiques SVT (Sciences de la Vie et de la Terre)
pour la bibliotheque globale du Builder de Parcours.

Usage: cd backend && python seed_svt_elements.py
Idempotent: verifie les titres avant insertion.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import random
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"
engine = create_engine(DATABASE_URL)


# ── SVT Matiere IDs (from DB) ──────────────────────────────────
SVT_MATIERES = {
    87: 640,   # 7eme Base
    88: 655,   # 8eme Base
    89: 670,   # 9eme Base
    90: 685,   # 1ere Secondaire
    92: 709,   # 2eme Sciences
    96: 755,   # 3eme Maths
    97: 767,   # 3eme Sciences Exp
    102: 820,  # Bac Maths
    103: 832,  # Bac Sciences Exp
}

NIVEAUX_NAMES = {
    87: "7eme Base",
    88: "8eme Base",
    89: "9eme Base",
    90: "1ere Secondaire",
    92: "2eme Sciences",
    96: "3eme Maths",
    97: "3eme Sciences Exp",
    102: "Bac Maths",
    103: "Bac Sciences Exp",
}

AUTHOR_ID = 1

# ── SVT Content Data ───────────────────────────────────────────

TEXTES = [
    ("La cellule : structure et fonction", "La cellule est l'unite fondamentale du vivant. Elle est constituee d'une membrane plasmique qui delimite son perimetre et regle les echanges avec l'exterieur. Le cytoplasme contient les organites : noyau (contenant l'ADN), mitochondries (respiration cellulaire), reticulum endoplasmique, ribosomes (synthese proteique), apparatus de Golgi (secretion), et lysosomes (digestion intracellulaire)."),
    ("Les organites cellulaires", "Chaque organelle a un role specifique. Les mitochondries produisent l'ATP par phosphorylation oxydative. Le noyau controle l'expression genetique. Les ribosomes traduisent l'ARNm en proteines. Le reticulum endoplasmique rough synthetise les proteines destinees a la secretion, tandis que le smooth synthetise les lipides."),
    ("La membrane plasmique", "La membrane plasmique suit le modele de la mosaique fluide. Elle est composee d'une double couche de phospholipides avec des proteines integrales (transmembranaires) et peripheriques. Les cholesterol regulent la fluidite. Les glycoproteines et glycolipides participent a la reconnaissance cellulaire."),
    ("La mitose et la meiose", "La mitose est une division cellulaire produant deux cellules filtres identiques a la cellule mere. Elle comprend 4 phases : prophase, meta phase, anaphase, telephase. La meiose est une division reductionnelle produisant 4 gametes haploides. Elle comporte deux divisions successives (meiose I et II)."),
    ("Le cycle cellulaire", "Le cycle cellulaire comprend l'interphase (G1, S, G2) et la phase M (mitose + cytokinese). Pendant G1, la cellule grandit. En S, l'ADN est replicate. En G2, la cellule se prepare a la division. Les checkpoints G1/S et G2/M empechent les erreurs de replication."),
    ("L'ADN et la replication", "L'ADN est une double helice de nucleotides (A-T, G-C). La replication est semi-conservative : chaque brin sert de matrice. L'ADN polymerase III synthetise le brin leader en continu et le brin retardataire en fragments d'Okazaki. La ligase joint ces fragments."),
    ("La transcription et la traduction", "La transcription copie l'ADN en ARNm par l'ARN polymerase. La traduction se fait au niveau des ribosomes : l'ARNm est decode en sequence d'acides amines selon le code genetique (triplets/codons). L'ARNt amene les acides amines correspondants."),
    ("La photosynthese : generalites", "La photosynthese transforme l'energie lumineuse en energie chimique. Elle se deroule dans les chloroplastes en deux etapes : les reactions photodependantes (thylakoides) et le cycle de Calvin (stroma). Les reactifs sont CO2 + H2O, les produits sont glucose + O2."),
    ("Les reactions photodependantes", "Dans les thylakoides, les photons excitent les pigments photosynthetiques (chlorophylle a et b, carotenoides). Le photosysteme II (PSII) scinde l'eau (photolyse) liberant O2. La chaine de transport d'electrons genere un gradient protonique. Le photosysteme I (PSI) reduit le NADP+ en NADPH. L'ATP synthase produce l'ATP par chemiosmose."),
    ("Le cycle de Calvin", "Le cycle de Calvin (stroma) fixe le CO2 en glucose en 3 etapes : 1) Fixation par la rubisco formant du 3-PGA, 2) Reduction en G3P utilisant ATP et NADPH, 3) Regeneration du RuBP. Trois CO2 sont necessaires pour produire un G3P. Six tours produisent un glucose."),
    ("La respiration cellulaire", "La respiration cellulaire oxyde le glucose en CO2 et H2O pour produire l'ATP. Elle comprend 3 etapes : 1) Glycolyse (cytoplasme) : glucose -> 2 pyruvate + 2 ATP + 2 NADH, 2) Cycle de Krebs (matrice mitochondriale) : pyruvate -> CO2 + NADH + FADH2, 3) Chaine d'electron transport (membrane interne) : NADH/FADH2 -> H2O + 34 ATP."),
    ("La glycolyse", "La glycolyse se deroule dans le cytoplasme en 10 etapes enzymatiques. Elle convertit le glucose (6C) en 2 pyruvates (3C). Elle consomme 2 ATP en phase d'investissement et en produit 4 en phase de gain (bilan net : 2 ATP). Elle genere egalement 2 NADH."),
    ("Le cycle de Krebs", "Le cycle de Krebs (acide citrique) se deroule dans la matrice mitochondriale. L'acetyl-CoA (2C) se combine avec l'oxaloacetate (4C) pour former le citrate (6C). En 8 etapes, il est decarboxyle en regenerant l'oxaloacetate. Bilan : 2 CO2 + 3 NADH + 1 FADH2 + 1 GTP par tour."),
    ("La chaine de transport d'electrons", "Sur la membrane interne mitochondriale, les complexe I a IV transferent les electrons du NADH et FADH2 vers O2 (accepteur final). Le gradient de protons (H+) genere est utilise par l'ATP synthase (complex V) pour produire l'ATP (chemiosmose). O2 est reduit en H2O."),
    ("Le systeme digestif humain", "Le tube digestif comprend : bouche (mastication, amylase salivaire), oesophage (deglutition), estomac (pepsine, HCl), intestin grele (absorption : villosites, microvillosites), gros intestin (absorption eau, bacteries), rectum et anus (excretion). Les annexes : foie, pancreas, vesicule biliaire."),
    ("L'estomac et la digestion proteique", "L'estomac secrete le suc gastrique : HCl (pH 1.5-2.5, denaturation proteique, activation pepsinogene), pepsinogene -> pepsine (hydrolyse proteique). Le mucus protege la paroi gastrique. La gastrine stimule la secretion acide. Le cholagogue stimule la contraction vesiculaire."),
    ("L'intestin grele et l'absorption", "L'intestin grele (duodenum, jelon, ileon) est le principal site d'absorption. Les villosites et microvillosites augmentent la surface absorptive (x600). Les sucs pancreatiques (lipases, amylases, proteases) et biliaires (emulsification lipides) completent la digestion. Les entero absorbe nutriments via diffusion, osmose ou transport actif."),
    ("Le foie et le pancreas", "Le foie a des fonctions multiples : secretion biliaire (emulsification lipides), metabolisme du glucose (glycogenolyse, glycogenese, gluconeoegenese), detoxification, stockage vitamines et fer. Le pancreas exocrine secrete les sucs digestifs. Le pancreas endocrine (ilots de Langerhans) secrete insuline et glucagon."),
    ("Le coeur et la circulation sanguine", "Le coeur est un muscle creux a 4 cavites : oreillettes (reception) et ventricules (ejection). La circulation grande (systemique) : ventricule gauche -> aorte -> arteres -> capillaires -> veines -> veine cave -> oreillette droite. La circulation pulmonaire : ventricule droit -> artere pulmonaire -> poumons -> veine pulmonaire -> oreillette gauche."),
    ("Le systeme cardiovasculaire", "Le sang est constitue de plasma (55%), globules rouges (45%, hemoglobine, transport O2), globules blancs (defense immune), plaquettes (coagulation). Les arteres transportent le sang oxygene (sauf pulmonaire). Les veines retournent le sang au coeur (sauf pulmonaire). Les capillaires assurent les echanges."),
    ("La pression arterielle", "La pression arterielle est le rapport de la force exercee par le sang sur la paroi vasculaire. Systolique (max, contraction ventriculaire) / Diastolique (min, relachement). Normale : 12/8 cmHg. Regulee par : systeme nerveux sympathique, systeme renine-angiotensine, atrial natriuretique."),
    ("Le systeme respiratoire", "Les voies aeriennes : nez/pharynx/larynx/conduits bronchiques/bronchioles/alveoles. Les alveoles (300 millions) sont le site des echanges gazeux. Surface totale : 70 m2. Le surfactant pulmonaire empeche l'effondrement alveolaire. La ventilation est regulee par le centre respiratoire (bulbe rachidien)."),
    ("Les echanges gazeux", "Les echanges gazeux se font par diffusion passive selon les pressions partielles. PO2 alveolaire > PO2 sanguine = oxygene diffuse vers le sang. PCO2 sanguine > PCO2 alveolaire = CO2 diffuse vers les alveoles. L'hemoglobine transporte 97% de l'O2 (oxyhemoglobine) et le CO2 sous forme de bicarbonates (70%)."),
    ("Le systeme nerveux", "Le systeme nerveux central (cerveau + moelle epiniere) et peripherique (nerfs). Le neurone : soma, dendrites (reception), axone (conduction), myeline (gaine de Schwann). La synapse chimique : liberation de neurotransmetteurs (acetylcholine, dopamine, serotonine). Potentiel d'action : depolarisation/repolarisation."),
    ("Le potentiel d'action", "Le potentiel d'action est une inversion rapide du potentiel de membrane. Au repos : -70 mV (canaux K+ ouverts). Stimulation -> ouverture canaux Na+ -> depolarisation (+30 mV) -> fermeture canaux Na+, ouverture canaux K+ -> repolarisation -> hyperpolarisation. Refractarite : pas de nouveau PA possible."),
    ("La transmission synaptique", "A la synapse chimique, le potentiel d'action arrive au bout terminal -> ouverture canaux Ca2+ -> liberation du neurotransmetteur dans la fente synaptique -> liaison aux recepteurs postsynaptiques (ionotropes ou metabotropes) -> generation d'un potentiel postsynaptique (excitateur EPSP ou inhibiteur IPSP)."),
    ("Le systeme endocrinien", "Le systeme endocrinien regule les fonctions par les hormones (messagers chimiques). Glandes principales : hypothalamus (CRH), hypophyse (TSH, ACTH, GH), thyroide (T3, T4), surrenales (cortisol, adrenaline), pancreas (insuline, glucagon), gonades (oestrogenes, testosterone). Feedback negatif."),
    ("L'homéostasie", "L'homéostasie est le maintien du milieu interieur stable. Exemples : glycemie (insuline/glucagon), temperature (vasodilatation/vasoconstriction), calcemie (PTH/calcitonine), pression osmotique (ADH). Regulation par feedback negatif (inverse) ou positif (amplificateur)."),
    ("La reproduction humaine", "La reproduction humaine est sexuee. Spermatogenese (testicules, 74 jours, millions de spermatozoides) et ovogenese (ovaires, cyclicite menstruelle). Fecundation dans la trompe de Fallope -> zygote -> morula -> blastocyste -> implantation (jour 6-7). Placenta : echanges nutritifs et gazeux."),
    ("La genetique mendelienne", "Gregor Mendel (1866) a decouvert les lois de l'heredite. 1) Disjonction des alleles : chaque parent transmet un allele. 2) Independance des caracteres. 3) Dominance : l'allele dominant masque le recessif. Genotype (AA, Aa, aa) et phenotype. Ratio mendelien : 3:1 (F2)."),
    ("L'heredite et les chromosomes", "L'ADN est organise en chromosomes (23 paires, 46 au total). Le caryotype montre les chromosomes en meta phase. Les autosomes (22 paires) portent les genes somatiques. Le chromosome 23 determine le sexe (XX = femme, XY = homme). Les genes sont des segments d'ADN codant pour des proteines."),
    ("Les mutations genetiques", "Les mutations sont des alterations de la sequence d'ADN. Point mutation (substitution, insertion, deletion). Frameshift (insertion/deletion de nucleotides). Chromosomique (translocation, duplication, inversion, deletion). Les mutations peuvent etre silencieuses, missense (acide amine change), nonsense (codon stop), ou splice."),
    ("L'ecosysteme et ses composants", "Un ecosysteme est un ensemble d'organismes (biocenose) et de leur environnement (biotope). Composants biotiques : producteurs (plantes), consommateurs (herbivores, carnivores), decomposeurs (bacteries, champignons). Composants abiotiques : temperature, lumiere, eau, sol, mineraux."),
    ("Les chaines et reseaux alimentaires", "La chaine alimentaire est un parcours d'energie : producteur -> herbiore -> carnivore primaire -> carnivore secondaire. A chaque etape, 90% de l'energie est perdue (chaleur). Le reseau alimentaire croise les chaines. Pyramide des nombres, biomasse, energie."),
    ("La biodiversite", "La biodiversite comprend la diversite genetique, specifique et ecosystemique. Elle est menacee par : destruction des habitats, pollution, changements climatiques, especes invasives, surexploitation. Les aires protegees (parcs nationaux, reserves) et les conventions (CITES, CBD) visent sa conservation."),
    ("Les cycles biogeochimiques", "Les elements chimiques circulent entre biotope et biocenose. Cycle de l'eau : evaporation, condensation, precipitation, ruissellement. Cycle du carbone : photosynthese, respiration, fossilisation. Cycle de l'azote : fixation bacterienne, nitrification, denitrification. Cycle du phosphore : roches -> sol -> organismes."),
    ("L'evolution et la selection naturelle", "Charles Darwin (1859) : la selection naturelle favorise les individus les mieux adaptes a leur environnement. Variabilite genetique (mutations, recombinaison) -> competition pour les ressources -> survie et reproduction differentialles -> evolution des populations (changement de frequences alléliques)."),
    ("La teire et sa composition", "La Terre a une structure concentrique : croûte (5-70 km), manteau (2900 km), noyau externe (liquide, 2200 km), noyau interne (solide, 1200 km). La croûte continentale (granite, 35 km) et oceanique (basalte, 7 km). Les plaques tectoniques se deplacent sur l'asthenosphere."),
    ("La lithosphere et les plaques tectoniques", "La lithosphere (croûte + manteau superieur rigide) est decoupee en 15 plaques principales. Les limites : divergentes (dorsales oceaniques, rift), convergentes (zones de subduction, collision), transformantes (failles decrochantes). Le volcanisme et les seismes sont lies a ces limites."),
    ("Les seismes et les volcans", "Un seisme est une liberation brutale d'energie le long d'une faille. Focus (hypocentre), epicentre, ondes sismiques (P, S, L). L'echelle de Richter mesure la magnitude. Un volcan est un orifice terrestre rejetant lave, gaz, cendres. Types : bouclier, composite, stratovolcan. Eruptions : effusive/explosive."),
    ("La composition de l'atmosphere terrestre", "L'atmosphere terrestre : N2 (78%), O2 (21%), Ar (0.9%), CO2 (0.04%), vapeur d'eau (variable). Zones : troposphere (0-12 km, meteo), stratosphere (12-50 km, couche d'ozone), mesosphere (50-80 km), thermosphere (80-700 km), exosphere (>700 km)."),
    ("Le cycle de l'eau", "Le cycle de l'eau (cycle hydrologique) : evaporation (oceans, lacs), transpiration (plantes), condensation (nuages), precipitation (pluie, neige), ruissellement (rivières), infiltration (eaux souterraines), et evaporation a nouveau. 97% dans les oceans, 2% glaciers, 1% eaux douces."),
    ("Les perturbations de l'environnement", "Le rechauffement climatique (augmentation CO2, effet de serre), la pollution (atmospherique, eau, sol), la deforestation, l'erosion, la desertification, les dechets plastiques. Solutions : energies renouvelables, recyclage, foresterie durable, agriculture biologique."),
    ("Le microscope et l'observation biologique", "Le microscope optique grossit x1000. Le microscope electronique a transmission (MET) grossit x500000 (ultrastructure). Le microscope electronique a balayage (MEB) donne des images 3D de surface. Techniques : coloration (hematoxiline-eosine, Gram), coupes ultra-fines, cryofracture."),
    ("La classification du vivant", "La classification biologique (Linnee, 1735) organise le vivant en domaines, royaumes, embranchements, classes, ordres, familles, genres, especes. La classification phylogenetique (cladistique) groupe les organismes selon leur ancetre commun. Les domaines : Bacteria, Archaea, Eukarya."),
    ("Les bacteries et les virus", "Les bacteries sont des procaryotes unicellulaires (ADN libre). Parois (peptidoglycane), flagelles, plasmides. Reproduction : bipartition. Les virus sont des parasites intracellulaires obligatoires (ADN ou ARN, capside). Repliquation : lytique (destruction) ou lysogenique (integration)."),
]

VIDEOS = [
    ("Vidéo : La cellule et ses organites", "https://www.youtube.com/watch?v=FzcAgr8Bhhg", 600, "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=400"),
    ("Vidéo : La mitose expliquée", "https://www.youtube.com/watch?v=aJg3u2dLz0w", 540, "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400"),
    ("Vidéo : La photosynthèse complète", "https://www.youtube.com/watch?v=sQK3Yr4Sc_k", 720, "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=400"),
    ("Vidéo : Le cycle de Calvin", "https://www.youtube.com/watch?v=RvKxdlZMB5k", 480, "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400"),
    ("Vidéo : La respiration cellulaire", "https://www.youtube.com/watch?v=obp1Pk5tVqs", 660, "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400"),
    ("Vidéo : Le cycle de Krebs", "https://www.youtube.com/watch?v=kfR1mZ1T0gQ", 540, "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400"),
    ("Vidéo : Le système digestif humain", "https://www.youtube.com/watch?v=G018aVn1K8o", 780, "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400"),
    ("Vidéo : Le cœur et la circulation", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 720, "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400"),
    ("Vidéo : Le système nerveux", "https://www.youtube.com/watch?v=H71nX6WA9Rw", 600, "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400"),
    ("Vidéo : Le potentiel d'action", "https://www.youtube.com/watch?v=W2hKfAdSidg", 540, "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=400"),
    ("Vidéo : Le système endocrinien", "https://www.youtube.com/watch?v=Vq1LhNwJnMs", 660, "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=400"),
    ("Vidéo : La génétique mendelienne", "https://www.youtube.com/watch?v=K4G7xHt8tBk", 720, "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400"),
    ("Vidéo : Les chromosomes", "https://www.youtube.com/watch?v=VzDGz-0nVbY", 480, "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400"),
    ("Vidéo : L'écosystème et ses composants", "https://www.youtube.com/watch?v=0rJDh35pmbI", 600, "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=400"),
    ("Vidéo : La biodiversité menacée", "https://www.youtube.com/watch?v=3b5bX8zK3yI", 540, "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400"),
    ("Vidéo : Les cycles biogéochimiques", "https://www.youtube.com/watch?v=V4UPO9e9yYs", 660, "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400"),
    ("Vidéo : L'évolution et sélection naturelle", "https://www.youtube.com/watch?v=GhHOjC4oxh8", 720, "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400"),
    ("Vidéo : Les plaques tectoniques", "https://www.youtube.com/watch?v=MnL4m6n0Y4k", 600, "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400"),
    ("Vidéo : Les séismes et volcans", "https://www.youtube.com/watch?v=UzgwgZ3hOHs", 540, "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=400"),
    ("Vidéo : L'atmosphère terrestre", "https://www.youtube.com/watch?v=R8WnMBc7z0o", 480, "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=400"),
    ("Vidéo : Le cycle de l'eau", "https://www.youtube.com/watch?v=cDk2UqR_yzY", 660, "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400"),
    ("Vidéo : La reproduction humaine", "https://www.youtube.com/watch?v=z8Ia5NcT3qA", 720, "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=400"),
    ("Vidéo : La microbiologie", "https://www.youtube.com/watch?v=FzcAgr8Bhhg", 600, "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400"),
    ("Vidéo : Le MEB et observation", "https://www.youtube.com/watch?v=sQK3Yr4Sc_k", 540, "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400"),
    ("Vidéo : L'homéostasie", "https://www.youtube.com/watch?v=aJg3u2dLz0w", 660, "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400"),
    ("Vidéo : Le réseau alimentaire", "https://www.youtube.com/watch?v=W2hKfAdSidg", 480, "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=400"),
    ("Vidéo : La pression artérielle", "https://www.youtube.com/watch?v=VzDGz-0nVbY", 540, "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400"),
    ("Vidéo : La classification du vivant", "https://www.youtube.com/watch?v=K4G7xHt8tBk", 600, "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400"),
    ("Vidéo : Le foie et le pancréas", "https://www.youtube.com/watch?v=0rJDh35pmbI", 660, "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400"),
    ("Vidéo : Les échanges gazeux", "https://www.youtube.com/watch?v=3b5bX8zK3yI", 540, "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400"),
    ("Vidéo : Le système respiratoire", "https://www.youtube.com/watch?v=V4UPO9e9yYs", 600, "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=400"),
    ("Vidéo : Les mutations génétiques", "https://www.youtube.com/watch?v=GhHOjC4oxh8", 720, "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400"),
    ("Vidéo : La transmission synaptique", "https://www.youtube.com/watch?v=MnL4m6n0Y4k", 540, "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=400"),
    ("Vidéo : Le système lymphatique", "https://www.youtube.com/watch?v=UzgwgZ3hOHs", 480, "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400"),
    ("Vidéo : Le rein et l'équilibre hydrique", "https://www.youtube.com/watch?v=R8WnMBc7z0o", 660, "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=400"),
]

IMAGES = [
    ("Schéma : Structure de la cellule animale", "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800", "Schéma d'une cellule animale montrant les organites principaux"),
    ("Schéma : Structure de la cellule végétale", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800", "Schéma d'une cellule végétale avec paroi et chloroplastes"),
    ("Image : La mitose - phases", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Schéma des 4 phases de la mitose"),
    ("Schéma : Le cycle cellulaire", "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800", "Représentation du cycle cellulaire avec les phases G1, S, G2 et M"),
    ("Image : La double hélice de l'ADN", "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800", "Modèle de la structure en double hélice de l'ADN"),
    ("Schéma : La photosynthèse", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Schéma des réactions photo-dépendantes et du cycle de Calvin"),
    ("Schéma : La respiration cellulaire", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Schéma de la glycolyse, du cycle de Krebs et de la chaîne respiratoire"),
    ("Image : Le système digestif humain", "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800", "Vue d'ensemble du tube digestif et des organes annexes"),
    ("Schéma : Le cœur humain", "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=800", "Anatomie du cœur avec 4 cavités et circulation sanguine"),
    ("Schéma : Le réseau de neurones", "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800", "Architecture d'un neurone avec soma, dendrites et axone"),
    ("Image : Le cerveau humain", "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800", "Carte des aires fonctionnelles du cerveau"),
    ("Schéma : Le système endocrinien", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800", "Localisation des principales glandes endocrines"),
    ("Image : Les chromosomes (caryotype)", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Caryotype humain montrant les 23 paires de chromosomes"),
    ("Schéma : L'hérédité mendelienne", "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800", "Carré de Punnett montrant les ratios phénotypiques"),
    ("Image : Un écosystème forestier", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Photo d'une forêt avec ses composants biotiques et abiotiques"),
    ("Schéma : La chaîne alimentaire", "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800", "Chaîne alimentaire : producteur -> consommateur -> décomposeur"),
    ("Image : La biodiversité", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Collage de différentes espèces animales et végétales"),
    ("Schéma : Le cycle du carbone", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Circulation du carbone entre atmosphère, biosphère et géosphère"),
    ("Schéma : Le cycle de l'eau", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800", "Cycle hydrologique complet : evaporation, condensation, precipitation"),
    ("Image : Les plaques tectoniques", "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800", "Carte des plaques tectoniques majeures de la Terre"),
    ("Schéma : Un volcan en coupe", "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800", "Anatomie interne d'un volcan avec cheminée et chambre magmatique"),
    ("Image : Le microscope optique", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800", "Schéma d'un microscope optique avec ses composants"),
    ("Schéma : Le système respiratoire", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Arbre respiratoire des alvéoles aux bronches"),
    ("Image : L'atmosphère terrestre", "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800", "Les couches de l'atmosphère avec altitudes"),
    ("Schéma : La membrane plasmique", "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800", "Modèle en mosaïque fluide de la membrane plasmique"),
    ("Image : Les bactéries au MEB", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Image de bactéries au microscope électronique à balayage"),
    ("Schéma : Le rein en coupe", "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800", "Anatomie du rein avec néphrons et vascularisation"),
    ("Image : La reproduction humaine", "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800", "Schéma de l'appareil reproducteur humain"),
    ("Schéma : Le système lymphatique", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800", "Réseau des vaisseaux lymphatiques et ganglions"),
    ("Image : Le plancton marin", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Micrographie du plancton marin (phytoplancton et zooplancton)"),
    ("Schéma : L'homéostasie", "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800", "Diagramme du principe de régulation par feedback négatif"),
    ("Image : Les zones humides", "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800", "Photo d'une zone humide avec sa biodiversité"),
    ("Schéma : Le système sanguin", "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800", "Composition du sang : globules rouges, blancs, plaquettes, plasma"),
    ("Image : Le corail et la récif", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?w=800", "Récif corallien menacé par le réchauffement climatique"),
    ("Schéma : Les os et articulations", "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800", "Anatomie d'un os long et d'une articulation synoviale"),
]

QUIZZES = [
    ("Quiz : La cellule", [
        {"question": "Quel organite est le lieu de la respiration cellulaire ?", "options": ["Ribosome", "Mitochondrie", "Appareil de Golgi", "Lysosome"], "correct": 1},
        {"question": "Quel est le rôle principal du noyau ?", "options": ["Production d'ATP", "Stockage de l'information génétique", "Digestion intracellulaire", "Synthèse des lipides"], "correct": 1},
    ]),
    ("Quiz : La photosynthèse", [
        {"question": "Quel gaz est libéré lors de la photosynthèse ?", "options": ["CO2", "N2", "O2", "H2"], "correct": 2},
        {"question": "Dans quel organite se déroule le cycle de Calvin ?", "options": ["Mitochondrie", "Ribosome", "Chloroplaste", "Noyau"], "correct": 2},
    ]),
    ("Quiz : La respiration cellulaire", [
        {"question": "Combien d'ATP sont produits par glycolyse ?", "options": ["4", "2", "36", "38"], "correct": 1},
        {"question": "Quel est le dernier accepteur d'électrons dans la chaîne respiratoire ?", "options": ["NAD+", "CO2", "O2", "FAD"], "correct": 2},
    ]),
    ("Quiz : Le système digestif", [
        {"question": "Dans quel organe commence la digestion des protéines ?", "options": ["Bouche", "Estomac", "Duodénum", "Jéjunum"], "correct": 1},
        {"question": "Quel suc digestif est sécrété par le foie ?", "options": ["Pepsine", "Trypsine", "Bile", "Amylase"], "correct": 2},
    ]),
    ("Quiz : Le système cardiovasculaire", [
        {"question": "Combien de cavités a le cœur humain ?", "options": ["2", "3", "4", "5"], "correct": 2},
        {"question": "Quel vaisseau transporte le sang oxygéné des poumons au cœur ?", "options": ["Aorte", "Veine cave", "Artère pulmonaire", "Veine pulmonaire"], "correct": 3},
    ]),
    ("Quiz : Le système nerveux", [
        {"question": "Quel est le potentiel de membrane au repos ?", "options": ["0 mV", "-30 mV", "-70 mV", "+30 mV"], "correct": 2},
        {"question": "Quel neurotransmetteur est associé à la contraction musculaire ?", "options": ["Dopamine", "Sérotonine", "Acétylcholine", "GABA"], "correct": 2},
    ]),
    ("Quiz : La génétique", [
        {"question": "Quel est le ratio phénotypique en F2 pour un croisement hétérozygote ?", "options": ["1:1", "2:1", "3:1", "4:1"], "correct": 2},
        {"question": "Combien de chromosomes a un humain ?", "options": ["23", "44", "46", "48"], "correct": 2},
    ]),
    ("Quiz : L'écologie", [
        {"question": "Quel pourcentage d'énergie est perdu à chaque échelon trophique ?", "options": ["10%", "50%", "90%", "99%"], "correct": 2},
        {"question": "Quel terme désigne l'ensemble des organismes d'une même espèce dans un territoire ?", "options": ["Communauté", "Population", "Écosystème", "Biome"], "correct": 1},
    ]),
    ("Quiz : La géologie", [
        {"question": "Quelle est la couche la plus externe de la Terre ?", "options": ["Manteau", "Noyau", "Croûte", "Asténosphère"], "correct": 2},
        {"question": "Quel type de limite de plaque crée des volcans ?", "options": ["Transformante", "Divergente", "Convergente", "Les trois"], "correct": 1},
    ]),
    ("Quiz : L'atmosphère", [
        {"question": "Quel gaz constitue 78% de l'atmosphère ?", "options": ["Oxygène", "Argon", "Azote", "CO2"], "correct": 2},
        {"question": "Dans quelle couche se trouve la couche d'ozone ?", "options": ["Troposphère", "Stratosphère", "Mésosphère", "Thermosphère"], "correct": 1},
    ]),
    ("Quiz : L'évolution", [
        {"question": "Qui a proposé la théorie de la sélection naturelle ?", "options": ["Linné", "Lamarck", "Darwin", "Mendel"], "correct": 2},
        {"question": "Qu'est-ce qu'une espèce ? définition biologique", "options": ["Groupe d'individus semblables", "Groupe pouvant s'entre-croiser et produire une descendance fertile", "Groupe vivant dans le même habitat", "Groupe de même couleur"], "correct": 1},
    ]),
    ("Quiz : Le rein", [
        {"question": "Quelle est l'unité fonctionnelle du rein ?", "options": ["Néphron", "Glomérule", "Canal collecteur", "Cortex"], "correct": 0},
        {"question": "Quelle hormone régule la réabsorption d'eau au niveau du rein ?", "options": ["Insuline", "ADH", "Cortisol", "Thyroxine"], "correct": 1},
    ]),
    ("Quiz : La reproduction", [
        {"question": "Combien de jours dure la spermatogenèse ?", "options": ["24 heures", "7 jours", "74 jours", "9 mois"], "correct": 2},
        {"question": "Dans quel organe se déroule la fécondation ?", "options": ["Utérus", "Ovaire", "Trompe de Fallope", "Col de l'utérus"], "correct": 2},
    ]),
    ("Quiz : La microbiologie", [
        {"question": "Les virus sont-ils considérés comme vivants ?", "options": ["Oui, toujours", "Non, ce sont des parasites intracellulaires obligatoires", "Oui, uniquement à l'état libre", "Ça dépend de l'espèce"], "correct": 1},
        {"question": "Quel est le rôle des ribosomes ?", "options": ["Synthèse d'ADN", "Synthèse de protéines", "Synthèse de lipides", "Digestion"], "correct": 1},
    ]),
    ("Quiz : Les cycles biogéochimiques", [
        {"question": "Quel processus convertit N2 atmosphérique en NH3 ?", "options": ["Nitrification", "Dé nitrification", "Fixation biologique", "Ammonification"], "correct": 2},
        {"question": "Quel est le principal réservoir de carbone à long terme ?", "options": ["Océans", "Atmosphère", "Roches sédimentaires", "Forêts"], "correct": 2},
    ]),
    ("Quiz : Le système lymphatique", [
        {"question": "Quelle est la fonction principale du système lymphatique ?", "options": ["Transport de l'oxygène", "Drainage de l'excès de liquide interstitiel", "Production d'hormones", "Digestion des graisses"], "correct": 1},
    ]),
    ("Quiz : Le microscope", [
        {"question": "Quel microscope permet d'observer l'ultrastructure cellulaire ?", "options": ["Optique", "MEB", "MET", "À fluorescence"], "correct": 2},
    ]),
    ("Quiz : L'homéostasie", [
        {"question": "Quel type de régulation ramène un paramètre à sa valeur normale ?", "options": ["Feedback positif", "Feedback négatif", "Réaction en chaîne", "Catalyse"], "correct": 1},
    ]),
    ("Quiz : La classification", [
        {"question": "Quel est le plus petit taxon de la classification ?", "options": ["Genre", "Espèce", "Famille", "Ordre"], "correct": 1},
    ]),
    ("Quiz : Le système respiratoire", [
        {"question": "Quelle est la pression partielle d'O2 dans l'air inspiré ?", "options": ["21 mmHg", "100 mmHg", "150 mmHg", "40 mmHg"], "correct": 2},
    ]),
]


def seed(session: Session):
    """Main seed function."""
    print("=" * 60)
    print("  SEED ELEMENTS PEDAGOGIQUES SVT")
    print("=" * 60)

    # ── Step 0: Find existing titles (idempotent) ──
    existing_titles = set()
    rows = session.execute(text("SELECT titre FROM elements_pedagogiques")).fetchall()
    for r in rows:
        existing_titles.add(r[0])
    print(f"\n[INFO] Existing elements: {len(existing_titles)}")

    # ── Step 1: Create Parcours + Chapitres + Lecons per niveau ──
    niveau_parcours = {}  # niveau_id -> {parcours_id, chapitre_id, lecon_ids: []}

    for niveau_id, matiere_id in SVT_MATIERES.items():
        niveau_name = NIVEAUX_NAMES[niveau_id]
        parcours_titre = f"SVT {niveau_name} - Parcours General"

        # Check if parcours exists
        existing_p = session.execute(
            text("SELECT id FROM parcours WHERE titre = :t"),
            {"t": parcours_titre}
        ).fetchone()

        if existing_p:
            parcours_id = existing_p[0]
            print(f"  [SKIP] Parcours exists: {parcours_titre} (id={parcours_id})")
        else:
            result = session.execute(
                text("""INSERT INTO parcours (titre, description, matiere, niveau_scolaire, difficulte, auteur_id, est_publique, est_actif, created_at, updated_at)
                         VALUES (:titre, :desc, :matiere, :niveau, :diff, :auteur, true, true, :now, :now) RETURNING id"""),
                {
                    "titre": parcours_titre,
                    "desc": f"Parcours complet de Sciences de la Vie et de la Terre pour {niveau_name}",
                    "matiere": "علوم طبيعية",
                    "niveau": niveau_name,
                    "diff": "moyen",
                    "auteur": AUTHOR_ID,
                    "now": datetime.now(timezone.utc),
                }
            ).fetchone()
            parcours_id = result[0]
            session.commit()
            print(f"  [OK] Created parcours: {parcours_titre} (id={parcours_id})")

        # Create 2 chapitres per niveau
        chapitre_ids = []
        for ch_idx, ch_titre in enumerate([
            f"Chapitre 1: Biologie - {niveau_name}",
            f"Chapitre 2: Géologie et Environnement - {niveau_name}",
        ], 1):
            existing_ch = session.execute(
                text("SELECT id FROM chapitres WHERE titre = :t AND parcours_id = :p"),
                {"t": ch_titre, "p": parcours_id}
            ).fetchone()

            if existing_ch:
                chapitre_ids.append(existing_ch[0])
                continue

            result = session.execute(
                text("""INSERT INTO chapitres (parcours_id, titre, description, ordre, created_at, updated_at)
                         VALUES (:pid, :titre, :desc, :ordre, :now, :now) RETURNING id"""),
                {
                    "pid": parcours_id,
                    "titre": ch_titre,
                    "desc": f"Contenus biologiques et géologiques pour {niveau_name}",
                    "ordre": ch_idx,
                    "now": datetime.now(timezone.utc),
                }
            ).fetchone()
            chapitre_ids.append(result[0])
            session.commit()
            print(f"  [OK] Created chapitre: {ch_titre} (id={result[0]})")

        # Create 1 lecon per chapitre (elements will attach here)
        lecon_ids = []
        for ch_id in chapitre_ids:
            ch_info = session.execute(
                text("SELECT titre FROM chapitres WHERE id = :id"), {"id": ch_id}
            ).fetchone()
            lecon_titre = f"Leçon - {ch_info[0]}"

            existing_l = session.execute(
                text("SELECT id FROM lecons WHERE titre = :t AND chapitre_id = :c"),
                {"t": lecon_titre, "c": ch_id}
            ).fetchone()

            if existing_l:
                lecon_ids.append(existing_l[0])
                continue

            result = session.execute(
                text("""INSERT INTO lecons (chapitre_id, titre, description, duree_minutes, ordre, created_at, updated_at)
                         VALUES (:cid, :titre, :desc, 60, 1, :now, :now) RETURNING id"""),
                {
                    "cid": ch_id,
                    "titre": lecon_titre,
                    "desc": "Leçon de SVT",
                    "now": datetime.now(timezone.utc),
                }
            ).fetchone()
            lecon_ids.append(result[0])
            session.commit()

        niveau_parcours[niveau_id] = {
            "parcours_id": parcours_id,
            "chapitre_ids": chapitre_ids,
            "lecon_ids": lecon_ids,
        }

    print(f"\n[DONE] Parcours structure created for {len(niveau_parcours)} niveaux")

    # ── Step 2: Create Elements ──
    # Distribute elements across niveaux
    niveau_ids = list(SVT_MATIERES.keys())

    counts = {"texte": 0, "video": 0, "image": 0, "quiz": 0}

    def assign_niveau(idx):
        return niveau_ids[idx % len(niveau_ids)]

    def get_lecon_id(niveau_id):
        info = niveau_parcours[niveau_id]
        lecons = info["lecon_ids"]
        return lecons[0]  # All elements go to first lecon of their niveau

    # ── TEXTES ──
    print(f"\n--- Creating {len(TEXTES)} texte elements ---")
    for i, (titre, corps) in enumerate(TEXTES):
        if titre in existing_titles:
            print(f"  [SKIP] {titre}")
            continue

        niveau_id = assign_niveau(i)
        matiere_id = SVT_MATIERES[niveau_id]
        lecon_id = get_lecon_id(niveau_id)
        diff = random.choice(["basique", "moyen", "difficile"])

        result = session.execute(
            text("""INSERT INTO elements_pedagogiques
                     (type, titre, description, lecon_id, paragraphe_id, matiere_id, niveau_etude_id,
                      auteur_id, statut, difficulte, metadonnees, est_global, est_libre, created_at, updated_at)
                     VALUES ('texte', :titre, :desc, :lecon_id, NULL, :matiere_id, :niveau_id,
                             :auteur, 'publie', :diff, '{}', true, false, :now, :now)
                     RETURNING id"""),
            {
                "titre": titre,
                "desc": corps[:200] + "...",
                "lecon_id": lecon_id,
                "matiere_id": matiere_id,
                "niveau_id": niveau_id,
                "auteur": AUTHOR_ID,
                "diff": diff,
                "now": datetime.now(timezone.utc),
            }
        ).fetchone()

        session.execute(
            text("INSERT INTO elements_texte (element_id, corps) VALUES (:eid, :corps)"),
            {"eid": result[0], "corps": corps}
        )
        session.commit()
        existing_titles.add(titre)
        counts["texte"] += 1
        print(f"  [OK] ({counts['texte']}) {titre} (niveau={NIVEAUX_NAMES[niveau_id]}, diff={diff})")

    # ── VIDEOS ──
    print(f"\n--- Creating {len(VIDEOS)} video elements ---")
    for i, (titre, url, duree, thumb) in enumerate(VIDEOS):
        if titre in existing_titles:
            print(f"  [SKIP] {titre}")
            continue

        niveau_id = assign_niveau(i)
        matiere_id = SVT_MATIERES[niveau_id]
        lecon_id = get_lecon_id(niveau_id)
        diff = random.choice(["basique", "moyen", "difficile"])

        result = session.execute(
            text("""INSERT INTO elements_pedagogiques
                     (type, titre, description, lecon_id, paragraphe_id, matiere_id, niveau_etude_id,
                      auteur_id, statut, difficulte, metadonnees, est_global, est_libre, created_at, updated_at)
                     VALUES ('video', :titre, :desc, :lecon_id, NULL, :matiere_id, :niveau_id,
                             :auteur, 'publie', :diff, '{}', true, false, :now, :now)
                     RETURNING id"""),
            {
                "titre": titre,
                "desc": f"Vidéo éducative SVT : {titre}",
                "lecon_id": lecon_id,
                "matiere_id": matiere_id,
                "niveau_id": niveau_id,
                "auteur": AUTHOR_ID,
                "diff": diff,
                "now": datetime.now(timezone.utc),
            }
        ).fetchone()

        session.execute(
            text("""INSERT INTO elements_video (element_id, url, duree_secondes, thumbnail_url)
                     VALUES (:eid, :url, :duree, :thumb)"""),
            {"eid": result[0], "url": url, "duree": duree, "thumb": thumb}
        )
        session.commit()
        existing_titles.add(titre)
        counts["video"] += 1
        print(f"  [OK] ({counts['video']}) {titre} (niveau={NIVEAUX_NAMES[niveau_id]}, diff={diff})")

    # ── IMAGES ──
    print(f"\n--- Creating {len(IMAGES)} image elements ---")
    for i, (titre, url, alt) in enumerate(IMAGES):
        if titre in existing_titles:
            print(f"  [SKIP] {titre}")
            continue

        niveau_id = assign_niveau(i)
        matiere_id = SVT_MATIERES[niveau_id]
        lecon_id = get_lecon_id(niveau_id)
        diff = random.choice(["basique", "moyen", "difficile"])

        result = session.execute(
            text("""INSERT INTO elements_pedagogiques
                     (type, titre, description, lecon_id, paragraphe_id, matiere_id, niveau_etude_id,
                      auteur_id, statut, difficulte, metadonnees, est_global, est_libre, created_at, updated_at)
                     VALUES ('image', :titre, :desc, :lecon_id, NULL, :matiere_id, :niveau_id,
                             :auteur, 'publie', :diff, '{}', true, false, :now, :now)
                     RETURNING id"""),
            {
                "titre": titre,
                "desc": alt,
                "lecon_id": lecon_id,
                "matiere_id": matiere_id,
                "niveau_id": niveau_id,
                "auteur": AUTHOR_ID,
                "diff": diff,
                "now": datetime.now(timezone.utc),
            }
        ).fetchone()

        session.execute(
            text("INSERT INTO elements_image (element_id, url, alt_text) VALUES (:eid, :url, :alt)"),
            {"eid": result[0], "url": url, "alt": alt}
        )
        session.commit()
        existing_titles.add(titre)
        counts["image"] += 1
        print(f"  [OK] ({counts['image']}) {titre} (niveau={NIVEAUX_NAMES[niveau_id]}, diff={diff})")

    # ── QUIZZES ──
    print(f"\n--- Creating {len(QUIZZES)} quiz elements ---")
    import json
    for i, (titre, questions) in enumerate(QUIZZES):
        if titre in existing_titles:
            print(f"  [SKIP] {titre}")
            continue

        niveau_id = assign_niveau(i)
        matiere_id = SVT_MATIERES[niveau_id]
        lecon_id = get_lecon_id(niveau_id)
        diff = random.choice(["moyen", "difficile"])

        result = session.execute(
            text("""INSERT INTO elements_pedagogiques
                     (type, titre, description, lecon_id, paragraphe_id, matiere_id, niveau_etude_id,
                      auteur_id, statut, difficulte, metadonnees, est_global, est_libre, created_at, updated_at)
                     VALUES ('quiz', :titre, :desc, :lecon_id, NULL, :matiere_id, :niveau_id,
                             :auteur, 'publie', :diff, '{}', true, false, :now, :now)
                     RETURNING id"""),
            {
                "titre": titre,
                "desc": f"Quiz de validation : {titre}",
                "lecon_id": lecon_id,
                "matiere_id": matiere_id,
                "niveau_id": niveau_id,
                "auteur": AUTHOR_ID,
                "diff": diff,
                "now": datetime.now(timezone.utc),
            }
        ).fetchone()

        session.execute(
            text("""INSERT INTO elements_quiz (element_id, questions_json, score_reussite)
                     VALUES (:eid, :qjson, :score)"""),
            {
                "eid": result[0],
                "qjson": json.dumps(questions, ensure_ascii=False),
                "score": 0.6,
            }
        )
        session.commit()
        existing_titles.add(titre)
        counts["quiz"] += 1
        print(f"  [OK] ({counts['quiz']}) {titre} (niveau={NIVEAUX_NAMES[niveau_id]}, diff={diff})")

    # ── SUMMARY ──
    total = sum(counts.values())
    print("\n" + "=" * 60)
    print("  SEED TERMINE")
    print("=" * 60)
    print(f"  Textes :  {counts['texte']}")
    print(f"  Videos :  {counts['video']}")
    print(f"  Images :  {counts['image']}")
    print(f"  Quizzes : {counts['quiz']}")
    print(f"  TOTAL  :  {total}")
    print(f"\n  Auteur : user_id={AUTHOR_ID}")
    print(f"  Statut : tous 'publie' + est_global=true")
    print(f"  Niveaux : {len(niveau_parcours)} niveaux couverts")
    print(f"  Prets pour le Builder de Parcours (Drag & Drop)")
    print("=" * 60)


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
