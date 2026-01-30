import csv
import os

def handle_parser(argv=None):

    import argparse

    parser = argparse.ArgumentParser(description='CSDI')
    parser.add_argument("--action", type=str, default="none")
    parser.add_argument("--values", type=str, default="none")

    args, _unknown = parser.parse_known_args(argv)

    return args

def _group_and_sort(hereliande):
    """Return grouped & sorted lists."""
    wadjs = []
    wverbes = []
    wbasics = []
    wnames = []
    wpronom= []
    wdeter= []
    wnegation= []

    for h in hereliande:
        whereliande, wfrench, wgroup = h
        if wgroup == "adjectif":
            wadjs.append((whereliande, wfrench))
        elif wgroup == "verbe":
            wverbes.append((whereliande, wfrench))
        elif wgroup == "nom":
            wnames.append((whereliande, wfrench))
        elif wgroup == "pronom":
            wpronom.append((whereliande, wfrench))
        elif wgroup == "determinant":
            wdeter.append((whereliande, wfrench))
        elif wgroup == "negation":
            wnegation.append((whereliande, wfrench))
        else:
            wbasics.append((whereliande, wfrench))

    # sort each group by the Hereliande word
    for lst in (wpronom, wdeter, wnegation, wbasics, wnames, wverbes, wadjs):
        lst.sort(key=lambda x: x[1])

    return wpronom, wdeter, wnegation, wbasics, wnames, wverbes, wadjs

def translate(hereliande, dtext=None):

    if dtext == "none":
        text = input("Votre hérésie: ")
    else:
        text = dtext
    text = text.lower()
    s_input = text.split()


    translation = []
    to_create = []
    for word in s_input:
        inside = False

        for h in hereliande:
            whereliande, wfrench, wgroup = h
            if word == wfrench:
                translation.append(whereliande)
                inside = True
                break

        if not inside:
            to_create.append(word)
            translation.append("______")


    print(f"\n{text = }\n")
    for t in translation:
        print(t, sep=" ", end=" ")

    if len(to_create) > 0:
        print("\n\n\nto create:")
        for c in to_create:
            print(c, sep=" ", end=" ")

    print("\n\n\n")

def printer(hereliande):
    wpronom, wdeter, wnegation, wbasics, wnames, wverbes, wadjs = _group_and_sort(hereliande)

    # compute global max length of the first column
    all_words = wpronom + wbasics + wnames + wverbes + wadjs
    max_len = max((len(h) for h, _ in all_words), default=0)

    def fmt_here(h):
        # keep a fixed distance between the two columns
        return h.ljust(max_len + 2)

    print("\n\npronoms:")
    for here, french in wpronom:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\ndéterminant:")
    for here, french in wdeter:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\nnégation:")
    for here, french in wnegation:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\nbasics:")
    for here, french in wbasics:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\nnoms:")
    for here, french in wnames:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\nverbe:")
    for here, french in wverbes:
        print(f"\t{fmt_here(here)}{french}")

    print("\n\nadjectif:")
    for here, french in wadjs:
        print(f"\t{fmt_here(here)}{french}")


def export_to_csv(hereliande, filename):
    """
    Export the printed values to a CSV file, separated by ';',
    in the same order as printer().
    """
    wpronom, wdeter, wnegation, wbasics, wnames, wverbes, wadjs = _group_and_sort(hereliande)

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=';')

        # if you don't want a header row, remove the next line
        writer.writerow(["hereliande", "french"])

        for group in (wpronom, wdeter, wnegation, wbasics, wnames, wverbes, wadjs):
            for here, french in group:
                writer.writerow([here, french])

if __name__ == "__main__":


    hereliande = [
        ('‘a', 'avoir', 'verbe'),
        ('‘al', 'pouvoir', 'verbe'),
        ('‘celar', 'regarder', 'verbe'),
        ('‘dis', 'tracer', 'verbe'),
        ('‘dis', 'guider', 'verbe'),
        ('‘esil', 'protection', 'nom'),
        ('‘esil', 'protéger', 'verbe'),
        ('‘esme', 'danser', 'verbe'),
        ('‘kirihe', 'mourir', 'verbe'),
        ('‘lorwen', 'revoir', 'verbe'),
        ('‘lorwen', 'retrouver', 'verbe'),
        ('‘merhilas', 'rencontrer', 'verbe'),
        ('‘res', 'devoir', 'verbe'),
        ('‘s', 'être', 'verbe'),
        ('‘ves', 'venir', 'verbe'),
        ('‘z', 'ne', 'negation'),
        ('a', 'la', 'determinant'),
        ('a', 'le', 'determinant'),
        ('alezie', 'temps', 'nom'),
        ('alphard', 'origine', 'nom'),
        ('amia', 'présent', 'nom'),
        ('anz', 'noir', 'nom'),
        ('aria', 'futur', 'nom'),
        ('astoria', 'la-plus-éclaire-des-étoiles', 'nom'),
        ('astoria', 'étoile', 'nom'),
        ('astums', 'tous', 'basic'),
        ('astums', 'unir', 'verbe'),
        ('atiese', 'prince', 'nom'),
        ('atiese', 'princesse', 'nom'),
        ('aturia', 'roi', 'nom'),
        ('caer', 'château', 'nom'),
        ('cea', 'sorcière', 'nom'),
        ('cea', 'magie', 'nom'),
        ('cor', 'comme', 'basic'),
        ('deon', 'souverain', 'nom'),
        ('deon', 'empereur', 'nom'),
        ('devo', 'vide', 'nom'),
        ('doimh', 'cité', 'nom'),
        ('É', 'mon', 'determinant'),
        ('É', 'me', 'basic'),
        ('éa', 'je', 'pronom'),
        ('eaze', 'vert', 'nom'),
        ('elia', 'enfant', 'nom'),
        ('éliande', 'sacré', 'nom'),
        ('elwen', 'épéiste', 'nom'),
        ('enor', 'ciel', 'nom'),
        ('ereus', 'vérité', 'nom'),
        ('ereus', 'réalité', 'nom'),
        ('erium', 'énergie', 'nom'),
        ('erium', 'puissance', 'nom'),
        ('eru', 'divinité', 'nom'),
        ('esabel', 'serviteur', 'nom'),
        ('freea', 'glace', 'nom'),
        ('gid', 'nuage', 'nom'),
        ('gid', 'brume', 'nom'),
        ('heara', 'eau', 'nom'),
        ('her', 'langue', 'nom'),
        ('I', 'ton', 'determinant'),
        ('I', 'te', 'basic'),
        ('ia', 'tu', 'pronom'),
        ('ifen', 'enfin', 'basic'),
        ('ihnte', 'vent', 'nom'),
        ('ihntia', 'amour', 'nom'),
        ('ihntia', 'aimer', 'verbe'),
        ('ihntia', 'pardon', 'nom'),
        ('inae', 'rouge', 'adjectif'),
        ('inae', 'rubis', 'adjectif'),
        ('ires', 'larmes', 'nom'),
        ('irill', 'bleu', 'adjectif'),
        ('irill', 'saphir', 'adjectif'),
        ('irilla', 'illusion', 'nom'),
        ('irilla', 'rêve', 'nom'),
        ('laud', 'hiver', 'nom'),
        ('lazias', 'la-plus-sombre-des-nuits', 'nom'),
        ('lazias', 'nuit', 'nom'),
        ('lias', 'merci', 'basic'),
        ('liem', 'traître', 'nom'),
        ('lirium', 'sylphide', 'nom'),
        ('llia', 'foudre', 'nom'),
        ('lmine', 'rivière', 'nom'),
        ('lyr', 'vie', 'nom'),
        ('maloyw', 'légende', 'nom'),
        ('maloyw', 'histoire', 'nom'),
        ('mereus', 'mensonge', 'nom'),
        ('metui', 'cher', 'basic'),
        ('metui', 'respecté', 'adjectif'),
        ('metui', 'aimé', 'adjectif'),
        ('meum', 'réserve', 'nom'),
        ('mila', 'calme', 'nom'),
        ('mir', 'pareil', 'basic'),
        ('mir', 'identique', 'nom'),
        ('nat', 'destin', 'nom'),
        ('néa', 'nous', 'pronom'),
        ('neacht', 'désert', 'nom'),
        ('neacht', 'sable', 'nom'),
        ('nix', 'détenteur', 'nom'),
        ('nix', 'possesseur', 'nom'),
        ('nix', 'maître', 'nom'),
        ('odan', 'fidèle', 'adjectif'),
        ('olh', 'de', 'basic'),
        ('olh', 'du', 'basic'),
        ('omias', 'guide', 'nom'),
        ('ora', 'après', 'basic'),
        ('oria', 'lumière', 'nom'),
        ('oyven', 'paradis', 'nom'),
        ('res', 'vache', 'nom'),
        ('res', 'gibier', 'nom'),
        ('riem', 'argent', 'nom'),
        ('riem', 'argenté', 'adjectif'),
        ('riem', 'faux', 'adjectif'),
        ('ryks', 'solide', 'adjectif'),
        ('ryks', 'dur', 'adjectif'),
        ('sacrilenta', 'sacrifice', 'nom'),
        ('silda', 'ami', 'nom'),
        ('silda', 'compère', 'nom'),
        ('sill', 'délicat', 'adjectif'),
        ('u', 'un', 'determinant'),
        ('u', 'une', 'determinant'),
        ('uhe', 'que', 'basic'),
        ('uhe', 'seulement', 'basic'),
        ('ulgur', 'loup', 'nom'),
        ('unwe', 'yeux', 'nom'),
        ('vatar', 'puissant', 'adjectif'),
        ('vell', 'poison', 'nom'),
        ('vespia', 'lune', 'nom'),
        ('via', 'vous', 'pronom'),
        ('vols', 'tempête', 'nom'),
        ('volus', 'monstre', 'nom'),
        ('we', 'blanc', 'adjectif'),
        ('ween', 'feuille', 'nom'),
        ('wek', 'souterrain', 'nom'),
        ('wen', 'automne', 'nom'),
        ('wvil', 'mine', 'nom'),
        ('wvil', 'fort', 'adjectif'),
        ('yas', 'pur', 'adjectif'),
        ('ygg', 'arbre', 'nom'),
        ('zias', 'ténèbres', 'nom'),
        ('zisht', 'passé', 'nom'),
        ('ahis-sela', 'sphère-de-l’hérésie', 'nom'),
        ('ahis', 'artefact', 'nom'),
        ('ahis', 'sphère', 'nom'),
        ('ahis', 'trésor', 'nom'),
        ('sela', 'hérésie', 'nom'),
        ('sela', 'affront', 'nom'),
        ('irs', 'mort', 'nom'),
        ('lys', 'froid', 'adjectif'),
        ('liehts', 'pauvre', 'adjectif'),

        # new
        ('fal', 'loin', 'adjectif'),
        ('orar', 'par-delà', 'basic'),
        ('devorh', 'trou', 'nom'),
        ('toh', 'au', 'determinant'),
        ('lirne', 'fond', 'adjectif'),
        ('lirne', 'profond', 'adjectif'),
        ('iredra', 'temple', 'nom'),
        ('der', 'dans', 'basic'),
        ('asmas', 'démon', 'nom'),
        ('owa', 'où', 'basic'),
        ('‘ysil', 'cacher', 'verbe'),
        ('‘ysil', 'se-cacher', 'verbe'),
        ('-', '-', '-'),

    ]

    args = handle_parser()

    if args.action == "none":
        text = input("translate / printer / export >>> ")
        text = text.lower()
    else:
        text = args.action

    if text == "translate" or text == "t":
        translate(hereliande=hereliande, dtext=args.values)
    elif text == "print" or text == "p":
        printer(hereliande=hereliande)
    elif text == "export" or text == "e":

        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "hereliande.csv")

        export_to_csv(hereliande=hereliande, filename=path)


"""
loin par-delà le trou du désert - dans le temple où se-cacher le démon - le héros avec ses puissant épée - bénir le doimhien et le gardien Liad
"""

