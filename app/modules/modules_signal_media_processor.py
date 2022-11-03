from signalstickers_client import StickersClient
from signalstickers_client.models import LocalStickerPack, Sticker
import glob
import uuid
import ffmpeg
import requests
import zipfile
import io
import time
import os
import json
import shutil
import asyncio
from apng import APNG, PNG
from PIL import Image, ImageSequence, ImageOps
from .apng_square_and_optimize import resize
import subprocess
SIGNAL_USERNAME = os.environ.get('SIGNAL_USERNAME')
SIGNAL_PASSWORD = os.environ.get('SIGNAL_PASSWORD')


class SignalMediaProcessor(object):
    def __init__(self):
        self.line_url_prefix = 'https://stickershop.line-scdn.net/stickershop/v1/product/'
        self.line_url_suffix = '/iphone/stickerpack@2x.zip'
        self.line_url_suffix_static = '/iphone/stickers@2x.zip'
        self.line_sticker_id = None
        self.file_name = None
        self.output_files = None
        self.title = None
        self.author = None
        self.output_path = None

    def resize_with_padding(self, img, expected_size):
        # print(img.mode)
        if(img.mode != 'RGBA'):
            img = img.convert('RGBA')
        x, y, z = 0, 0, 0
        pix = img.load()
        img.thumbnail((expected_size[0], expected_size[1]))
        delta_width = expected_size[0] - img.size[0]
        delta_height = expected_size[1] - img.size[1]
        pad_width = delta_width // 2
        pad_height = delta_height // 2
        padding = (pad_width, pad_height, delta_width -
                   pad_width, delta_height - pad_height)
        # print("=================" , img, padding,"===========================")
        return ImageOps.expand(img, padding, fill=(0, 0, 0, 0))

    def resize_apng(self, image_path, output_dir, no_resize):
        original_apng = APNG.open(os.path.join(image_path))
        new_apng = APNG()
        if no_resize == 1:
            largest = 512
        else:
            largest = 460
        for i, (png, control) in enumerate(original_apng.frames):
            if png.width > largest:
                largest = png.width
            if png.height > largest:
                largest = png.height
        for i, (png, control) in enumerate(original_apng.frames):
            if i == 0:
                first_frame = os.path.join('temp_extract', str(
                    image_path).split('\\')[-1].split('.')[0]+"_first.png")
                png.save(first_frame)
                back = self.resize_with_padding(
                    Image.open(first_frame), [largest, largest])
                back = back.save(first_frame, 'PNG')
                new_y = (largest - control.height) / 2
                new_x = (largest - control.width) / 2
            # print(control.width, control.height)
            width = control.width
            height = control.height
            x_offset = int(new_x) + control.x_offset
            y_offset = int(new_y) + control.y_offset
            delay = control.delay
            delay_den = control.delay_den
            depose_op = control.depose_op
            blend_op = control.blend_op
            if i == 0:
                new_apng.append(PNG.open_any(first_frame), **
                                {'delay': 0, 'delay_den':  0})
            else:
                if width > 1 or height > 1:
                    temp = str(uuid.uuid4()) + ".png"
                    png.save(temp)
                    with Image.open(temp) as temp_image:
                        if temp_image.mode != 'RGBA':
                            temp_image = temp_image.convert('RGBA')
                            temp_image.save(temp, 'PNG')

                        new_apng.append_file(temp, **{'width': width, 'height': height, 'x_offset': x_offset, 'y_offset': y_offset,
                                             'delay': delay, 'delay_den':  delay_den, 'depose_op':  depose_op, 'blend_op':  blend_op})
                    os.remove(temp)
                    # os.remove(first_frame)
        new_apng.save(output_dir)

        return

    def get_size_by_id(self, id):
        stickers = self.meta.get('stickers')
        stickers = list(stickers)
        for sticker in stickers:
            if sticker['id'] == int(id):
                return int(sticker['width']), int(sticker['height'])

    def download_media(self, line_sticker_id):
        self.line_sticker_id = line_sticker_id
        self.file_name = time.time()
        self.is_animated = False
        try:
            line_url = self.line_url_prefix + line_sticker_id + self.line_url_suffix
            res = requests.get(line_url, stream=True)
            z = zipfile.ZipFile(io.BytesIO(res.content))
            self.is_animated = True
        except:
            pass

        if not self.is_animated:
            line_url = self.line_url_prefix + line_sticker_id + self.line_url_suffix_static
            res = requests.get(line_url, stream=True)
            z = zipfile.ZipFile(io.BytesIO(res.content))
        extract_path = os.path.join(
            os.getcwd(), 'temp_extract', str(self.file_name))

        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        z.extractall(extract_path)

    def process_stickers(self, type, no_resize):
        if type == 'telegram_animated':
            url = self.process_telegram_animated(no_resize)
            return url
        elif type == 'telegram_static':
            url = self.process_telegram_static()
            return url

    def process_telegram_animated(self, no_resize):
        self.output_files = []

        input_dir = 'temp_extract/' + \
            str(self.file_name) + \
            ('/animation@2x' if not self.is_popup else '/popup')
        output_dir = 'temp_output/' + str(self.file_name) + '/apng'

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file in os.listdir(input_dir):
            print('converting file', file)
            self.resize_apng(os.path.join(input_dir, file),
                             os.path.join(output_dir, file), no_resize)

        self.scale_up_sticker(output_dir)
        self.compress_size(output_dir)
        url = asyncio.run(self.create_package(output_dir))
        return url

    def png_transform(self, image_path, output_dir):
        sticker_id = image_path.split('/')[-1].split('.')[0].replace('@2x', '')
        width, height = self.get_size_by_id(sticker_id)
        output_path = output_dir + '/' + \
            image_path.split('/')[-1].split('.')[0] + '.png'
        subprocess.call(['ffmpeg', '-i', image_path, '-pix_fmt',
                        'rgba', '-vf', 'scale=-512:512', output_path])
        return output_path

    def process_telegram_static(self):
        self.output_files = []

        input_dir = 'temp_extract/' + str(self.file_name)
        output_dir = 'temp_output/' + str(self.file_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file in os.listdir(input_dir):
            if file.endswith('.png') and 'tab' not in file and '_key' not in file:
                output = self.png_transform(input_dir + '/' + file, output_dir)
                if output.endswith('.png'):
                    self.output_files.append(output)

        url = asyncio.run(self.create_package(output_dir))
        return url

    def get_sticker_pack_meta(self):
        extract_path = 'temp_extract/' + str(self.file_name)
        for root, dirs, files in os.walk(extract_path):
            for i in (files):
                if i == 'productInfo.meta':
                    with open(os.path.join(root, i), 'r', encoding="utf-8") as f:
                        metadata = json.load(f)
                        self.title = (metadata.get('title').get('en'))
                        self.author = (metadata.get('author').get('en'))
                        self.is_animated = (metadata.get('hasAnimation'))
                        self.is_popup = 'popup' in list(
                            metadata.get('stickers'))[0]
                        self.meta = metadata
                    break

        return {
            'id': self.line_sticker_id,
            'title': self.title,
            'author': self.author,
            'stickers': self.output_files
        }

    def scale_up_sticker(self, output_dir):
        if not os.path.exists(output_dir+'-y'):
            os.makedirs(output_dir+'-y')
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file == 'productInfo.meta':
                    continue
                sticker_id = file.split(
                    '/')[-1].split('.')[0].replace('@2x', '')
                image_path = os.path.join(output_dir, file)
                input = ffmpeg.input(image_path)
                input = ffmpeg.filter(input, 'scale', 512, 512)
                output_path = os.path.join(
                    output_dir + '-y', sticker_id + '.apng')
                stream = ffmpeg.output(input, output_path)
                ffmpeg.run(stream, overwrite_output=True)
                os.rename(output_path, output_path.replace('.apng', '.png'))
        shutil.rmtree(output_dir)
        os.rename(output_dir+'-y', output_dir)

    def add_sticker(self, pack, path, emoji):
        stick = Sticker()
        stick.id = pack.nb_stickers
        stick.emoji = emoji
        with open(path, "rb") as f_in:
            stick.image_data = f_in.read()
        pack._addsticker(stick)

    async def create_package(self, outout_dir):
        pack = LocalStickerPack()
        pack.title = self.title
        pack.author = self.author
        all_sticker = glob.glob(outout_dir+"/*.png")
        for filename in all_sticker:  # assuming gif
            self.add_sticker(pack, filename, "😃")

        cover = Sticker()
        cover.id = pack.nb_stickers
        # Set the cover file here
        with open(all_sticker[0], "rb") as f_in:
            cover.image_data = f_in.read()
        pack.cover = cover

        # Instanciate the client with your Signal crendentials
    
        print('uploading to signal')
        async with StickersClient(SIGNAL_USERNAME, SIGNAL_PASSWORD) as client:
            pack_id, pack_key = await client.upload_pack(pack)

        print("Pack uploaded!\n\nhttps://signal.art/addstickers/#pack_id={}&pack_key={}".format(pack_id, pack_key))
        return ("https://signal.art/addstickers/#pack_id={}&pack_key={}".format(pack_id, pack_key))

    def compress_size(self, image_path):
        for root, dirs, files in os.walk(image_path):
            for file in files:
                compress_rate = 256
                while os.stat(os.path.join(image_path, file)).st_size / 1000 > 300:
                    with open(os.path.join(image_path, file), 'rb') as f:
                        data = f.read()
                        data = bytearray(data)
                        print(compress_rate)
                        byte = resize(data, int(compress_rate))
                        byte.save(os.path.join(image_path, file))
                    compress_rate /= 2

    def cleanup_folders(self):
        shutil.rmtree('temp_extract/' + str(self.file_name))
        shutil.rmtree('temp_output/' + str(self.file_name))
