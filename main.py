# ==============================================================================
# Xabat - Predator Reporting & Triage Bot
# Copyright (C) [Year] [Your Name/GitHub Username]
#
# Licensed under the Xabat Ethical Source License (XESL) v1.2.
# ==============================================================================

import discord
from discord.ext import commands, tasks
import os
import re
import time
import aiosqlite
import secrets
import asyncio
import io
import tempfile
import logging
import threading
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from discord import app_commands
from flask import Flask

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("xabat")

load_dotenv()

try:
    from nudenet import NudeDetector
    nude_detector = NudeDetector()
    log.info("NudeNet AI loaded successfully.")
except ImportError:
    log.warning("NudeNet is not installed! Please run 'pip install nudenet'")
    nude_detector = None
except Exception as e:
    log.warning(f"Failed to initialize NudeNet: {e}")
    nude_detector = None

def get_env_var(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(f"Environment variable {key} is missing or empty. Bot cannot start.")
    return val

BOT_TOKEN = get_env_var("BOT_TOKEN")
SECURE_CHANNEL_ID = int(get_env_var("SECURE_CHANNEL_ID").strip())       
MOD_LOG_CHANNEL_ID = int(get_env_var("MOD_LOG_CHANNEL_ID").strip())    
MOD_ROLE_ID = int(get_env_var("MOD_ROLE_ID").strip())                  
GUILD_ID = int(os.getenv("GUILD_ID", "0").strip())                     
ISSUE_CHANNEL_ID = int(os.getenv("ISSUE_CHANNEL_ID", "0").strip())     
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", "0").strip())     
CONVERSATION_FORUM_CHANNEL_ID = int(os.getenv("CONVERSATION_FORUM_CHANNEL_ID", "0").strip())

UPLOAD_SESSION_TIMEOUT = 600        
UPLOAD_SESSION_HARD_LIMIT = 3600   
EVIDENCE_RETENTION_DAYS = 120      
CLOSED_CASE_RETENTION_DAYS = 180   
AUDIT_LOG_RETENTION_DAYS = 365     

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  
MAX_EVIDENCE = 25                  

# CONSENT_LAWS Reference Data
def _gn(age, notes=""):
    """Helper for gender-neutral jurisdictions."""
    return {"male": age, "female": age, "jurisdiction_specific": False, "notes": notes}

_china = {"male": None, "female": 14, "jurisdiction_specific": False, "notes": "Statutory provision specifically concerns intercourse involving a girl below 14."}
_srilanka = {"male": None, "female": 16, "jurisdiction_specific": False, "notes": "Statutory provision is sex-specific and the legal framework concerning boys is different."}
_malaysia = {"male": None, "female": 16, "jurisdiction_specific": False, "notes": "Statutory provision is sex-specific and applies to girls."}
_benin = {"male": None, "female": 18, "jurisdiction_specific": False, "notes": "No corresponding single numeric statutory threshold encoded for boys."}
_tuvalu = {"male": None, "female": 15, "jurisdiction_specific": False, "notes": "Statutory provision is sex-specific."}
_solomonislands = {"male": None, "female": 15, "jurisdiction_specific": False, "notes": "Statutory provision is sex-specific."}
_saintvincent = {"male": None, "female": 15, "jurisdiction_specific": False, "notes": "Statutory provision is sex-specific."}
_tanzania = {"male": None, "female": 18, "jurisdiction_specific": True, "notes": "Mainland Tanzania differs from Zanzibar; Zanzibar is 18 for both."}
_jordan = {"male": None, "female": 18, "jurisdiction_specific": False, "notes": "Relevant sexual-offense provisions treat boys and girls differently; male side is not represented by an equivalent single numeric threshold."}
_kuwait = {"male": None, "female": 21, "jurisdiction_specific": False, "notes": "Relevant provisions distinguish treatment of girls and boys; do not interpret 21 as a universal male/female consent age."}
_guineabissau = {"male": 12, "female": 16, "jurisdiction_specific": False, "notes": "Genuine numeric male/female difference."}

_usa = {"male": None, "female": None, "jurisdiction_specific": True, "notes": "Varies by state."}
_australia = {"male": None, "female": None, "jurisdiction_specific": True, "notes": "Varies by state/territory."}
_mexico = {"male": None, "female": None, "jurisdiction_specific": True, "notes": "Varies by state."}
_none_multi = {"male": None, "female": None, "jurisdiction_specific": False, "notes": "Multiple statutory thresholds exist; no single numeric value assigned."}

CONSENT_LAWS = {
    "afghanistan": _gn(18), "af": _gn(18), "albania": _gn(18), "al": _gn(18),
    "algeria": _gn(16), "dz": _gn(16), "andorra": _gn(18), "ad": _gn(18),
    "angola": _gn(14), "ao": _gn(14), "antiguaandbarbuda": _gn(16), "antigua": _gn(16), "ag": _gn(16),
    "argentina": _gn(13), "ar": _gn(13), "armenia": _gn(16), "am": _gn(16),
    "australia": _australia, "aus": _australia, "oz": _australia, "au": _australia,
    "austria": _gn(18), "at": _gn(18), "azerbaijan": _gn(16), "az": _gn(16),
    "bahamas": _gn(18), "bs": _gn(18), "bahrain": _gn(21), "bh": _gn(21),
    "bangladesh": _gn(14), "bd": _gn(14), "barbados": _gn(16), "bb": _gn(16),
    "belarus": _gn(16), "by": _gn(16), "belgium": _gn(18), "be": _gn(18),
    "belize": _gn(16), "bz": _gn(16), "benin": _benin, "bj": _benin,
    "bhutan": _gn(18), "bt": _gn(18), "bolivia": _gn(18), "bo": _gn(18),
    "bosniaandherzegovina": _gn(18), "bosnia": _gn(18), "bih": _gn(18),
    "botswana": _gn(18), "bw": _gn(18), "brazil": _gn(14), "brasil": _gn(14), "br": _gn(14),
    "brunei": _gn(16), "bn": _gn(16), "bulgaria": _gn(14), "bg": _gn(14),
    "burkinafaso": _gn(18), "bf": _gn(18), "burundi": _gn(18), "bi": _gn(18),
    "caboverde": _gn(16), "capeverde": _gn(16), "cv": _gn(16), "cambodia": _gn(15), "kh": _gn(15),
    "cameroon": _gn(21), "cm": _gn(21), "canada": _gn(18), "ca": _gn(18),
    "centralafricanrepublic": _gn(18), "car": _gn(18), "cf": _gn(18), "chad": _gn(16), "td": _gn(16),
    "chile": _gn(18), "cl": _gn(18), "china": _china, "prc": _china, "peoplerepublicofchina": _china, "cn": _china,
    "colombia": _gn(14), "co": _gn(14), "comoros": _gn(15), "km": _gn(15),
    "congo": _gn(18), "republicofthecongo": _gn(18), "cg": _gn(18), "costarica": _gn(18), "cr": _gn(18),
    "croatia": _gn(15), "hr": _gn(15), "cuba": _gn(16), "cu": _gn(16), "cyprus": _gn(17), "cy": _gn(17),
    "czechia": _gn(15), "czechrepublic": _gn(15), "cz": _gn(15), "denmark": _gn(15), "dk": _gn(15),
    "djibouti": _gn(18), "dj": _gn(18), "dominica": _gn(16), "dm": _gn(16),
    "dominicanrepublic": _gn(18), "dr": _gn(18), "do": _gn(18), "ecuador": _gn(14), "ec": _gn(14),
    "egypt": _gn(18), "eg": _gn(18), "elsalvador": _gn(15), "sv": _gn(15), "equatorialguinea": _gn(18), "gq": _gn(18),
    "eritrea": _gn(18), "er": _gn(18), "estonia": _gn(18), "ee": _gn(18), "eswatini": _gn(18), "swaziland": _gn(18), "sz": _gn(18),
    "ethiopia": _gn(18), "et": _gn(18), "fiji": _gn(16), "fj": _gn(16), "finland": _gn(18), "fi": _gn(18),
    "france": _gn(15), "fr": _gn(15), "gabon": _gn(21), "ga": _gn(21), "gambia": _gn(18), "gm": _gn(18),
    "georgia": _gn(16), "ge": _gn(16), "germany": _gn(18), "de": _gn(18), "ghana": _gn(16), "gh": _gn(16),
    "greece": _gn(18), "gr": _gn(18), "grenada": _gn(16), "gd": _gn(16), "guatemala": _gn(18), "gt": _gn(18),
    "guinea": _gn(15), "gn": _gn(15), "guineabissau": _guineabissau, "gw": _guineabissau, "guyana": _gn(16), "gy": _gn(16),
    "haiti": _gn(15), "ht": _gn(15), "honduras": _gn(18), "hn": _gn(18), "hongkong": _gn(21), "hk": _gn(21),
    "hungary": _gn(18), "hu": _gn(18), "iceland": _gn(18), "is": _gn(18), "india": _gn(18), "in": _gn(18),
    "indonesia": _gn(18), "id": _gn(18), "iran": _gn(18), "ir": _gn(18), "iraq": _gn(18), "iq": _gn(18),
    "ireland": _gn(17), "ie": _gn(17), "israel": _gn(16), "il": _gn(16), "italy": _gn(16), "it": _gn(16),
    "jamaica": _gn(16), "jm": _gn(16), "japan": _gn(18), "jp": _gn(18), "jordan": _jordan, "jo": _jordan,
    "kazakhstan": _gn(16), "kz": _gn(16), "kenya": _gn(18), "ke": _gn(18), "kiribati": _gn(15), "ki": _gn(15),
    "kuwait": _kuwait, "kw": _kuwait, "kyrgyzstan": _gn(16), "kg": _gn(16), "laos": _gn(15), "la": _gn(15),
    "latvia": _gn(16), "lv": _gn(16), "lebanon": _gn(18), "lb": _gn(18), "lesotho": _gn(18), "ls": _gn(18),
    "liberia": _gn(18), "lr": _gn(18), "libya": _gn(18), "ly": _gn(18), "liechtenstein": _gn(18), "li": _gn(18),
    "lithuania": _gn(18), "lt": _gn(18), "luxembourg": _gn(16), "lu": _gn(16), "macau": _gn(14), "mo": _gn(14),
    "madagascar": _none_multi, "mg": _none_multi, "malawi": _gn(16), "mw": _gn(16), "malaysia": _malaysia, "my": _malaysia,
    "maldives": _gn(18), "mv": _gn(18), "mali": _gn(15), "ml": _gn(15), "malta": _gn(16), "mt": _gn(16),
    "marshallislands": _gn(16), "mh": _gn(16), "mauritania": _gn(18), "mr": _gn(18), "mauritius": _gn(16), "mu": _gn(16),
    "mexico": _mexico, "mx": _mexico, "micronesia": _gn(16), "fm": _gn(16), "moldova": _gn(16), "md": _gn(16),
    "monaco": _gn(15), "mc": _gn(15), "mongolia": _gn(16), "mn": _gn(16), "montenegro": _gn(18), "me": _gn(18),
    "morocco": _gn(18), "ma": _gn(18), "mozambique": _gn(18), "mz": _gn(18), "myanmar": _gn(16), "burma": _gn(16), "mm": _gn(16),
    "namibia": _gn(16), "na": _gn(16), "nauru": _gn(17), "nr": _gn(17), "nepal": _gn(18), "np": _gn(18),
    "netherlands": _gn(18), "nl": _gn(18), "newzealand": _gn(16), "nz": _gn(16), "nicaragua": _gn(18), "ni": _gn(18),
    "niger": _none_multi, "ne": _none_multi, "nigeria": _gn(18), "ng": _gn(18), "northkorea": _gn(15), "dprk": _gn(15), "kp": _gn(15),
    "northmacedonia": _gn(18), "macedonia": _gn(18), "mk": _gn(18), "norway": _gn(16), "no": _gn(16), "oman": _gn(18), "om": _gn(18),
    "pakistan": _gn(18), "pk": _gn(18), "palau": _gn(16), "pw": _gn(16), "palestine": _gn(18), "stateofpalestine": _gn(18), "ps": _gn(18),
    "panama": _gn(18), "pa": _gn(18), "papuanewguinea": _none_multi, "pg": _none_multi, "paraguay": _gn(16), "py": _gn(16),
    "peru": _gn(18), "pe": _gn(18), "philippines": _gn(18), "ph": _gn(18), "poland": _gn(18), "pl": _gn(18),
    "portugal": _gn(14), "pt": _gn(14), "qatar": _gn(18), "qa": _gn(18), "romania": _gn(18), "ro": _gn(18),
    "russia": _gn(16), "russianfederation": _gn(16), "ru": _gn(16), "rwanda": _gn(18), "rw": _gn(18),
    "saintkittsandnevis": _gn(16), "saintkitts": _gn(16), "kn": _gn(16), "saintlucia": _gn(16), "lc": _gn(16),
    "saintvincentandthegrenadines": _saintvincent, "saintvincent": _saintvincent, "vc": _saintvincent, "samoa": _gn(16), "ws": _gn(16),
    "sanmarino": _gn(18), "sm": _gn(18), "saotomeandprincipe": _gn(16), "saotome": _gn(16), "st": _gn(16),
    "saudiarabia": _gn(18), "saudi": _gn(18), "ksa": _gn(18), "sa": _gn(18), "senegal": _gn(16), "sn": _gn(16),
    "serbia": _gn(18), "rs": _gn(18), "seychelles": _gn(15), "sc": _gn(15), "sierraleone": _gn(18), "sl": _gn(18),
    "singapore": _gn(18), "sg": _gn(18), "slovakia": _gn(15), "sk": _gn(15), "slovenia": _gn(15), "si": _gn(15),
    "solomonislands": _solomonislands, "sb": _solomonislands, "somalia": _gn(18), "so": _gn(18), "southafrica": _gn(16), "za": _gn(16),
    "southkorea": _gn(16), "korea": _gn(16), "republicofkorea": _gn(16), "kr": _gn(16), "southsudan": _gn(18), "ss": _gn(18),
    "spain": _gn(18), "es": _gn(18), "srilanka": _srilanka, "sri": _srilanka, "lk": _srilanka, "sudan": _gn(13), "sd": _gn(13),
    "suriname": _gn(16), "sr": _gn(16), "sweden": _gn(18), "se": _gn(18), "switzerland": _gn(16), "ch": _gn(16),
    "syria": _gn(15), "sy": _gn(15), "taiwan": _gn(16), "tw": _gn(16), "tajikistan": _gn(16), "tj": _gn(16),
    "tanzania": _tanzania, "tz": _tanzania, "thailand": _gn(15), "th": _gn(15), "timorleste": _gn(14), "easttimor": _gn(14), "tl": _gn(14),
    "togo": _gn(15), "tg": _gn(15), "tonga": _gn(16), "to": _gn(16), "trinidadandtobago": _gn(18), "trinidad": _gn(18), "tt": _gn(18),
    "tunisia": _gn(18), "tn": _gn(18), "turkey": _gn(18), "turkiye": _gn(18), "tr": _gn(18), "turkmenistan": _gn(16), "tm": _gn(16),
    "tuvalu": _tuvalu, "tv": _tuvalu, "uganda": _gn(18), "ug": _gn(18), "ukraine": _gn(16), "ua": _gn(16),
    "uae": _gn(18), "unitedarabemirates": _gn(18), "ae": _gn(18), "uk": _gn(18), "unitedkingdom": _gn(18), "britain": _gn(18),
    "england": _gn(18), "scotland": _gn(18), "wales": _gn(18), "greatbritain": _gn(18), "gb": _gn(18),
    "usa": _usa, "us": _usa, "unitedstates": _usa, "unitedstatesofamerica": _usa, "america": _usa,
    "uruguay": _gn(18), "uy": _gn(18), "uzbekistan": _gn(16), "uz": _gn(16), "vanuatu": _gn(18), "vu": _gn(18),
    "vaticancity": _gn(18), "vatican": _gn(18), "va": _gn(18), "venezuela": _gn(16), "ve": _gn(16),
    "vietnam": _gn(16), "vn": _gn(16), "yemen": _gn(9), "ye": _gn(9), "zambia": _gn(16), "zm": _gn(16),
    "zimbabwe": _gn(16), "zw": _gn(16)
}

CRISIS_RESOURCES = [
    {"name": "Immediate Crisis Support (US/Canada)", "value": "**Crisis Text Line:** Text HOME to `741741`\n**Childhelp National Child Abuse:** Call/Text `1-800-422-4453`\n**988 Suicide & Crisis Lifeline:** Call or Text `988`"},
    {"name": "Sexual Abuse & Exploitation (US)", "value": "**RAINN (Rape/Abuse/Incest):** `1-800-656-HOPE` | [rainn.org](https://www.rainn.org)\n**NCMEC CyberTipline:** [report.cybertipline.org](https://report.cybertipline.org)"},
    {"name": "United Kingdom", "value": "**Childline:** `0800 1111` | [childline.org.uk](https://www.childline.org.uk)\n**NSPCC:** `0808 800 5000` | [nspcc.org.uk](https://www.nspcc.org.uk)\n**Rape Crisis:** `0808 802 9999` | [rapecrisis.org.uk](https://rapecrisis.org.uk)"},
    {"name": "Canada", "value": "**Kids Help Phone:** `1-800-668-6868` | [kidshelpphone.ca](https://kidshelpphone.ca)\n**Canadian Centre for Child Protection:** [protectchildren.ca](https://www.protectchildren.ca)"},
    {"name": "Australia", "value": "**Kids Helpline:** `1800 55 1800` | [kidshelpline.com.au](https://kidshelpline.com.au)\n**Bravehearts:** `1800 272 831` | [bravehearts.org.au](https://bravehearts.org.au)"},
    {"name": "India", "value": "**Childline India:** `1098` | [childlineindia.org.in](https://www.childlineindia.org.in)\n**Vandrevala Foundation:** `9999 666 555`"},
    {"name": "International Support", "value": "**Befrienders Worldwide:** [befrienders.org](https://www.befrienders.org)\n**Find A Helpline:** [findahelpline.com](https://findahelpline.com)\n**International Association for Suicide Prevention:** [iasp.info](https://www.iasp.info)"},
    {"name": "Removing Explicit Images", "value": "**Take It Down (NCMEC - Under 18):** [takendown.org](https://takendown.org)\n**StopNCII (Adults 18+):** [stopncii.org](https://stopncii.org)"},
    {"name": "Sextortion / Online Blackmail", "value": "**FBI Internet Crime Complaint Center:** [ic3.gov](https://www.ic3.gov)\n**Stop Sextortion (NCMEC):** [stopsextortion.com](https://www.stopsextortion.com)"}
]

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

secure_channel_cache = None
mod_log_channel_cache = None
issue_channel_cache = None
forum_channel_cache = None
conversation_forum_channel_cache = None
commands_synced = False

async def init_db():
    async with aiosqlite.connect("reports.db") as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""CREATE TABLE IF NOT EXISTS pending_uploads (
                            user_id INTEGER, report_id TEXT PRIMARY KEY, thread_id INTEGER, 
                            msg_id INTEGER, last_activity REAL, created_timestamp REAL)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS rate_limits (
                            user_id INTEGER PRIMARY KEY, last_report REAL)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS reports (
                            report_id TEXT PRIMARY KEY, status TEXT DEFAULT 'Pending', 
                            created TEXT, closed TEXT, assigned_mod INTEGER, evidence_count INTEGER DEFAULT 0,
                            report_type TEXT, reporter_id INTEGER, msg_id INTEGER, is_anonymous INTEGER DEFAULT 0,
                            reported_handle TEXT, thread_id INTEGER, thread_created_timestamp REAL,
                            forum_thread_id INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS dm_replies (
                            message_id INTEGER PRIMARY KEY, report_id TEXT, user_id INTEGER)""")
        
        await db.execute("""CREATE TABLE IF NOT EXISTS evidence (
                            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            report_id TEXT NOT NULL,
                            discord_message_id INTEGER,
                            uploader_id INTEGER,
                            filename TEXT,
                            status TEXT DEFAULT 'approved',
                            created_at TEXT,
                            FOREIGN KEY (report_id) REFERENCES reports(report_id))""")

        await db.execute("""CREATE TABLE IF NOT EXISTS audit_log (
                            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            report_id TEXT,
                            actor_id INTEGER,
                            action TEXT,
                            timestamp TEXT)""")

        try: await db.execute("ALTER TABLE reports ADD COLUMN victim_sex TEXT")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN forum_msg_id INTEGER")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN conversation_thread_id INTEGER")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN conversation_msg_id INTEGER")
        except aiosqlite.OperationalError: pass
            
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pending_user ON pending_uploads(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_evidence_report ON evidence(report_id)")
            
        await db.commit()

async def log_audit_action(report_id: str, actor_id: int, action: str):
    async with aiosqlite.connect("reports.db") as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("INSERT INTO audit_log (report_id, actor_id, action, timestamp) VALUES (?, ?, ?, ?)",
                         (report_id, actor_id, action, datetime.now(timezone.utc).isoformat()))
        await db.commit()

def is_moderator(interaction: discord.Interaction):
    if isinstance(interaction.user, discord.User): return False
    if interaction.user.guild_permissions.administrator: return True
    if MOD_ROLE_ID in [r.id for r in interaction.user.roles]: return True
    return False

async def is_explicit_image(image_bytes: bytes) -> bool:
    if not nude_detector:
        return True 
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
            temp.write(image_bytes)
            temp_path = temp.name
            
        try:
            detections = await asyncio.wait_for(asyncio.to_thread(nude_detector.detect, temp_path), timeout=30.0)
        except asyncio.TimeoutError:
            log.error(f"NudeNet scan timed out on temp file {temp_path}")
            return True 
        
        explicit_labels = {
            "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED",
            "MALE_GENITALIA_EXPOSED", "BUTTOCKS_EXPOSED", "ANUS_EXPOSED"
        }
        
        for det in detections:
            if det['class'] in explicit_labels:
                return True
                
        return False
    except Exception as e:
        log.error(f"NudeNet scan error on temp file {temp_path}: {e}")
        return True 
    finally:
        if temp_path:
            try: os.remove(temp_path)
            except OSError: pass

async def create_evidence_thread(report_id: str, reported_handle: str, report_msg: discord.Message):
    thread_name = f"{report_id} - {reported_handle[:40]}" if reported_handle else report_id
    try:
        thread = await report_msg.create_thread(name=thread_name, auto_archive_duration=1440)
        return thread
    except discord.HTTPException as e:
        log.error(f"Failed to create evidence thread for {report_id}: {e}")
        return None

def get_consent_reference(country_raw: str, victim_sex: str):
    """Helper to lookup consent reference based on country and victim sex."""
    country_data = CONSENT_LAWS.get(country_raw)
    if not country_data:
        sorted_keys = sorted([k for k in CONSENT_LAWS.keys() if len(k) >= 4], key=len, reverse=True)
        for key in sorted_keys:
            if key in country_raw:
                country_data = CONSENT_LAWS[key]
                break
    
    if not country_data:
        return None, False, ""
        
    is_jurisdiction_specific = country_data.get("jurisdiction_specific", False)
    notes = country_data.get("notes", "")
    
    if victim_sex == "Male":
        return country_data.get("male"), is_jurisdiction_specific, notes
    elif victim_sex == "Female":
        return country_data.get("female"), is_jurisdiction_specific, notes
    else:
        return None, is_jurisdiction_specific, notes


class TriageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def approve_image(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to do this.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)

        msg = interaction.message
        match = re.search(r'PR-\d{8}-[A-F0-9]{8}', msg.content)
        if not match:
            return await interaction.followup.send("Could not find the Report ID in the message.", ephemeral=True)
        report_id = match.group(0)

        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT status, thread_id, reported_handle, msg_id FROM reports WHERE report_id=?", (report_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return await interaction.followup.send("Report not found in database.", ephemeral=True)
                if row[0] in ["Resolved", "False Report"]:
                    return await interaction.followup.send("Case is closed. Cannot approve evidence.", ephemeral=True)
                
                status, thread_id, reported_handle, report_msg_id = row

        if not thread_id and report_msg_id:
            try:
                report_msg = await secure_channel_cache.fetch_message(report_msg_id)
                thread = await create_evidence_thread(report_id, reported_handle, report_msg)
                if thread:
                    thread_id = thread.id
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("UPDATE reports SET thread_id=?, thread_created_timestamp=? WHERE report_id=?", (thread_id, time.time(), report_id))
                        await db.commit()
            except discord.HTTPException as e:
                log.error(f"Failed to create thread for {report_id}: {e}")

        if not thread_id:
            return await interaction.followup.send("Failed to find or create evidence thread.", ephemeral=True)

        try:
            thread = bot.get_channel(thread_id) or await bot.fetch_channel(thread_id)
        except (discord.NotFound, discord.Forbidden):
            return await interaction.followup.send("Failed to find evidence thread.", ephemeral=True)

        attachments_to_process = msg.attachments
        success_count = 0
        
        for att in attachments_to_process:
            async with aiosqlite.connect("reports.db") as db:
                await db.execute("BEGIN IMMEDIATE")
                cursor = await db.execute("UPDATE reports SET evidence_count = evidence_count + 1 WHERE report_id=? AND evidence_count < ?", 
                                         (report_id, MAX_EVIDENCE))
                if cursor.rowcount == 0:
                    await db.execute("ROLLBACK")
                    break 
                
                await db.execute("INSERT INTO evidence (report_id, discord_message_id, uploader_id, filename, status, created_at) VALUES (?, ?, ?, ?, 'approved', ?)",
                                 (report_id, msg.id, msg.author.id, att.filename, datetime.now(timezone.utc).isoformat()))
                await db.execute("COMMIT")

            try:
                file = await att.to_file()
                await thread.send(content=f"📸 **Approved Evidence for {report_id}**", file=file)
                success_count += 1
            except discord.HTTPException as e:
                log.error(f"Failed to forward file {att.filename} for {report_id}: {e}")

        if success_count == 0:
            return await interaction.followup.send("Failed to forward files or max evidence reached.", ephemeral=True)

        try:
            await msg.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            log.error(f"Failed to delete triage message for {report_id}: {e}")

        await log_audit_action(report_id, interaction.user.id, "evidence_approved")
        await interaction.followup.send(f"Approved {success_count} image(s). Moved to case thread.", ephemeral=True)

    async def reject_image(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to do this.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            log.error(f"Error deleting triage image: {e}")
            
        report_id_match = re.search(r'PR-\d{8}-[A-F0-9]{8}', interaction.message.content)
        if report_id_match:
            await log_audit_action(report_id_match.group(0), interaction.user.id, "evidence_rejected")

        await interaction.followup.send("Image nuked from the channel and blocked from logs.", ephemeral=True)

    @discord.ui.button(label="✅ Approve & Move", style=discord.ButtonStyle.success, custom_id="triage_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.approve_image(interaction)

    @discord.ui.button(label="❌ Delete (Illegal/Nuke)", style=discord.ButtonStyle.danger, custom_id="triage_delete")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.reject_image(interaction)


class ModActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_report(self, interaction: discord.Interaction, status: str, is_closed: bool = False):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to manage reports.", ephemeral=True)

        if not interaction.message.embeds or not interaction.message.embeds[0].author:
            return await interaction.response.send_message("Error: Could not find report embed.", ephemeral=True)

        report_id = interaction.message.embeds[0].author.name

        await interaction.response.defer(ephemeral=True)

        global forum_channel_cache
        if not forum_channel_cache and FORUM_CHANNEL_ID != 0:
            try:
                forum_channel_cache = bot.get_channel(FORUM_CHANNEL_ID) or await bot.fetch_channel(FORUM_CHANNEL_ID)
            except discord.NotFound:
                log.error("ERROR: FORUM_CHANNEL_ID not found during status update!")
            except discord.Forbidden:
                log.error("ERROR: Bot lacks permissions to view FORUM_CHANNEL_ID.")

        # Fetch reporter_id to send them a DM
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT status, thread_id, reported_handle, msg_id, forum_thread_id, reporter_id FROM reports WHERE report_id=?", (report_id,)) as cur:
                row = await cur.fetchone()
                if row and row[0] in ["Resolved", "False Report"]:
                    return await interaction.followup.send("This case is already closed and cannot be modified.", ephemeral=True)
                if row: 
                    thread_id, reported_handle, msg_id, forum_thread_id, reporter_id = row[1], row[2], row[3], row[4], row[5]
                else:
                    return await interaction.followup.send("Report not found.", ephemeral=True)

            await db.execute("UPDATE reports SET status=?, assigned_mod=?, closed=? WHERE report_id=?", 
                             (status, interaction.user.id, datetime.now(timezone.utc).isoformat() if is_closed else None, report_id))
            await db.commit()
        
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT evidence_count FROM reports WHERE report_id=?", (report_id,)) as cur:
                row = await cur.fetchone()
                ev_count = row[0] if row else 0

        embed = interaction.message.embeds[0]
        
        view_to_send = ModActionView()
        if is_closed:
            for child in view_to_send.children: child.disabled = True
            embed.title = f"🔒 CASE CLOSED: {status}"
            embed.color = discord.Color.dark_grey()
            embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)

        embed.set_footer(text=f"Status: {status} | Evidence: {ev_count} attachments")

        if status == "Under Review" and not thread_id:
            try:
                thread = await create_evidence_thread(report_id, reported_handle, interaction.message)
                if thread:
                    thread_id = thread.id
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("UPDATE reports SET thread_id=?, thread_created_timestamp=? WHERE report_id=?", (thread_id, time.time(), report_id))
                        await db.commit()
                    await thread.send("🔍 This case is now under review. Evidence will be posted here.")
            except Exception as e:
                log.error(f"Failed to auto-create evidence thread for {report_id}: {e}")

        try:
            await interaction.message.edit(embed=embed, view=view_to_send)
        except discord.NotFound:
            log.warning(f"Failed to edit message for {report_id}: Message not found.")

        thread_name = reported_handle[:90] if reported_handle else report_id
        
        if not forum_thread_id and forum_channel_cache:
            try:
                forum_thread = await forum_channel_cache.create_thread(name=thread_name, embed=embed)
                if isinstance(forum_thread, tuple):
                    forum_thread = forum_thread[0]
                
                forum_thread_id = forum_thread.id
                forum_msg_id = forum_thread.id  # Discord API: starter message ID is the same as thread ID
                
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("UPDATE reports SET forum_thread_id=?, forum_msg_id=? WHERE report_id=?", (forum_thread_id, forum_msg_id, report_id))
                    await db.commit()
            except Exception as e:
                log.error(f"Failed to create forum post for {report_id}: {e}")
        elif forum_thread_id:
            try:
                async with aiosqlite.connect("reports.db") as db:
                    async with db.execute("SELECT forum_msg_id FROM reports WHERE report_id=?", (report_id,)) as cur:
                        row = await cur.fetchone()
                        forum_msg_id = row[0] if row and row[0] else None
                
                if forum_msg_id is None:
                    log.warning(f"Cannot update forum post for {report_id}: forum_msg_id is missing from DB.")
                else:
                    forum_thread = await bot.fetch_channel(forum_thread_id)
                    forum_msg = await forum_thread.fetch_message(forum_msg_id)
                    await forum_msg.edit(embed=embed)
            except Exception as e:
                log.error(f"Failed to update forum post for {report_id}: {e}")

        if mod_log_channel_cache:
            try:
                log_embed = discord.Embed(
                    title=f"Case Status Updated: {report_id}",
                    description=f"Status changed to **{status}** by {interaction.user.mention}.",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                await mod_log_channel_cache.send(embed=log_embed)
            except Exception as e:
                log.error(f"Failed to send mod log for {report_id}: {e}")

        if is_closed and thread_id:
            try:
                thread = await bot.fetch_channel(thread_id)
                await thread.send("🔒 This case has been closed. The thread is now locked.")
                await thread.edit(archived=True, locked=True)
            except discord.HTTPException as e:
                log.error(f"Failed to lock thread for {report_id}: {e}")
                
        await log_audit_action(report_id, interaction.user.id, f"status_changed_{status}")

        # DM the reporter about the status change
        if reporter_id:
            try:
                reporter = bot.get_user(reporter_id) or await bot.fetch_user(reporter_id)
                if reporter:
                    dm_msg = ""
                    if status == "Under Review":
                        dm_msg = f"Your report (**{report_id}**) is now under review by our moderation team. We will reach out if we need more information."
                    elif status == "Resolved":
                        dm_msg = f"Your report (**{report_id}**) has been marked as resolved. Thank you for bringing this to our attention. If you need further help, please use `/resources`."
                    elif status == "False Report":
                        dm_msg = f"Your report (**{report_id}**) has been reviewed and closed. Thank you for your submission."
                    
                    if dm_msg:
                        await reporter.send(dm_msg)
            except discord.Forbidden:
                log.warning(f"Could not DM reporter {reporter_id} for status update on {report_id} (DMs closed).")
            except Exception as e:
                log.error(f"Failed to send status update DM for {report_id}: {e}")
        
        if is_closed:
            await interaction.followup.send(f"Report status updated to: **{status}**. Case archived and thread locked.", ephemeral=True)
        else:
            await interaction.followup.send(f"Report status updated to: **{status}**", ephemeral=True)

    @discord.ui.button(label="Under Review", style=discord.ButtonStyle.primary, custom_id="mod_btn_review")
    async def review_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_report(interaction, "Under Review")

    @discord.ui.button(label="Resolved", style=discord.ButtonStyle.success, custom_id="mod_btn_resolved")
    async def resolved_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_report(interaction, "Resolved", is_closed=True)

    @discord.ui.button(label="False Report", style=discord.ButtonStyle.danger, custom_id="mod_btn_false")
    async def false_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_report(interaction, "False Report", is_closed=True)


class AnonView(discord.ui.View):
    def __init__(self, report_type: str):
        super().__init__(timeout=300)
        self.report_type = report_type
        self.message = None

    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(view=self)
            except discord.NotFound: pass

    @discord.ui.button(label="Stay Anonymous", style=discord.ButtonStyle.green)
    async def anon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(is_anonymous=True, report_type=self.report_type))

    @discord.ui.button(label="Share My Discord Name", style=discord.ButtonStyle.blurple)
    async def name_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(is_anonymous=False, report_type=self.report_type))


class ReportModal(discord.ui.Modal, title='Predator Report Form'):
    def __init__(self, is_anonymous: bool, report_type: str):
        super().__init__()
        self.is_anonymous = is_anonymous
        self.report_type = report_type

    online_name = discord.ui.TextInput(label="Reported Subject's Online Handle", placeholder="Discord username, display name, or tag", required=True, max_length=100)
    age_pedo = discord.ui.TextInput(label="Reported Subject's Age", placeholder="Numbers only (e.g., 24)", required=True, max_length=3)
    age_victim = discord.ui.TextInput(label="Victim Age & Sex (M/F)", placeholder="e.g., 15 M or 16 Female", required=True, max_length=20)
    country = discord.ui.TextInput(label="Country/Jurisdiction", placeholder="e.g., USA, UK, Malaysia", required=True, max_length=50)
    details = discord.ui.TextInput(label="Full Details of Incident", style=discord.TextStyle.paragraph, placeholder="Explain the allegation. If you know the subject's real name, put it here.", required=True, max_length=2000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            pedo_age_str = self.age_pedo.value.strip()
            pedo_age_match = re.search(r'\d+', pedo_age_str)
            if not pedo_age_match: raise ValueError("Invalid subject age")
            pedo_age = int(pedo_age_match.group())
            if not (1 <= pedo_age <= 120): raise ValueError("Invalid subject age")

            victim_input_str = self.age_victim.value.strip()
            age_match = re.search(r'\d+', victim_input_str)
            if not age_match: raise ValueError("Invalid victim age")
            victim_age = int(age_match.group())
            if not (1 <= victim_age <= 120): raise ValueError("Invalid victim age")
            
            letters_only = re.sub(r'[^a-zA-Z]', '', victim_input_str).lower()
            if 'female' in letters_only or letters_only == 'f':
                victim_sex = "Female"
            elif 'male' in letters_only or letters_only == 'm':
                victim_sex = "Male"
            else:
                raise ValueError("Missing victim sex (M/F)")

        except ValueError as e:
            return await interaction.followup.send(f"Validation Error: {str(e)}. Please ensure you include numbers for ages and M/F for the victim's sex.", ephemeral=True)

        async with aiosqlite.connect("reports.db") as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute("SELECT last_report FROM rate_limits WHERE user_id=?", (interaction.user.id,))
            row = await cursor.fetchone()
            if row and (time.time() - row[0]) < 300:
                await db.execute("ROLLBACK")
                return await interaction.followup.send("Thank you for reaching out. To ensure our system can handle every report securely, please wait about 5 minutes before submitting another one.", ephemeral=True)
            await db.execute("""INSERT INTO rate_limits (user_id, last_report) VALUES (?, ?) 
                                ON CONFLICT(user_id) DO UPDATE SET last_report = excluded.last_report""", 
                             (interaction.user.id, time.time()))
            await db.execute("COMMIT")

        country_raw = re.sub(r'[^a-zA-Z0-9]', '', self.country.value).lower()
        country_str = self.country.value.strip()
        
        legal_age, is_jurisdiction_specific, consent_notes = get_consent_reference(country_raw, victim_sex)

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        report_id = f"PR-{date_str}-{secrets.token_hex(4).upper()}"

        embed = discord.Embed(
            title=f"🚨 {self.report_type.upper()} INCIDENT",
            description=self.details.value,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name=report_id)
        embed.set_footer(text="Status: Pending | Evidence: 0 attachments")
        embed.add_field(name="Report ID", value=f"`{report_id}`", inline=False)

        if self.is_anonymous:
            embed.add_field(name="Reporter Contact", value="Anonymous (Use /reply to message them)", inline=False)
        else:
            embed.add_field(name="Reporter Contact", value=f"{interaction.user.mention} ({interaction.user.name})", inline=False)

        embed.add_field(name="Online Handle", value=self.online_name.value, inline=True)
        embed.add_field(name="Subject Age", value=str(pedo_age), inline=True)
        embed.add_field(name="Victim Info", value=f"{victim_age} ({victim_sex})", inline=True)
        embed.add_field(name="Jurisdiction", value=country_str, inline=True)

        false_report_flag = False
        if pedo_age < 10 or victim_age < 5:
            false_report_flag = True
            embed.add_field(name="🚨 POTENTIAL FALSE REPORT 🚨", value="System flagged this due to impossible or unrealistic ages. Review carefully.", inline=False)

        if not false_report_flag:
            if legal_age is not None and victim_age < legal_age:
                embed.add_field(name="⚠️ AGE THRESHOLD REVIEW SIGNAL ⚠️", value=f"**Moderator review required.** The supplied victim age ({victim_age}) is below the configured reference threshold ({legal_age}) for the reported sex and jurisdiction. This is a screening signal only and does not determine whether conduct is criminal.", inline=False)
            elif legal_age is None and (is_jurisdiction_specific or consent_notes):
                base_msg = "The reference dataset does not provide a single numeric threshold for the reported victim sex in this jurisdiction. A moderator must review the applicable law."
                if consent_notes:
                    base_msg += f" ({consent_notes})"
                embed.add_field(name="⚠️ LEGAL REVIEW REQUIRED ⚠️", value=base_msg, inline=False)

        global secure_channel_cache, conversation_forum_channel_cache
        if not secure_channel_cache:
            secure_channel_cache = bot.get_channel(SECURE_CHANNEL_ID) or await bot.fetch_channel(SECURE_CHANNEL_ID)

        if not conversation_forum_channel_cache and CONVERSATION_FORUM_CHANNEL_ID != 0:
            try:
                conversation_forum_channel_cache = bot.get_channel(CONVERSATION_FORUM_CHANNEL_ID) or await bot.fetch_channel(CONVERSATION_FORUM_CHANNEL_ID)
            except discord.NotFound:
                log.error("ERROR: CONVERSATION_FORUM_CHANNEL_ID not found during report creation!")
            except discord.Forbidden:
                log.error("ERROR: Bot lacks permissions to view CONVERSATION_FORUM_CHANNEL_ID.")

        async with aiosqlite.connect("reports.db") as db:
            try:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute("INSERT INTO reports (report_id, report_type, reporter_id, status, created, evidence_count, is_anonymous, reported_handle, victim_sex) VALUES (?, ?, ?, 'Pending', ?, 0, ?, ?, ?)", 
                                 (report_id, self.report_type, interaction.user.id, datetime.now(timezone.utc).isoformat(), 1 if self.is_anonymous else 0, self.online_name.value, victim_sex))
                
                await db.execute("DELETE FROM pending_uploads WHERE user_id=?", (interaction.user.id,))
                await db.execute("INSERT OR REPLACE INTO pending_uploads (user_id, report_id, thread_id, msg_id, last_activity, created_timestamp) VALUES (?, ?, NULL, NULL, ?, ?)",
                                 (interaction.user.id, report_id, time.time(), time.time()))
                await db.commit()
            except aiosqlite.Error as e:
                log.error(f"DB Insert failed for {report_id}: {e}")
                return await interaction.followup.send("We ran into a technical issue saving your report. Please try again in a moment.", ephemeral=True)

        try:
            report_msg = await secure_channel_cache.send(embed=embed, view=ModActionView())
            async with aiosqlite.connect("reports.db") as db:
                await db.execute("UPDATE reports SET msg_id=? WHERE report_id=?", (report_msg.id, report_id))
                await db.commit()
        except discord.HTTPException as e:
            log.error(f"Failed to send to secure channel for {report_id}: {e}")
            async with aiosqlite.connect("reports.db") as db:
                await db.execute("DELETE FROM reports WHERE report_id=?", (report_id,))
                await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                await db.commit()
            return await interaction.followup.send("We ran into a technical issue submitting this to the team. Please try again later.", ephemeral=True)

        # Create Conversation Thread dynamically if cache exists or was just fetched
        if conversation_forum_channel_cache:
            try:
                conv_thread_name = f"{self.online_name.value[:80]} - {report_id}"
                reporter_info = "Anonymous" if self.is_anonymous else f"{interaction.user.mention} ({interaction.user.name})"
                init_content = f"Conversations between us and the victim.\n**Victim:** {reporter_info}\n**Report ID:** `{report_id}`"
                
                # Discord API requires a starting message when creating a forum thread
                conv_thread = await conversation_forum_channel_cache.create_thread(name=conv_thread_name, content=init_content)
                
                if isinstance(conv_thread, tuple):
                    conv_thread = conv_thread[0]
                
                conversation_thread_id = conv_thread.id
                conversation_msg_id = conv_thread.id  # Discord API: starter message ID is the same as thread ID
                
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("UPDATE reports SET conversation_thread_id=?, conversation_msg_id=? WHERE report_id=?", (conversation_thread_id, conversation_msg_id, report_id))
                    await db.commit()
            except Exception as e:
                log.error(f"Failed to create conversation thread for {report_id}: {e}")
        else:
            if CONVERSATION_FORUM_CHANNEL_ID == 0:
                log.error("CONVERSATION_FORUM_CHANNEL_ID is 0 or missing from .env. Replies will fall back to secure channel.")
            else:
                log.error("Conversation Forum Channel cache is None. Check bot permissions.")

        await log_audit_action(report_id, interaction.user.id, "report_created")
        await interaction.followup.send("Thank you for reaching out. It takes courage to speak up, and your report has been securely received and forwarded to our team.\n\n**Please check your Direct Messages (DMs) from me** to upload any screenshots you have.", ephemeral=True)

        try:
            await interaction.user.send(
                f"Hi there. We've received your report (**{report_id}**), and our team will be reviewing the information you provided.\n\n"
                f"If you have screenshots of the conversations, you can upload them directly here in our DMs. Take your time. When you're finished, just type `done`. This channel is private and secure.\n\n"
                f"⚠️ **IMPORTANT DISCLAIMER REGARDING EVIDENCE:**\n"
                f"Please **DO NOT** upload explicit nudity or Child Sexual Abuse Material (CSAM). Our system automatically scans for explicit content to protect our moderation team. If your chat logs or evidence contain explicit imagery, you must crop it out or redact it so that only the text of the conversation is visible."
            )
        except discord.Forbidden:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log.error(f"Modal error in {self.__class__.__name__}: {error}", exc_info=True)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong processing this. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong processing this. Please try again.", ephemeral=True)
        except Exception:
            pass


class IssueReplyModal(discord.ui.Modal, title='Reply to Issue Reporter'):
    def __init__(self, reporter_id: int):
        super().__init__()
        self.reporter_id = reporter_id

    reply = discord.ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, placeholder="Type your response to the user who reported this issue...", required=True, max_length=2000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            reporter = bot.get_user(self.reporter_id) or await bot.fetch_user(self.reporter_id)
        except (discord.NotFound, discord.HTTPException):
            return await interaction.followup.send("Could not find that user.", ephemeral=True)
            
        if not reporter:
            return await interaction.followup.send("Could not find that user.", ephemeral=True)
        
        try:
            await reporter.send(f"**Update from the Development/Mod Team regarding your bot issue:**\n\n{self.reply.value}")
            await interaction.followup.send("Reply sent successfully.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Failed to send DM. The user has their DMs closed.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log.error(f"Modal error in {self.__class__.__name__}: {error}", exc_info=True)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong processing this. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong processing this. Please try again.", ephemeral=True)
        except Exception:
            pass


class IssueView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💬 Reply to Reporter", style=discord.ButtonStyle.primary, custom_id="issue_reply_btn")
    async def reply_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)
        
        if not interaction.message.embeds:
            return await interaction.response.send_message("Could not find embed data.", ephemeral=True)
            
        reporter_id = None
        footer_text = interaction.message.embeds[0].footer.text
        if footer_text:
            match = re.search(r'ID: (\d+)', footer_text)
            if match: reporter_id = int(match.group(1))
            
        if not reporter_id:
            return await interaction.response.send_message("Could not find the reporter's ID.", ephemeral=True)
            
        await interaction.response.send_modal(IssueReplyModal(reporter_id=reporter_id))

    @discord.ui.button(label="✅ Mark Resolved", style=discord.ButtonStyle.success, custom_id="issue_resolve_btn")
    async def resolve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)
        
        for child in self.children: child.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Issue Resolved"
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("Issue marked as resolved.", ephemeral=True)

    @discord.ui.button(label="❌ Mark as False/Invalid", style=discord.ButtonStyle.danger, custom_id="issue_false_btn")
    async def false_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)
        
        for child in self.children: child.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        embed.title = "❌ Issue Marked as False/Invalid"
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("Issue marked as false/invalid.", ephemeral=True)


class ReportGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="report", description="Report an incident to the moderation team")

    async def _send_view(self, interaction: discord.Interaction, report_type: str):
        view = AnonView(report_type=report_type)
        await interaction.response.send_message(f"You selected **{report_type}**. Please know that this process is entirely confidential. Choose how you would like to submit your report to our team:", view=view, ephemeral=True)
        try:
            view.message = await interaction.original_response()
        except Exception:
            pass

    @app_commands.command(name="grooming", description="Report a grooming incident.")
    async def grooming(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Grooming")

    @app_commands.command(name="sexual_abuse", description="Report a Sexual Abuse incident.")
    async def sexual_abuse(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Sexual Abuse")

    @app_commands.command(name="rape", description="Report a rape incident.")
    async def rape(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Rape")

    @app_commands.command(name="sextortion", description="Report a sextortion incident.")
    async def sextortion(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Sextortion")

    @app_commands.command(name="endangerment", description="Report a child endangerment incident.")
    async def endangerment(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Child Endangerment")

    @app_commands.command(name="other", description="Report another type of predator incident.")
    async def other(self, interaction: discord.Interaction):
        await self._send_view(interaction, "Other")

bot.tree.add_command(ReportGroup())

class SystemGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="system", description="System commands and utilities")

    @app_commands.command(name="issue", description="Report a bug or issue with the bot.")
    @app_commands.describe(
        title="A short title summarizing the issue.",
        description="Describe the issue you are experiencing in detail."
    )
    async def issue(self, interaction: discord.Interaction, title: str, description: str):
        await interaction.response.defer(ephemeral=True)
        
        global issue_channel_cache
        if not issue_channel_cache and ISSUE_CHANNEL_ID != 0:
            try:
                issue_channel_cache = bot.get_channel(ISSUE_CHANNEL_ID) or await bot.fetch_channel(ISSUE_CHANNEL_ID)
            except discord.Forbidden:
                log.error("Bot lacks permissions to view ISSUE_CHANNEL_ID.")
            except discord.NotFound:
                log.error("ISSUE_CHANNEL_ID does not exist.")
            except Exception as e:
                log.error(f"Failed to fetch ISSUE_CHANNEL_ID: {e}")
        
        if not issue_channel_cache:
            return await interaction.followup.send("I couldn't find the issue reporting channel. Please ensure the bot has the 'View Channel' permission for it.", ephemeral=True)
        
        safe_title = title[:90]
        
        embed = discord.Embed(
            title=f"🛠️ Issue: {safe_title}",
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Reported By", value=f"{interaction.user.mention} ({interaction.user.name})", inline=False)
        embed.add_field(name="Location", value=f"Guild: {interaction.guild.name} ({interaction.guild.id})" if interaction.guild else "DMs", inline=False)
        embed.set_footer(text=f"ID: {interaction.user.id}") 
        
        try:
            if isinstance(issue_channel_cache, discord.ForumChannel):
                await issue_channel_cache.create_thread(name=safe_title, embed=embed, view=IssueView())
            else:
                await issue_channel_cache.send(embed=embed, view=IssueView())
                
            await interaction.followup.send("Thank you, your issue has been reported to the developers.", ephemeral=True)
        except Exception as e:
            log.error(f"Failed to submit issue: {e}")
            await interaction.followup.send("Failed to submit the issue. Please try again later.", ephemeral=True)

bot.tree.add_command(SystemGroup())

@bot.tree.command(name="reply", description="Send a message to the person who submitted a report via DM.")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(report_id="The ID of the report (e.g., PR-2023...)", message="The message to send them")
async def reply(interaction: discord.Interaction, report_id: str, message: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    
    async with aiosqlite.connect("reports.db") as db:
        async with db.execute("SELECT reporter_id, status, msg_id, conversation_thread_id FROM reports WHERE report_id=?", (report_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return await interaction.followup.send("Report ID not found.", ephemeral=True)
            reporter_id, status, orig_msg_id, conv_thread_id = row

    if status in ["Resolved", "False Report"]:
        return await interaction.followup.send("This case is closed. You cannot reply to it.", ephemeral=True)

    try:
        reporter = bot.get_user(reporter_id) or await bot.fetch_user(reporter_id)
    except (discord.NotFound, discord.HTTPException):
        return await interaction.followup.send("Could not find the user. They may have deleted their account.", ephemeral=True)

    if not reporter:
        return await interaction.followup.send("Could not find the user.", ephemeral=True)

    # 1. Send to victim (no mod name)
    victim_msg_content = f"**A message from our Moderation Team regarding your report `{report_id}`:**\n\n{message}\n\n*(Reply to this message to respond to the moderation team)*"
    try:
        sent_msg = await reporter.send(victim_msg_content)
        async with aiosqlite.connect("reports.db") as db:
            await db.execute("INSERT INTO dm_replies (message_id, report_id, user_id) VALUES (?, ?, ?)", 
                             (sent_msg.id, report_id, reporter_id))
            await db.commit()
    except discord.Forbidden:
        return await interaction.followup.send("I couldn't reach them. It looks like they have their DMs closed.", ephemeral=True)

    # 2. Send to conversation thread (with mod name, rephrased)
    # Auto-create conversation thread if it's missing
    global conversation_forum_channel_cache
    if not conversation_forum_channel_cache and CONVERSATION_FORUM_CHANNEL_ID != 0:
        try:
            conversation_forum_channel_cache = bot.get_channel(CONVERSATION_FORUM_CHANNEL_ID) or await bot.fetch_channel(CONVERSATION_FORUM_CHANNEL_ID)
        except discord.NotFound:
            log.error("ERROR: CONVERSATION_FORUM_CHANNEL_ID not found during /reply!")

    if not conv_thread_id and conversation_forum_channel_cache:
        try:
            async with aiosqlite.connect("reports.db") as db:
                async with db.execute("SELECT reported_handle, is_anonymous FROM reports WHERE report_id=?", (report_id,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        reported_handle, is_anon = row
                        conv_thread_name = f"{reported_handle[:80] if reported_handle else 'Unknown'} - {report_id}"
                        reporter_info = "Anonymous" if is_anon else f"<@{reporter_id}>"
                        init_content = f"Conversations between us and the victim.\n**Victim:** {reporter_info}\n**Report ID:** `{report_id}`"
                        
                        conv_thread = await conversation_forum_channel_cache.create_thread(name=conv_thread_name, content=init_content)
                        if isinstance(conv_thread, tuple):
                            conv_thread = conv_thread[0]
                        conv_thread_id = conv_thread.id
                        
                        await db.execute("UPDATE reports SET conversation_thread_id=?, conversation_msg_id=? WHERE report_id=?", (conv_thread_id, conv_thread_id, report_id))
                        await db.commit()
        except Exception as e:
            log.error(f"Failed to auto-create conversation thread for {report_id}: {e}")

    if conv_thread_id:
        try:
            conv_channel = bot.get_channel(conv_thread_id) or await bot.fetch_channel(conv_thread_id)
            mod_msg_content = f"**📤 {interaction.user.mention} ({interaction.user.name}) sent a reply to the reporter for case `{report_id}`:**\n> {message}"
            await conv_channel.send(content=mod_msg_content)
        except discord.HTTPException as e:
            log.error(f"Failed to send mod reply copy to conversation thread: {e}")
    else:
        # Fallback to secure channel if conv thread is missing for some reason
        if secure_channel_cache:
            mod_msg_content = f"**📤 {interaction.user.mention} ({interaction.user.name}) sent a reply to the reporter for case `{report_id}`:**\n> {message}"
            try:
                ref = None
                if orig_msg_id:
                    ref = discord.MessageReference(message_id=orig_msg_id, channel_id=secure_channel_cache.id)
                await secure_channel_cache.send(content=mod_msg_content, reference=ref)
            except discord.HTTPException as e:
                log.error(f"Failed to send mod reply copy to secure channel: {e}")

    await log_audit_action(report_id, interaction.user.id, "reporter_contacted")
    await interaction.followup.send("Your message has been sent to them safely.", ephemeral=True)

@bot.tree.command(name="resources", description="Get confidential support resources for trauma, abuse, and image removal.")
async def resources(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support Resources",
        description="If you or someone you know is in danger or needs support, please reach out to the resources below.",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    for resource in CRISIS_RESOURCES:
        embed.add_field(name=resource['name'], value=resource['value'], inline=False)
    
    embed.set_footer(text="If you are in immediate physical danger, please contact your local emergency services.")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    log.error(f"App command error: {error}")
    try:
        if interaction.response.is_done():
            await interaction.followup.send("An unexpected error occurred.", ephemeral=True)
        else:
            await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)
    except Exception:
        pass 


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return

    # Handle pings in servers
    if message.guild and bot.user.mentioned_in(message) and not message.mention_everyone:
        if message.content.strip() in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]:
            await message.reply("Hi! I am Xabat, I'm here to help you with reporting traumatic experiences. If you would like to report something, kindly use the `/report` commands! If you want helpline resources, use `/resources`. Thanks!", mention_author=False)
            return

    if isinstance(message.channel, discord.DMChannel):
        if message.reference and message.reference.message_id:
            async with aiosqlite.connect("reports.db") as db:
                async with db.execute("SELECT report_id FROM dm_replies WHERE message_id=?", (message.reference.message_id,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        r_id = row[0]
                        async with db.execute("SELECT status, is_anonymous, msg_id, conversation_thread_id FROM reports WHERE report_id=?", (r_id,)) as cur2:
                            r2 = await cur2.fetchone()
                            if r2:
                                status, is_anon, orig_msg_id, conv_thread_id = r2
                                
                                if status in ["Resolved", "False Report"]:
                                    await message.channel.send("This case is now closed. If you need further help, please submit a new report or use /resources.")
                                    return
                                
                                display_name = "Anonymous" if is_anon else message.author.name
                                content = f"💬 **Reply from {display_name} ({r_id})**:\n{message.content}"
                                
                                # Auto-create conversation thread if it's missing
                                global conversation_forum_channel_cache
                                if not conversation_forum_channel_cache and CONVERSATION_FORUM_CHANNEL_ID != 0:
                                    try:
                                        conversation_forum_channel_cache = bot.get_channel(CONVERSATION_FORUM_CHANNEL_ID) or await bot.fetch_channel(CONVERSATION_FORUM_CHANNEL_ID)
                                    except discord.NotFound:
                                        log.error("ERROR: CONVERSATION_FORUM_CHANNEL_ID not found during on_message!")

                                if not conv_thread_id and conversation_forum_channel_cache:
                                    try:
                                        async with aiosqlite.connect("reports.db") as db2:
                                            async with db2.execute("SELECT reported_handle, is_anonymous FROM reports WHERE report_id=?", (r_id,)) as cur3:
                                                r3 = await cur3.fetchone()
                                                if r3:
                                                    reported_handle, is_anon_temp = r3
                                                    conv_thread_name = f"{reported_handle[:80] if reported_handle else 'Unknown'} - {r_id}"
                                                    reporter_info = "Anonymous" if is_anon_temp else f"{message.author.mention} ({message.author.name})"
                                                    init_content = f"Conversations between us and the victim.\n**Victim:** {reporter_info}\n**Report ID:** `{r_id}`"
                                                    
                                                    conv_thread = await conversation_forum_channel_cache.create_thread(name=conv_thread_name, content=init_content)
                                                    if isinstance(conv_thread, tuple):
                                                        conv_thread = conv_thread[0]
                                                    conv_thread_id = conv_thread.id
                                                    
                                                    await db2.execute("UPDATE reports SET conversation_thread_id=?, conversation_msg_id=? WHERE report_id=?", (conv_thread_id, conv_thread_id, r_id))
                                                    await db2.commit()
                                    except Exception as e:
                                        log.error(f"Failed to auto-create conversation thread for {r_id}: {e}")

                                if conv_thread_id:
                                    try:
                                        conv_channel = bot.get_channel(conv_thread_id) or await bot.fetch_channel(conv_thread_id)
                                        await conv_channel.send(content=content)
                                        try:
                                            await message.add_reaction("✅")
                                        except Exception:
                                            pass
                                        
                                        if message.attachments:
                                            for att in message.attachments[:10]:
                                                ext = os.path.splitext(att.filename)[1].lower()
                                                if ext not in ALLOWED_EXTENSIONS or (att.content_type and not att.content_type.startswith('image/')):
                                                    await message.channel.send(f"I'm sorry, but for safety reasons, we can only accept image files (like .png or .jpg). `{att.filename}` was rejected.")
                                                    continue
                                                if att.size > MAX_FILE_SIZE:
                                                    await message.channel.send(f"I'm sorry, but `{att.filename}` is too large. Please keep images under 10MB.")
                                                    continue
                                                
                                                try:
                                                    image_bytes = await att.read()
                                                    scanning_msg = await message.channel.send("🔍 Scanning image for explicit content...")
                                                    is_explicit = await is_explicit_image(image_bytes)
                                                    try:
                                                        await scanning_msg.delete()
                                                    except Exception:
                                                        pass

                                                    if is_explicit:
                                                        await message.channel.send(
                                                            f"🚫 **UPLOAD BLOCKED**: `{att.filename}` was flagged by our AI as containing explicit nudity.\n\n"
                                                            f"**DISCLAIMER:** Please **DO NOT** upload explicit nudity or CSAM. If you are a victim of exploitation, please contact local authorities or use `/resources`. "
                                                            f"Only upload screenshots of text conversations."
                                                        )
                                                        if r_id:
                                                            await log_audit_action(r_id, message.author.id, "evidence_rejected_explicit_reply")
                                                        continue
                                                    
                                                    file = discord.File(io.BytesIO(image_bytes), filename=att.filename)
                                                    await secure_channel_cache.send(
                                                        content=f"⚠️ **PENDING TRIAGE: {r_id}** (Reply Attachment)\n*Review image. If safe, click Approve. If illegal, click Delete.*",
                                                        file=file,
                                                        view=TriageView()
                                                    )
                                                except (discord.HTTPException, discord.Forbidden, discord.NotFound):
                                                    await message.channel.send(f"I ran into an issue uploading `{att.filename}`. Please try sending it again.")
                                    except discord.HTTPException:
                                        await message.channel.send("I wasn't able to deliver your message to the team right now. Please try again later.")
                                else:
                                    # Fallback to secure channel if conv thread is STILL missing
                                    if secure_channel_cache:
                                        try:
                                            ref = None
                                            if orig_msg_id:
                                                ref = discord.MessageReference(message_id=orig_msg_id, channel_id=secure_channel_cache.id)
                                            await secure_channel_cache.send(content=content, reference=ref)
                                            try:
                                                await message.add_reaction("✅")
                                            except Exception:
                                                pass
                                            
                                            if message.attachments:
                                                for att in message.attachments[:10]:
                                                    ext = os.path.splitext(att.filename)[1].lower()
                                                    if ext not in ALLOWED_EXTENSIONS or (att.content_type and not att.content_type.startswith('image/')):
                                                        await message.channel.send(f"I'm sorry, but for safety reasons, we can only accept image files (like .png or .jpg). `{att.filename}` was rejected.")
                                                        continue
                                                    if att.size > MAX_FILE_SIZE:
                                                        await message.channel.send(f"I'm sorry, but `{att.filename}` is too large. Please keep images under 10MB.")
                                                        continue
                                                    
                                                    try:
                                                        image_bytes = await att.read()
                                                        scanning_msg = await message.channel.send("🔍 Scanning image for explicit content...")
                                                        is_explicit = await is_explicit_image(image_bytes)
                                                        try:
                                                            await scanning_msg.delete()
                                                        except Exception:
                                                            pass

                                                        if is_explicit:
                                                            await message.channel.send(
                                                                f"🚫 **UPLOAD BLOCKED**: `{att.filename}` was flagged by our AI as containing explicit nudity.\n\n"
                                                                f"**DISCLAIMER:** Please **DO NOT** upload explicit nudity or CSAM. If you are a victim of exploitation, please contact local authorities or use `/resources`. "
                                                                f"Only upload screenshots of text conversations."
                                                            )
                                                            if r_id:
                                                                await log_audit_action(r_id, message.author.id, "evidence_rejected_explicit_reply")
                                                            continue
                                                        
                                                        file = discord.File(io.BytesIO(image_bytes), filename=att.filename)
                                                        await secure_channel_cache.send(
                                                            content=f"⚠️ **PENDING TRIAGE: {r_id}**\n*Review image. If safe, click Approve. If illegal, click Delete.*",
                                                            file=file,
                                                            view=TriageView()
                                                        )
                                                    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
                                                        await message.channel.send(f"I ran into an issue uploading `{att.filename}`. Please try sending it again.")
                                        except discord.HTTPException:
                                            await message.channel.send("I wasn't able to deliver your message to the team right now. Please try again later.")
                                return

        session = None
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT report_id, thread_id, msg_id, last_activity, created_timestamp FROM pending_uploads WHERE user_id=?", (message.author.id,)) as cur:
                session = await cur.fetchone()
                
        if session:
            report_id, thread_id, orig_msg_id, last_activity, created_timestamp = session
            
            case_status = None
            async with aiosqlite.connect("reports.db") as db:
                async with db.execute("SELECT status FROM reports WHERE report_id=?", (report_id,)) as cur:
                    row = await cur.fetchone()
                    if row: case_status = row[0]
            
            if case_status in ["Resolved", "False Report"]:
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                    await db.commit()
                await message.channel.send("This case has been closed by the moderation team. You can no longer upload evidence for it. If you need to submit a new report, please use `/report`.")
                return
            
            if time.time() - last_activity > UPLOAD_SESSION_TIMEOUT or time.time() - created_timestamp > UPLOAD_SESSION_HARD_LIMIT:
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                    await db.commit()
                await message.channel.send("Your upload session has expired. If you still need to upload screenshots, please start a new report by using the `/report` command in the server.")
                return
            
            if message.content.lower().strip() in ['done', 'cancel', 'stop']:
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                    await db.commit()
                await message.channel.send("Thank you for providing this information. Your evidence has been passed securely to our team. If we need anything else, we will reach out to you here. Please take care.")
                return

            if message.attachments:
                if not secure_channel_cache:
                    await message.channel.send("I'm having a little trouble connecting to the server right now. Please try again in just a moment.")
                    return

                ev_count = 0
                async with aiosqlite.connect("reports.db") as db:
                    async with db.execute("SELECT evidence_count FROM reports WHERE report_id=?", (report_id,)) as cur:
                        row = await cur.fetchone()
                        if row: ev_count = row[0]

                remaining = MAX_EVIDENCE - ev_count
                if remaining <= 0:
                    await message.channel.send("We've received the maximum amount of evidence for this case. If you have more, please summarize it in text, or let a moderator know.")
                    return

                files_sent = 0
                for att in message.attachments[:remaining]:
                    ext = os.path.splitext(att.filename)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS or (att.content_type and not att.content_type.startswith('image/')):
                        await message.channel.send(f"I'm sorry, but for safety reasons, we can only accept image files (like .png or .jpg). `{att.filename}` was rejected.")
                        continue
                    if att.size > MAX_FILE_SIZE:
                        await message.channel.send(f"I'm sorry, but `{att.filename}` is too large. Please keep images under 10MB.")
                        continue
                    
                    try:
                        image_bytes = await att.read()
                        
                        scanning_msg = await message.channel.send("🔍 Scanning image for explicit content...")
                        
                        is_explicit = await is_explicit_image(image_bytes)
                        
                        try:
                            await scanning_msg.delete()
                        except Exception:
                            pass

                        if is_explicit:
                            await message.channel.send(
                                f"🚫 **UPLOAD BLOCKED**: `{att.filename}` was flagged by our AI as containing explicit nudity.\n\n"
                                f"**DISCLAIMER:** Please **DO NOT** upload explicit nudity or CSAM. If you are a victim of exploitation, please contact local authorities or use `/resources`. "
                                f"Only upload screenshots of text conversations."
                            )
                            continue
                        
                        file = discord.File(io.BytesIO(image_bytes), filename=att.filename)
                        await secure_channel_cache.send(
                            content=f"⚠️ **PENDING TRIAGE: {report_id}**\n*Review image. If safe, click Approve. If illegal, click Delete.*",
                            file=file,
                            view=TriageView()
                        )
                        files_sent += 1
                        await asyncio.sleep(0.5)
                    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
                        await message.channel.send(f"I ran into an issue uploading `{att.filename}`. Please try sending it again.")
                
                if files_sent > 0:
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("UPDATE pending_uploads SET last_activity=? WHERE report_id=?", (time.time(), report_id))
                        await db.commit()
                    
                    word = "image" if files_sent == 1 else "images"
                    await message.channel.send(f"We've received {files_sent} {word} and passed them to our team. You can send more, or type `done` when you're finished.")
                return
            else:
                await message.channel.send("If you have screenshots, please upload them directly here. When you're finished, type `done`.")
                return

        await message.channel.send("If you need to submit a new report, please use the `/report` command in the server. If a moderator has reached out to you, please reply directly to their message so it goes to the right case.")

    await bot.process_commands(message)


@tasks.loop(hours=1)
async def cleanup_db():
    try:
        async with aiosqlite.connect("reports.db") as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            await db.execute("DELETE FROM pending_uploads WHERE last_activity < ? OR created_timestamp < ?", 
                             (time.time() - UPLOAD_SESSION_TIMEOUT, time.time() - UPLOAD_SESSION_HARD_LIMIT))
            
            await db.execute("DELETE FROM rate_limits WHERE last_report < ?", (time.time() - 86400,))
            
            case_threshold = (datetime.now(timezone.utc) - timedelta(days=CLOSED_CASE_RETENTION_DAYS)).isoformat()
            
            async with db.execute("SELECT thread_id, report_id FROM reports WHERE status IN ('Resolved', 'False Report') AND closed IS NOT NULL AND closed < ?", (case_threshold,)) as cur:
                rows = await cur.fetchall()
                for row in rows:
                    t_id, r_id = row
                    if t_id:
                        try:
                            thread = await bot.fetch_channel(t_id)
                            await thread.delete()
                        except discord.NotFound:
                            pass
                        except Exception as e:
                            log.error(f"Failed to delete thread {t_id} for {r_id}: {e}")
                    
                    await db.execute("DELETE FROM evidence WHERE report_id=?", (r_id,))
                    await db.execute("DELETE FROM reports WHERE report_id=?", (r_id,))
            
            audit_threshold = (datetime.now(timezone.utc) - timedelta(days=AUDIT_LOG_RETENTION_DAYS)).isoformat()
            await db.execute("DELETE FROM audit_log WHERE timestamp < ?", (audit_threshold,))
            
            await db.commit()
    except Exception as e:
        log.error(f"Database cleanup error: {e}")

@cleanup_db.before_loop
async def before_cleanup():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    await init_db()
    
    bot.add_view(ModActionView())
    bot.add_view(TriageView())
    bot.add_view(IssueView()) 
    
    global secure_channel_cache, mod_log_channel_cache, issue_channel_cache, forum_channel_cache, conversation_forum_channel_cache, commands_synced
    
    try:
        secure_channel_cache = bot.get_channel(SECURE_CHANNEL_ID) or await bot.fetch_channel(SECURE_CHANNEL_ID)
    except discord.NotFound:
        log.error("ERROR: SECURE_CHANNEL_ID not found!")
        
    try:
        mod_log_channel_cache = bot.get_channel(MOD_LOG_CHANNEL_ID) or await bot.fetch_channel(MOD_LOG_CHANNEL_ID)
    except discord.NotFound:
        log.error("ERROR: MOD_LOG_CHANNEL_ID not found!")
    
    if ISSUE_CHANNEL_ID != 0:
        try:
            issue_channel_cache = bot.get_channel(ISSUE_CHANNEL_ID) or await bot.fetch_channel(ISSUE_CHANNEL_ID)
        except discord.NotFound:
            log.error("ERROR: ISSUE_CHANNEL_ID not found!")
        except discord.Forbidden:
            log.error("ERROR: Bot lacks permissions to view ISSUE_CHANNEL_ID. Check channel permissions.")
        except Exception as e:
            log.error(f"ERROR: Failed to cache ISSUE_CHANNEL_ID: {e}")
            
    if FORUM_CHANNEL_ID != 0:
        try:
            forum_channel_cache = bot.get_channel(FORUM_CHANNEL_ID) or await bot.fetch_channel(FORUM_CHANNEL_ID)
        except discord.NotFound:
            log.error("ERROR: FORUM_CHANNEL_ID not found!")
        except discord.Forbidden:
            log.error("ERROR: Bot lacks permissions to view FORUM_CHANNEL_ID.")

    if CONVERSATION_FORUM_CHANNEL_ID != 0:
        try:
            conversation_forum_channel_cache = bot.get_channel(CONVERSATION_FORUM_CHANNEL_ID) or await bot.fetch_channel(CONVERSATION_FORUM_CHANNEL_ID)
        except discord.NotFound:
            log.error("ERROR: CONVERSATION_FORUM_CHANNEL_ID not found!")
        except discord.Forbidden:
            log.error("ERROR: Bot lacks permissions to view CONVERSATION_FORUM_CHANNEL_ID.")
    
    if not cleanup_db.is_running():
        cleanup_db.start()
    
    if not commands_synced:
        try:
            if GUILD_ID != 0:
                guild = discord.Object(id=GUILD_ID)
                synced = await bot.tree.sync(guild=guild)
                log.info(f"Synced {len(synced)} commands to guild {GUILD_ID}.")
            else:
                synced = await bot.tree.sync()
                log.info(f"Synced {len(synced)} commands globally.")
            commands_synced = True
        except Exception as e:
            log.error(f"Failed to sync commands: {e}")

# --- RENDER HEALTH CHECK KEEP-ALIVE ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Xabat Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
if __name__ == "__main__":
    keep_alive()
    bot.run(BOT_TOKEN)
