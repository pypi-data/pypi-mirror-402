import os
import stat
import sys
import hashlib
import mimetypes
import datetime
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Any, Optional

# ==== dependensi opsional, aman bila tidak terpasang ====
try:
    import magic  # python-magic / python-magic-bin
except Exception:
    magic = None

try:
    from PIL import Image, ExifTags
except Exception:
    Image, ExifTags = None, None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import mutagen  # audio tags
except Exception:
    mutagen = None

try:
    from pymediainfo import MediaInfo  # video, opsional
except Exception:
    MediaInfo = None


# ==================
# Utils
# ==================
def _to_iso(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    try:
        # pakai local time; kalau ingin UTC ganti ke utcfromtimestamp
        return datetime.datetime.fromtimestamp(ts).isoformat()
    except Exception:
        return None


def _hashes(path: str, do_md5: bool, do_sha256: bool):
    md5hex = shahex = None
    if not (do_md5 or do_sha256):
        return md5hex, shahex
    md5 = hashlib.md5() if do_md5 else None
    sha = hashlib.sha256() if do_sha256 else None
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                if md5:
                    md5.update(chunk)
                if sha:
                    sha.update(chunk)
        if md5:
            md5hex = md5.hexdigest()
        if sha:
            shahex = sha.hexdigest()
    except Exception:
        pass
    return md5hex, shahex


def _mime_guess(path: str) -> Optional[str]:
    if magic:
        try:
            return magic.from_file(path, mime=True)
        except Exception:
            pass
    mt, _ = mimetypes.guess_type(path)
    return mt


def _owner_name(st: os.stat_result) -> Optional[str]:
    # Linux/macOS: map UID ke username
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        try:
            import pwd
            return pwd.getpwuid(st.st_uid).pw_name
        except Exception:
            try:
                return str(st.st_uid)
            except Exception:
                return None
    # Windows: tidak sederhana; kembalikan None
    return None


def _xattrs(path: str) -> Dict[str, Any]:
    # Extended attributes (Linux/macOS); aman bila tidak ada
    out = {}
    try:
        if hasattr(os, "listxattr") and hasattr(os, "getxattr"):
            for key in os.listxattr(path):
                if isinstance(key, bytes):
                    k = key.decode("utf-8", errors="ignore")
                else:
                    k = key
                val = os.getxattr(path, key)
                if isinstance(val, bytes):
                    try:
                        sval = val.decode("utf-8")
                    except Exception:
                        sval = val.hex()[:128]
                else:
                    sval = str(val)
                out[f"xattr_{k}"] = (sval or "")[:256]
    except Exception:
        pass
    return out


# ==================
# Extractors khusus
# ==================
def _exif_dict(path: str) -> Dict[str, Any]:
    out = {}
    if Image is None:
        return out
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return out
            tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
            mapping = {
                "Make": "exif_make",
                "Model": "exif_model",
                "DateTime": "exif_datetime",
                "Software": "exif_software",
                "Artist": "exif_artist",
                "ExifImageWidth": "exif_width",
                "ExifImageHeight": "exif_height",
            }
            for k, nk in mapping.items():
                if k in tag_map:
                    out[nk] = str(tag_map[k])
    except Exception:
        pass
    return out


def _pdf_meta(path: str) -> Dict[str, Any]:
    out = {}
    if PdfReader is None:
        return out
    try:
        reader = PdfReader(path)
        info = reader.metadata or {}
        mapping = {
            "/Author": "pdf_author",
            "/Producer": "pdf_producer",
            "/Creator": "pdf_creator",
            "/Title": "pdf_title",
            "/Subject": "pdf_subject",
            "/CreationDate": "pdf_creation_date",
            "/ModDate": "pdf_mod_date",
        }
        for k, nk in mapping.items():
            v = info.get(k)
            if v:
                out[nk] = str(v)
        # jumlah halaman
        try:
            out["pdf_pages"] = len(reader.pages)
        except Exception:
            pass
    except Exception:
        pass
    return out


def _office_core_props_from_zip(path: str) -> dict:
    """
    docx/xlsx/pptx: docProps/core.xml (Dublin Core)
    """
    out = {}
    try:
        with zipfile.ZipFile(path) as z:
            if "docProps/core.xml" not in z.namelist():
                return out
            core = ET.fromstring(z.read("docProps/core.xml"))
            m = {
                "{http://purl.org/dc/elements/1.1/}title": "office_title",
                "{http://purl.org/dc/elements/1.1/}subject": "office_subject",
                "{http://purl.org/dc/elements/1.1/}creator": "office_creator",
                "{http://purl.org/dc/elements/1.1/}description": "office_description",
                "{http://purl.org/dc/elements/1.1/}publisher": "office_publisher",
                "{http://purl.org/dc/elements/1.1/}contributor": "office_contributor",
                "{http://purl.org/dc/elements/1.1/}type": "office_type",
                "{http://purl.org/dc/elements/1.1/}identifier": "office_identifier",
                "{http://purl.org/dc/elements/1.1/}language": "office_language",
                "{http://purl.org/dc/elements/1.1/}coverage": "office_coverage",
                "{http://purl.org/dc/elements/1.1/}rights": "office_rights",
                "{http://purl.org/dc/terms/}created": "office_created",
                "{http://purl.org/dc/terms/}modified": "office_modified",
                "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy": "office_lastModifiedBy",
                "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}category": "office_category",
                "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}contentStatus": "office_status",
                "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}keywords": "office_keywords",
                "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}revision": "office_revision",
            }
            for el in core:
                tag = el.tag
                if tag in m and el.text:
                    out[m[tag]] = el.text
    except Exception:
        pass
    return out


def _office_app_props_from_zip(path: str) -> dict:
    """
    docx/xlsx/pptx: docProps/app.xml (Word/Slide/Page/Company/LastPrinted/...).
    """
    out = {}
    try:
        with zipfile.ZipFile(path) as z:
            if "docProps/app.xml" not in z.namelist():
                return out
            root = ET.fromstring(z.read("docProps/app.xml"))
            map_simple = {
                "Application": "application_name",
                "AppVersion": "application_version",
                "Company": "office_company",
                "Manager": "office_manager",
                "DocSecurity": "office_security",
                "HyperlinksChanged": "hyperlinks_changed",
                "LinksUpToDate": "links_up_to_date",
                "SharedDoc": "shared_doc",
                "Template": "template",
                "TotalTime": "edit_time",  # menit kumulatif
                "LastPrinted": "last_printed",
                # hitungan/ukuran
                "Characters": "char_count",
                "CharactersWithSpaces": "char_with_spaces_count",
                "Words": "word_count",
                "Lines": "line_count",
                "Paragraphs": "paragraph_count",
                "Pages": "page_count",
                "Slides": "slide_count",
                "Notes": "note_count",
                "HiddenSlides": "hidden_slide_count",
                "MMClips": "multimedia_clip_count",
            }
            for child in root:
                tag = child.tag.split("}")[-1]
                if tag in map_simple and child.text is not None:
                    out[map_simple[tag]] = child.text
            # variasi nama elemen di sebagian file
            for el in root:
                t = el.tag.split("}")[-1]
                if t == "LinksDirty":
                    out["links_dirty"] = el.text
                if t in {"ScaleCrop", "Scale"}:
                    out["scale"] = el.text
    except Exception:
        pass
    return out


def _office_metadata(path: str) -> dict:
    d = {}
    d.update(_office_core_props_from_zip(path))
    d.update(_office_app_props_from_zip(path))
    return d


def _audio_tags(path: str) -> Dict[str, Any]:
    out = {}
    if mutagen is None:
        return out
    try:
        f = mutagen.File(path, easy=True)
        if not f:
            return out
        for k in ["artist", "album", "title", "genre", "date", "tracknumber"]:
            if k in f:
                v = f.get(k)
                if isinstance(v, (list, tuple)):
                    v = ", ".join(map(str, v))
                out[f"audio_{k}"] = str(v)
        try:
            out["audio_length_seconds"] = round(getattr(f.info, "length", None) or 0, 3)
        except Exception:
            pass
        for k in ["bitrate", "sample_rate", "channels"]:
            val = getattr(f.info, k, None)
            if val:
                out[f"audio_{k}"] = val
    except Exception:
        pass
    return out


def _video_mediainfo(path: str) -> Dict[str, Any]:
    out = {}
    if MediaInfo is None:
        return out
    try:
        mi = MediaInfo.parse(path)
        v = next((t for t in mi.tracks if t.track_type == "Video"), None)
        a = next((t for t in mi.tracks if t.track_type == "Audio"), None)
        g = next((t for t in mi.tracks if t.track_type == "General"), None)
        if g:
            if g.file_size:
                out["video_file_size"] = int(g.file_size)
            if g.duration:
                out["video_duration_ms"] = int(g.duration)
            if g.format:
                out["video_container"] = g.format
        if v:
            if v.width:
                out["video_width"] = int(v.width)
            if v.height:
                out["video_height"] = int(v.height)
            if v.frame_rate:
                try:
                    out["video_fps"] = float(str(v.frame_rate).split()[0])
                except Exception:
                    pass
            if v.codec_id:
                out["video_codec"] = v.codec_id
        if a:
            if a.channel_s_:
                out["video_audio_channels"] = a.channel_s_
            if a.sampling_rate:
                out["video_audio_samplerate"] = int(a.sampling_rate)
            if a.format:
                out["video_audio_format"] = a.format
    except Exception:
        pass
    return out


# ==================
# Opsi & entry point
# ==================
@dataclass
class ExtractOptions:
    compute_md5: bool = False
    compute_sha256: bool = False
    include_exif: bool = True
    include_pdf: bool = True
    include_office: bool = True     # docx/xlsx/pptx
    include_audio: bool = True      # mutagen
    include_video: bool = False     # pymediainfo (opsional)
    include_xattrs: bool = False    # extended attributes
    glob_pattern: str = "*"


def extract_one(path: str, opts: ExtractOptions) -> Dict[str, Any]:
    # stat dasar
    try:
        st = os.stat(path, follow_symlinks=False)
    except Exception as e:
        return {"path": path, "error": f"stat_failed: {e}"}

    md5hex, shahex = _hashes(path, opts.compute_md5, opts.compute_sha256)
    mime = _mime_guess(path)
    ext = os.path.splitext(path)[1].lower()

    base = {
        "path": path,
        "dir": os.path.dirname(path),
        "name": os.path.basename(path),
        "ext": ext,
        "size_bytes": st.st_size,
        "mode": stat.filemode(st.st_mode),
        "is_readonly": not bool(st.st_mode & stat.S_IWUSR),
        "owner": _owner_name(st),
        "ctime": _to_iso(getattr(st, "st_ctime", None)),
        "mtime": _to_iso(getattr(st, "st_mtime", None)),
        "atime": _to_iso(getattr(st, "st_atime", None)),
        "mime": mime,
        "md5": md5hex,
        "sha256": shahex,
        "is_symlink": os.path.islink(path),
    }

    if opts.include_xattrs:
        base.update(_xattrs(path))

    # tipe-spesifik
    # EXIF
    if opts.include_exif and (
        (mime or "").startswith("image/")
        or ext in {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp", ".heic"}
    ):
        base.update(_exif_dict(path))

    # PDF
    if opts.include_pdf and (ext == ".pdf" or (mime or "") == "application/pdf"):
        base.update(_pdf_meta(path))

    # Office OpenXML (docx/xlsx/pptx)
    if opts.include_office and ext in {".docx", ".xlsx", ".pptx"}:
        base.update(_office_metadata(path))

    # Audio
    if opts.include_audio and ((mime or "").startswith("audio/") or ext in {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"}):
        base.update(_audio_tags(path))

    # Video
    if opts.include_video and ((mime or "").startswith("video/") or ext in {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".mpeg", ".mpg", ".webm"}):
        base.update(_video_mediainfo(path))

    return base
