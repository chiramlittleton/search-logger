FROM elixir:1.16

# Install hex + rebar
RUN mix local.hex --force && mix local.rebar --force

WORKDIR /app

# Copy project files
COPY mix.exs mix.lock ./
COPY config config

# ENV to skip buggy type checker
ENV ERL_COMPILER_OPTIONS="no_type_check"

# Install deps first (cached)
RUN mix deps.get

# Copy the rest
COPY . .

# Compile the project
RUN mix compile

# Run the server
CMD ["mix", "phx.server"]
