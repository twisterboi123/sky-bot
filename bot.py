import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

# Load environment variables (prefer existing environment vars over .env)
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Simple in-memory storage for welcome/leave channels per guild
# Format: {guild_id: {"welcome_channel": channel_id, "leave_channel": channel_id}}
guild_settings = {}

# In-memory storage for autorole and verification config
# Format: {guild_id: {"autorole": role_id, "verification": {"channel_id": ..., "message_id": ..., "role_id": ...}}}
autorole_settings = {}

# In-memory storage for announcement channel per guild
# Format: {guild_id: channel_id}
announcement_channels = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    # Set presence to Online with a friendly activity
    try:
        activity = discord.Activity(type=discord.ActivityType.watching, name="for /raiz • /diag | Support: discord.gg/DZEkJ29dZ3")
        await bot.change_presence(status=discord.Status.online, activity=activity)
    except Exception as e:
        print(f'Failed to set presence: {e}')
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Slash command: RAIZ
@bot.tree.command(name="raiz", description="Spam your message like a broken record 🔁")
@app_commands.describe(
    message="Your message (choose wisely)",
    times="How many times? (1-10, don't go crazy)",
    public="Make everyone see it (or keep it secret)"
)
async def raiz(interaction: discord.Interaction, message: str, times: int, public: bool=True):
    # Validate the times parameter (respond quickly for invalid input)
    if times < 1 or times > 10:
        try:
            await interaction.response.send_message("❌ Please choose a number between 1 and 10!", ephemeral=True)
        except Exception as e:
            print(f"[raiz] Failed to send validation error: {e}")
        return

    if not public:
        # Private (no extra perms required): single ephemeral block
        repeated = ("\n").join([message] * times)
        if len(repeated) > 1900:
            repeated = repeated[:1900] + "…"
        try:
            await interaction.response.send_message(repeated, ephemeral=True)
            print(f"[raiz] Ephemeral only; sent preview for {times}")
        except Exception as e:
            print(f"[raiz] Failed to send ephemeral: {e}")
        return

    # Public flow (optional). Uses interaction follow-ups so only
    # Use External Apps + Application Commands are needed (no Send Messages).
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
    except Exception as e:
        print(f"[raiz] Failed to defer interaction: {e}")
        return

    sent = 0
    chunks = 0
    max_chunks = 5  # Discord limits follow-ups per interaction
    allowed_mentions = discord.AllowedMentions.none()
    send_failed = None
    try:
        while sent < times and chunks < max_chunks:
            remaining = times - sent
            slots_left = max_chunks - chunks
            per_chunk = (remaining + slots_left - 1) // slots_left
            block = ("\n").join([message] * per_chunk)
            if len(block) > 1900:
                # Trim to avoid 2000 char limit
                max_lines = max(1, 1900 // max(1, len(message) + 1))
                block = ("\n").join([message] * max_lines)
            try:
                await interaction.followup.send(block, wait=True, allowed_mentions=allowed_mentions)
                sent += block.count("\n") + 1
                chunks += 1
            except Exception as e:
                send_failed = e
                break
    except Exception as e:
        send_failed = e

    print(f"[raiz] Requested {times}, actually sent {min(sent, times)} in {chunks} chunk(s)")
    try:
        if sent >= times:
            await interaction.edit_original_response(content=f"✅ Sent {times}/{times} message(s) to the channel.")
        elif sent > 0:
            await interaction.edit_original_response(content=f"⚠️ Sent {sent}/{times}. Hit follow-up limit; try fewer repeats.")
        else:
            preview = ("\n").join([message] * min(times, 10))
            if len(preview) > 1900:
                preview = preview[:1900] + "…"
            reason = "I couldn't post publicly here."
            if isinstance(send_failed, discord.Forbidden):
                reason = "I'm missing permission to post app messages here."
            elif isinstance(send_failed, discord.HTTPException) and getattr(send_failed, 'status', None) == 403:
                reason = "Public app messages are blocked in this channel."
            await interaction.edit_original_response(content=(
                f"❌ {reason}\n"
                "Ask a mod to enable 'Use External Apps' for this channel, or grant the bot 'Send Messages'.\n\n" + preview
            ))
    except Exception as e:
        print(f"[raiz] Failed to edit original response: {e}")

# Slash command: RAIZ V2 (big text with spacing)
@bot.tree.command(name="raizv2", description="Spam but BIGGER and LOUDER 📢")
@app_commands.describe(
    message="Your message (in CAPS energy)",
    times="How many times? (1-10, scream responsibly)",
    public="Make it rain big text (or whisper privately)"
)
async def raizv2(interaction: discord.Interaction, message: str, times: int, public: bool=True):
    # Validate the times parameter
    if times < 1 or times > 10:
        try:
            await interaction.response.send_message("❌ Please choose a number between 1 and 10!", ephemeral=True)
        except Exception as e:
            print(f"[raizv2] Failed to send validation error: {e}")
        return

    # Format message with # for big text - single line breaks
    formatted_msg = f"# {message}"
    
    if not public:
        # Private preview
        repeated = ("\n").join([formatted_msg] * times)
        if len(repeated) > 1900:
            repeated = repeated[:1900] + "…"
        try:
            await interaction.response.send_message(repeated, ephemeral=True)
            print(f"[raizv2] Ephemeral only; sent preview for {times}")
        except Exception as e:
            print(f"[raizv2] Failed to send ephemeral: {e}")
        return

    # Public flow
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
    except Exception as e:
        print(f"[raizv2] Failed to defer interaction: {e}")
        return

    sent = 0
    chunks = 0
    max_chunks = 5
    allowed_mentions = discord.AllowedMentions.none()
    send_failed = None
    
    try:
        while sent < times and chunks < max_chunks:
            remaining = times - sent
            slots_left = max_chunks - chunks
            per_chunk = (remaining + slots_left - 1) // slots_left
            block = ("\n").join([formatted_msg] * per_chunk)
            if len(block) > 1900:
                # Trim to avoid 2000 char limit
                max_lines = max(1, 1900 // max(1, len(formatted_msg) + 1))
                block = ("\n").join([formatted_msg] * max_lines)
            try:
                await interaction.followup.send(block, wait=True, allowed_mentions=allowed_mentions)
                sent += block.count("\n") + 1
                chunks += 1
            except Exception as e:
                send_failed = e
                break
    except Exception as e:
        send_failed = e

    print(f"[raizv2] Requested {times}, actually sent {min(sent, times)} in {chunks} chunk(s)")
    try:
        if sent >= times:
            await interaction.edit_original_response(content=f"✅ Sent {times}/{times} big message(s) to the channel.")
        elif sent > 0:
            await interaction.edit_original_response(content=f"⚠️ Sent {sent}/{times}. Hit follow-up limit; try fewer repeats.")
        else:
            preview = ("\n").join([formatted_msg] * min(times, 5))
            if len(preview) > 1900:
                preview = preview[:1900] + "…"
            reason = "I couldn't post publicly here."
            if isinstance(send_failed, discord.Forbidden):
                reason = "I'm missing permission to post app messages here."
            elif isinstance(send_failed, discord.HTTPException) and getattr(send_failed, 'status', None) == 403:
                reason = "Public app messages are blocked in this channel."
            await interaction.edit_original_response(content=(
                f"❌ {reason}\n"
                "Ask a mod to enable 'Use External Apps' for this channel, or grant the bot 'Send Messages'.\n\n" + preview
            ))
    except Exception as e:
        print(f"[raizv2] Failed to edit original response: {e}")

# Slash command: Femboy Meter
@bot.tree.command(name="femboymeter", description="Scientifically calculate someone's femboy levels 🎀")
@app_commands.describe(user="The victim... I mean subject")
async def femboymeter(interaction: discord.Interaction, user: discord.Member):
    import random
    
    # Generate a random percentage between 1-100
    percentage = random.randint(1, 100)
    
    # Determine the message based on percentage
    if percentage > 50:
        result_msg = f"🎀 {user.mention} is **{percentage}%** femboy! They are a femboy! 💖"
    else:
        result_msg = f"🎀 {user.mention} is **{percentage}%** femboy!"
    
    # Direct public response (visible to all, shows invoker in system message)
    try:
        await interaction.response.send_message(
            result_msg,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"[femboymeter] Sent result for {user.display_name}: {percentage}%")
    except Exception as e:
        print(f"[femboymeter] Failed to send: {e}")
        try:
            await interaction.response.send_message(
                f"❌ Couldn't post the result. Preview: {result_msg}",
                ephemeral=True
            )
        except Exception:
            pass

# Slash command: Gay Meter (playful)
@bot.tree.command(name="gaymeter", description="Measure the rainbow levels 🌈 (totally legit science)")
@app_commands.describe(user="Your totally straight friend")
async def gaymeter(interaction: discord.Interaction, user: discord.Member):
    import random
    percentage = random.randint(1, 100)
    # Keep messaging light and respectful
    result_msg = f"🌈 {user.mention} is {percentage}% on the gay‑o‑meter — just for fun!"

    # Direct public response (visible to all, shows invoker in system message)
    try:
        await interaction.response.send_message(
            result_msg,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"[gaymeter] Sent result for {user.display_name}: {percentage}%")
    except Exception as e:
        print(f"[gaymeter] Failed to send: {e}")
        try:
            await interaction.response.send_message(
                f"❌ Couldn't post the result. Preview: {result_msg}",
                ephemeral=True
            )
        except Exception:
            pass

# Slash command: Skid Meter
@bot.tree.command(name="skidmeter", description="Rate how much of a 💩 someone is (brutally honest)")
@app_commands.describe(user="The lucky participant")
async def skidmeter(interaction: discord.Interaction, user: discord.Member):
    import random
    percentage = random.randint(1, 100)
    result_msg = f"💩 {user.mention} is **{percentage}%** a skid not sigma!"

    # Direct public response (visible to all, shows invoker in system message)
    try:
        await interaction.response.send_message(
            result_msg,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"[skidmeter] Sent result for {user.display_name}: {percentage}%")
    except Exception as e:
        print(f"[skidmeter] Failed to send: {e}")
        try:
            await interaction.response.send_message(
                f"❌ Couldn't post the result. Preview: {result_msg}",
                ephemeral=True
            )
        except Exception:
            pass

# Slash command: Coin Flip
@bot.tree.command(name="coinflip", description="Let fate decide (because you can't) 🪙")
async def coinflip(interaction: discord.Interaction):
    import random
    result = random.choice(["Heads", "Tails"])
    result_msg = f"🪙 The coin landed on: **{result}**!"

    # Direct public response
    try:
        await interaction.response.send_message(result_msg)
        print(f"[coinflip] Flipped: {result} for {interaction.user.name}")
    except Exception as e:
        print(f"[coinflip] Failed to send: {e}")
        try:
            await interaction.response.send_message(
                f"❌ Couldn't flip the coin. Result was: {result}",
                ephemeral=True
            )
        except Exception:
            pass

# Slash command: Hack
@bot.tree.command(name="hack", description="Hack someone (not really, it's fake lol) 💻")
@app_commands.describe(user="The victim to 'hack'")
async def hack(interaction: discord.Interaction, user: discord.Member):
    import asyncio
    
    try:
        await interaction.response.send_message(f"🔓 Initiating hack on {user.mention}...")
    except Exception:
        pass
    
    stages = [
        "⚙️ Bypassing Discord firewall...",
        "📡 Connecting to mainframe...",
        "💾 Downloading data... 10%",
        "💾 Downloading data... 45%",
        "💾 Downloading data... 78%",
        "💾 Downloading data... 100%",
        f"✅ Successfully hacked {user.mention}!\n\n**Stolen Data:**\n🔑 Password: `ilovemom123`\n📧 Email: `{user.name}@totallyrealmail.com`\n💳 Credit Card: `6767 6767 6767 6767`\n📍 IP Address: `127.0.0.1`\n⚠️ Browser History: *[REDACTED - too embarrassing]*"
    ]
    
    try:
        for stage in stages:
            await asyncio.sleep(1.5)
            await interaction.edit_original_response(content=stage)
        print(f"[hack] 'Hacked' {user.display_name}")
    except Exception as e:
        print(f"[hack] Failed: {e}")
        try:
            await interaction.followup.send(f"❌ Hack failed. {user.mention} has antivirus!", ephemeral=True)
        except Exception:
            pass

# Slash command: Emojify
@bot.tree.command(name="emojify", description="Turn text into PURE EMOJI ENERGY ✨")
@app_commands.describe(text="The text to emojify")
async def emojify(interaction: discord.Interaction, text: str):
    emoji_map = {
        'a': '🅰️', 'b': '🅱️', 'c': '🅲', 'd': '🅳', 'e': '🅴',
        'f': '🅵', 'g': '🅶', 'h': '🅷', 'i': '🅸', 'j': '🅹',
        'k': '🅺', 'l': '🅻', 'm': '🅼', 'n': '🅽', 'o': '🅾️',
        'p': '🅿️', 'q': '🆀', 'r': '🆁', 's': '🆂', 't': '🆃',
        'u': '🆄', 'v': '🆅', 'w': '🆆', 'x': '🆇', 'y': '🆈', 'z': '🆉',
        '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
        '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣',
        '!': '❗', '?': '❓', ' ': '  '
    }
    
    result = ''.join(emoji_map.get(char.lower(), char) for char in text)
    
    if len(result) > 2000:
        result = result[:1997] + "..."
    
    try:
        await interaction.response.send_message(result)
        print(f"[emojify] Emojified text for {interaction.user.name}")
    except Exception as e:
        print(f"[emojify] Failed: {e}")
        try:
            await interaction.response.send_message("❌ Text too long or failed to emojify!", ephemeral=True)
        except Exception:
            pass

# Slash command: UwU Meter
@bot.tree.command(name="uwumeter", description="Check someone's UwU levels (OwO what's this?) 👉👈")
@app_commands.describe(user="The person to check")
async def uwumeter(interaction: discord.Interaction, user: discord.Member):
    import random
    percentage = random.randint(1, 100)
    
    if percentage < 30:
        vibe = "Barely any UwU energy... kinda sus ngl 😐"
    elif percentage < 60:
        vibe = "Moderate UwU vibes detected owo"
    elif percentage < 90:
        vibe = "HIGH UwU LEVELS!! They're dangerously cute!! >w<"
    else:
        vibe = "🚨 MAXIMUM UwU OVERLOAD!! *notices your bulge* OwO 🚨"
    
    result_msg = f"💕 {user.mention} is **{percentage}%** UwU!\n{vibe}"
    
    try:
        await interaction.response.send_message(
            result_msg,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"[uwumeter] {user.display_name}: {percentage}%")
    except Exception as e:
        print(f"[uwumeter] Failed: {e}")
        try:
            await interaction.response.send_message(f"❌ Failed! Preview: {result_msg}", ephemeral=True)
        except Exception:
            pass

# Slash command: Touch Grass
@bot.tree.command(name="touch", description="Check if someone needs to touch grass 🌱")
@app_commands.describe(user="The terminally online suspect")
async def touch(interaction: discord.Interaction, user: discord.Member):
    import random
    percentage = random.randint(1, 100)
    
    if percentage < 20:
        verdict = f"{user.mention} is SEVERELY grass-deficient!! 🚨\n**Prescription:** Go outside IMMEDIATELY!"
    elif percentage < 50:
        verdict = f"{user.mention} needs to touch grass soon... ⚠️\nIt's been a while, hasn't it?"
    elif percentage < 80:
        verdict = f"{user.mention} touches grass occasionally. Acceptable. ✅"
    else:
        verdict = f"{user.mention} is a certified grass-toucher!! 🌿\nTeach us your ways, master!"
    
    result_msg = f"🌱 **Touch Grass Meter: {percentage}%**\n{verdict}"
    
    try:
        await interaction.response.send_message(
            result_msg,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"[touch] {user.display_name}: {percentage}%")
    except Exception as e:
        print(f"[touch] Failed: {e}")
        try:
            await interaction.response.send_message(f"❌ Failed! Preview: {result_msg}", ephemeral=True)
        except Exception:
            pass

# Slash command: Get Profile Picture
@bot.tree.command(name="getpfp", description="Get anyone's profile picture with size options 🖼️")
@app_commands.describe(
    user="Whose pfp? (optional, defaults to you)",
    size="Image size (128/256/512/1024/2048)"
)
async def getpfp(
    interaction: discord.Interaction,
    user: discord.User | None = None,
    size: int = 1024,
):
    try:
        target = user or interaction.user
        allowed_sizes = {128, 256, 512, 1024, 2048}
        if size not in allowed_sizes:
            size = 1024

        avatar_asset = target.display_avatar
        sized_url = avatar_asset.with_size(size).url
        original_url = avatar_asset.url

        embed = discord.Embed(
            title=f"{getattr(target, 'display_name', getattr(target, 'name', 'User'))}'s Profile Picture",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=sized_url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • Size {size}")

        # Link buttons
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"Open {size}px", url=sized_url))
        # Always offer 2048 as max for convenience
        try:
            max_url = avatar_asset.with_size(2048).url
            view.add_item(discord.ui.Button(label="Open 2048px", url=max_url))
        except Exception:
            pass
        # If animated, offer GIF link
        try:
            if getattr(avatar_asset, "is_animated", False) and avatar_asset.is_animated():
                gif_url = avatar_asset.with_format("gif").with_size(size).url
                view.add_item(discord.ui.Button(label="Open GIF", url=gif_url))
        except Exception:
            pass
        # Fallback original
        view.add_item(discord.ui.Button(label="Open Original", url=original_url))

        await interaction.response.send_message(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
        print(f"[getpfp] Sent pfp for {getattr(target, 'display_name', getattr(target, 'name', 'User'))} at {size}px")
    except Exception as e:
        print(f"[getpfp] Failed: {e}")
        try:
            await interaction.response.send_message(
                "❌ Couldn't get profile picture. Try again in another channel.",
                ephemeral=True,
            )
        except Exception:
            pass

# Slash command: Webhook Send
@bot.tree.command(name="webhooksend", description="Become an identity thief (but legal) 🕵️")
@app_commands.describe(
    webhook_url="The secret passage (webhook URL)",
    message="Your undercover message",
    webhook_name="Your fake identity (optional)"
)
async def webhooksend(interaction: discord.Interaction, webhook_url: str, message: str, webhook_name: str = None):
    import aiohttp
    from urllib.parse import urlparse
    
    # Defer the response to avoid timeout
    try:
        await interaction.response.defer(ephemeral=True)
    except Exception:
        pass
    
    # Validate webhook URL (robust: trim, parse host & path)
    normalized = (webhook_url or "").strip()
    parsed = urlparse(normalized)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""
    allowed_hosts = {
        "discord.com",
        "discordapp.com",
        "canary.discord.com",
        "ptb.discord.com",
    }
    if host not in allowed_hosts or not path.startswith("/api/webhooks/"):
        try:
            await interaction.edit_original_response(
                content=(
                    "❌ Invalid webhook URL. Must start with one of:\n"
                    "- https://discord.com/api/webhooks/\n"
                    "- https://discordapp.com/api/webhooks/\n"
                    "- https://canary.discord.com/api/webhooks/\n"
                    "- https://ptb.discord.com/api/webhooks/"
                )
            )
        except Exception:
            pass
        return
    
    # Send via webhook
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"content": message}
            if webhook_name:
                payload["username"] = webhook_name
            
            async with session.post(normalized, json=payload) as resp:
                if resp.status == 204 or resp.status == 200:
                    await interaction.edit_original_response(content="✅ Message sent via webhook!")
                    print(f"[webhooksend] Sent message via webhook (name: {webhook_name or 'default'})")
                else:
                    error_text = await resp.text()
                    await interaction.edit_original_response(content=f"❌ Webhook request failed with status {resp.status}.\n```\n{error_text[:500]}\n```")
                    print(f"[webhooksend] Failed with status {resp.status}: {error_text}")
    except Exception as e:
        try:
            await interaction.edit_original_response(content=f"❌ Failed to send webhook: {str(e)[:200]}")
        except Exception:
            pass
        print(f"[webhooksend] Exception: {e}")

# Slash command: Diagnostics (permissions in current channel)
@bot.tree.command(name="diag", description="Show the bot's permissions in this channel")
async def diag(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
    except Exception:
        pass

    ch = interaction.channel
    guild = interaction.guild
    me = guild.me if guild else None

    is_thread = isinstance(ch, discord.Thread)
    perms = None
    details = []

    # Basic context
    try:
        details.append(f"Channel: {getattr(ch, 'name', str(ch.id))} ({ch.id})")
    except Exception:
        details.append("Channel: <unknown>")

    details.append(f"Type: {'Thread' if is_thread else 'Text/Other'}")
    if is_thread:
        try:
            details.append(f"Thread archived: {ch.archived}")
            details.append(f"Thread locked: {ch.locked}")
        except Exception:
            pass

    # Permissions
    try:
        if me and hasattr(ch, 'permissions_for'):
            perms = ch.permissions_for(me)
    except Exception as e:
        details.append(f"Permission check error: {e}")

    def yn(v: bool | None):
        return 'Yes' if v else 'No'

    if perms is not None:
        try:
            details.append(f"View Channel: {yn(perms.view_channel)}")
            details.append(f"Send Messages: {yn(perms.send_messages)}")
            # send_messages_in_threads may not exist in very old versions; guard it
            smit = getattr(perms, 'send_messages_in_threads', True)
            details.append(f"Send In Threads: {yn(smit)}")
            details.append(f"Embed Links: {yn(perms.embed_links)}")
            details.append(f"Attach Files: {yn(perms.attach_files)}")
        except Exception:
            pass
    else:
        details.append("Could not resolve permissions (no guild or channel).")

    # Summary recommendation
    recs = []
    try:
        if perms is None or not perms.view_channel:
            recs.append("Grant the bot View Channel in this channel.")
        if perms is None or not perms.send_messages:
            recs.append("Grant the bot Send Messages in this channel.")
        smit = getattr(perms, 'send_messages_in_threads', None) if perms else None
        if is_thread and (smit is None or not smit):
            recs.append("Enable Send Messages in Threads for the bot role.")
        if is_thread and hasattr(ch, 'archived') and ch.archived:
            recs.append("Unarchive the thread or create a new open thread.")
        if is_thread and hasattr(ch, 'locked') and ch.locked:
            recs.append("Unlock the thread to allow posting.")
    except Exception:
        pass

    body = "\n".join(details)
    if recs:
        body += "\n\nRecommendations:\n- " + "\n- ".join(recs)

    try:
        await interaction.edit_original_response(content=f"```\n{body}\n```")
    except Exception as e:
        print(f"[diag] Failed to send diagnostics: {e}")

# Slash command: Setup Welcome/Leave (Server Only, Admin)
@bot.tree.command(name="setupwelcome", description="Configure welcome and leave notifications (Admin only) 👋")
@app_commands.describe(
    welcome_channel="Channel for welcome messages (optional)",
    leave_channel="Channel for leave messages (optional)"
)
@app_commands.checks.has_permissions(administrator=True)
async def setupwelcome(
    interaction: discord.Interaction,
    welcome_channel: discord.TextChannel | None = None,
    leave_channel: discord.TextChannel | None = None
):
    # Only works in guilds (servers)
    if not interaction.guild:
        try:
            await interaction.response.send_message("❌ This command only works in servers, not DMs!", ephemeral=True)
        except Exception:
            pass
        return
    
    try:
        await interaction.response.defer(ephemeral=True)
    except Exception:
        pass
    
    guild_id = interaction.guild.id
    if guild_id not in guild_settings:
        guild_settings[guild_id] = {}
    
    changes = []
    if welcome_channel:
        guild_settings[guild_id]["welcome_channel"] = welcome_channel.id
        changes.append(f"✅ Welcome notifications → {welcome_channel.mention}")
    
    if leave_channel:
        guild_settings[guild_id]["leave_channel"] = leave_channel.id
        changes.append(f"✅ Leave notifications → {leave_channel.mention}")
    
    if not changes:
        try:
            await interaction.edit_original_response(
                content="ℹ️ No channels specified. Use:\n`/setupwelcome welcome_channel:#channel leave_channel:#channel`"
            )
        except Exception:
            pass
        return
    
    response = "**Welcome/Leave Setup Updated:**\n" + "\n".join(changes)
    try:
        await interaction.edit_original_response(content=response)
        print(f"[setupwelcome] Guild {guild_id}: {changes}")
    except Exception as e:
        print(f"[setupwelcome] Failed: {e}")

# Slash command: Disable Welcome/Leave (Server Only, Admin)
@bot.tree.command(name="disablewelcome", description="Disable welcome/leave notifications (Admin only) 🚫")
@app_commands.checks.has_permissions(administrator=True)
async def disablewelcome(interaction: discord.Interaction):
    if not interaction.guild:
        try:
            await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        except Exception:
            pass
        return
    
    guild_id = interaction.guild.id
    if guild_id in guild_settings:
        del guild_settings[guild_id]
        try:
            await interaction.response.send_message("✅ Welcome and leave notifications disabled.", ephemeral=True)
            print(f"[disablewelcome] Disabled for guild {guild_id}")
        except Exception:
            pass
    else:
        try:
            await interaction.response.send_message("ℹ️ No notifications were configured for this server.", ephemeral=True)
        except Exception:
            pass

@bot.event
async def on_member_join(member):
    # Skip DM welcome, use server channel if configured
    guild_id = member.guild.id
    settings = guild_settings.get(guild_id, {})
    welcome_ch_id = settings.get("welcome_channel")
    
    if welcome_ch_id:
        channel = member.guild.get_channel(welcome_ch_id)
        if channel:
            try:
                embed = discord.Embed(
                    title="👋 Welcome!",
                    description=f"{member.mention} just joined the server!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{len(member.guild.members)}")
                await channel.send(embed=embed)
                print(f"[on_member_join] Sent welcome for {member} in guild {guild_id}")
            except Exception as e:
                print(f"[on_member_join] Failed to send welcome: {e}")

    # Autorole assignment
    guild_id = member.guild.id
    autorole_conf = autorole_settings.get(guild_id, {})
    role_id = autorole_conf.get("autorole")
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason="Autorole on join")
                print(f"[on_member_join] Assigned autorole {role.name} to {member}")
            except Exception as e:
                print(f"[on_member_join] Failed to assign autorole: {e}")

@bot.event
async def on_member_remove(member):
    # Send leave notification if configured
    guild_id = member.guild.id
    settings = guild_settings.get(guild_id, {})
    leave_ch_id = settings.get("leave_channel")
    
    if leave_ch_id:
        channel = member.guild.get_channel(leave_ch_id)
        if channel:
            try:
                embed = discord.Embed(
                    title="👋 Goodbye!",
                    description=f"{member.mention} left the server.",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
                print(f"[on_member_remove] Sent leave for {member} in guild {guild_id}")
            except Exception as e:
                print(f"[on_member_remove] Failed to send leave: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process commands
    await bot.process_commands(message)

# Verification reaction role handler
@bot.event
async def on_raw_reaction_add(payload):
    guild_id = payload.guild_id
    user_id = payload.user_id
    if not guild_id or not user_id:
        return
    conf = autorole_settings.get(guild_id, {}).get("verification")
    if not conf:
        return
    if payload.channel_id == conf["channel_id"] and payload.message_id == conf["message_id"] and str(payload.emoji) == "✅":
        guild = bot.get_guild(guild_id)
        member = guild.get_member(user_id) if guild else None
        role = guild.get_role(conf["role_id"]) if guild else None
        if member and role:
            try:
                await member.add_roles(role, reason="Verified via reaction")
                print(f"[verification] Assigned {role.name} to {member}")
            except Exception as e:
                print(f"[verification] Failed to assign role: {e}")

# Slash command: Send test welcome message (Admin only)
@bot.tree.command(name="welcometest", description="Send a test welcome message to the configured channel (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def welcometest(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return
    guild_id = guild.id
    settings = guild_settings.get(guild_id, {})
    welcome_ch_id = settings.get("welcome_channel")
    if not welcome_ch_id:
        await interaction.response.send_message("ℹ️ No welcome channel configured. Use /setupwelcome first.", ephemeral=True)
        return
    channel = guild.get_channel(welcome_ch_id)
    if not channel:
        await interaction.response.send_message("❌ Configured welcome channel not found.", ephemeral=True)
        return
    embed = discord.Embed(
        title="👋 Welcome! (Test)",
        description=f"{interaction.user.mention} just joined the server!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"Test message • Member #{len(guild.members)}")
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Test welcome sent to {channel.mention}.", ephemeral=True)

# Slash command: Send test leave message (Admin only)
@bot.tree.command(name="leavetest", description="Send a test leave message to the configured channel (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def leavetest(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return
    guild_id = guild.id
    settings = guild_settings.get(guild_id, {})
    leave_ch_id = settings.get("leave_channel")
    if not leave_ch_id:
        await interaction.response.send_message("ℹ️ No leave channel configured. Use /setupwelcome first.", ephemeral=True)
        return
    channel = guild.get_channel(leave_ch_id)
    if not channel:
        await interaction.response.send_message("❌ Configured leave channel not found.", ephemeral=True)
        return
    embed = discord.Embed(
        title="👋 Goodbye! (Test)",
        description=f"{interaction.user.mention} left the server.",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="Test message")
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Test leave sent to {channel.mention}.", ephemeral=True)

# Slash command: Make Announcement Channel (Admin only)
@bot.tree.command(name="makeannc", description="Set the announcement channel (Admin only)")
@app_commands.describe(channel="Channel to use for announcements")
@app_commands.checks.has_permissions(administrator=True)
async def makeannc(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return
    guild_id = interaction.guild.id
    announcement_channels[guild_id] = channel.id
    await interaction.response.send_message(f"✅ Announcement channel set to {channel.mention}.", ephemeral=True)

# Slash command: Announce
@bot.tree.command(name="annc", description="Send an announcement to the configured channel")
@app_commands.describe(message="The announcement message")
async def annc(interaction: discord.Interaction, message: str):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return
    guild_id = guild.id
    channel_id = announcement_channels.get(guild_id)
    if not channel_id:
        await interaction.response.send_message("ℹ️ No announcement channel set. Use /makeannc first.", ephemeral=True)
        return
    channel = guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ Configured announcement channel not found.", ephemeral=True)
        return
    embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.gold())
    embed.set_footer(text=f"Sent by {interaction.user.display_name}")
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}.", ephemeral=True)

# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN is not None:
        TOKEN = TOKEN.strip()
        if TOKEN.lower().startswith('bot '):
            TOKEN = TOKEN[4:].strip()
    if TOKEN is None:
        print('Error: DISCORD_TOKEN not found in environment variables')
    else:
        bot.run(TOKEN)
