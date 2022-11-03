import ffmpeg
import requests
import zipfile
import io
import time
import os
import json
import math
import subprocess
import shutil

class MediaProcessor(object):
    def __init__(self):
        self.line_url_prefix = 'https://stickershop.line-scdn.net/stickershop/v1/product/'
        self.line_url_suffix = '/iphone/stickerpack@2x.zip'
        self.line_url_suffix_static = '/iphone/stickers@2x.zip'
        self.line_sticker_id = None
        self.file_name = None
        self.output_files = None
        self.title = None
        self.author = None

    def apng_to_webm(self, image_path, output_dir):
        # input = ffmpeg.input(image_path, pix_fmt='pal8')

        ffmpeg_cmd = ['ffmpeg', '-i', image_path]

        image_size = self.get_image_file_size(image_path)

        if image_size / 2 > 128 * 1024:
            ffmpeg_cmd.extend(['-b:v', '32k'])
        elif image_size / 2 > 64 * 1024:
            ffmpeg_cmd.extend(['-b:v', '100k'])


        sticker_id = image_path.split('/')[-1].split('.')[0].replace('@2x', '')

        # width, height = self.get_size(image_path)
        num_of_frame, avg_frame_rate, r_frame_rate = self.get_number_of_frame(image_path)

        width, height = self.get_size_by_id(sticker_id)

        # input = ffmpeg.filter(input, 'scale', -1, 512) if height > width else ffmpeg.filter(input, 'scale', 512, -1)

        filter = 'scale=-1:512' if height > width else 'scale=512:-1'

        if num_of_frame / r_frame_rate > 3:
            ratio = math.ceil(3 / (num_of_frame / r_frame_rate) * 10) / 10 * 0.6
            # input = ffmpeg.filter(input, 'setpts', str(ratio) + '*PTS')
            filter = 'setpts=' + str(ratio) + '*PTS,' + filter

        output_path = output_dir + '/' + image_path.split('/')[-1].split('.')[0] + '.webm'

        # stream = ffmpeg.output(input, output_path)
        #
        # ffmpeg.run(stream)

        ffmpeg_cmd.extend(['-filter:v', filter, output_path])

        subprocess.call(ffmpeg_cmd)

        return output_path

    def png_transform(self, image_path, output_dir):
        sticker_id = image_path.split('/')[-1].split('.')[0].replace('@2x', '')

        width, height = self.get_size_by_id(sticker_id)

        output_path = output_dir + '/' + image_path.split('/')[-1].split('.')[0] + '.png'

        subprocess.call(['ffmpeg', '-i', image_path, '-pix_fmt', 'rgba', '-vf', 'scale=-1:512' if height > width else 'scale=512:-1', output_path])

        return output_path

    def get_image_file_size(self, file_path):
        return os.path.getsize(file_path)

    def get_number_of_frame(self, image_path):
        probe = ffmpeg.probe(image_path, cmd='ffprobe', select_streams='v:0', show_entries='stream=nb_read_frames', count_frames=None)

        num_of_frame = int(probe['streams'][0]['nb_read_frames'])

        probe = ffmpeg.probe(image_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        avg_frame_rate = video_stream['avg_frame_rate']
        avg_frame_rate = avg_frame_rate.split('/')
        avg_frame_rate = int(avg_frame_rate[0]) / int(avg_frame_rate[1])

        r_frame_rate = video_stream['r_frame_rate']
        r_frame_rate = r_frame_rate.split('/')
        r_frame_rate = int(r_frame_rate[0]) / int(r_frame_rate[1])

        return num_of_frame, math.floor(avg_frame_rate), math.floor(r_frame_rate)

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

        extract_path = os.path.join(os.getcwd(), 'temp_extract', str(self.file_name))

        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        z.extractall(extract_path)

    def process_stickers(self, type):
        if type == 'telegram_animated':
            self.process_telegram_animated()
        elif type == 'telegram_static':
            self.process_telegram_static()

    def process_telegram_animated(self):
        self.output_files = []

        input_dir = 'temp_extract/' + str(self.file_name) + ('/animation@2x' if not self.is_popup else '/popup')
        output_dir = 'temp_output/' + str(self.file_name) + '/webm'

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file in os.listdir(input_dir):
            output = self.apng_to_webm(input_dir + '/' + file, output_dir)
            if output.endswith('.webm'):
                self.output_files.append(output)

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
                        self.is_popup = 'popup' in list(metadata.get('stickers'))[0]
                        self.meta = metadata
                    break

        return {
            'id': self.line_sticker_id,
            'title': self.title,
            'author': self.author,
            'stickers': self.output_files
        }

    def cleanup_folders(self):
        shutil.rmtree('temp_extract/' + str(self.file_name))
        shutil.rmtree('temp_output/' + str(self.file_name))