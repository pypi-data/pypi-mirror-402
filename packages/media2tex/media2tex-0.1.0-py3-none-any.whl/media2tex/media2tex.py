def table2tex(table):
    return "\\begin{tabular}{ |" + "c|" * len(table[0]) + " }\n" \
            + "\\hline\n" \
            + " \\\\\n\\hline\n".join([' & '.join(row) for row in table]) \
            + " \\\\\n" \
            + "\\hline\n" \
            + "\\end{tabular}"


def image2tex(image_path):
    return "\\begin{figure}[h]\n" \
            "\\centering\n" \
            "\\includegraphics[width=0.5\\textwidth]{" + image_path + "}\n" \
            "\\end{figure}\n"


def document_from_blocks(*blocks: str):
    return "\\documentclass{article}\n" \
          + "\\usepackage{graphicx}" \
          + "\\begin{document}\n" \
          + "\n".join(blocks) + "\n" \
          + "\\end{document}\n"


if __name__ == "__main__":
    table = [["Name", "Age", "Sex"], ["Alex", "32", "M"], ["Brenda", "24", "F"], ["Catherine", "57", "F"]]
    print(table2tex(table))
