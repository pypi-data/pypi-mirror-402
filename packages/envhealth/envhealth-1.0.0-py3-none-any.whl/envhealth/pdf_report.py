from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Environment Health Report")
    y -= 40

    c.setFont("Helvetica", 12)

    for section, values in data.items():
        c.drawString(50, y, f"[{section.upper()}]")
        y -= 20

        for k, v in values.items():
            c.drawString(60, y, f"{k}: {v}")
            y -= 20

            if y < 80:
                c.showPage()
                y = height - 50

    c.save()
