import os
import sys
import argparse
from builder import rebuild_project

def main():
    parser = argparse.ArgumentParser(prog="myframework")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("target", nargs="?", help="Target folder for project")
    args = parser.parse_args()

    if args.command == "init":
        target_dir = args.target or "my_project"
        dump_file = os.path.join(os.path.dirname(__file__), "dump.json")
        print(f"Building project in {target_dir}...")
        rebuild_project(dump_file, target_dir)
        print("Project created! 🎉")
