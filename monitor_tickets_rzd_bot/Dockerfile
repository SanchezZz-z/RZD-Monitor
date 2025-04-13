FROM python:3.11-slim

# Установим необходимые пакеты и локали
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

# Установка переменных окружения для локалей
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Если необходимо использовать другую локаль, можно также установить её
# Например, для русской локали
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# get BOT_NAME from .env !
ENV BOT_NAME=monitor_tickets_rzd_bot

WORKDIR /usr/src/app/${monitor_tickets_rzd_bot}

COPY requirements.txt /usr/src/app/${monitor_tickets_rzd_bot}

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH=/usr/src/app

RUN pip3 install --upgrade setuptools

RUN pip3 install -r /usr/src/app/${monitor_tickets_rzd_bot}/requirements.txt

COPY . /usr/src/app/${monitor_tickets_rzd_bot}

# Проверка локали для отладки
RUN locale

#CMD ["python", "bot.py"]
