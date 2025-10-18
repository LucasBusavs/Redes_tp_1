#!/bin/sh
set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -U "$POSTGRES_USER"; do
  >&2 echo "⏳ Aguardando o banco de dados em $host..."
  sleep 2
done

>&2 echo "✅ Banco de dados disponível — iniciando API!"
exec $cmd
