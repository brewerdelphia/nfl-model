import os

def list_directory_structure(startpath):
    """
    Recursively lists the directory structure and returns it as a string.
    """
    output = []
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        output.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            output.append(f"{subindent}{f}")
    return "\n".join(output)

if __name__ == "__main__":
    project_root = "C:/Users/12676/PycharmProjects/lineMaker/code/nfl-model"  # Replace with your actual project path
    output_file = "project_structure.txt"

    structure_text = list_directory_structure(project_root)

    with open(output_file, "w") as f:
        f.write(structure_text)

    print(f"Project structure saved to {output_file}")