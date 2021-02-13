# -*- coding: utf-8 -*-


# Hackintosh5 is gay

# API Author: @mishase
# Module Author: @rf0x1d

# requires: Pillow requests

import asyncio
import functools
import io
import json
import logging
import os

import PIL
import requests
import telethon
from telethon.tl.types import (
    ChannelParticipantCreator,
    ChannelParticipantsAdmins,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUrl,
    MessageMediaUnsupported,
    PeerChannel,
    PeerChat,
    User,
)

from userbot.events import register

logger = logging.getLogger(__name__)

strings = {
    "name": "mQuotes",
    "silent_processing_cfg_doc": ("Process quote " "silently(mostly" " w/o editing)"),
    "api_endpoint_cfg_doc": "API endpoint URL",
    "quote_limit_cfg_doc": "Limit for messages per quote",
    "max_width_cfg_doc": "Maximum quote width in pixels",
    "scale_factor_cfg_doc": "Quote quality (up to 5.5)",
    "square_avatar_cfg_doc": "Square avatar in quote",
    "text_color_cfg_doc": "Color of text in quote",
    "reply_line_color_cfg_doc": "Reply line color",
    "reply_thumb_radius_cfg_doc": ("Reply media thumbnail " "radius in pixels"),
    "admintitle_color_cfg_doc": "Admin title color",
    "message_radius_cfg_doc": "Message radius in px",
    "picture_radius_cfg_doc": "Media picture radius in px",
    "background_color_cfg_doc": "Quote background color",
    "quote_limit_reached": ("The maximum number " "of messages in " "multiquote - {}."),
    "processing": "<b>Processing...</b>",
    "unreachable_error": "<b>API Host is unreachable now. Please try again later.</b>",  # noqa: e501
    "server_error": "<b>API Error occured :)</b>",
    "no_reply": "<b>You didn't reply to a message.</b>",
    "creator": "creator",
    "admin": "admin",
    "channel": "channel",
    "media_type_photo": "Photo",
    "media_type_video": "📹Video",
    "media_type_videomessage": "📹Video message",
    "media_type_voice": "🎵Voice message",
    "media_type_audio": "🎧Music: {} - {}",
    "media_type_contact": "👤Contact: {}",
    "media_type_poll": "📊Poll: ",
    "media_type_quiz": "📊Quiz: ",
    "media_type_location": "📍Location",
    "media_type_gif": "🖼GIF",
    "media_type_sticker": "Sticker",
    "media_type_file": "💾File",
    "dice_type_dice": "Dice",
    "dice_type_dart": "Dart",
    "ball_thrown": "Ball thrown",
    "ball_kicked": "Ball kicked",
    "dart_thrown": "Dart thrown",
    "dart_almostthere": "almost there!",
    "dart_missed": "missed!",
    "dart_bullseye": "bullseye!",
}

config = dict(
    {
        "API_ENDPOINT": "https://quotes.mishase.dev/create",
        "QUOTE_MESSAGES_LIMIT": 15,
        "MAX_WIDTH": 384,
        "SCALE_FACTOR": 5,
        "SQUARE_AVATAR": False,
        "TEXT_COLOR": "white",
        "REPLY_LINE_COLOR": "white",
        "REPLY_THUMB_BORDER_RADIUS": 2,
        "ADMINTITLE_COLOR": "#969ba0",
        "MESSAGE_BORDER_RADIUS": 10,
        "PICTURE_BORDER_RADIUS": 8,
        "BACKGROUND_COLOR": "#162330",
    }
)


def run_sync(func, *args, **kwargs):
    """Run a non-async function in a new thread and return an awaitable"""

    # Returning a coro
    return asyncio.get_event_loop().run_in_executor(
        None, functools.partial(func, *args, **kwargs)
    )


@register(outgoing=True, pattern=r"^\.quote(?: |$)(.*)")
async def mquotes(message):
    """Quote a message using MishaseQuotes API"""
    await message.edit(strings["processing"])
    args = message.pattern_match.group(1)
    reply = await message.get_reply_message()
    if not reply:
        return await message.edit(strings["no_reply"])
    if not args or not args.isdigit():
        count = 1
    else:
        count = int(args.strip())
        if count <= 0:
            count = 1
        if count > config["QUOTE_MESSAGES_LIMIT"]:
            return await message.edit(
                strings["quote_limit_reached"].format(config["QUOTE_MESSAGES_LIMIT"])
            )
    messages = list()
    messages_client = list()
    media_files = dict()
    current_message = reply.id
    end_message = current_message + count
    while current_message != end_message:
        msg = await message.client.get_messages(message.to_id, ids=current_message)
        if msg:
            messages_client.append(msg)
        current_message += 1
    for msg in messages_client:
        text = msg.raw_text
        markdown = await get_markdown(msg)
        admintitle = str()
        if isinstance(msg.to_id, PeerChannel) and msg.fwd_from:
            user = msg.forward.chat
        elif isinstance(msg.to_id, PeerChat):
            chat = await message.client(
                telethon.tl.functions.messages.GetFullChatRequest(
                    msg.to_id
                )  # noqa: e501
            )
            participants = chat.full_chat.participants.participants
            participant = next(
                filter(lambda x: x.user_id == msg.from_id.user_id, participants), None
            )  # noqa: e501
        else:
            user = await msg.get_sender()
        if msg.fwd_from:
            if msg.fwd_from.saved_from_peer:
                print(msg.forward.chat)
                id = msg.fwd_from.saved_from_peer.channel_id
            elif msg.fwd_from.channel_id:
                id = msg.fwd_from.channel_id
            elif msg.fwd_from.from_id:
                id = msg.fwd_from.from_id
            else:
                id = None
            if not id:
                id = 1234567890
                name = msg.fwd_from.from_name
                pfp = None
            else:
                sender = await message.client.get_entity(id)
                name = telethon.utils.get_display_name(sender)
                pfp = media_files.get("@av{}".format(str(id).lstrip("-")), None)
                if msg.fwd_from.saved_from_peer:
                    profile_photo_url = msg.forward.chat
                elif msg.fwd_from.from_name:
                    name = msg.fwd_from.from_name
                    profile_photo_url = None
                elif msg.forward.sender:
                    name = telethon.utils.get_display_name(msg.forward.sender)
                    profile_photo_url = msg.forward.sender.id
                elif msg.forward.chat:
                    profile_photo_url = user
                if msg.fwd_from is not None and msg.fwd_from.post_author is not None:
                    name += f" ({msg.fwd_from.post_author})"
                if not pfp:
                    pfp = await message.client.download_profile_photo(
                        profile_photo_url, "mishase_cache/"
                    )
                    if pfp:
                        media_files["@av{}".format(str(id).lstrip("-"))] = pfp
        else:
            id = msg.from_id if msg.from_id != 1087968824 else message.chat_id
            if not message.chat or (
                id != message.chat_id or isinstance(message.chat, User)
            ):
                sender = await message.client.get_entity(id)
                name = telethon.utils.get_display_name(sender)
                pfp = media_files.get("@av{}".format(str(id).lstrip("-")), None)
                if not pfp:
                    pfp = await message.client.download_profile_photo(
                        msg.from_id, "mishase_cache/"
                    )
                    if pfp:
                        media_files["@av{}".format(str(id).lstrip("-"))] = pfp
            else:
                name = message.chat.title
                try:
                    dl_chat_pfp = await message.client.download_profile_photo(
                        id, "mishase_cache/"
                    )
                    no_pfp = False
                except Exception as e:
                    logger.error(e, exc_info=True)
                    no_pfp = True
                if no_pfp is False:
                    media_files["@av{}".format(str(id).lstrip("-"))] = dl_chat_pfp
        media_files = await check_media(message.client, msg, media_files, False)
        message_reply = await msg.get_reply_message()
        if message_reply:
            reply_text = message_reply.raw_text
            media_caption = await get_media_caption(message_reply)
            if media_caption != "":
                if not reply_text:
                    reply_text = media_caption
                else:
                    reply_text = '{} "{}"'.format(media_caption, reply_text)
            if message_reply.fwd_from:
                if message_reply.forward.chat:
                    reply_sender = message_reply.forward.chat
                    reply_name = telethon.utils.get_display_name(reply_sender)
                    media_files = await check_media(
                        message.client, message_reply, media_files, True
                    )
                    reply_message = {
                        "author": reply_name,
                        "text": reply_text,
                    }
                    if "@mediareply{}".format(message_reply.id) in media_files:
                        reply_message["thumbnail"] = {
                            "file": "@mediareply{}".format(
                                message_reply.id
                            )  # noqa: e501
                        }
                elif message_reply.fwd_from.from_id:
                    reply_sender = message_reply.fwd_from.from_id
                    reply_user = await message.client(
                        GetFullUserRequest(message_reply.fwd_from.from_id)
                    )
                    reply_name = telethon.utils.get_display_name(reply_user.user)
                    media_files = await check_media(
                        message.client, message_reply, media_files, True
                    )
                    reply_message = {
                        "author": reply_name,
                        "text": reply_text,
                    }
                    if "@mediareply{}".format(message_reply.id) in media_files:
                        reply_message["thumbnail"] = {
                            "file": "@mediareply{}".format(
                                message_reply.id
                            )  # noqa: e501
                        }
                else:
                    media_files = await check_media(
                        message.client, message_reply, media_files, True
                    )
                    reply_message = {
                        "author": message_reply.fwd_from.from_name,
                        "text": reply_text,
                    }
                    if "@mediareply" in media_files:
                        reply_message["thumbnail"] = {"file": "@mediareply"}
            elif message_reply.from_id:
                reply_sender = message_reply.sender
                reply_name = telethon.utils.get_display_name(reply_sender)
                media_files = await check_media(
                    message.client, message_reply, media_files, True
                )
                reply_message = {"author": reply_name, "text": reply_text}
                if "@mediareply{}".format(message_reply.id) in media_files:
                    reply_message["thumbnail"] = {
                        "file": "@mediareply{}".format(message_reply.id)
                    }
            else:
                reply_name = message.chat.title
                media_files = await check_media(
                    message.client, message_reply, media_files, True
                )
                reply_message = {"author": reply_name, "text": reply_text}
                if "@mediareply{}".format(message_reply.id) in media_files:
                    reply_message["thumbnail"] = {
                        "file": "@mediareply{}".format(message_reply.id)
                    }
        else:
            reply_message = None
        if message.chat:
            if msg.from_id and not msg.fwd_from:
                admins = await message.client.get_participants(
                    message.to_id, filter=ChannelParticipantsAdmins
                )
                if msg.sender in admins:
                    admin = admins[admins.index(msg.sender)].participant
                    if not admin:
                        admintitle = " "
                    else:
                        admintitle = admin.rank
                    if not admintitle:
                        if isinstance(admin, ChannelParticipantCreator):
                            admintitle = strings["creator"]
                        else:
                            admintitle = strings["admin"]
            elif msg.fwd_from.saved_from_peer:
                admintitle = strings["channel"]
            elif msg.fwd_from.channel_id:
                admintitle = strings["channel"]
            else:
                admintitle = reply.post_author if reply.post_author else " "
        message_to_append = {
            "text": text,
            "reply": reply_message,
            "entities": markdown,
            "author": {
                "id": str(id).lstrip("-"),
                "name": name,
                "adminTitle": admintitle,
            },
        }
        if f"@av{str(id).lstrip('-')}" in media_files:
            message_to_append["author"]["picture"] = {
                "file": f"@av{str(id).lstrip('-')}"
            }
        if "@media{}".format(msg.id) in media_files:
            message_to_append["picture"] = {"file": "@media{}".format(msg.id)}
        messages.append(message_to_append)
    data = {
        "messages": messages,
        "maxWidth": config["MAX_WIDTH"],
        "scaleFactor": config["SCALE_FACTOR"],
        "squareAvatar": config["SQUARE_AVATAR"],
        "textColor": config["TEXT_COLOR"],
        "replyLineColor": config["REPLY_LINE_COLOR"],
        "adminTitleColor": config["ADMINTITLE_COLOR"],
        "messageBorderRadius": config["MESSAGE_BORDER_RADIUS"],
        "replyThumbnailBorderRadius": config["REPLY_THUMB_BORDER_RADIUS"],  # noqa: e501
        "pictureBorderRadius": config["PICTURE_BORDER_RADIUS"],
        "backgroundColor": config["BACKGROUND_COLOR"],
    }
    files = []
    for file in media_files.keys():
        files.append(("files", (file, open(media_files[file], "rb"), "image/jpg")))
    if not files:
        files.append(("files", ("file", bytearray(), "text/text")))
    print(files)
    try:
        req = await run_sync(
            requests.post,
            config["API_ENDPOINT"],
            data={"data": json.dumps(data)},
            files=files,
            timeout=100,
        )
    except (requests.ConnectionError, requests.exceptions.Timeout):
        await clean_files()
        return await message.edit(strings["unreachable_error"])
    if req.status_code >= 520:
        await clean_files()
        return await message.edit(strings["unreachable_error"])
    if req.status_code >= 500:
        await clean_files()
        return await message.edit(strings["server_error"])
    await clean_files()
    image = io.BytesIO()
    image.name = "quote.webp"
    try:
        PIL.Image.open(io.BytesIO(req.content)).save(image, "WEBP")
        image.seek(0)
        return await message.respond(image)
    except Exception as e:
        logger.error(e, exc_info=True)
        return await message.edit(strings["server_error"])


async def clean_files():
    return os.system("rm -rf mishase_cache/*")


async def check_media(client, reply, media_files: dict, is_reply: bool):
    allowed_exts = [".png", ".webp", ".jpg", ".jpeg"]
    if reply and reply.media:
        if reply.photo:
            data = reply.photo
        elif reply.document:
            if reply.gif or reply.video or reply.audio or reply.voice:
                return media_files
            elif reply.file.ext not in allowed_exts:
                return media_files
            data = reply.media.document
        else:
            return media_files
    else:
        return media_files
    if not data or data is None:
        return media_files
    else:
        data = await client.download_media(data, "mishase_cache/")
        if not is_reply:
            media_files["@media{}".format(reply.id)] = data
        else:
            media_files["@mediareply{}".format(reply.id)] = data
        return media_files


async def get_media_caption(reply_message):
    if reply_message and reply_message.media:
        if isinstance(reply_message.media, MessageMediaUnsupported):
            return "Unsupported message media"
        if reply_message.photo:
            return strings["media_type_photo"]
        dice = False
        try:
            dice = True if reply_message.dice else False
        except AttributeError:
            try:
                dice = (
                    True
                    if isinstance(
                        reply_message.media, telethon.tl.types.MessageMediaDice
                    )
                    else False
                )
            except AttributeError:
                pass
        if dice:
            dice_type = ""
            dice_text = reply_message.media.value
            if reply_message.media.emoticon == "🎲":
                dice_type = strings["dice_type_dice"]
                return "{} {}: {}".format(
                    reply_message.media.emoticon, dice_type, dice_text
                )
            elif reply_message.media.emoticon == "🎯":
                if dice_text == 1:
                    dice_text = strings["dart_missed"]
                elif dice_text == 5:
                    dice_text = strings["dart_almostthere"]
                elif dice_text == 6:
                    dice_text = strings["dart_bullseye"]
                else:
                    return "{} {}".format(
                        reply_message.media.emoticon, strings["dart_thrown"]
                    )
                dice_type = strings["dice_type_dart"]
                return "{} {}: {}".format(
                    reply_message.media.emoticon, dice_type, dice_text
                )
            elif reply_message.media.emoticon == "🏀":
                return "{} {}".format(
                    reply_message.media.emoticon, strings["ball_thrown"]
                )
            elif reply_message.media.emoticon == b"\xe2\x9a\xbd".decode():
                return "{} {}".format(
                    reply_message.media.emoticon, strings["ball_kicked"]
                )
            else:
                return "Unsupported dice type ({}): {}".format(
                    reply_message.media.emoticon, reply_message.media.value
                )
        elif reply_message.poll:
            if reply_message.poll.poll.quiz:
                return strings["media_type_quiz"] + reply_message.poll.poll.question
            else:
                return strings["media_type_poll"] + reply_message.poll.poll.question
        elif reply_message.geo:
            return strings["media_type_location"]
        elif reply_message.contact:
            name = (
                reply_message.contact.first_name + reply_message.contact.last_name
            )  # noqa: e501
            return strings["media_type_contact"].format(name)
        elif reply_message.document:
            if reply_message.gif:
                return strings["media_type_gif"]
            elif reply_message.video:
                if reply_message.video.attributes[0].round_message:
                    return strings["media_type_videomessage"]
                else:
                    return strings["media_type_video"]
            elif reply_message.audio:
                return strings["media_type_audio"].format(
                    reply_message.audio.attributes[0].performer,
                    reply_message.audio.attributes[0].title,
                )
            elif reply_message.voice:
                return strings["media_type_voice"]
            elif reply_message.sticker:
                emoji = reply_message.file.emoji
                caption = (
                    "{} {}".format(emoji, strings["media_type_sticker"])
                    if emoji
                    else strings["media_type_sticker"]
                )
                return caption
            elif reply_message.file:
                try:
                    file_name = reply_message.file.name
                    file_size = await humanize(reply_message.file.size)
                    return "{} {} ({})".format(
                        strings["media_type_file"], file_name, file_size
                    )
                except Exception:
                    return strings["media_type_file"]
        else:
            return ""
    else:
        return ""
    return ""


async def humanize(num: float, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


async def get_markdown(message):
    entities = []
    if not message.entities:
        return []
    for entity in message.entities:
        entity_type = type(entity)
        start = entity.offset
        end = entity.length
        if entity_type is MessageEntityBold:
            etype = "bold"
        elif entity_type is MessageEntityItalic:
            etype = "italic"
        elif entity_type in [MessageEntityUrl, MessageEntityPhone]:
            etype = "url"
        elif entity_type is MessageEntityCode:
            etype = "monospace"
        elif entity_type is MessageEntityStrike:
            etype = "strikethrough"
        elif entity_type is MessageEntityUnderline:
            etype = "underline"
        elif entity_type in [
            MessageEntityMention,
            MessageEntityTextUrl,
            MessageEntityMentionName,
            MessageEntityHashtag,
            MessageEntityCashtag,
            MessageEntityBotCommand,
        ]:
            etype = "bluetext"
        entities.append({"type": etype, "offset": start, "length": end})
    return entities
