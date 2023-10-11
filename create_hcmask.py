import itertools

def generate_masks(length):
    masks = []
    characters = ['?u', '?l', '?d']  # Maj, min et chiffres
    combinations = itertools.product(characters, repeat=length)
    for combo in combinations:
        masks.append(''.join(combo))
    return masks


def write_hcmask_file(filename="combinations.hcmask", masks=''):
    with open(filename, 'w') as file:
        for mask in masks:
            file.write(mask + '\n')


if __name__ == '__main__':
    password_length = 3
    output_filename = 'combinations.hcmask'

    masks = generate_masks(password_length)
    write_hcmask_file(output_filename, masks)

    print(f"Fichier .hcmask généré avec {len(masks)} masques pour une longueur de mot de passe de {password_length}.")
