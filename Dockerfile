FROM python:3.8.2-slim

RUN addgroup --system arrnounced && \
    adduser --system --no-create-home --shell /bin/false --ingroup arrnounced arrnounced && \
    mkdir /config /trackers /arrnounced

VOLUME /config
EXPOSE 3467

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY autodl-trackers/trackers/ /trackers
COPY src/ /arrnounced

RUN chown -R arrnounced:arrnounced /config /trackers /arrnounced

WORKDIR /arrnounced
USER arrnounced

# TODO: Control verbose via env
CMD ["./arrnounced.py", \
    "--data", "/config", \
    "--config", "/config/settings.cfg", \
    "--trackers", "/trackers", \
    "--verbose"]
