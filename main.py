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
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from discord import app_commands
load_dotenv()

# --- NUDENET AI IMPORT ---
try:
    from nudenet import NudeDetector
    nude_detector = NudeDetector()
except ImportError:
    print("WARNING: NudeNet is not installed! Please run 'pip install nudenet'")
    nude_detector = None
except Exception as e:
    print(f"Failed to initialize NudeNet: {e}")
    nude_detector = None

# --- CONFIGURATION ---
def get_env_var(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(f"Environment variable {key} is missing or empty. Bot cannot start.")
    return val

BOT_TOKEN = get_env_var("BOT_TOKEN")
SECURE_CHANNEL_ID = int(get_env_var("SECURE_CHANNEL_ID")) 
MOD_LOG_CHANNEL_ID = int(get_env_var("MOD_LOG_CHANNEL_ID"))
MOD_ROLE_ID = int(get_env_var("MOD_ROLE_ID"))
GUILD_ID = int(os.getenv("GUILD_ID", "0")) 
ISSUE_CHANNEL_ID = int(os.getenv("ISSUE_CHANNEL_ID", "0"))
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", "0"))

# Web-Verified Global Age of Consent Dictionary
CONSENT_LAWS = {
    "afghanistan": 18, "af": 18, "albania": 14, "al": 14, "algeria": 16, "dz": 16, "andorra": 16, "ad": 16,
    "angola": 12, "ao": 12, "antiguaandbarbuda": 16, "antigua": 16, "ag": 16, "argentina": 13, "ar": 13,
    "armenia": 16, "am": 16, "australia": 16, "aus": 16, "oz": 16, "au": 16, "austria": 14, "at": 14,
    "azerbaijan": 16, "az": 16, "bahamas": 16, "bs": 16, "bahrain": 16, "bh": 16, "bangladesh": 18, "bd": 18,
    "barbados": 16, "bb": 16, "belarus": 16, "by": 16, "belgium": 16, "be": 16, "belize": 16, "bz": 16,
    "benin": 16, "bj": 16, "bhutan": 18, "bt": 18, "bolivia": 14, "bo": 14, "bosniaandherzegovina": 14, "bosnia": 14, "bih": 14,
    "botswana": 16, "bw": 16, "brazil": 14, "brasil": 14, "br": 14, "brunei": 16, "bn": 16, "bulgaria": 14, "bg": 14,
    "burkinafaso": 15, "bf": 15, "burundi": 18, "bi": 18, "caboverde": 14, "capeverde": 14, "cv": 14, "cambodia": 15, "kh": 15,
    "cameroon": 16, "cm": 16, "canada": 16, "ca": 16, "centralafricanrepublic": 18, "car": 18, "cf": 18, "chad": 15, "td": 15,
    "chile": 14, "cl": 14, "china": 14, "prc": 14, "peoplerepublicofchina": 14, "cn": 14, "colombia": 14, "co": 14, "comoros": 13, "km": 13,
    "congo": 18, "drcongo": 18, "republicofthecongo": 18, "cg": 18, "drc": 18, "costarica": 15, "cr": 15, "cotedivoire": 15, "ivorycoast": 15, "ci": 15,
    "croatia": 15, "hr": 15, "cuba": 16, "cu": 16, "cyprus": 17, "cy": 17, "czechia": 15, "czechrepublic": 15, "cz": 15, "denmark": 15, "dk": 15,
    "djibouti": 18, "dj": 18, "dominica": 16, "dm": 16, "dominicanrepublic": 18, "dr": 18, "do": 18, "ecuador": 14, "ec": 14, "egypt": 18, "eg": 18,
    "elsalvador": 18, "sv": 18, "equatorialguinea": 18, "gq": 18, "eritrea": 18, "er": 18, "estonia": 14, "ee": 14, "eswatini": 16, "swaziland": 16, "sz": 16,
    "ethiopia": 18, "et": 18, "fiji": 16, "fj": 16, "finland": 16, "fi": 16, "france": 15, "fr": 15, "gabon": 18, "ga": 18, "gambia": 18, "gm": 18,
    "georgia": 16, "ge": 16, "germany": 14, "de": 14, "ghana": 16, "gh": 16, "greece": 15, "gr": 15, "grenada": 16, "gd": 16, "guatemala": 18, "gt": 18,
    "guinea": 15, "gn": 15, "guineabissau": 18, "gw": 18, "guyana": 16, "gy": 16, "haiti": 18, "ht": 18, "honduras": 15, "hn": 15, "hongkong": 16, "hk": 16,
    "hungary": 14, "hu": 14, "iceland": 15, "is": 15, "india": 18, "in": 18, "indonesia": 18, "id": 18, "iran": 13, "ir": 13, "iraq": 18, "iq": 18,
    "ireland": 17, "ie": 17, "israel": 16, "il": 16, "italy": 14, "it": 14, "jamaica": 16, "jm": 16, "japan": 16, "jp": 16, "jordan": 18, "jo": 18,
    "kazakhstan": 16, "kz": 16, "kenya": 18, "ke": 18, "kiribati": 16, "ki": 16, "kuwait": 18, "kw": 18, "kyrgyzstan": 16, "kg": 16, "laos": 15, "la": 15,
    "latvia": 16, "lv": 16, "lebanon": 18, "lb": 18, "lesotho": 16, "ls": 16, "liberia": 16, "lr": 16, "libya": 18, "ly": 18, "liechtenstein": 14, "li": 14,
    "lithuania": 16, "lt": 16, "luxembourg": 16, "lu": 16, "macau": 16, "mo": 16, "madagascar": 14, "mg": 14, "malawi": 16, "mw": 16, "malaysia": 16, "my": 16,
    "maldives": 18, "mv": 18, "mali": 18, "ml": 18, "malta": 18, "mt": 18, "marshallislands": 16, "mh": 16, "mauritania": 18, "mr": 18, "mauritius": 16, "mu": 16,
    "mexico": 18, "mx": 18, "micronesia": 16, "fm": 16, "moldova": 16, "md": 16, "monaco": 15, "mc": 15, "mongolia": 16, "mn": 16, "montenegro": 14, "me": 14,
    "morocco": 18, "ma": 18, "mozambique": 16, "mz": 16, "myanmar": 18, "burma": 18, "mm": 18, "namibia": 16, "na": 16, "nauru": 16, "nr": 16, "nepal": 18, "np": 18,
    "netherlands": 16, "nl": 16, "newzealand": 16, "nz": 16, "nicaragua": 18, "ni": 18, "niger": 13, "ne": 13, "nigeria": 11, "ng": 11, "northkorea": 15, "dprk": 15, "kp": 15,
    "northmacedonia": 14, "macedonia": 14, "mk": 14, "norway": 16, "no": 16, "oman": 18, "om": 18, "pakistan": 18, "pk": 18, "palau": 16, "pw": 16, "palestine": 16, "stateofpalestine": 16, "ps": 16,
    "panama": 18, "pa": 18, "papuanewguinea": 16, "pg": 16, "paraguay": 14, "py": 14, "peru": 14, "pe": 14, "philippines": 16, "ph": 16, "poland": 15, "pl": 15, "portugal": 14, "pt": 14,
    "qatar": 18, "qa": 18, "romania": 16, "ro": 16, "russia": 16, "russianfederation": 16, "ru": 16, "rwanda": 18, "rw": 18, "saintkittsandnevis": 16, "saintkitts": 16, "kn": 16,
    "saintlucia": 16, "lc": 16, "saintvincentandthegrenadines": 16, "saintvincent": 16, "vc": 16, "samoa": 16, "ws": 16, "sanmarino": 14, "sm": 14, "saotomeandprincipe": 16, "saotome": 16, "st": 16,
    "saudiarabia": 18, "saudi": 18, "ksa": 18, "sa": 18, "senegal": 16, "sn": 16, "serbia": 14, "rs": 14, "seychelles": 15, "sc": 15, "sierraleone": 18, "sl": 18, "singapore": 16, "sg": 16,
    "slovakia": 15, "sk": 15, "slovenia": 15, "si": 15, "solomonislands": 16, "sb": 16, "somalia": 18, "so": 18, "southafrica": 16, "za": 16, "southkorea": 16, "korea": 16, "republicofkorea": 16, "kr": 16,
    "southsudan": 18, "ss": 18, "spain": 16, "es": 16, "srilanka": 16, "sri": 16, "lk": 16, "sudan": 18, "sd": 18, "suriname": 16, "sr": 16, "sweden": 15, "se": 15, "switzerland": 16, "ch": 16,
    "syria": 15, "sy": 15, "taiwan": 16, "tw": 16, "tajikistan": 16, "tj": 16, "tanzania": 18, "tz": 18, "thailand": 15, "th": 15, "timorleste": 14, "easttimor": 14, "tl": 14, "togo": 16, "tg": 16,
    "tonga": 16, "to": 16, "trinidadandtobago": 18, "trinidad": 18, "tt": 18, "tunisia": 18, "tn": 18, "turkey": 18, "tr": 18, "turkiye": 18, "turkmenistan": 16, "tm": 16, "tuvalu": 16, "tv": 16,
    "uganda": 18, "ug": 18, "ukraine": 16, "ua": 16, "uae": 18, "unitedarabemirates": 18, "ae": 18, "uk": 16, "unitedkingdom": 16, "britain": 16, "england": 16, "scotland": 16, "wales": 16, "greatbritain": 16, "gb": 16,
    "usa": 18, "us": 18, "unitedstates": 18, "unitedstatesofamerica": 18, "america": 18, "uruguay": 15, "uy": 15, "uzbekistan": 16, "uz": 16, "vanuatu": 16, "vu": 16, "vaticancity": 18, "vatican": 18, "va": 18,
    "venezuela": 16, "ve": 16, "vietnam": 18, "vn": 18, "yemen": 18, "ye": 18, "zambia": 16, "zm": 16, "zimbabwe": 16, "zw": 16
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_EVIDENCE = 25

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

secure_channel_cache = None
mod_log_channel_cache = None
issue_channel_cache = None
forum_channel_cache = None
commands_synced = False

# --- DATABASE SETUP ---
async def init_db():
    async with aiosqlite.connect("reports.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS pending_uploads (
                            user_id INTEGER, report_id TEXT PRIMARY KEY, thread_id INTEGER, 
                            msg_id INTEGER, last_activity REAL, created_timestamp REAL)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS rate_limits (
                            user_id INTEGER PRIMARY KEY, last_report REAL)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS reports (
                            report_id TEXT PRIMARY KEY, status TEXT DEFAULT 'Pending', 
                            created TEXT, closed TEXT, assigned_mod INTEGER, evidence_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS dm_replies (
                            message_id INTEGER PRIMARY KEY, report_id TEXT, user_id INTEGER)""")
        
        try: await db.execute("ALTER TABLE reports ADD COLUMN report_type TEXT")
        except aiosqlite.OperationalError: pass 
        try: await db.execute("ALTER TABLE reports ADD COLUMN reporter_id INTEGER")
        except aiosqlite.OperationalError: pass 
        try: await db.execute("ALTER TABLE reports ADD COLUMN msg_id INTEGER")
        except aiosqlite.OperationalError: pass 
        try: await db.execute("ALTER TABLE reports ADD COLUMN is_anonymous INTEGER DEFAULT 0")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN pedo_name TEXT")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN thread_id INTEGER")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN thread_created_timestamp REAL")
        except aiosqlite.OperationalError: pass
        try: await db.execute("ALTER TABLE reports ADD COLUMN forum_thread_id INTEGER")
        except aiosqlite.OperationalError: pass

        await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pending_user ON pending_uploads(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pending_report ON pending_uploads(report_id)")
            
        await db.commit()

# --- HELPER: PERMISSION CHECK ---
def is_moderator(interaction: discord.Interaction):
    if isinstance(interaction.user, discord.User): return False
    if interaction.user.guild_permissions.administrator: return True
    if MOD_ROLE_ID in [r.id for r in interaction.user.roles]: return True
    return False

# --- HELPER: NUDENET EXPLICIT SCAN ---
async def is_explicit_image(image_bytes: bytes) -> bool:
    if not nude_detector:
        return True # Fail closed. If AI didn't load, block the image.
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
            temp.write(image_bytes)
            temp_path = temp.name
            
        detections = await asyncio.to_thread(nude_detector.detect, temp_path)
        
        explicit_labels = {
            "FEMALE_BREAST_EXPOSED",
            "FEMALE_GENITALIA_EXPOSED",
            "MALE_GENITALIA_EXPOSED",
            "BUTTOCKS_EXPOSED",
            "ANUS_EXPOSED"
        }
        
        for det in detections:
            if det['class'] in explicit_labels:
                return True
                
        return False
    except Exception as e:
        print(f"NudeNet scan error: {e}")
        return True # Fail closed. If AI crashes, block the image.
    finally:
        if temp_path:
            try: os.remove(temp_path)
            except: pass

# --- HELPER: EVIDENCE THREAD CREATION ---
async def create_evidence_thread(report_id: str, pedo_name: str, report_msg: discord.Message):
    thread_name = f"{report_id} - {pedo_name[:40]}" if pedo_name else report_id
    try:
        thread = await report_msg.create_thread(name=thread_name, auto_archive_duration=1440)
        return thread
    except discord.HTTPException as e:
        print(f"Failed to create evidence thread: {e}")
        return None

# --- TRIAGE VIEW (For Images) ---
class TriageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def approve_image(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)

        msg = interaction.message
        match = re.search(r'PR-\d{8}-[A-F0-9]{4}', msg.content)
        if not match:
            return await interaction.followup.send("Could not find Report ID in message.", ephemeral=True)
        report_id = match.group(0)

        ev_count = 0
        thread_id = None
        pedo_name = None
        report_msg_id = None
        
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT evidence_count, thread_id, pedo_name, msg_id FROM reports WHERE report_id=?", (report_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    ev_count, thread_id, pedo_name, report_msg_id = row

        remaining = MAX_EVIDENCE - ev_count
        if remaining <= 0:
            return await interaction.followup.send(f"❌ Cannot approve. Report already reached max evidence ({MAX_EVIDENCE}).", ephemeral=True)

        if not thread_id and report_msg_id:
            try:
                report_msg = await secure_channel_cache.fetch_message(report_msg_id)
                thread = await create_evidence_thread(report_id, pedo_name, report_msg)
                if thread:
                    thread_id = thread.id
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("UPDATE reports SET thread_id=?, thread_created_timestamp=? WHERE report_id=?", (thread_id, time.time(), report_id))
                        await db.commit()
            except discord.HTTPException as e:
                print(f"Failed to create thread: {e}")

        if not thread_id:
            return await interaction.followup.send("Failed to find or create evidence thread.", ephemeral=True)

        try:
            thread = bot.get_channel(thread_id) or await bot.fetch_channel(thread_id)
        except (discord.NotFound, discord.Forbidden):
            return await interaction.followup.send("Failed to find evidence thread.", ephemeral=True)

        attachments_to_process = msg.attachments[:remaining]
        success_count = 0
        
        for att in attachments_to_process:
            try:
                file = await att.to_file()
                await thread.send(content=f"📸 **Approved Evidence for {report_id}**", file=file)
                success_count += 1
            except discord.HTTPException:
                pass 

        if success_count == 0:
            return await interaction.followup.send("Failed to forward files to the thread. The triage message was kept.", ephemeral=True)

        try:
            await msg.delete()
        except Exception as e:
            print(f"Failed to delete triage message instantly: {e}")
        
        if success_count > 0:
            async with aiosqlite.connect("reports.db") as db:
                await db.execute("UPDATE reports SET evidence_count = evidence_count + ? WHERE report_id=?", (success_count, report_id))
                await db.commit()

        await interaction.followup.send(f"Approved {success_count} image(s). Moved to case thread.", ephemeral=True)

    async def reject_image(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            return await interaction.response.send_message("You do not have permission.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"Error deleting triage image: {e}")
            
        await interaction.followup.send("Image nuked from #pedo-proof and blocked from logs.", ephemeral=True)

    @discord.ui.button(label="✅ Approve & Move", style=discord.ButtonStyle.success, custom_id="triage_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.approve_image(interaction)

    @discord.ui.button(label="❌ Delete (Illegal/Nuke)", style=discord.ButtonStyle.danger, custom_id="triage_delete")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.reject_image(interaction)

# --- PERSISTENT MOD VIEW (For Report Status) ---
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

        thread_id = None
        pedo_name = None
        msg_id = None
        forum_thread_id = None
        
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT status, thread_id, pedo_name, msg_id, forum_thread_id FROM reports WHERE report_id=?", (report_id,)) as cur:
                row = await cur.fetchone()
                if row and row[0] in ["Resolved", "False Report"]:
                    return await interaction.followup.send("This case is already closed and cannot be modified.", ephemeral=True)
                if row: 
                    thread_id = row[1]
                    pedo_name = row[2]
                    msg_id = row[3]
                    forum_thread_id = row[4]

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
                thread = await create_evidence_thread(report_id, pedo_name, interaction.message)
                if thread:
                    thread_id = thread.id
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("UPDATE reports SET thread_id=?, thread_created_timestamp=? WHERE report_id=?", (thread_id, time.time(), report_id))
                        await db.commit()
                    await thread.send("🔍 This case is now under review. Evidence will be posted here.")
            except Exception as e:
                print(f"Failed to auto-create evidence thread: {e}")

        try:
            await interaction.message.edit(embed=embed, view=view_to_send)
        except: pass

        thread_name = pedo_name[:90] if pedo_name else report_id
        
        if not forum_thread_id and forum_channel_cache:
            try:
                forum_thread_obj = await forum_channel_cache.create_thread(name=thread_name, embed=embed)
                if isinstance(forum_thread_obj, discord.Thread):
                    forum_thread = forum_thread_obj
                elif hasattr(forum_thread_obj, 'thread'):
                    forum_thread = forum_thread_obj.thread
                else:
                    forum_thread = forum_thread_obj[0]
                
                forum_thread_id = forum_thread.id
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("UPDATE reports SET forum_thread_id=? WHERE report_id=?", (forum_thread_id, report_id))
                    await db.commit()
            except Exception as e:
                print(f"Failed to create forum post: {e}")
        elif forum_thread_id:
            try:
                forum_thread = await bot.fetch_channel(forum_thread_id)
                forum_msg = await forum_thread.fetch_message(forum_thread_id)
                await forum_msg.edit(embed=embed)
            except Exception as e:
                print(f"Failed to update forum post: {e}")

        if is_closed and thread_id:
            try:
                thread = await bot.fetch_channel(thread_id)
                await thread.send("🔒 This case has been closed. The thread is now locked.")
                await thread.edit(archived=True, locked=True)
            except discord.HTTPException:
                pass
                
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

# --- ANONYMITY BUTTONS ---
class AnonView(discord.ui.View):
    def __init__(self, report_type: str):
        super().__init__(timeout=300)
        self.report_type = report_type
        self.message = None

    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(view=self)
            except: pass

    @discord.ui.button(label="Stay Anonymous", style=discord.ButtonStyle.green)
    async def anon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(is_anonymous=True, report_type=self.report_type))

    @discord.ui.button(label="Share My Discord Name", style=discord.ButtonStyle.blurple)
    async def name_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(is_anonymous=False, report_type=self.report_type))

# --- REPORT FORM (MODAL) ---
class ReportModal(discord.ui.Modal, title='Predator Report Form'):
    def __init__(self, is_anonymous: bool, report_type: str):
        super().__init__()
        self.is_anonymous = is_anonymous
        self.report_type = report_type

    online_name = discord.ui.TextInput(label="Predator's Online Name/Handle", placeholder="Discord username, display name, or tag", required=True, max_length=100)
    age_pedo = discord.ui.TextInput(label="Predator's Age", placeholder="Numbers only (e.g., 24)", required=True, max_length=3)
    age_victim = discord.ui.TextInput(label="Victim's Age", placeholder="Numbers only (e.g., 15)", required=True, max_length=3)
    country = discord.ui.TextInput(label="Country/Jurisdiction", placeholder="e.g., USA, UK, Malaysia", required=True, max_length=50)
    details = discord.ui.TextInput(label="Full Details of Incident", style=discord.TextStyle.paragraph, placeholder="Explain everything. If you know the predator's real name, put it here.", required=True, max_length=2000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT last_report FROM rate_limits WHERE user_id=?", (interaction.user.id,)) as cur:
                row = await cur.fetchone()
                if row and (time.time() - row[0]) < 300:
                    return await interaction.followup.send("We hear you, and we want to help. To protect our system, please wait about 5 minutes before submitting another report.", ephemeral=True)
            await db.execute("""INSERT INTO rate_limits (user_id, last_report) VALUES (?, ?) 
                                ON CONFLICT(user_id) DO UPDATE SET last_report = excluded.last_report""", 
                             (interaction.user.id, time.time()))
            await db.commit()

        try:
            pedo_age_str = self.age_pedo.value.strip()
            victim_age_str = self.age_victim.value.strip()
            if not pedo_age_str.isdigit() or not victim_age_str.isdigit(): raise ValueError
            pedo_age = int(pedo_age_str)
            victim_age = int(victim_age_str)
            if not (1 <= pedo_age <= 120) or not (1 <= victim_age <= 120): raise ValueError
        except ValueError:
            return await interaction.followup.send("It looks like there was a small typo in the age fields. Please try again and use numbers only (like 16 or 24).", ephemeral=True)

        country_raw = re.sub(r'[^a-zA-Z0-9]', '', self.country.value).lower()
        country_str = self.country.value.strip()
        
        legal_age = CONSENT_LAWS.get(country_raw)
        if not legal_age:
            sorted_keys = sorted(CONSENT_LAWS.keys(), key=len, reverse=True)
            for key in sorted_keys:
                if key in country_raw:
                    legal_age = CONSENT_LAWS[key]
                    break

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

        embed.add_field(name="Online Name", value=self.online_name.value, inline=True)
        embed.add_field(name="Predator Age", value=str(pedo_age), inline=True)
        embed.add_field(name="Victim Age", value=str(victim_age), inline=True)
        embed.add_field(name="Jurisdiction", value=country_str, inline=True)

        false_report_flag = False
        if pedo_age < 10 or victim_age < 5:
            false_report_flag = True
            embed.add_field(name="🚨 POTENTIAL FALSE REPORT 🚨", value="System flagged this due to impossible or unrealistic ages. Review carefully.", inline=False)

        # Fix 2: Explicitly state if it's illegal/statutory rape
        if not false_report_flag and legal_age is not None and victim_age < legal_age:
            embed.add_field(name="⚠️ STATUTORY / AGE OF CONSENT FLAG ⚠️", value=f"**Potential Illegal Activity:** Victim's age ({victim_age}) is below the general age of consent ({legal_age}) in {country_str}. This may constitute statutory rape or illegal sexual activity depending on local laws. Please verify specific regional exceptions.", inline=False)

        global secure_channel_cache
        if not secure_channel_cache:
            secure_channel_cache = bot.get_channel(SECURE_CHANNEL_ID) or await bot.fetch_channel(SECURE_CHANNEL_ID)

        async with aiosqlite.connect("reports.db") as db:
            try:
                await db.execute("INSERT INTO reports (report_id, report_type, reporter_id, status, created, evidence_count, is_anonymous, pedo_name) VALUES (?, ?, ?, 'Pending', ?, 0, ?, ?)", 
                                 (report_id, self.report_type, interaction.user.id, datetime.now(timezone.utc).isoformat(), 1 if self.is_anonymous else 0, self.online_name.value))
                await db.commit()
            except Exception as e:
                print(f"DB Insert failed: {e}")
                return await interaction.followup.send("I'm sorry, we ran into a technical issue saving your report. Please try again in a moment.", ephemeral=True)

        try:
            report_msg = await secure_channel_cache.send(embed=embed, view=ModActionView())
        except discord.HTTPException as e:
            print(f"Failed to send to secure channel: {e}")
            async with aiosqlite.connect("reports.db") as db:
                await db.execute("DELETE FROM reports WHERE report_id=?", (report_id,))
                await db.commit()
            return await interaction.followup.send("I'm sorry, we ran into a technical issue submitting this to the team. Please try again later.", ephemeral=True)

        async with aiosqlite.connect("reports.db") as db:
            await db.execute("UPDATE reports SET msg_id=? WHERE report_id=?", (report_msg.id, report_id))
            await db.execute("INSERT OR REPLACE INTO pending_uploads (user_id, report_id, thread_id, msg_id, last_activity, created_timestamp) VALUES (?, ?, NULL, ?, ?, ?)",
                             (interaction.user.id, report_id, report_msg.id, time.time(), time.time()))
            await db.commit()

        await interaction.followup.send("Thank you for your courage in speaking up. We believe you, and your report has been safely received.\n\n**Please check your Direct Messages (DMs) from me** to upload any screenshots you have.", ephemeral=True)

        try:
            await interaction.user.send(
                f"Hi there. We received your report (**{report_id}**). We believe you, and our team is reviewing your message now.\n\n"
                f"If you have screenshots of the conversations, you can upload them directly here in our DMs. Take your time. When you're finished, just type `done`. You are safe here.\n\n"
                f"⚠️ **IMPORTANT DISCLAIMER REGARDING EVIDENCE:**\n"
                f"Please **DO NOT** upload explicit nudity or Child Sexual Abuse Material (CSAM). Our system automatically scans for and blocks explicit images to protect our team and comply with the law.\n"
                f"If your chat logs contain explicit images or CSAM, **please crop them out or redact them** so that only the text of the conversation is visible. We only need to see the text to verify the report."
            )
        except discord.Forbidden:
            pass

# --- ISSUE SYSTEM VIEWS & MODALS ---
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

# --- SLASH COMMANDS ---
class ReportGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="report", description="Report an incident to the moderation team")

    async def _send_view(self, interaction: discord.Interaction, report_type: str):
        view = AnonView(report_type=report_type)
        await interaction.response.send_message(f"We are so sorry you are going through this. You selected **{report_type}**. Please choose how you would like to submit your report to our team:", view=view, ephemeral=True)
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
        
        if not issue_channel_cache:
            return await interaction.followup.send("I couldn't find the issue reporting channel. Please contact an admin.", ephemeral=True)
        
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
            print(f"Failed to submit issue: {e}")
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
        async with db.execute("SELECT reporter_id, status FROM reports WHERE report_id=?", (report_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return await interaction.followup.send("Report ID not found.", ephemeral=True)
            reporter_id, status = row

    if status in ["Resolved", "False Report"]:
        return await interaction.followup.send("This case is closed. You cannot reply to it.", ephemeral=True)

    try:
        reporter = bot.get_user(reporter_id) or await bot.fetch_user(reporter_id)
    except (discord.NotFound, discord.HTTPException):
        return await interaction.followup.send("Could not find the user. They may have deleted their account.", ephemeral=True)

    if not reporter:
        return await interaction.followup.send("Could not find the user.", ephemeral=True)

    try:
        sent_msg = await reporter.send(f"**A message from our Moderation Team regarding your report `{report_id}`:**\n\n{message}\n\n*(Reply to this message to respond to the moderation team)*")
        async with aiosqlite.connect("reports.db") as db:
            await db.execute("INSERT INTO dm_replies (message_id, report_id, user_id) VALUES (?, ?, ?)", 
                             (sent_msg.id, report_id, reporter_id))
            await db.commit()
        await interaction.followup.send("Your message has been sent to them safely.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I couldn't reach them. It looks like they have their DMs closed.", ephemeral=True)

@bot.tree.command(name="resources", description="Get confidential support resources for trauma, abuse, and image removal.")
async def resources(interaction: discord.Interaction):
    embed = discord.Embed(
        title="You Are Not Alone",
        description="If you or someone you know is in danger or needs support, please reach out to the resources below. There are people who care and want to help you through this.",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="🆘 Immediate Crisis Support (US/Canada)", value="**Crisis Text Line:** Text HOME to `741741`\n**Childhelp National Child Abuse:** Call/Text `1-800-422-4453`\n**988 Suicide & Crisis Lifeline:** Call or Text `988`", inline=False)
    embed.add_field(name="🛑 Sexual Abuse & Exploitation (US)", value="**RAINN (Rape/Abuse/Incest):** `1-800-656-HOPE` | [rainn.org](https://www.rainn.org)\n**NCMEC CyberTipline:** [report.cybertipline.org](https://report.cybertipline.org)", inline=False)
    embed.add_field(name="🇬🇧 United Kingdom", value="**Childline:** `0800 1111` | [childline.org.uk](https://www.childline.org.uk)\n**NSPCC:** `0808 800 5000` | [nspcc.org.uk](https://www.nspcc.org.uk)\n**Rape Crisis:** `0808 802 9999` | [rapecrisis.org.uk](https://rapecrisis.org.uk)", inline=False)
    embed.add_field(name="🇨🇦 Canada", value="**Kids Help Phone:** `1-800-668-6868` | [kidshelpphone.ca](https://kidshelpphone.ca)\n**Canadian Centre for Child Protection:** [protectchildren.ca](https://www.protectchildren.ca)", inline=False)
    embed.add_field(name="🇦🇺 Australia", value="**Kids Helpline:** `1800 55 1800` | [kidshelpline.com.au](https://www.kidshelpline.com.au)\n**Bravehearts:** `1800 272 831` | [bravehearts.org.au](https://bravehearts.org.au)", inline=False)
    embed.add_field(name="🇮🇳 India", value="**Childline India:** `1098` | [childlineindia.org.in](https://www.childlineindia.org.in)\n**Vandrevala Foundation:** `9999 666 555`", inline=False)
    embed.add_field(name="🌍 International Support", value="**Befrienders Worldwide:** [befrienders.org](https://www.befrienders.org)\n**Find A Helpline:** [findahelpline.com](https://findahelpline.com)\n**International Association for Suicide Prevention:** [iasp.info](https://www.iasp.info)", inline=False)
    embed.add_field(name="📸 Removing Explicit Images (Under 18 & Adults)", value="**Take It Down (NCMEC - Under 18):** [takendown.org](https://takendown.org)\n**StopNCII (Adults 18+):** [stopncii.org](https://stopncii.org)", inline=False)
    embed.add_field(name="💻 Sextortion / Online Blackmail", value="**FBI Internet Crime Complaint Center:** [ic3.gov](https://www.ic3.gov)\n**Stop Sextortion (NCMEC):** [stopsextortion.com](https://www.stopsextortion.com)", inline=False)
    embed.set_footer(text="If you are in immediate physical danger, please contact your local emergency services (e.g., 911, 999, 112).")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- GLOBAL SLASH COMMAND ERROR HANDLER ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"An error occurred: `{error}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: `{error}`", ephemeral=True)
    except Exception:
        pass 

# --- DM ATTACHMENT & REPLY HANDLER ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return

    # Handle pings in servers
    if message.guild and bot.user.mentioned_in(message) and not message.mention_everyone:
        if message.content.strip() in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]:
            await message.reply("Hi! I am Xabat, I'm here to help you with any traumatic experiences such as rape, grooming, etc. If you would like to report something, kindly use the `/report` commands!! If you want helpline resources, use /resources. Thanks!", mention_author=False)
            return

    if isinstance(message.channel, discord.DMChannel):
        # Check for DM reply FIRST to prevent upload session hijacking
        if message.reference and message.reference.message_id:
            async with aiosqlite.connect("reports.db") as db:
                async with db.execute("SELECT report_id FROM dm_replies WHERE message_id=?", (message.reference.message_id,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        r_id = row[0]
                        async with db.execute("SELECT status, is_anonymous, msg_id FROM reports WHERE report_id=?", (r_id,)) as cur2:
                            r2 = await cur2.fetchone()
                            if r2:
                                status, is_anon, orig_msg_id = r2
                                
                                if status in ["Resolved", "False Report"]:
                                    await message.channel.send("This case is now closed. If you need further help, please submit a new report or use /resources.")
                                    return
                                
                                display_name = "Anonymous" if is_anon else message.author.name
                                content = f"💬 **Reply from {display_name} ({r_id})**:\n{message.content}"
                                
                                files = []
                                for att in message.attachments[:10]:
                                    try:
                                        files.append(await att.to_file())
                                    except:
                                        pass
                                
                                if secure_channel_cache:
                                    try:
                                        await secure_channel_cache.send(content=content, files=files, reference=discord.MessageReference(message_id=orig_msg_id, channel_id=secure_channel_cache.id))
                                        try:
                                            await message.add_reaction("✅")
                                        except:
                                            pass
                                    except:
                                        await message.channel.send("I wasn't able to deliver your message to the team right now. Please try again later.")
                                return

        # 2. Check for active upload session
        session = None
        async with aiosqlite.connect("reports.db") as db:
            async with db.execute("SELECT report_id, thread_id, msg_id, last_activity, created_timestamp FROM pending_uploads WHERE user_id=? ORDER BY last_activity DESC LIMIT 1", (message.author.id,)) as cur:
                session = await cur.fetchone()
                
        if session:
            report_id, thread_id, orig_msg_id, last_activity, created_timestamp = session
            
            # FIX 1: Check if the case has been closed by a mod!
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
            
            if time.time() - last_activity > 600 or time.time() - created_timestamp > 3600:
                async with aiosqlite.connect("reports.db") as db:
                    await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                    await db.commit()
                await message.channel.send("It's been a while since we last spoke. If you still need to upload screenshots, please start a new report by using the `/report` command in the server. Take care.")
                return
            else:
                if message.content.lower().strip() in ['done', 'cancel', 'stop']:
                    async with aiosqlite.connect("reports.db") as db:
                        await db.execute("DELETE FROM pending_uploads WHERE report_id=?", (report_id,))
                        await db.commit()
                    await message.channel.send("Thank you for trusting us with this. Your evidence has been passed to our team. If we need anything else, we will reach out to you here. Please take care of yourself.")
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
                        await message.channel.send("We've received a lot of evidence for this case already. If you have more, please summarize it in text, or let a moderator know.")
                        return

                    files_sent = 0
                    for att in message.attachments[:remaining]:
                        ext = os.path.splitext(att.filename)[1].lower()
                        if ext not in ALLOWED_EXTENSIONS or (att.content_type and not att.content_type.startswith('image/')):
                            await message.channel.send(f"I'm sorry, but for safety reasons, we can only accept image files (like .png or .jpg). `{att.filename}` was rejected.")
                        elif att.size > MAX_FILE_SIZE:
                            await message.channel.send(f"I'm sorry, but `{att.filename}` is too large. Please keep images under 10MB.")
                        else:
                            try:
                                image_bytes = await att.read()
                                
                                scanning_msg = await message.channel.send("🔍 Scanning image for explicit content...")
                                
                                is_explicit = await is_explicit_image(image_bytes)
                                
                                try:
                                    await scanning_msg.delete()
                                except:
                                    pass

                                if is_explicit:
                                    await message.channel.send(
                                        f"🚫 **UPLOAD BLOCKED**: `{att.filename}` was flagged by our AI as containing explicit nudity.\n\n"
                                        f"**DISCLAIMER:** Please **DO NOT** upload CSAM or explicit nudity. If you are a victim of exploitation, please contact local authorities or use `/resources`. "
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
                        await message.channel.send(f"Thank you. We've safely received {files_sent} {word} and passed them to our team. You can send more, or type `done` when you're finished.")
                    return
                else:
                    await message.channel.send("If you have screenshots, please upload them directly here. When you're finished, type `done`.")
                    return

        await message.channel.send("Thank you for reaching out. If you need to submit a new report, please use the `/report` command in the server. If a moderator has reached out to you, please reply directly to their message so it goes to the right case.")

    await bot.process_commands(message)

# --- BACKGROUND CLEANUP TASK ---
@tasks.loop(hours=1)
async def cleanup_db():
    try:
        async with aiosqlite.connect("reports.db") as db:
            await db.execute("DELETE FROM pending_uploads WHERE last_activity < ? OR created_timestamp < ?", (time.time() - 600, time.time() - 3600))
            await db.execute("DELETE FROM rate_limits WHERE last_report < ?", (time.time() - 86400,))
            
            four_months_ago = time.time() - (120 * 86400)
            async with db.execute("SELECT thread_id, report_id FROM reports WHERE thread_created_timestamp IS NOT NULL AND thread_created_timestamp < ?", (four_months_ago,)) as cur:
                rows = await cur.fetchall()
                for row in rows:
                    t_id, r_id = row
                    if t_id:
                        try:
                            thread = await bot.fetch_channel(t_id)
                            await thread.delete()
                            await db.execute("UPDATE reports SET thread_id=NULL, thread_created_timestamp=NULL WHERE report_id=?", (r_id,))
                        except discord.NotFound:
                            await db.execute("UPDATE reports SET thread_id=NULL, thread_created_timestamp=NULL WHERE report_id=?", (r_id,))
                        except Exception as e:
                            print(f"Failed to delete thread {t_id}: {e}")
            
            threshold = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
            await db.execute("DELETE FROM reports WHERE status IN ('Resolved', 'False Report') AND closed IS NOT NULL AND closed < ?", (threshold,))
            await db.commit()
    except Exception as e:
        print(f"Database cleanup error: {e}")

@cleanup_db.before_loop
async def before_cleanup():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    await init_db()
    bot.add_view(ModActionView())
    bot.add_view(TriageView())
    bot.add_view(IssueView()) 
    
    global secure_channel_cache, mod_log_channel_cache, issue_channel_cache, forum_channel_cache, commands_synced
    
    try:
        secure_channel_cache = bot.get_channel(SECURE_CHANNEL_ID) or await bot.fetch_channel(SECURE_CHANNEL_ID)
    except discord.NotFound:
        print("ERROR: SECURE_CHANNEL_ID not found!")
        
    try:
        mod_log_channel_cache = bot.get_channel(MOD_LOG_CHANNEL_ID) or await bot.fetch_channel(MOD_LOG_CHANNEL_ID)
    except discord.NotFound:
        print("ERROR: MOD_LOG_CHANNEL_ID not found!")
    
    if ISSUE_CHANNEL_ID != 0:
        try:
            issue_channel_cache = bot.get_channel(ISSUE_CHANNEL_ID) or await bot.fetch_channel(ISSUE_CHANNEL_ID)
        except discord.NotFound:
            print("ERROR: ISSUE_CHANNEL_ID not found!")
            
    if FORUM_CHANNEL_ID != 0:
        try:
            forum_channel_cache = bot.get_channel(FORUM_CHANNEL_ID) or await bot.fetch_channel(FORUM_CHANNEL_ID)
        except discord.NotFound:
            print("ERROR: FORUM_CHANNEL_ID not found!")
    
    if not cleanup_db.is_running():
        cleanup_db.start()
    
    if not commands_synced:
        try:
            if GUILD_ID != 0:
                guild = discord.Object(id=GUILD_ID)
                synced = await bot.tree.sync(guild=guild)
                print(f"Synced {len(synced)} commands to guild {GUILD_ID}.")
            else:
                synced = await bot.tree.sync()
                print(f"Synced {len(synced)} commands globally.")
            commands_synced = True
        except Exception as e:
            print(e)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
