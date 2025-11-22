import sys
import os

# Fix for WeasyPrint on macOS (Homebrew)
if sys.platform == 'darwin':
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

import markdown
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import matplotlib
import io
import re

# Load Brand Style
assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
matplotlib.style.use(os.path.join(assets_dir, 'brand.mplstyle'))

class ReportRenderer:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(assets_dir))
        self.template = self.env.get_template('template.html')

    def _make_svg_chart(self, chart_config):
        """Generate SVG chart based on configuration."""
        if not chart_config or not chart_config.get('data'):
            return ""
        
        plt.close('all')
        
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', '')
        data = chart_config.get('data')
        x_label = chart_config.get('x_label', '')
        y_label = chart_config.get('y_label', '')
        
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Handle different data formats
        if isinstance(data, dict):
            # Simple key-value data
            labels = list(data.keys())
            values = list(data.values())
            
            if chart_type == 'bar':
                bars = ax.bar(labels, values)
                ax.bar_label(bars, padding=3)
            elif chart_type == 'horizontal_bar':
                bars = ax.barh(labels, values)
                ax.bar_label(bars, padding=3)
            elif chart_type == 'line':
                ax.plot(labels, values, marker='o', linewidth=2, markersize=6)
            elif chart_type == 'scatter':
                ax.scatter(labels, values, s=100, alpha=0.7)
                
        elif isinstance(data, list):
            # Multi-series data
            for series in data:
                series_name = series.get('name', 'Series')
                series_values = series.get('values', [])
                series_labels = series.get('labels', range(len(series_values)))
                
                if chart_type == 'line':
                    ax.plot(series_labels, series_values, marker='o', label=series_name, linewidth=2, markersize=6)
                elif chart_type in ['bar', 'stacked_bar']:
                    # For now, simple multiple bars (stacked would need more complex logic)
                    ax.bar(series_labels, series_values, label=series_name, alpha=0.8)
            
            if len(data) > 1:
                ax.legend(loc='best', frameon=False)
        
        ax.set_title(title, loc='left', pad=15)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        
        # Rotate x-axis labels if they're long
        if isinstance(data, dict) and max([len(str(k)) for k in data.keys()]) > 10:
            plt.xticks(rotation=45, ha='right')
        
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

    def _generate_list_of_figures(self, figures_list):
        if not figures_list: return ""
        html = '<div class="list-of-figures"><h1>List of Figures</h1>'
        for fig in figures_list:
            html += f'''
            <div class="list-item">
                <div class="list-item-number">{fig['number']}</div>
                <div class="list-item-title"><a href="#{fig['id']}">{fig['caption']}</a></div>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_list_of_tables(self, tables_list):
        if not tables_list: return ""
        html = '<div class="list-of-tables"><h1>List of Tables</h1>'
        for table in tables_list:
            html += f'''
            <div class="list-item">
                <div class="list-item-number">{table['number']}</div>
                <div class="list-item-title"><a href="#{table['id']}">{table['caption']}</a></div>
            </div>
            '''
        html += '</div>'
        return html
        
    def _generate_list_of_boxes(self, boxes_list):
        if not boxes_list: return ""
        html = '<div class="list-of-boxes"><h1>List of Boxes</h1>'
        for box in boxes_list:
            html += f'''
            <div class="list-item">
                <div class="list-item-number">{box['number']}</div>
                <div class="list-item-title"><a href="#{box['id']}">{box['caption']}</a></div>
            </div>
            '''
        html += '</div>'
        return html

    def create_pdf(self, data_package, output_path="report.pdf"):
        html_sections = ""
        
        # Generate TOC and Assign IDs
        toc_html = '<div class="toc"><h1>Table of Contents</h1>'
        
        for i, section in enumerate(data_package['sections']):
            section_id = f"section-{i}"
            section['id'] = section_id
            title = section.get('title', 'Untitled')
            
            # Add to TOC if it's a Chapter or Front Matter
            if section.get('layout') in ['chapter', 'front_matter', 'split', 'executive_summary', 'abbreviations', 'acknowledgements', 'annex', 'references']:
                toc_html += f'<div class="toc-item"><a href="#{section_id}">{title}</a></div>'
        
        toc_html += '</div>'

        # Track items for lists
        figures_list = []
        tables_list = []
        boxes_list = []

        # Track chapter numbers for figure/table numbering
        current_chapter = 0
        chapter_figure_count = 0
        chapter_table_count = 0
        roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

        # Render Sections
        for section in data_package['sections']:
            layout = section.get('layout', 'standard')
            section_id = section.get('id')
            
            # Track chapter for numbering
            if layout == "chapter":
                current_chapter += 1
                chapter_figure_count = 0
                chapter_table_count = 0
            
            # Render Markdown (Enable Tables, Footnotes, and Extra Features)
            md_extensions = ['tables', 'footnotes', 'extra', 'nl2br', 'sane_lists']
            main_md = markdown.markdown(section.get('main_text', ''), extensions=md_extensions)
            side_md = markdown.markdown(section.get('side_text', ''), extensions=md_extensions)
            
            # Process Tables in Markdown
            # Find <table> tags and wrap them with captions/numbering
            def table_replacer(match):
                nonlocal chapter_table_count
                chapter_table_count += 1
                chapter_roman = roman_numerals[current_chapter - 1] if current_chapter > 0 else ""
                table_num = f"{chapter_roman}.{chapter_table_count}" if chapter_roman else str(chapter_table_count)
                table_id = f"table-{table_num}"
                
                # Try to find a caption provided in the section data or use a generic one
                # For now, we'll use a generic one or extract from previous paragraph if we were smarter
                # But let's check if 'tables' metadata exists in section
                caption = f"Table {table_num}"
                if section.get('tables') and len(section['tables']) >= chapter_table_count:
                    caption = section['tables'][chapter_table_count-1].get('caption', caption)
                
                tables_list.append({'number': table_num, 'caption': caption, 'id': table_id})
                
                return f'<div class="table-wrapper" id="{table_id}"><div class="table-caption">Table {table_num}: {caption}</div>{match.group(0)}</div>'

            main_md = re.sub(r'<table>.*?</table>', table_replacer, main_md, flags=re.DOTALL)

            
            # Generate Chart with chapter-based numbering
            chart_svg = ""
            if section.get('chart'):
                chapter_figure_count += 1
                chapter_roman = roman_numerals[current_chapter - 1] if current_chapter > 0 else ""
                figure_num = f"{chapter_roman}.{chapter_figure_count}" if chapter_roman else str(chapter_figure_count)
                fig_id = f"fig-{figure_num}"
                
                svg_raw = self._make_svg_chart(section['chart'])
                chart_title = section["chart"].get("title", "Untitled Chart")
                
                figures_list.append({'number': figure_num, 'caption': chart_title, 'id': fig_id})
                
                chart_svg = f'<div class="chart-wrapper" id="{fig_id}">{svg_raw}<div class="chart-caption">Figure {figure_num}: {chart_title}</div></div>'

            # Handle Images (AI-generated or external) with chapter-based numbering
            image_html = ""
            if section.get('image'):
                chapter_figure_count += 1
                chapter_roman = roman_numerals[current_chapter - 1] if current_chapter > 0 else ""
                figure_num = f"{chapter_roman}.{chapter_figure_count}" if chapter_roman else str(chapter_figure_count)
                fig_id = f"fig-{figure_num}"
                
                image_config = section['image']
                image_path = None
                
                # Use existing path if provided
                if image_config.get('path'):
                    image_path = image_config['path']
                
                if image_path and os.path.exists(image_path):
                    image_url = "file://" + os.path.abspath(image_path)
                    caption = image_config.get('caption', f'Figure {figure_num}')
                    # If caption doesn't already have Figure number, add it
                    if not caption.startswith('Figure'):
                        caption_text = caption
                        caption = f'Figure {figure_num}: {caption}'
                    else:
                        caption_text = caption.split(':', 1)[1].strip() if ':' in caption else caption
                    
                    figures_list.append({'number': figure_num, 'caption': caption_text, 'id': fig_id})
                    
                    image_html = f'''
                    <div class="figure" id="{fig_id}">
                        <img src="{image_url}" class="figure-image" alt="{caption}">
                        <div class="figure-caption">{caption}</div>
                    </div>
                    '''

            # Pull Quote
            pull_quote_html = ""
            if section.get('pull_quote'):
                pull_quote_html = f'<div class="pull-quote">{section["pull_quote"]}</div>'

            # Layout Construction
            if layout == "chapter":
                chapter_classes = "layout-chapter"
                if current_chapter == 1:
                    chapter_classes += " first-chapter"
                
                html_sections += f"""
                <section id="{section_id}" class="{chapter_classes}">
                    <div class="chapter-content">
                        <div class="chapter-number">CHAPTER</div>
                        <h1 class="chapter-title">{section.get('title', 'Chapter')}</h1>
                        {self._get_graphic()}
                    </div>
                </section>
                """

            elif layout == "front_matter":
                html_sections += f"""
                <section id="{section_id}" class="layout-front-matter">
                    <h1>{section.get('title', 'Section')}</h1>
                    {self._get_graphic()}
                    {main_md}
                </section>
                """
                
            elif layout == "abbreviations":
                html_sections += f"""
                <section id="{section_id}" class="layout-front-matter layout-abbreviations">
                    <h1>{section.get('title', 'Abbreviations')}</h1>
                    {self._get_graphic()}
                    {main_md}
                </section>
                """

            elif layout == "acknowledgements":
                html_sections += f"""
                <section id="{section_id}" class="layout-front-matter layout-acknowledgements">
                    <h1>{section.get('title', 'Acknowledgements')}</h1>
                    {self._get_graphic()}
                    {main_md}
                </section>
                """

            elif layout == "executive_summary":
                html_sections += f"""
                <section id="{section_id}" class="layout-executive-summary">
                    <h1>{section.get('title', 'Executive Summary')}</h1>
                    {self._get_graphic()}
                    {main_md}
                </section>
                """

            elif layout == "references":
                html_sections += f"""
                <section id="{section_id}" class="layout-references">
                    <h1>{section.get('title', 'References')}</h1>
                    {self._get_graphic()}
                    <div class="references-list">
                        {main_md}
                    </div>
                </section>
                """

            elif layout == "annex":
                html_sections += f"""
                <section id="{section_id}" class="layout-annex">
                    <h1>Annex: {section.get('title', 'Appendix')}</h1>
                    {self._get_graphic()}
                    {main_md}
                    {chart_svg}
                </section>
                """

            elif layout == "box":
                # Track box
                chapter_roman = roman_numerals[current_chapter - 1] if current_chapter > 0 else ""
                # Box numbering usually per chapter too, or sequential. Let's do per chapter.
                # But we need a box counter. Let's assume box numbering is handled or we add it.
                # For now, just list it.
                box_title = section.get('title', 'Box')
                boxes_list.append({'number': '', 'caption': box_title, 'id': section_id})
                
                html_sections += f"""
                <section id="{section_id}" class="layout-box">
                    <div class="box-header">
                        <div class="box-label">{box_title}</div>
                    </div>
                    <div class="box-content">
                        {image_html}
                        {main_md}
                        {chart_svg}
                    </div>
                </section>
                """

            elif layout == "split":
                html_sections += f"""
                <section id="{section_id}" class="layout-split">
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
                <section id="{section_id}" class="layout-sidebar">
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
                <section id="{section_id}" class="layout-hero">
                    <div class="hero-container">
                        {main_md}
                        {chart_svg}
                    </div>
                </section>
                """
                
            else: # Standard Columns
                html_sections += f"""
                <section id="{section_id}" class="layout-standard">
                    {pull_quote_html}
                    {image_html}
                    {chart_svg}
                    {main_md}
                </section>
                """

        # Append Lists to TOC/Front Matter
        # We want them after TOC.
        lists_html = ""
        if figures_list:
            lists_html += self._generate_list_of_figures(figures_list)
        if tables_list:
            lists_html += self._generate_list_of_tables(tables_list)
        if boxes_list:
            lists_html += self._generate_list_of_boxes(boxes_list)
            
        # Combine TOC and Lists
        toc_and_lists = toc_html + lists_html

        # Assembly
        logo_path = "file://" + os.path.abspath("assets/logo.png") if os.path.exists("assets/logo.png") else ""
        
        full_html = self.template.render(
            title=data_package['meta']['title'],
            subtitle=data_package['meta']['subtitle'],
            date=data_package['meta']['date'],
            summary=data_package['meta']['summary'],
            logo_path=logo_path,
            toc=toc_and_lists,
            dynamic_content=html_sections
        )

        # PDF Generation
        html_obj = HTML(string=full_html, base_url=assets_dir)
        css_obj = CSS(filename=os.path.join(assets_dir, 'style.css'))
        html_obj.write_pdf(output_path, stylesheets=[css_obj])
        
        return output_path
