# Line-Sticker-to-Telegram/Signal (Telegram bot)

## Run Locally

Clone the project

```bash
  git clone https://link-to-project
```

Go to the project directory

```bash
  cd my-project/app
```

Install dependencies

```bash
  pip install -r requirements.txt
```

create a .env file

```
  TOKEN=YOUR_TOKEN
  APP_ENV=test
  SIGNAL_USERNAME=SIGNAL_USERNAME
  SIGNAL_PASSWORD=SIGNAL_USERNAME
```

To get signal username & password

> **You will need your Signal credentials** To obtain them, run the Signal Desktop
> app with the flag `--enable-dev-tools`, open the Developer Tools, and type
> `window.reduxStore.getState().items.uuid_id` to get your USER, and
> `window.reduxStore.getState().items.password` to get your PASSWORD.
> (source from https://github.com/signalstickers/signalstickers-client)

Start the telegram bot

```bash
  python start.py
```

convert to telegram

```bash
/convert [line_sticker_id]
```
![image](https://user-images.githubusercontent.com/38665439/199755349-5173b07c-2c93-4d3d-9c44-977cd6d792da.png)

convert to signal

```bash
/signal [line_sticker_id]
```
![image](https://user-images.githubusercontent.com/38665439/199755448-98abdbec-520b-46f2-a019-4cba39381fe5.png)

Due to the limitation of signal upload sticker limit. Please use your own signal credentials to run the bot to prevent going over the limit.
