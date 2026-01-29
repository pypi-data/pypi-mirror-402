import json
from pathlib import Path

from .pdf_report import export_pdf


def desktop_path():
    home = Path.home()
    desktop = home / "Desktop"
    return desktop if desktop.exists() else home


class Reporter:
    def __init__(self, data):
        self.data = data

    def pretty_text(self):
        lines = []

        def section(title, content):
            lines.append(f"=== {title.upper()} ===")
            if isinstance(content, dict):
                for k, v in content.items():
                    lines.append(f"{k}: {v}")
            elif isinstance(content, list):
                for item in content:
                    lines.append(f"- package: {item['package']}")
                    for k, v in item.items():
                        if k != "package":
                            lines.append(f"  {k}: {v}")
            lines.append("")

        for key in self.data:
            section(key, self.data[key])

        return "\n".join(lines)

    def save_json(self, path=None):
        target = path or desktop_path()
        target.mkdir(parents=True, exist_ok=True)
        file = target / "envhealth_report.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        print(f"JSON report saved to: {file}")
        return file

    def save_html(self, path=None):
        target = path or desktop_path()
        target.mkdir(parents=True, exist_ok=True)
        file = target / "envhealth_report.html"
        with open(file, "w", encoding="utf-8") as f:
            f.write("<pre>")
            f.write(self.pretty_text())
            f.write("</pre>")
        print(f"HTML report saved to: {file}")
        return file

    def save_pdf(self, path=None):
        target = path or desktop_path()
        target.mkdir(parents=True, exist_ok=True)
        file = target / "envhealth_report.pdf"
        export_pdf(self.data, file)
        print(f"PDF report saved to: {file}")
        return file
