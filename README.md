# Line-Sticker-to-Signal

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

Due to the limitation of signal upload sticker limit. Please use your own signal credentials to run the bot to prevent going over the limit.
