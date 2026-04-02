#!/bin/bash

# Ambil lokasi absolut dari folder tempat script ini berada
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# Pindah ke direktori scripts agar path di orchestrator.py tetap benar
cd "$PROJECT_DIR/scripts"

# Jalankan orchestrator dengan argument dari user
# Menggunakan python3 (pastikan sudah install requirements)
python3 orchestrator.py "$1"
