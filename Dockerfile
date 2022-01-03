FROM python:3.9.9-slim

COPY autodl-trackers/trackers/ /trackers

RUN addgroup --system arrnounced && \
    adduser --system --no-create-home --shell /bin/false --ingroup arrnounced arrnounced && \
    mkdir /config && \
    chown -R arrnounced:arrnounced /config /trackers && \
    pip install arrnounced

VOLUME /config
EXPOSE 3467

USER arrnounced

CMD ["arrnounced", \
    "--data", "/config", \
    "--config", "/config/settings.toml", \
    "--trackers", "/trackers"]
