# https://hub.docker.com/_/python?tab=tags&page=1&name=3.9
FROM python:3.9.19-slim as release

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

FROM release as dev
USER root
COPY dist/arrnounced-*.tar.gz /arr.tar.gz
RUN pip install --force-reinstall /arr.tar.gz
USER arrnounced
