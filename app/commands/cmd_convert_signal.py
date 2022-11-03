import sys

sys.path.append('../modules')

from modules.hub import *

def convert_signal(update, context):
    no_resize = False
    if len(context.args) == 2:
        if context.args[1] == '--no-resize':
            no_resize = True
    if not context.args:
        update.message.reply_text("Line sticker pack id missing, e.g. /convert 1295557")
    else:
        user_id = update.message.from_user.id
        line_sticker_id = context.args[0]
        mp = SignalMediaProcessor()

        try:
            message = context.bot.send_message(chat_id=user_id, text='Processing...')

            context.bot.edit_message_text(chat_id=user_id, text='Downloaded sticker set...',
                                          message_id=message.message_id)

            mp.download_media(line_sticker_id)
            mp.get_sticker_pack_meta()


            sticker_pack_name = 'smb_' + str(line_sticker_id) + ('_a' if mp.is_animated else '_s') + '_by_sticker_microservice_bot'

            sticker_set = None

            if sticker_set:
                context.bot.edit_message_text(chat_id=user_id, text='Done!', message_id=message.message_id)

                context.bot.send_sticker(chat_id=user_id, sticker=sticker_set.stickers[0].file_id)
                return

            context.bot.edit_message_text(chat_id=user_id, text='Converting sticker set to signal...',
                                          message_id=message.message_id)
            is_apng = mp.is_animated or mp.is_popup

            url = ''
            if is_apng:
                url = mp.process_stickers('telegram_animated',no_resize)
            else:
                url = mp.process_stickers('telegram_static',no_resize)


            context.bot.edit_message_text(chat_id=user_id, text='Done!', message_id=message.message_id)

            context.bot.send_message(chat_id=user_id, text=url)


        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=user_id, text='Something went wrong. Please try again.')
            context.bot.send_message(chat_id=user_id, text=str(e))

        try:
            mp.cleanup_folders()
        except:
            pass