from fpdf import FPDF

class ForecastPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Forecast Report", ln=1, align="C")

    def add_summary(self, stats, comparison, changepoint_summary):
        self.set_font("Arial", size=12)
        self.cell(0, 10, "Summary Statistics:", ln=1)
        for k, v in stats.items():
            self.cell(0, 10, f"{k.capitalize()}: {v}", ln=1)

        self.ln(5)
        self.cell(0, 10, f"Current Avg: {comparison[0]}", ln=1)
        self.cell(0, 10, f"Previous Avg: {comparison[1]}", ln=1)
        self.cell(0, 10, f"YoY Change: {comparison[2]}%", ln=1)

        self.ln(5)
        self.multi_cell(0, 10, f"""Changepoint Insight:

{changepoint_summary}""")

    def add_image(self, path, w=180, h=0):
        self.image(path, w=w, h=h)

    def save_pdf(self, filename="outputs/report.pdf"):
        self.output(filename)
