import hashlib
import random
import string
from subprocess import run
from create_hcmask import *
from os import system as cmd
from os import name as os
from os.path import isdir, exists, basename
from os import chdir, getcwd
from time import perf_counter
try:
    from requests import get
except:
    run("python3 -m pip install requests".split(' '))
    from requests import get

if os == "nt":
    if isdir("hashcat"):
        hashcat = ".\hashcat.exe"
    else:
        hashcat = "hashcat"
    sep = "\\"
else:
    hashcat = "hashcat"
    sep = "/"


def generate_random_string(n):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def hash_salt(password, salt):
    # Créer un objet de hachage SHA-256
    sha256 = hashlib.sha256()

    # Mettre à jour le hachage avec le mot de passe et le sel, en encodant en UTF-8
    sha256.update(password.encode('utf-8'))
    sha256.update(salt.encode('utf-8'))

    # Obtenir le hachage final sous forme d'hexadécimal
    hashed_password = sha256.hexdigest()

    # Concaténer le hachage avec le sel
    return f"{hashed_password}:{salt}"


def write_test(password_lenght, n_test, manual_password=None):
    open("hashes.hash", 'w').write('')
    with open("hashes.hash", 'a') as hashes:
        for i in range(n_test):
            if manual_password:
                hash_sha256 = hash_salt(manual_password, generate_random_string(random.randint(5, 21)))
            else:
                hash_sha256 = hash_salt(generate_random_string(password_lenght), generate_random_string(random.randint(5, 21)))

            hashes.write(f"{hash_sha256}\n")
            print(hash_sha256)
    print("write_test -> DONE")


def start_test():
    global hashcat
    print("Test starting..")
    if isdir("hashcat"):
        print("hashcat folder detected")
        chdir("hashcat")
        #command = f"{hashcat} -i --increment-min 3 -m 1410 -a 3 -O ..{sep}hashes.hash ..{sep}combinations.hcmask"
        command = f"{hashcat} --self-test-disable -m 1410 -a 3 -O ..{sep}hashes.hash ..{sep}combinations.hcmask"
    else:
        command = f"{hashcat} --self-test-disable -m 1410 -a 3 -O hashes.hash combinations.hcmask"
    if cmd(command) != 0:
        print("ERROR: hashcat")
        if os == "nt":
            if basename(getcwd()) == "hashcat":
                chdir("..")
            if not isdir("hashcat"):
                if not exists("hashcat.7z"):
                    request = get("https://hashcat.net/files/hashcat-6.2.6.7z")
                    if request.status_code == 200:
                        open("hashcat.7z", 'wb').write(request.content)
                        print("Archive Downloaded")
                    else:
                        print("ERROR: cannot download this link 'https://hashcat.net/files/hashcat-6.2.6.7z'")

                try:
                    import patoolib
                except:
                    print("Installing python packages to extract archive...")
                    run("python3 -m pip install patool".split(' '))
                    import patoolib
                    print("Installed !")

                print("Extracting Archive...")
                patoolib.extract_archive("hashcat.7z", outdir=".")
                print("Archive extracted !")
                run("mv hashcat-* hashcat")
                chdir("hashcat")
        else:
            print("Démerdes toi surtout si c'est t'es sur mac")
            return

        print("Hashcat is installed !")
        print("Test starting...")

        cmd(command)

    output = run(f"{hashcat} -i --increment-min 3 -m 1410 -a 3 -O hashes.hash combinations.hcmask --show".split(' '), capture_output=True)
    results = output.stdout
    print(output.stdout)
    for line in str(results).split("\\n"):
        parts = line.split(":")
        try:
            print(f"Hash = {parts[0]}\nSalt = {parts[1]}\n          PASSWORD = {parts[2]}\n==========================")
        except:
            break
    print("\n\ntest -> DONE !")


if __name__ == "__main__":
    manual_password = None
    # manual_password = input("Entrez un mot de passe test: ")
    if manual_password:
        password_length = len(manual_password)
    else:
        password_length = 5
    n_test = 1
    write_test(password_length, n_test, manual_password)
    masks = generate_masks(password_length)
    write_hcmask_file(masks=masks)
    start = perf_counter()
    start_test()
    print(f"Test fini en {round(perf_counter()-start)}s")
