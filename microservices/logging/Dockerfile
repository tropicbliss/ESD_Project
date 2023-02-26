FROM rust:slim-buster
WORKDIR /usr/src/app
COPY . .
RUN cargo install --path .
RUN rm -r *
ENTRYPOINT [ "logging" ]