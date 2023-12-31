from subprocess import Popen, run
from create_hcmask import generate_masks, write_hcmask_file
from json import loads, dumps
from os import name, chdir, getcwd, remove, listdir
from time import perf_counter
from os import system as cmd
from os.path import exists, basename, isdir, isfile
from print_color import print_color
from new_menu import Menu
from threading import Thread

if name == "nt":
    hashcat = ".\hashcat.exe"
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
    if name == "nt":
        chdir("hashcat")
        command = ".\hashcat.exe -m 1410 -b"
    else:
        command = "hashcat -m 1410 -b"
    process = run(command.split(' '), capture_output=True)
    for line in str(process.stdout).split("\\n"):
        if "H/s" in line:
            print(line)
            if "MH/s" in line:
                return int(float(line[19:line.index("H/s")-1])) * 1_000_000
            elif "KH/s" in line:
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

class MainBrutForce:

    def __init__(self, setup_filename="setup.json", hash256='',
                 salt='', password_lenght=10, new_menu=True):
        self.os = name
        self.password_length = password_lenght
        self.hash = hash256
        self.salt = salt
        self.setup_filename = setup_filename
        self.setup_json = {}
        self.masks = []
        self.bad_masks = []
        self.selected_mask = 0
        self.checkpoint_filename = "checkpoint.restore"
        self.selected_mask_filename = "selected_mask.hcmask"
        self.masks_filename = "combinations.hcmask"
        self.command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -O -w 3 hashes.hash {} --restore-file-path={}"
        self.folder_command = "{} -i --increment-min {} --increment-max {} -m 1410 -a 3 -O ..{}hashes.hash ..{}{} --restore-file-path={}"
        self.continue_command = "hashcat --restore-file-path=checkpoint.restore --restore"
        self.new_menu = new_menu

    def run(self):
        self.info("Starting setup...")
        self.setup()
        n_mask = 0
        open(".quit", 'w').write('')  # reset quit signal
        for mask in self.masks:
            if mask not in self.bad_masks:
                self.selected_mask = n_mask
                self.process_selected_mask()
                self.bad_masks.append(n_mask)
                self.write_setup()
                self.check_dir()
                if "quit" in open(".quit").read():
                    self.quit()
            n_mask += 1

    def test_return(self, obj):
        if obj is None:
            self.quit()

    def options(self):
        options = ["Select a mask", "Choose a Hashcat checkpoint", ' ', "Show bad_masks", 'Show selected mask']
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
        self.setup_json = loads(open(self.setup_filename, 'r', encoding='UTF-8').read())
        self.password_length = self.setup_json["password_length"]
        self.masks = open(self.setup_json["masks_filename"], 'r').read().split("\n")
        self.bad_masks = self.setup_json["bad_masks"]
        self.selected_mask = self.setup_json["selected_mask"]
        self.checkpoint_filename = self.setup_json["checkpoint_filename"]

    def write_setup(self):
        self.check_dir()
        self.setup_json["password_length"] = self.password_length
        self.setup_json["masks_filename"] = self.masks_filename
        self.setup_json["bad_masks"] = self.bad_masks
        self.setup_json["selected_mask"] = self.selected_mask
        self.setup_json["checkpoint_filename"] = self.checkpoint_filename
        open(self.setup_filename, 'w', encoding="UTF-8").write(dumps(self.setup_json))

    def process_selected_mask(self):
        self.info("Starting hashcat on {mask}", f"{self.selected_mask} / {len(self.masks)}  ({self.masks[self.selected_mask]})",
                  important=True)
        open(self.selected_mask_filename, 'w', encoding='UTF-8').write(self.masks[self.selected_mask])
        if isdir("hashcat"):
            assert basename(getcwd()) == "BrutBios", "You must be in the BrutBios folder"
            chdir("hashcat")
            command = self.folder_command.format(hashcat, self.password_length, self.password_length, sep, sep, self.masks[self.selected_mask], f"..{sep}{self.checkpoint_filename}")
        else:
            command = self.command.format(hashcat, self.password_length, self.password_length, self.masks[self.selected_mask], f"..{sep}{self.checkpoint_filename}")
        if exists(self.checkpoint_filename):
            command = self.continue_command
        self.info(f"running command : {command}")
        # t = Thread(target=run_command, args=[command])
        # t.start()

        start = perf_counter()
        execut = cmd(command)
        # while t.is_alive():
        #     pass
        print(execut)
        if execut in [1, 0]:
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

    main = MainBrutForce(hash256="26a5d2826c1fdbf2f93b1380d356c383f85b086aaa5c489838f8ac5ff22e1fe9",
                         salt="00000000000000000000", new_menu=USE_NEW_MENU)
    main.setup()
    choices = ["Benchmark", "Run MainBrutForce", "Options"]

    if USE_NEW_MENU:
        try:
            menu = Menu(choices, n_return=True, title="What function do you want to run ?").show()
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


