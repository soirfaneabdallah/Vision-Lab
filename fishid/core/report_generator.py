# fishid/core/report_generator.py
from fpdf import FPDF
import os
import datetime
from PIL import Image as PILImage
import tempfile
import math

DPI = 200                           # résolution d'impression nette
DESIRED_IMG_WIDTH_MM = 50           # largeur souhaitée d'une image (mm)
SPACING_MM = 8                      # espace horizontal entre images
LEGEND_HEIGHT = 6                   # hauteur de la légende
LINE_SPACING = 4                    # espace vertical entre les lignes

class FishIDPDF(FPDF):
    def __init__(self, logo_path, author="FishID Team"):
        super().__init__()
        self.logo_path = logo_path
        self.author = author

    def header(self):
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=10, y=5, h=20)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(30, 60, 120)
        self.cell(0, 10, "Vision Lab - Rapport d'analyse", ln=True, align="C")
        self.set_draw_color(30, 60, 120)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
        self.cell(0, 10, f"Créé par {self.author}", align="R")


class ReportGenerator:
    def __init__(self, output_dir="output", video_name="", author="Vision Lab", logo_path=None):
        self.output_dir = output_dir
        self.video_name = video_name
        self.author = author
        if logo_path and os.path.exists(logo_path):
            self.logo_path = logo_path
        else:
            from fishid.utils import find_asset_path
            self.logo_path = find_asset_path("assets/logos/icon.png")

    def generate(self, stats: dict, best_images: dict, filename="rapport_fishid.pdf"):
        pdf = FishIDPDF(self.logo_path, self.author)
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # --- Informations générales ---
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, f"Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 8, f"Vidéo : {self.video_name}", ln=True)
        pdf.cell(0, 8, f"Durée d'analyse : {stats.get('duration', 'N/A')}", ln=True)
        pdf.ln(5)

        # --- Résumé des indices ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 10, "Indices de diversité", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, f"Abondance totale : {stats.get('total', 0)}", ln=True)
        pdf.cell(0, 8, f"Espèces distinctes : {stats.get('species', 0)}", ln=True)
        pdf.cell(0, 8, f"Images inconnues : {stats.get('anomalies', 0)}", ln=True)
        pdf.cell(0, 8, f"Richesse spécifique : {stats.get('richness', 0)}", ln=True)
        pdf.cell(0, 8, f"Indice de Shannon (H') : {stats.get('shannon', 0):.2f}", ln=True)
        pdf.cell(0, 8, f"Indice de Simpson (1-D) : {stats.get('simpson', 0):.3f}", ln=True)
        pdf.cell(0, 8, f"Équitabilité de Pielou (J') : {stats.get('pielou', 0):.3f}", ln=True)
        pdf.ln(6)

        # --- Tableau des espèces ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 10, "Espèces détectées", ln=True)
        pdf.set_fill_color(230, 240, 250)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(65, 8, "Espèce", border=1, fill=True)
        pdf.cell(25, 8, "Effectif", border=1, fill=True, align="C")
        pdf.cell(35, 8, "Confiance moy.", border=1, fill=True, align="C")
        pdf.cell(35, 8, "% Abondance", border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 10)
        for entry in stats.get('species_list', []):
            pdf.cell(65, 7, entry['name'][:40], border=1)
            pdf.cell(25, 7, str(entry['count']), border=1, align="C")
            pdf.cell(35, 7, f"{entry['confidence']:.1%}", border=1, align="C")
            pdf.cell(35, 7, f"{entry['abundance']:.1f} %", border=1, align="C")
            pdf.ln()
        pdf.ln(8)

        # --- Meilleures images – grille adaptative, centrée et sans débordement ---
        if best_images:
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(30, 60, 120)
            pdf.cell(0, 10, "Meilleures images par espèce", ln=True)
            pdf.ln(4)

            margin = pdf.l_margin
            usable_width = pdf.w - 2 * margin

            # Nombre d'images par ligne en fonction de la largeur souhaitée
            n_per_line = max(1, int((usable_width + SPACING_MM) / (DESIRED_IMG_WIDTH_MM + SPACING_MM)))

            # Largeur réelle de chaque image (elles sont toutes de la même largeur)
            total_spacing = (n_per_line - 1) * SPACING_MM
            img_width = (usable_width - total_spacing) / n_per_line
            img_height = img_width   # carré

            image_items = list(best_images.items())
            if not image_items:
                pdf.ln(2)
                pdf.set_font("Helvetica", "I", 10)
                pdf.cell(0, 8, "Aucune image disponible.", ln=True)
                return

            y_current = pdf.get_y()
            idx = 0
            total = len(image_items)

            while idx < total:
                line = image_items[idx:idx + n_per_line]
                num_images = len(line)

                # Calcul de l'offset pour centrer la ligne (même s'il n'y a qu'une image)
                total_width = num_images * img_width + (num_images - 1) * SPACING_MM
                center_offset = (usable_width - total_width) / 2

                # Vérifier si la ligne tient dans la page
                if y_current + img_height + LEGEND_HEIGHT + LINE_SPACING > pdf.h - pdf.b_margin:
                    pdf.add_page()
                    y_current = pdf.get_y()

                for col, (class_name, img_path) in enumerate(line):
                    x = margin + center_offset + col * (img_width + SPACING_MM)
                    y = y_current

                    if os.path.exists(img_path):
                        try:
                            with PILImage.open(img_path) as pil_img:
                                if pil_img.mode != 'RGB':
                                    pil_img = pil_img.convert('RGB')
                                orig_w, orig_h = pil_img.size
                            if orig_w > 0 and orig_h > 0:
                                # Calcul de la taille en mm en conservant le ratio
                                if orig_w / orig_h > img_width / img_height:
                                    w_mm = img_width
                                    h_mm = img_width * orig_h / orig_w
                                else:
                                    h_mm = img_height
                                    w_mm = img_height * orig_w / orig_h

                                # Dimensions en pixels à la résolution DPI
                                px_w = int(w_mm * DPI / 25.4)
                                px_h = int(h_mm * DPI / 25.4)

                                # Redimensionnement LANCZOS
                                with PILImage.open(img_path) as pil_img:
                                    if pil_img.mode != 'RGB':
                                        pil_img = pil_img.convert('RGB')
                                    resized = pil_img.resize((px_w, px_h), PILImage.LANCZOS)
                                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                        resized.save(tmp.name, 'PNG')
                                        tmp_path = tmp.name

                                # Centrer dans la cellule
                                offset_x = x + (img_width - w_mm) / 2
                                offset_y = y + (img_height - h_mm) / 2
                                pdf.image(tmp_path, x=offset_x, y=offset_y, w=w_mm, h=h_mm)
                                os.unlink(tmp_path)
                            else:
                                raise ValueError("Dimensions nulles")
                        except Exception:
                            pdf.set_fill_color(230, 230, 230)
                            pdf.rect(x, y, img_width, img_height, style="DF")
                            pdf.set_font("Helvetica", "", 7)
                            pdf.set_xy(x, y + img_height/2 - 4)
                            pdf.cell(img_width, 8, "Image illisible", align="C")
                    else:
                        pdf.set_fill_color(230, 230, 230)
                        pdf.rect(x, y, img_width, img_height, style="DF")
                        pdf.set_font("Helvetica", "", 8)
                        pdf.set_xy(x, y + img_height/2 - 4)
                        pdf.cell(img_width, 8, "Image absente", align="C")

                    # Légende centrée sous l'image
                    pdf.set_xy(x, y + img_height + 1)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(img_width, LEGEND_HEIGHT, class_name[:35], align="C")

                y_current += img_height + LEGEND_HEIGHT + LINE_SPACING
                idx += n_per_line

            pdf.set_x(margin)

        # Sauvegarde
        os.makedirs(self.output_dir, exist_ok=True)
        save_path = os.path.join(self.output_dir, filename)
        pdf.output(save_path)
        return save_path