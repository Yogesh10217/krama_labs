import os
import sys

def fix_migration(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    in_alter = False
    for line in lines:
        if "alter_column" in line:
            in_alter = True
            new_lines.append(f"# {line}")
        elif in_alter:
            new_lines.append(f"# {line}")
            if ")" in line and "existing_nullable" in line:
                in_alter = False
        else:
            new_lines.append(line)
            
    with open(filepath, "w") as f:
        f.writelines(new_lines)
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_migration(sys.argv[1])
