#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import toml
import tty
import termios
from pathlib import Path

RED = "\033[31m"
RESET = "\033[0m"
VERSION = "Alpha 0.1.0 - Onigiri"
ARSTR = "~/.jasmine/active.rice"
ARPATH = Path(ARSTR).expanduser()
ARSTR = str(ARPATH)

##########################################################################
"""THIS CHECKBOX STUFF WAS VIBECODED BUT IT WORKS FOR NOW"""

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":  # arrow keys
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def checkbox(prompt, options, default="none"):
    """
    prompt: str shown to user
    options: list of strings
    default: "none" -> all unchecked, "all" -> all checked
    """
    os.system("clear")
    if default == "all":
        selected = [True] * len(options)
    else:
        selected = [False] * len(options)

    idx = 0

    # initial render
    print(prompt)
    for i, opt in enumerate(options):
        cursor = ">" if i == idx else " "
        mark = "[x]" if selected[i] else "[ ]"
        print(f"{cursor} {mark} {opt}")

    while True:
        key = getch()
        old_idx = idx

        if key in ("\x1b[A", "k"):       # up
            idx = (idx - 1) % len(options)
        elif key in ("\x1b[B", "j"):     # down
            idx = (idx + 1) % len(options)
        elif key == " ":                 # toggle current
            selected[idx] = not selected[idx]
            # redraw current line only
            print(f"\033[{idx+2}H", end="")  # move cursor to line
            mark = "[x]" if selected[idx] else "[ ]"
            cursor = ">" if idx == old_idx else " "
            print(f"{cursor} {mark} {options[idx]}  ", end="", flush=True)
            continue
        elif key in ("\r", "\n"):        # enter
            return [opt for opt, sel in zip(options, selected) if sel]
        elif key in ("\x03", "\x1b"):    # ctrl-c / esc
            return None

        # redraw only old and new cursor positions
        if old_idx != idx:
            # old line: remove cursor
            print(f"\033[{old_idx+2}H", end="")
            mark = "[x]" if selected[old_idx] else "[ ]"
            print(f"  {mark} {options[old_idx]}  ", end="")

            # new line: add cursor
            print(f"\033[{idx+2}H", end="")
            mark = "[x]" if selected[idx] else "[ ]"
            print(f"> {mark} {options[idx]}  ", end="", flush=True)

#######################################################################

def validate_path(path_str, code, error_msg=""):
    """Validate that a path exists and is a file"""
    path = Path(path_str).expanduser()
    
    if not path.exists():
        print(f"{RED}Error: {path} does not exist{RESET}")
        if error_msg:
            print(f"\r{error_msg}")
        return 0
    
    if path.is_dir():
        return 2

    if not path.is_file():
        print(f"{RED}Error: {path} is not a file{RESET}")
        if error_msg:
            print(f"\r{error_msg}")
        return 3
    if code == 1:
        try:
            with open(path, 'r') as f:
                toml.load(f)
        except toml.TomlDecodeError as e:
            print(f"{RED}Error: invalid TOML file{RESET}")
            print(f"  {e}")
            return 0
        except Exception as e:
            print(f"{RED}Error reading file: {e}{RESET}")
            return 0
    
    return 1

def validate_flags(arg, valid_flags):
    flags = []
    
    if not arg.startswith('-'):
        print(f"{RED}Error: invalid argument '{arg}'{RESET}")
        return None

    arg = arg[1:]

    for flag in arg:
        if flag not in valid_flags:
            print(f"{RED}Error: unknown flag '{flag}'{RESET}")
            print(f"Valid flags: {valid_flags}")
            flags = []
            return flags
        else:
            flags.append(flag)
    
    return flags

def validate_arg_count(args, min_args, max_args, usage):
    if len(args) < min_args:
        print(f"{RED}Error: not enough arguments{RESET}")
        print(f"Usage: {usage}")
        return False
    
    if len(args) > max_args:
        print(f"{RED}Error: too many arguments{RESET}")
        print(f"Usage: {usage}")
        return False
    
    return len(args)

#############################################################################

def load_entry(name, src, trg, n, b, fname, jdir="~/.jasmine"):
    print(fname)
    if validate_path(src, 0, f"{RED} This rice seed is incomplete! {name} is missing{RESET}") == 1:
        trg = Path(trg).expanduser()
        os.system(f"mkdir -p {trg.parent}")
        if b:
            os.system(f"mkdir -p {jdir}/{name}")
            os.system(f"cp {trg} {jdir}/{name}/OG_{trg.name}")
            print(f"The previous {trg.name} was backed up into {jdir}/{name}/OG_{trg.name}")
        print(f"Loading {name} from {src} to {trg}")
        os.system(f"cp {src} {trg}")
        if not n:
            os.system(f"mkdir -p {jdir}/{name}")
            os.system(f"cp {src} {jdir}/{name}/{fname}")
            print(f"{src.name} was copied into {jdir}/{name}/{fname}")
    print()
    
##############################################################################

def plant(path, flags):
    cpy_rice = 'c' in flags
    no_copy = 'n' in flags
    backup = 'b' in flags
    no_warning = 'r' in flags
    manual = 'm' in flags
    water = 'w' in flags
    abup = 'a' in flags
    empty = 'e' in flags
    rice = {}
    rname = ""
    if not empty:
        path = Path(path).expanduser()
        rice_dir = path.parent
        rname = path.stem
        if not no_warning:
            print(f"{RED}⚠️  WARNING: Rice packages can be dangerous!{RESET}")
            print("Unless you absolutely trust the creator, skim through at least the .rice file.")
            print("Reload commands and target paths are potential attack vectors we can do nothing about.")
            print("Use the -r flag if you understand so you don't see this again.")
            print()
            
            response = input("Plant rice? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        print(f"Loading {path}")
        rice = toml.load(open(path, 'r'))
        rice = rice.copy()
        if manual:
            entries = list(rice.keys())
            sall = "none" if input("Select all?[N/y]").lower() == "n" else "all"
            selected = checkbox("Pick which dotfiles you want:", entries, default=sall)
            os.system("clear")
            print(f"You picked: {selected}")
            print("Deleting useless dots...")
            to_delete = [k for k in entries if k not in selected]
            for k in to_delete:
                del rice[k]
            cpy_rice = True
        print()
        for name, data in rice.items():
            src = data["source"]
            src = Path(src)
            if not src.is_absolute():
                src = rice_dir / src
                no_copy = False
            else:
                src = src.expanduser()
            trg = data["target"]
            load_entry(name, src, trg, no_copy, backup, src.name)
            if not no_copy:
                data["source"] = f"~/.jasmine/{name}/{src.name}"
        if cpy_rice:
            bpath = Path(f"~/.jasmine/rices/{path.name}").expanduser()
            os.system(f"cp {path} {bpath}")
            print(f"Rice was copied into {bpath}")
            if manual:
                toml.dump(rice, open(str(bpath), "w"))
    else:
        rname = input("What is the name of the rice?")
        os.system(f"touch ~/.jasmine/rices/{rname}.rice")
    rice["jmcnfi"] = {"ncpy": str(no_copy), "bup": str(backup), "cpyr": str(cpy_rice), "name": rname}
    os.system(f"touch {ARSTR}")
    arice = toml.load(open(ARSTR, 'r'))
    if abup:
        os.system(f"cp {ARPATH} ~/.jasmine/rices/{arice[jmcnfi][name]}.rice")
    toml.dump(rice, open(ARSTR, 'w'))
    if empty and cpy_rice:
        os.system(f"cp {ARPATH} ~/.jasmine/rices/{rname}.rice")
    if water:
        water([])

#####################################################################################

def bloom(name, src, trg, rld, fname, flags=[]):
    awater = 'w' in flags
    if validate_path(ARSTR, 1):
        src = Path(src).expanduser()
        if not fname:
            fname = src.name
        rice = toml.load(open(ARSTR, 'r'))
        ncpy = rice["jmcnfi"]["ncpy"] == "True"
        bup  = rice["jmcnfi"]["bup"] == "True"
        rice[name] = {"source": str(src), "target": trg, "reload": rld}
        if not ncpy:
            rice[name]["source"] = f"~/.jasmine/{name}/{fname}"
        load_entry(name, src, trg, ncpy, bup, fname)
        toml.dump(rice, open(ARSTR, 'w'))
        if awater:
            water([name])
    else:
        print(f"{RED} You do not have a rice installed{RESET}, start a new one with jasmine plant -e")

def water(fields=[]):
    print("watering rice...")
    arice = toml.load(open(ARSTR, 'r'))
    if arice["jmcnfi"]["cpyr"] == "True":
        os.system(f"cp {ARPATH} ~/.jasmine/rices/{arice["jmcnfi"]["name"]}.rice")
    if not fields:
        fields = list(arice.keys())
        fields.remove("jmcnfi")
    for field in fields:
        try:
            src = arice[field]["source"]
            trg = arice[field]["target"]
            rld = arice[field]["reload"]
        except:
            print(f"{field} is not a field!")
        os.system(f"touch {src} {trg}")
        os.system(f"cp {src} {trg}")
        subprocess.Popen(
            rld,
            shell=True,
            env=os.environ,    
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )

def wither(name, flags=[]):
    delete = 'd' in flags
    if validate_path(ARPATH, 1):
        rice = toml.load(open(ARSTR, 'r'))
        try:
            del rice[name]
            if delete:
                os.system(f"rm -r ~/.jasmine/{name}")
            toml.dump(rice, open(ARSTR, 'w'))
        except:
            print(f"{RED}{name}  is not a field!{RESET}")
    else:
        print(f"{RED} You do not have a rice installed{RESET}, start a new one with jasmine plant -e")

def field(name, path, flags):
    awater = 'w' in flags
    if not path:
        pathstr = f"~/.jasmine/{name}"
        if validate_path(pathstr, 0) == 2:
            path = Path(pathstr).expanduser()
            file_names = [f.name for f in path.iterdir() if f.is_file()]
            for f in file_names:
                print(f)
        else:
            print(f"{name} does not exist or you have no_copy turned on")
    else:
        if validate_path(path, 0):
            path = Path(path).expanduser()
        elif validate_path(f"~/.jasmine/{name}/" + path, 0):
            path = Path(f"~/.jasmine/{name}/" + path).expanduser()
        else:
            return
        if validate_path(ARSTR, 1, f"{RED} You do not have a rice installed{RESET}, start a new one with jasmine plant -e"):
            arice = toml.load(open(ARSTR, 'r'))
            if name in arice:
                arice[name]["source"] = str(path)
                print(path)
                trg = arice[name]["target"]
                ncpy = arice["jmcnfi"]["ncpy"] == "True"
                bup = arice["jmcnfi"]["bup"] == "True"
                load_entry(name, path, trg, ncpy, bup, path.name)
                toml.dump(arice, open(ARSTR, 'w'))
                if awater:
                    water([name])
                
#######################################################################################

           
def harvest():
    seed_path = input("where to put the seed (folder):")
    rices = []
    if validate_path(seed_path, 0) == 2 and validate_path("~/.jasmine/active.rice", 1):
        pkg_name = input("enter pkg name:")
        which_rices = input("Which rices to export: [A - only active/m - pick from /rices/e - enter paths]")
        if which_rices.lower() == 'm':
            sall = "none" if input("Select all?[N/y]").lower() == "n" else "all"
            rice_list = [f.name for f in Path("~/.jasmine/rices").expanduser().iterdir() if f.is_file()]
            rice_list.append("active.rice")
            ricenames = checkbox("Pick which rices to export", rice_list, default=sall)
            os.system("clear")
            for name in ricenames:
                if name == "active.rice":
                    rices.append('a')
                else:
                    rices.append("~/.jasmine/rices/" + name)
        elif which_rices.lower() == 'e':
            while True:
                newpath = input("Enter path of rice or done to stop:")
                if newpath.lower() == 'done':
                    break
                if validate_path(newpath, 1):
                    rices.append(newpath)
        else:
            rices = ['a']
        for rice in rices:
            nrice = ''
            if rice == 'a':
                nrice = ARSTR
            else:
                nrice = str(Path(rice).expanduser())
            crice = toml.load(open(nrice, 'r'))
            rname = crice["jmcnfi"]["name"]
            del crice["jmcnfi"]
            pickman = input("pick manually: [y/N]")
            if pickman.lower() == 'y':
                sall = "none" if input("Select all?[N/y]").lower() == "n" else "all"
                toexp = checkbox("Pick which dotfiles to export:", list(crice.keys()), default=sall)
                os.system("clear")
                to_delete = [k for k in list(crice.keys()) if k not in toexp]
                for k in to_delete:
                    del crice[k]
            else:
                toexp = list(crice.keys())
            for name in toexp:
                src = Path(crice[name]["source"]).expanduser()
                load_entry(name, src, seed_path+'/'+pkg_name+'/'+name+'/'+src.name, True, False, src.name)
                crice[name]["source"] = f"{name}/{src.name}"
            os.system(f"touch {seed_path}/{pkg_name}/{rname}.rice")
            toml.dump(crice, open(str(Path(f"{seed_path}/{pkg_name}/{rname}.rice").expanduser()), 'w'))


    else:
        print(f"{seed_path} is not a folder")

##########################################################################################

def main():
    os.system("mkdir -p ~/.jasmine/rices")

    parser = argparse.ArgumentParser(description="Jasmine - rice manager")
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')    
    args = parser.parse_args()
    Args = args.args

    if args.command == None or args.command == '': 
        print("Jasmine - dotfile manager")
        print()
        print("COMMANDS:")
        print("plant <path> <flags> - installs dotfiles from a rice package")
        print("    flags: -c: back up the .rice file into .jasmine/rices - from here you can quickly swap between rices")
        print("           -n: do not copy source dotfiles into .jasmine (for testing purposes)")
        print("           -b: back up all existing dotfiles into .jasmine")
        print("           -m: pick which dotfiles to plant (doesn't overwrite original but runs -c automatically)")
        print("           -e: start an empty rice(use without path) and name it")
        print("           -w: automatically water all after planting")
        print()
        print("bloom <name> <source> <target> <reload> <flags> - starts tracking a new entry")
        print("    you can use 't' instead of the source to copy it from the target or 'tm' to enter a custom source filename too")
        print()
        print("water <name> - runs the reload command on all fields, abcks up active.rice and syncs changes from source to target ")
        print()
        print("wither <name> - deletes the field of the name from active.rice")
        print()
        print("field <name> <path> <flags> - list all backups of a afield or switch the variant")
        print("     flags: -w: automatically water after loading")
        print()
        print("harvest [dialog based] - export a rice or multiple with its dotfiles")
        print()
        print("<name> <flags> - opens the source of <name> in $EDITOR")
        print("    flags: -w: run water {name} ")

        print(f"{RED}! Do not modify files in ~/.jasmine directly unless you know why. It could break jasmine !{RESET}")
    elif args.command.lower() == "plant":
        arg_count = validate_arg_count(Args, 1, 2, "plant <path> <flags> - installs dotfiles from a rice package")
        if arg_count == 1:
            if Args[0].startswith('-'):
                if validate_flags(Args[0], ['e', 'n', 'b', 'c']):
                    plant("", Args[0])
            elif validate_path(Args[0], 1) == 1:
                plant(Args[0], [])
        elif arg_count == 2:
            if validate_flags(Args[1], ['c', 'n', 'b', 'm', 'e', 'w', 'r', 'a']) and validate_path(Args[0], 1):
                plant(Args[0], Args[1])
    elif args.command.lower() == "bloom":
        arg_count = validate_arg_count(Args, 4, 5, "bloom <name> <source> <target> <reload> <flags>")
        if arg_count:
            if Args[1] == "t" or Args[1] == "tm" or validate_path(Args[1], 0) == 1 :
                fname = ""
                if Args[1] == "t":
                    Args[1] = Args[2]
                elif Args[1] == "tm":
                    Args[1] = Args[2]
                    fname = input("Enter the name of the source file:")
                elif validate_path(Args[1], 0) == 1:
                    fname = Path(Args[1]).expanduser().name
                if validate_path(Args[2], 0) == 3:
                    os.system(f"touch {Args[2]}")
                if arg_count == 4:
                    bloom(Args[0], Args[1], Args[2], Args[3], fname)
                elif arg_count == 5:
                    if validate_flags(Args[4], ['w']):
                        bloom(Args[0], Args[1], Args[2], Args[3], fname, Args[4])
    elif args.command.lower() == "edit":
        editor = os.environ.get("EDITOR", "nano")
        os.system("touch ~/.jasmine/active.rice")
        os.system(f"{editor} ~/.jasmine/active.rice")
    elif args.command.lower() == "water":
        water(Args)
    elif args.command.lower() == "wither":
        arg_count = validate_arg_count(Args, 1, 2, "wither <name>")
        if arg_count == 2:
            if validate_flags(Args[1], ['d']):
                wither(Args[0], Args[1])
        elif arg_count:
            wither(Args[0])
    elif args.command.lower() == "field":
        arg_count = validate_arg_count(Args, 1, 3, "field <name> <path> <flags>")
        if arg_count == 1:
            Args.append("")
        if arg_count == 3:
            arg_count = validate_flags(Args[2], ['w'])
        else:
            Args.append([])
        if arg_count:
            field(Args[0], Args[1], Args[2])
    elif args.command.lower() == "harvest":
        harvest()
    else:
        arice = toml.load(open(ARSTR, 'r'))
        if args.command in list(arice.keys()):
            arg_count = validate_arg_count(Args, 0, 1, "<name> <flags>")
            editor = os.environ.get("EDITOR", "nano")
            src = Path(arice[args.command]["source"]).expanduser()
            os.system(f"touch {src}")
            os.system(f"{editor} {src}")
            if arg_count == 1:
                if validate_flags(Args[0], ['w']):
                    water([args.command])
                
        else:
            print(f"jasmine: invalid command: {args.command}")

#################################################################################################


if __name__ == "__main__":
    main()