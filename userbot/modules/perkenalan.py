from time import sleep

from userbot.events import register


@register(outgoing=True, pattern="^.ronal(?: |$)(.*)")
async def typewriter(typew):
    typew.pattern_match.group(1)
    sleep(3)
    await typew.edit("`Hai Perkenalkan Namaku Ronaldy Syach ☺️`")
    sleep(3)
    await typew.edit("`22 Tahun, Lulusan Sekolah 2017 ☺️`")
    sleep(1)
    await typew.edit("`Tinggal Di Tangerang Selatan, Salam Kenal Yakk:)`")


# Create by myself @localheart


@register(outgoing=True, pattern="^.sayang(?: |$)(.*)")
async def typewriter(typew):
    typew.pattern_match.group(1)
    sleep(3)
    await typew.edit("`Cuma Mau Bilang`")
    sleep(3)
    await typew.edit("`Aku Sayang Kamu`")
    sleep(1)
    await typew.edit("`I LOVE YOU 💞`")


# Create by myself @localheart


@register(outgoing=True, pattern="^.semangat(?: |$)(.*)")
async def typewriter(typew):
    typew.pattern_match.group(1)
    sleep(3)
    await typew.edit("`Apapun Yang Terjadi`")
    sleep(3)
    await typew.edit("`Tetaplah Bernapas`")
    sleep(1)
    await typew.edit("`Dan Selalu Bersyukur`")


# Create by myself @localheart
