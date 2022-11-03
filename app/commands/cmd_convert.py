import sys

sys.path.append('../modules')

from modules.hub import *

def convert(update, context):
    if not context.args:
        update.message.reply_text("Line sticker pack id missing, e.g. /convert 1295557")
    elif len(context.args) > 1:
        update.message.reply_text("Only 1 Line sticker pack id is required, e.g. /convert 1295557")
    else:
        user_id = update.message.from_user.id
        line_sticker_id = context.args[0]

        mp = MediaProcessor()

        try:
            message = context.bot.send_message(chat_id=user_id, text='Processing...')

            context.bot.edit_message_text(chat_id=user_id, text='Downloaded sticker set...',
                                          message_id=message.message_id)

            mp.download_media(line_sticker_id)

            mp.get_sticker_pack_meta()

            sticker_pack_name = 'smb_' + str(line_sticker_id) + ('_a' if mp.is_animated else '_s') + '_by_sticker_microservice_bot'

            sticker_set = None

            try:
                sticker_set = context.bot.get_sticker_set(sticker_pack_name)
            except:
                pass

            if sticker_set:
                # context.bot.edit_message_text(chat_id=user_id, text='Done!', message_id=message.message_id)

                # context.bot.send_sticker(chat_id=user_id, sticker=sticker_set.stickers[0].file_id)
                # return

                for sticker in sticker_set.stickers:
                    context.bot.delete_sticker_from_set(sticker.file_id)

            context.bot.edit_message_text(chat_id=user_id, text='Converting sticker set to webm...',
                                          message_id=message.message_id)

            is_webm = mp.is_animated or mp.is_popup

            if is_webm:
                mp.process_stickers('telegram_animated')
            else:
                mp.process_stickers('telegram_static')

            context.bot.edit_message_text(chat_id=user_id, text='Creating sticker set...',
                                          message_id=message.message_id)
            # context.bot.edit_message_text(chat_id=user_id, text=mp.output_files[0], message_id=message.message_id)

            if sticker_set is None:
                if is_webm:
                    context.bot.create_new_sticker_set(user_id, name=sticker_pack_name, title=mp.title,
                                                       webm_sticker=open(mp.output_files[0], 'rb'), emojis='👍')
                else:
                    context.bot.create_new_sticker_set(user_id, name=sticker_pack_name, title=mp.title,
                                                       png_sticker=open(mp.output_files[0], 'rb'), emojis='👍')

            idx = 1
            for file in mp.output_files[1:]:
                text = 'Adding stickers to sticker set ' + str(idx) + '/' + str(len(mp.output_files)) + '...'

                context.bot.edit_message_text(chat_id=user_id, text=text, message_id=message.message_id)

                if is_webm:
                    context.bot.add_sticker_to_set(user_id, name=sticker_pack_name, webm_sticker=open(file, 'rb'),
                                                   emojis='👍')
                else:
                    context.bot.add_sticker_to_set(user_id, name=sticker_pack_name, png_sticker=open(file, 'rb'),
                                                   emojis='👍')

                idx += 1

            sticker_set = context.bot.get_sticker_set(sticker_pack_name)

            context.bot.edit_message_text(chat_id=user_id, text='Done!', message_id=message.message_id)

            context.bot.send_sticker(chat_id=user_id, sticker=sticker_set.stickers[0].file_id)

        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=user_id, text='Something went wrong. Please try again.')
            context.bot.send_message(chat_id=user_id, text=str(e))

        try:
            mp.cleanup_folders()
        except:
            pass