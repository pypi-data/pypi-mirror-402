#!/bin/bash
# Beispiel-Verwendung von MusicList for Soundiiz

# 1. Einfacher CSV-Export
echo "=== Beispiel 1: Einfacher CSV-Export ==="
musiclist-for-soundiiz -i ~/Music -o soundiiz_playlist.csv

# 2. Nur MP3 und FLAC Dateien
echo -e "\n=== Beispiel 2: Nur MP3 und FLAC ==="
musiclist-for-soundiiz -i ~/Music -e .mp3 .flac -o high_quality.csv

# 3. JSON Export mit allen Metadaten
echo -e "\n=== Beispiel 3: JSON Export ==="
musiclist-for-soundiiz -i ~/Music -o music_backup.json -f json

# 4. M3U Playlist erstellen
echo -e "\n=== Beispiel 4: M3U Playlist ==="
musiclist-for-soundiiz -i ~/Music -o my_playlist.m3u -f m3u

# 5. Verbose Mode für Debugging
echo -e "\n=== Beispiel 5: Verbose Mode ==="
musiclist-for-soundiiz -i ~/Music -o output.csv -v

# 6. Nicht-rekursiv (nur aktuelles Verzeichnis)
echo -e "\n=== Beispiel 6: Nicht-rekursiv ==="
musiclist-for-soundiiz -i ~/Music/Favorites --no-recursive -o favorites.csv

# 7. Große Bibliothek mit CSV-Aufteilung
echo -e "\n=== Beispiel 7: Große Bibliothek (max 200 Songs pro Datei) ==="
musiclist-for-soundiiz -i ~/Music -o playlist.csv --max-songs-per-file 200

# 8. Stilles Ausführen (nur Fehler)
echo -e "\n=== Beispiel 8: Quiet Mode ==="
musiclist-for-soundiiz -i ~/Music -o output.csv -q

echo -e "\n✓ Alle Beispiele abgeschlossen!"
