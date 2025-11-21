import markdown
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import matplotlib
import io
import os

# Load Brand Style
assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
matplotlib.style.use(os.path.join(assets_dir, 'brand.mplstyle'))

class ReportRenderer:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(assets_dir))
        self.template = self.env.get_template('template.html')

    def _make_svg_chart(self, data, title):
        if not data: return ""
        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 4))
        
        bars = ax.bar(data.keys(), data.values())
        ax.set_title(title, loc='left', pad=15)
        ax.bar_label(bars, padding=3)
        
        buf = io.StringIO()
        plt.savefig(buf, format='svg', bbox_inches='tight', transparent=True)
        return buf.getvalue()

    def _get_graphic(self):
        """Returns a branded SVG divider."""
        return """
        <div style="margin: 20px 0; opacity: 0.6;">
            <svg width="50" height="6" viewBox="0 0 50 6">
                <rect width="50" height="6" fill="#bae9f4" />
            </svg>
        </div>
        """

    def create_pdf(self, data_package, output_path="report.pdf"):
        html_sections = ""
        
        for section in data_package['sections']:
            layout = section.get('layout', 'standard')
            
            # Render Markdown (Enable Tables & Footnotes)
            main_md = markdown.markdown(section.get('main_text', ''), extensions=['tables', 'footnotes'])
            side_md = markdown.markdown(section.get('side_text', ''))
            
            # Generate Chart
            chart_svg = ""
            if section.get('chart'):
                svg_raw = self._make_svg_chart(section['chart'].get('data'), section['chart'].get('title'))
                chart_svg = f'<div class="chart-wrapper">{svg_raw}<div class="chart-caption">FIGURE: {section["chart"].get("title")}</div></div>'

            # Layout Construction
            if layout == "split":
                html_sections += f"""
                <section class="layout-split">
                    <div class="split-left">
                        <h1>{section.get('title', 'Overview')}</h1>
                        {self._get_graphic()}
                        {main_md}
                    </div>
                    <div class="split-right">
                        {chart_svg}
                        <div style="font-size:1.1em; color:#56696d;">{side_md}</div>
                    </div>
                </section>
                """
            
            elif layout == "sidebar":
                html_sections += f"""
                <section class="layout-sidebar">
                    <div class="sidebar-col">
                        <h4>KEY INSIGHTS</h4>
                        {self._get_graphic()}
                        {side_md}
                    </div>
                    <div class="main-col">
                        {main_md}
                        {chart_svg}
                    </div>
                </section>
                """
                
            elif layout == "hero":
                html_sections += f"""
                <section class="layout-hero">
                    <div class="hero-container">
                        {main_md}
                        {chart_svg}
                    </div>
                </section>
                """
                
            else: # Standard Columns
                html_sections += f"""
                <section class="layout-standard">
                    {chart_svg}
                    {main_md}
                </section>
                """

        # Assembly
        logo_path = "file://" + os.path.abspath("assets/logo.png") if os.path.exists("assets/logo.png") else ""
        
        full_html = self.template.render(
            title=data_package['meta']['title'],
            subtitle=data_package['meta']['subtitle'],
            date=data_package['meta']['date'],
            summary=data_package['meta']['summary'],
            logo_path=logo_path,
            dynamic_content=html_sections
        )

        # PDF Generation
        html_obj = HTML(string=full_html, base_url=assets_dir)
        css_obj = CSS(filename=os.path.join(assets_dir, 'style.css'))
        html_obj.write_pdf(output_path, stylesheets=[css_obj])
        
        return output_path
