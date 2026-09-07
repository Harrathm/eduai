import logging
import os
import platform
import re
import shutil
import tempfile
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Détection mojibake (UTF-8 interprété comme cp1252/cp1256)
# ---------------------------------------------------------------------------
_MOJIBAKE_RE = re.compile(
    r"(?:[\xc3-\xc9][\x80-\xbf])+"  # séquences UTF-8 2-4 octets mal interprétées
    r"|[\x80-\x9f]{2,}"             # sequences cp1252 devenuesLatin
)
_REPLACEMENT_RATIO_THRESHOLD = 0.02  # >2% de U+FFFD → corrompu


def _is_garbled(text: str) -> bool:
    """Détecte si le texte extrait est du mojibake (encodage corrompu).
    
    Détection agressive :
    - Taux de remplacement Unicode élevé
    - Patterns mojibake UTF-8/cp1252
    - Ratio anormalement bas de caractères alphabétiques reconnus
    - Caractères de ponctuation mélangés de façon incohérente
    - Caractères latins non-ASCIIdans du texte censé être arabe
    """
    if not text:
        return True
    # Remplacement Unicode
    if text.count("\ufffd") / max(len(text), 1) > _REPLACEMENT_RATIO_THRESHOLD:
        return True
    # Patterns mojibake typiques arabe : Ø§Ù„Ø¹Ù
    if _MOJIBAKE_RE.search(text[:500]):
        return True
    
    # Détection de texte corrompu par analyse de fréquence des caractères
    sample = text[:2000]
    if len(sample) < 20:
        return False  # texte très court, pas assez d'info pour juger
    
    arabic_count = sum(1 for c in sample if '\u0600' <= c <= '\u06FF')
    latin_count = sum(1 for c in sample if 'a' <= c.lower() <= 'z')
    total_alpha = arabic_count + latin_count
    
    # Si très peu de caractères alphabétiques reconnus → probablement corrompu
    if total_alpha / max(len(sample), 1) < 0.05:
        return True
    
    # Détection de polices PDF corrompues : si le texte contient des
    # caractères latins non-ASCII(typiques d'un mauvais mapping CMap)
    # comme ɫ ɰ ȡ ɵ ƒ ∏ etc. en grande quantité
    weird_chars = sum(1 for c in sample if ord(c) > 127 
                      and not ('\u0600' <= c <= '\u06FF')  # pas arabe
                      and c not in 'àâäéèêëïîôùûüÿçœæ')  # pas français
    if weird_chars / max(len(sample), 1) > 0.15:
        return True
    
    return False


def _try_recover_mojibake(text: str) -> str:
    """Tente de récupérer du texte mojibake en réencodant cp1252→UTF-8.
    
    Ne retourne le texte récupéré que si la récupération produit
    significativement plus de caractères arabes que l'original.
    """
    try:
        recovered = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        if not recovered or len(recovered) < len(text) * 0.3:
            return text
        
        sample_orig = text[:2000]
        sample_recv = recovered[:2000]
        
        arabic_orig = sum(1 for c in sample_orig if '\u0600' <= c <= '\u06FF')
        arabic_recv = sum(1 for c in sample_recv if '\u0600' <= c <= '\u06FF')
        
        # La récupération doit produire au moins 5% de caractères arabes
        # ET plus que l'original (amélioration significative)
        if arabic_recv / max(len(sample_recv), 1) < 0.05:
            return text
        if arabic_recv <= arabic_orig:
            return text
            
        return recovered
    except Exception:
        pass
    return text


# ---------------------------------------------------------------------------
# pypdf (extraction alternative — meilleur pour arabe/UTF-8)
# ---------------------------------------------------------------------------
_PYPDF_AVAILABLE = False
try:
    from pypdf import PdfReader
    _PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None

# ---------------------------------------------------------------------------
# PyMuPDF (extraction native prioritaire — très fiable pour l'arabe)
# ---------------------------------------------------------------------------
_FITZ_AVAILABLE = False
try:
    import pymupdf  # PyMuPDF >= 1.24 (API moderne)
    _FITZ_AVAILABLE = True
except ImportError:
    try:
        import fitz  # ancienne API (module historique)
        pymupdf = fitz
        _FITZ_AVAILABLE = True
    except ImportError:
        pymupdf = None

# ---------------------------------------------------------------------------
# pdfplumber (extraction texte native — fallback)
# ---------------------------------------------------------------------------
PDF_SUPPORT_AVAILABLE = False
try:
    import pdfplumber
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    PDF_SUPPORT_AVAILABLE = True
except ImportError:
    pdfplumber = None
    RecursiveCharacterTextSplitter = None

# ---------------------------------------------------------------------------
# OCR — détection automatique de Tesseract + pdf2image
# Défauts plateforme, surchargés par $TESSERACT_CMD si défini.
# ---------------------------------------------------------------------------
TESSERACT_CMD: Optional[str] = None          # résolu à l'import
_OCR_LIBS_AVAILABLE = False
pytesseract = None
pdf2image = None


def _resolve_tesseract() -> Optional[str]:
    """Cherche l'exécutable Tesseract sur le système."""
    # 1) Variable d'environnement explicite
    env_cmd = os.environ.get("TESSERACT_CMD", "").strip()
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd
    # 2) Défauts plateforme
    candidates = []
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
        ]
    else:  # Linux / macOS
        candidates = ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # 3) PATH système
    found = shutil.which("tesseract")
    if found:
        return found
    return None


def _load_ocr_libs() -> bool:
    """Charge pytesseract et pdf2image (lazy, une seule fois)."""
    global pytesseract, pdf2image, _OCR_LIBS_AVAILABLE
    if _OCR_LIBS_AVAILABLE:
        return True
    try:
        import pytesseract as _pt
        import pdf2image as _p2i
        pytesseract = _pt
        pdf2image = _p2i
        _OCR_LIBS_AVAILABLE = True
        logger.info("OCR libs loaded (pytesseract + pdf2image)")
        return True
    except ImportError:
        logger.debug("OCR libs not available — pip install pytesseract pdf2image")
        return False


# Résolution immédiate au chargement du module
TESSERACT_CMD = _resolve_tesseract()
if TESSERACT_CMD:
    logger.info("Tesseract binary: %s", TESSERACT_CMD)


class PDFProcessor:
    """Extracteur de texte PDF avec fallback OCR automatique.

    Stratégie par document (UTF-8 garanti à chaque étape) :
      0. PyMuPDF — extraction native, très fiable pour l'arabe
      1. pypdf — meilleur gestion UTF-8/Arabe
      2. pdfplumber (fallback)
      3. Si texte corrompu/vide → OCR via Tesseract (fra+ara)
    """

    OCR_MIN_CHARS_PER_PAGE = 50
    OCR_LANG = "fra+ara"
    OCR_MAX_PAGES = 40        # limiter le temps d'OCR (≈ 2 pages/seconde)
    OCR_DPI = 300             # résolution de conversion image

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if not PDF_SUPPORT_AVAILABLE:
            raise ImportError("pdfplumber and langchain-text-splitters are required for PDF processing")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n## ",   # markdown section headers
                "\n\n",       # paragraph break (both languages)
                "\n",         # line break
                ". ",         # French sentence boundary
                "؟ ",         # Arabic question mark sentence boundary
                "! ",         # exclamation
                "؟",          # Arabic question mark (no space)
                "؛",          # Arabic semicolon
                "،",          # Arabic comma
                " ",          # word boundary
                "",
            ],
        )

    # ------------------------------------------------------------------
    # Extraction PDF : PyMuPDF → pypdf → pdfplumber → OCR
    # ------------------------------------------------------------------
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        # Étape 0 : PyMuPDF — le plus fiable pour l'arabe (forces UTF-8)
        text = None
        if _FITZ_AVAILABLE:
            text = self._extract_with_pymupdf(pdf_path)
            if text and not _is_garbled(text):
                logger.info("PyMuPDF: %d chars extraits (clean) — %s", len(text), os.path.basename(pdf_path))
                return text
            if text and _is_garbled(text):
                recovered = _try_recover_mojibake(text)
                if recovered and not _is_garbled(recovered):
                    logger.info("PyMuPDF: mojibake récupéré — %s", os.path.basename(pdf_path))
                    return recovered
            logger.info("PyMuPDF: texte corrompu ou vide, fallback pypdf — %s", os.path.basename(pdf_path))

        # Étape 1 : pypdf (meilleur pour arabe/UTF-8)
        if _PYPDF_AVAILABLE:
            text = self._extract_with_pypdf(pdf_path)
            if text and not _is_garbled(text):
                logger.info("pypdf: %d chars extraits (clean) — %s", len(text), os.path.basename(pdf_path))
                return text
            # Tentative de récupération mojibake
            if text and _is_garbled(text):
                recovered = _try_recover_mojibake(text)
                if recovered and not _is_garbled(recovered):
                    logger.info("pypdf: mojibake récupéré — %s", os.path.basename(pdf_path))
                    return recovered
            logger.info("pypdf: texte corrompu ou vide, fallback pdfplumber — %s", os.path.basename(pdf_path))

        # Étape 2 : pdfplumber + OCR fallback
        with pdfplumber.open(pdf_path) as pdf:
            return self._extract_with_ocr_fallback(pdf, source=pdf_path, is_bytes=False)

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        # Étape 0 : PyMuPDF peut aussi ouvrir des bytes
        if _FITZ_AVAILABLE:
            text = self._extract_with_pymupdf_bytes(pdf_bytes)
            if text and not _is_garbled(text):
                logger.info("PyMuPDF(bytes): %d chars extraits (clean)", len(text))
                return text
            if text and _is_garbled(text):
                recovered = _try_recover_mojibake(text)
                if recovered and not _is_garbled(recovered):
                    logger.info("PyMuPDF(bytes): mojibake récupéré")
                    return recovered

        # pypdf peut aussi ouvrir des bytes
        if _PYPDF_AVAILABLE:
            try:
                from io import BytesIO
                reader = PdfReader(BytesIO(pdf_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                if text and not _is_garbled(text):
                    logger.info("pypdf(bytes): %d chars extraits (clean)", len(text))
                    return text
                if text and _is_garbled(text):
                    recovered = _try_recover_mojibake(text)
                    if recovered and not _is_garbled(recovered):
                        logger.info("pypdf(bytes): mojibake récupéré")
                        return recovered
            except Exception as e:
                logger.debug("pypdf(bytes) failed: %s", e)

        with pdfplumber.open(pdf_bytes) as pdf:
            return self._extract_with_ocr_fallback(pdf, source="<bytes>", is_bytes=True)

    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """Extraction via pypdf — page par page."""
        try:
            reader = PdfReader(pdf_path)
            texts: List[str] = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                texts.append(page_text)
            return "\n\n".join(texts)
        except Exception as e:
            logger.warning("pypdf extraction failed: %s — %s", e, os.path.basename(pdf_path))
            return ""

    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extraction via PyMuPDF — fiable pour l'arabe (codage UTF-8 natif)."""
        try:
            doc = pymupdf.open(pdf_path)
            texts: List[str] = []
            for page in doc:
                page_text = page.get_text("text") or ""
                texts.append(page_text)
            doc.close()
            return "\n\n".join(texts)
        except Exception as e:
            logger.warning("PyMuPDF extraction failed: %s — %s", e, os.path.basename(pdf_path))
            return ""

    def _extract_with_pymupdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extraction PyMuPDF depuis des bytes."""
        try:
            from io import BytesIO
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            texts: List[str] = []
            for page in doc:
                page_text = page.get_text("text") or ""
                texts.append(page_text)
            doc.close()
            return "\n\n".join(texts)
        except Exception as e:
            logger.warning("PyMuPDF(bytes) extraction failed: %s", e)
            return ""

    # ------------------------------------------------------------------
    # Logique OCR centralisée (appelée par les deux méthodes ci-dessus)
    # ------------------------------------------------------------------
    def _extract_with_ocr_fallback(
        self,
        pdf_obj,
        source: str,
        is_bytes: bool,
    ) -> str:
        """Parcourt les pages, tente pdfplumber puis OCR si texte insuffisant OU corrompu."""
        texts: List[str] = []
        pages_needing_ocr: List[int] = []       # indices (0-based)
        all_page_texts: List[str] = []

        # Phase 1 : pdfplumber pour toutes les pages
        for i, page in enumerate(pdf_obj.pages):
            page_text = page.extract_text() or ""
            all_page_texts.append(page_text)
            # Accepter le texte si assez long ET non corrompu
            if len(page_text.strip()) >= self.OCR_MIN_CHARS_PER_PAGE and not _is_garbled(page_text):
                texts.append(page_text)
            else:
                pages_needing_ocr.append(i)

        # Phase 2 : OCR sur les pages texte court OU corrompu
        if pages_needing_ocr and self._try_ocr():
            pages_to_ocr = pages_needing_ocr[:self.OCR_MAX_PAGES]
            logger.info(
                "OCR activé : %d/%d pages sous seuil (%d chars) — %s",
                len(pages_to_ocr), len(pdf_obj.pages),
                self.OCR_MIN_CHARS_PER_PAGE, os.path.basename(source),
            )
            ocr_texts = self._ocr_pages(pdf_obj, pages_to_ocr, is_bytes)
            for page_idx, ocr_text in zip(pages_to_ocr, ocr_texts):
                if ocr_text and len(ocr_text.strip()) > 10:
                    texts.append(ocr_text)
                    logger.debug("OCR page %d: %d chars extraits", page_idx + 1, len(ocr_text))
                else:
                    logger.debug("OCR page %d: texte vide après traitement", page_idx + 1)

        return "\n\n".join(texts)

    def _try_ocr(self) -> bool:
        """Vérifie que les libs + binaire OCR sont disponibles."""
        if not _load_ocr_libs():
            return False
        if not TESSERACT_CMD:
            logger.debug("Tesseract binary not found — OCR disabled")
            return False
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        return True

    def _ocr_pages(self, pdf_obj, page_indices: List[int], is_bytes: bool) -> List[str]:
        """Convertit les pages en images puis OCR Tesseract.
        
        Garantit le retour UTF-8 pour l'arabe via pytesseract.
        """
        results: List[str] = []
        try:
            # pdf2image convert_from_path / convert_from_bytes
            if is_bytes:
                # Les bytes du PDF ont déjà été lus par pdfplumber — reconvertir impossible.
                # Solution : reconvertir depuis les pages pdfplumber elles-mêmes.
                # pdfplumber page → .to_image() → PIL Image → pytesseract
                for idx in page_indices:
                    try:
                        page = pdf_obj.pages[idx]
                        pil_image = page.to_image(resolution=self.OCR_DPI).original
                        # force output_type=Unicode pour garantir UTF-8
                        text = pytesseract.image_to_string(
                            pil_image, lang=self.OCR_LANG, output_type=pytesseract.Output.STRING
                        )
                        results.append(text or "")
                    except Exception as e:
                        logger.warning("OCR page %d failed: %s", idx + 1, e)
                        results.append("")
                return results

            # Cas fichier : pdf2image est plus rapide pour gros PDF
            # Extraire uniquement les pages demandées (1-based pour pdf2image)
            first, last = page_indices[0] + 1, page_indices[-1] + 1
            images = pdf2image.convert_from_path(
                pdf_obj.stream.name if hasattr(pdf_obj.stream, "name") else pdf_obj.stream,
                first_page=first,
                last_page=last,
                dpi=self.OCR_DPI,
                fmt="jpeg",
            )
            # Correspondance index → image (si first..last contient des trous,
            # pdf2image retourne quand même une image par page demandée)
            page_to_img = {idx: img for idx, img in zip(range(first - 1, last), images)}

            for idx in page_indices:
                pil_image = page_to_img.get(idx)
                if pil_image is None:
                    results.append("")
                    continue
                # force output_type=Unicode pour garantir UTF-8
                text = pytesseract.image_to_string(
                    pil_image, lang=self.OCR_LANG, output_type=pytesseract.Output.STRING
                )
                results.append(text or "")
        except Exception as e:
            logger.warning("OCR batch failed: %s", e)
            # Fallback : tenter page par page via pdfplumber.to_image
            results = []
            for idx in page_indices:
                try:
                    page = pdf_obj.pages[idx]
                    pil_image = page.to_image(resolution=self.OCR_DPI).original
                    text = pytesseract.image_to_string(
                        pil_image, lang=self.OCR_LANG, output_type=pytesseract.Output.STRING
                    )
                    results.append(text or "")
                except Exception as e2:
                    logger.warning("OCR page %d fallback failed: %s", idx + 1, e2)
                    results.append("")
        return results

    # ------------------------------------------------------------------
    # Chunking (inchangé)
    # ------------------------------------------------------------------
    def chunk_text(self, text: str) -> List[str]:
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        chunks = self.text_splitter.split_text(text)
        return [c.strip() for c in chunks if len(c.strip()) > 30]

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def process_pdf(self, pdf_path: str) -> List[dict]:
        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)
        return [
            {"content": chunk, "source": os.path.basename(pdf_path), "index": i}
            for i, chunk in enumerate(chunks)
        ]

    def process_pdf_bytes(self, pdf_bytes: bytes, source_name: str = "document") -> List[dict]:
        text = self.extract_text_from_bytes(pdf_bytes)
        chunks = self.chunk_text(text)
        return [
            {"content": chunk, "source": source_name, "index": i}
            for i, chunk in enumerate(chunks)
        ]