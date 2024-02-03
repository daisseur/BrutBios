from subprocess import Popen, run
from requests import get, post, put
from create_hcmask import generate_masks, write_hcmask_file
from json import loads, dumps
from os import name, chdir, getcwd, remove, listdir
import os
import sys
from time import perf_counter
from os import system as cmd
from os.path import exists, basename, isdir, isfile
from print_color import print_color
from new_menu import Menu
from threading import Thread

if name == "nt":
    if isdir("hashcat"):
        hashcat = r".\hashcat.exe"
    else:
        hashcat = fr"C:\Users\{os.getenv('USERNAME')}\scoop\apps\hashcat\current"
    sep = "\\"
else:
    hashcat = "hashcat"
    sep = "/"

# BENCHMARKS
def get_end_time(speed):
    """speed : int ( Kilo Hash / second)"""
    return 8.2576228e+17/(speed*10**3)/60/60/24

def benchmark():
    print("hashcat benchmark is starting ...")
    if name == "nt" and hashcat == r".\hashcat.exe":
        chdir("hashcat")
        command = f"{hashcat} -m 1410 -b"
    else:
        command = f"{hashcat} -m 1410 -b"
    process = run(command.split(' '), capture_output=True)
    for line in str(process.stdout).split("\\n"):
        if "H/s" in line:
            print(line)
            if "MH/s" in line:
                return int(float(line[19:line.index("H/s")-1])) * 1_000_000
            elif "kH/s" in line:
                return int(float(line[19:line.index("H/s")-1])) * 1000
    return "ERROR, (you have to run test.py)"

def show():
    bench = benchmark()
    print(f"Your computer can test {bench} Hash / second")
    remaining = get_end_time(bench)
    print(
        f"With the speed of your computer, it will take {remaining / 365} years (around {round(remaining / 30)} mouths)"
        f" ({round(remaining)} days) to test all the possibilities")

def run_command(command):
    run(command.split(' '))

def simple_menu(options=[]):
    ask = ""    
    n = 1
    for option in options:
        ask += f"[{n}] {option}\n"
        n += 1
    ask += "\n     >> "
    return input(ask)

def strize(lst):
    new = []
    for i in lst:
        new.append(str(i))

class MainBrutForce:

    def __init__(self, setup_filename="setup.json", hash256='',
                 salt='', password_length=None, max_length=20, new_menu=True, mode="client", api_addr="http://192.168.1.99:8000"):
        self.mode = mode
        self.os = name
        self.api = api_addr
        if password_length is None:
            self.password_length = 1
        else:
            self.password_length = password_length
        self.max_length = max_length
        self.hash = hash256
        self.salt = salt
        self.setup_filename = setup_filename
        self.setup_json = {}
        self.masks = []
        self.bad_masks = []
        self.selected_mask = 0
        self.running_masks = []
        self.checkpoint_filename = "checkpoint.restore"
        self.selected_mask_filename = "selected_mask.hcmask"
        self.masks_filename = "combinations.hcmask"
        if self.password_length >= 5:
            self.command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -O -w 3 hashes.hash {} --restore-file-path={}"
            self.folder_command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -w 3 -O ..{}hashes.hash {} --restore-file-path={}"
        else:
            self.command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -O -w 3 -S --self-test-disable hashes.hash {} --restore-file-path={}"
            self.folder_command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -w 3 -O -S --self-test-disable ..{}hashes.hash {} --restore-file-path={}"
        self.continue_command = "hashcat --restore-file-path={} --restore"
        self.new_menu = new_menu

    def add_running_masks(self):
        headers = {"Content-Type": "application/json"}
        if self.running_masks:
            print(self.running_masks)
            response = put(f"{self.api}/setup/update/running_masks/add",
                           json={'masks': [self.selected_mask]})
            if response.status_code == 200:
                self.setup_json = response.json()
                print(self.setup_json)
            else:
                self.info("[ERROR] Error while posting", response.status_code, response.reason, response.json())

    def remove_running_mask(self, running_nmask: int):
        headers = {"Content-Type": "application/json"}
        response = put(f"{self.api}/setup/update/running_masks/remove", json={'masks': [running_nmask]})
        if response.status_code == 200:
            self.setup_json = response.json()
            print(self.setup_json)
        else:
            self.info("[ERROR] Error while posting", response.status_code)

    def add_bad_masks(self):
        headers = {"Content-Type": "application/json"}
        if self.bad_masks:
            response = put(f"{self.api}/setup/update/bad_masks/", json={'masks': self.bad_masks})
            if response.status_code == 200:
                self.setup_json = response.json()
                print(self.setup_json)
            else:
                self.info("[ERROR] Error while posting", response.status_code)
    
    def get_data(self):
        response = get(f"{self.api}/setup/data/")
        if response.status_code == 200:
            setup = response.json()
            print(setup)
            return setup
        else:
            self.info("[ERROR] Error while fetching", response.status_code)
            return self.setup_json

    def run(self):
        self.info("Starting setup...")
        self.setup()
        n_mask = 0
        open(".quit", 'w').write('')  # reset quit signal
        if '' in self.masks:
            self.masks.remove('')
        for mask in self.masks:
            print(f"mask={mask} || n_mask={n_mask} || running_masks={self.running_masks}")
            if mask not in self.bad_masks and n_mask not in self.running_masks:
                self.selected_mask = n_mask
                self.running_masks.append(n_mask)
                self.add_running_masks()
                self.process_selected_mask()
                self.running_masks = []
                self.remove_running_mask(n_mask)
                self.write_setup()
                self.check_dir()
                if "quit" in open(".quit", 'r').read():
                    self.quit()
            n_mask += 1

    def test_return(self, obj):
        if obj is None:
            self.quit()

    def options(self):
        options = ["Select a mask", "Choose a Hashcat checkpoint", 'RESET', "Show bad_masks", 'Show selected mask']
        while True:
            if self.new_menu:
                try:
                    menu = Menu(options, n_return=True, title="What function do you want to run ?").show()
                except:
                    menu = simple_menu(options)
            else:
                menu = simple_menu(options)
            match menu:
                case "1":
                    self.test_return(self.select_mask())
                case "2":
                    self.test_return(self.select_checkpoint())
                case "3":
                    os.remove("setup.json")
                    os.remove("combinations.hcmask")
                    os.remove("selected_mask.hcmask")
                    print("Setup.json removed")
                    self.quit()
                case "4":
                    print(f"Bad masks : {self.bad_masks}")
                    input("continue..")
                    continue
                case "5":
                    print(f"Selected mask : {self.selected_mask}")
                    input("continue..")
                    continue
                case _:
                    print("BAD CHOICE")
                    self.quit()

    def select_checkpoint(self):
        print(f' .{sep}'.join(listdir()))
        while True:
            file = input("Checkpoint file : ")
            if file == '':
                return
            if isfile(file):
                self.checkpoint_filename = file
                self.write_setup()
                self.info("Checkpoint changed")
            else:
                print("File not found")

    def select_mask(self):
        while True:
            try:
                mask = input("Input the n_mask : ")
                if mask == '':
                   return
                mask = int(mask)
            except:
               print("You must enter a n_mask (int)")
               continue
            if mask in self.bad_masks:
                print("This is in bad_masks")
            elif mask in self.running_masks:
                print("The mask is running")
            else:
                continue
            sure = input("Are you sure ? ")
            if sure in ["y", "o", "yes", "oui"]:
               self.selected_mask = mask
               self.info("selected mask :", self.selected_mask)
               return True

    def check_dir(self, verif="hashcat", ex=".."):
        if basename(getcwd()) == verif:
            chdir(ex)

    def quit(self):
        self.info("Stopping...", important=True)
        if self.selected_mask in self.running_masks:
            self.running_masks = []
            self.remove_running_mask(self.selected_mask)
        self.write_setup()
        self.info("Stopped at mask", self.selected_mask)
        exit(0)

    def info(self, *args, important=False):
        if important:
            print_color("[INFO] ", color="yellow", effect="bold", end='')
        else:
            print_color("[INFO] ", color="blue", effect="bold", end='')
        print_color(' '.join(str(arg) for arg in args), effect="classic")

    def read_setup(self):
        self.check_dir()
        if self.mode == "server":
            self.setup_json = loads(open(self.setup_filename, 'r', encoding='UTF-8').read())
        elif self.mode == "client":
            self.setup_json = self.get_data()
        self.password_length = self.setup_json["password_length"]
        self.masks = open(self.setup_json["masks_filename"], 'r').read().split("\n")
        self.bad_masks = self.setup_json["bad_masks"]
        self.checkpoint_filename = self.setup_json["checkpoint_filename"]
        self.running_masks = self.setup_json["running_masks"]

    def write_setup(self):
        self.check_dir()
        self.setup_json = {} if not isfile(self.setup_filename) else (
            loads(open(self.setup_filename, 'r', encoding='UTF-8').read()))
        self.setup_json["password_length"] = self.password_length
        self.setup_json["masks_filename"] = self.masks_filename
        self.setup_json["bad_masks"] = self.bad_masks
        self.setup_json["selected_mask"] = self.selected_mask
        self.setup_json["checkpoint_filename"] = self.checkpoint_filename
        self.setup_json["running_masks"] = self.running_masks
        open(self.setup_filename, 'w', encoding="UTF-8").write(dumps(self.setup_json))
        if self.mode == "client":
            self.add_bad_masks()
            self.add_running_masks()

    def process_selected_mask(self):
        selected_mask = self.masks[self.selected_mask]
        checkpoint_filename = f"{self.selected_mask}_{self.checkpoint_filename}"
        self.info("Starting hashcat on {mask}", f"{self.selected_mask} / {len(self.masks)}  ({selected_mask})",
                  important=True)
        open(self.selected_mask_filename, 'w', encoding='UTF-8').write(selected_mask)

        if isdir("hashcat") and hashcat == ".\hashcat.exe":
            assert basename(getcwd()) == "BrutBios", "You must be in the BrutBios folder"
            chdir("hashcat")
            command = self.folder_command.format(hashcat, self.password_length, self.max_length, sep, selected_mask, f"..{sep}{checkpoint_filename}")
        else:
            assert basename(getcwd()) == "BrutBios", "You must be in the BrutBios folder"
            command = self.command.format(hashcat, self.password_length, self.max_length, selected_mask, f"{checkpoint_filename}")
        if exists(checkpoint_filename):
            command = self.continue_command.format(checkpoint_filename)
        self.info(f"running command : {command}")
        # t = Thread(target=run_command, args=[command])
        # t.start()

        start = perf_counter()
        execut = cmd(command)
        # while t.is_alive():
        #     pass
        print(execut)
        if execut in [1, 0, 256]:
            return
        else:
            self.quit()
        self.info(f"DONE in {perf_counter() - start} seconds :", "{mask}", f"{self.selected_mask} ({self.masks[self.selected_mask]})")

    def setup(self):
        if exists(self.setup_filename):
            self.info("Setup Found")
            try:
                self.read_setup()
            except Exception as error:
                self.info(f"ERROR while decoding json setup, making backup of file...\n{error}", important=True)
                backup = open(self.setup_filename, 'r', encoding='UTF-8').read()
                open("backup.setup.json", 'w', encoding='UTF-8').write(backup)
                remove(self.setup_filename)
                return
        else:
            self.info("Creating Setup...")
            open(self.masks_filename, 'w').write('')  # clear masks
            self.masks = generate_masks(self.password_length)
            write_hcmask_file(self.masks_filename, self.masks)
            self.write_setup()
            open('hashes.hash', 'w', encoding='UTF-8').write(f"{self.hash}:{self.salt}")
            self.info(f'hashes.hash writed with {self.hash}:{self.salt}')


if __name__ == "__main__":
    USE_NEW_MENU = True
    if name == "nt": USE_NEW_MENU = False
    if "server" in sys.argv:
        mode = "server"
    else:
        mode = "client"
        
    main = MainBrutForce(hash256="26a5d2826c1fdbf2f93b1380d356c383f85b086aaa5c489838f8ac5ff22e1fe9",
                     salt="00000000000000000000", new_menu=USE_NEW_MENU, password_length=10, max_length=10, mode=mode)
    # test
    #main = MainBrutForce(hash256="f5ee4b19dc64d333d8b50af6db4dfefc72a806400d19af1b9cf6201c99e6dbe8",
    #                     salt="00000000000000000000", new_menu=USE_NEW_MENU, password_length=4)
    main.setup()

    choices = ["Benchmark", "Run MainBrutForce", "Options", "Custom"]
    if USE_NEW_MENU:
        try:
            menu = Menu(choices, n_return=True, title=f"[{mode}]What function do you want to run ?").show()
        except:
            menu = simple_menu(choices)
    else:
        menu = simple_menu(choices)
    match menu:
        case "1":
            show()
        case "2":
            main.run()
        case "3":
            main.options()
        case "4":
            hash256 = input("hash256: ")
            salt=input("salt: ")
            password_length = input("password length: ")
            password_length = password_length if password_length else 3
            salt = salt if salt else "0"*20
            print("===== CUSTOM =====")
            print(f"{hash256}:{salt}  ==> {password_length}")
            main = MainBrutForce(hash256=hash256,
                                 salt=salt, new_menu=USE_NEW_MENU, password_length=password_length)
            main.run()


