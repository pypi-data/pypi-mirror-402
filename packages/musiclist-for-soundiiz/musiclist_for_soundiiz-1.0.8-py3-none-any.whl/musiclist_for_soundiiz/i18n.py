"""Internationalization (i18n) support for MusicList for Soundiiz."""

# Translation dictionaries for supported languages
TRANSLATIONS = {
    "en": {
        # Window
        "window_title": "MusicList for Soundiiz",
        "subtitle": "Extract music metadata and create playlists",
        
        # Sections
        "input_directories": "📁 Input Directories",
        "output": "📄 Output",
        "options": "⚙️ Options",
        "progress": "📊 Progress",
        
        # Input section
        "add_directory": "Add Directory",
        "remove_selected": "Remove Selected",
        "clear_all": "Clear All",
        "tip_add_directory": "💡 Tip: Click 'Add Directory' or drag folders here",
        
        # Output section
        "output_file": "Output File:",
        "browse": "Browse",
        "format": "Format:",
        "max_songs": "Max songs per file:",
        
        # Options
        "scan_recursive": "Scan subdirectories recursively",
        "detect_duplicates": "Detect duplicates",
        "remove_duplicates": "Remove duplicates",
        "strategy": "Strategy:",
        
        # Buttons
        "process_files": "🚀 Process Files",
        "clear_log": "Clear Log",
        "help": "Help",
        "about": "About",
        "language": "Language:",
        
        # Status
        "ready": "Ready",
        "ready_to_process": "Ready to process music files",
        "processing": "Processing...",
        "completed": "Completed successfully!",
        "error_occurred": "Error occurred",
        
        # Messages
        "info": "Info",
        "warning": "Warning",
        "error": "Error",
        "success": "Success",
        "already_added": "Directory already added",
        "processing_in_progress": "Processing already in progress!",
        "no_input_dir": "Please add at least one input directory",
        "no_output_file": "Please specify an output file",
        "no_files_found": "No music files found in selected directories",
        "success_message": "Successfully processed {count} songs!\\n\\nOutput: {file}",
        "error_message": "An error occurred:\\n{error}",
        
        # Log messages
        "added": "Added:",
        "removed": "Removed:",
        "cleared": "Cleared all directories",
        "starting_processing": "Starting processing...",
        "scanning": "Scanning:",
        "found_files": "Found {count} files",
        "total_found": "✓ Total files found: {count}",
        "processing_file": "Processing file {current}/{total}",
        "estimated_time": "Estimated time remaining: {time}",
        "no_music_files": "⚠️  No music files found!",
        "checking_duplicates": "\\nChecking for duplicates...",
        "found_duplicates": "⚠️  Found {groups} duplicate groups ({total} total files)",
        "removed_duplicates": "✓ Removed {count} duplicates",
        "unique_remaining": "✓ {count} unique songs remaining",
        "no_duplicates": "✓ No duplicates found",
        "exporting_to": "\\nExporting to {format}...",
        "export_completed": "✓ Export completed: {file}",
        
        # Help
        "help_title": "MusicList for Soundiiz - Help",
        "help_text": """1. Add Directories:
   Click 'Add Directory' to select music folders.
   You can add multiple directories.

2. Choose Output:
   Select output file and format (CSV, JSON, M3U, TXT).

3. Options:
   - Recursive: Scan subdirectories
   - Detect/Remove Duplicates: Find duplicate songs
   - Max songs: Split into multiple files
   
4. Process:
   Click 'Process Files' to start.
   
Supported Formats:
AAC, AU, FLAC, MP3, OGG, M4A, WAV, WMA

For more info, visit:
https://github.com/lucmuss/musiclist-for-soundiiz""",
        
        # About
        "about_title": "About",
        "about_text": """MusicList for Soundiiz
Version 1.0.0

Professional tool for extracting music metadata
and creating Soundiiz-compatible playlists.

Features:
• Multi-format support
• Duplicate detection
• Batch processing
• Multiple export formats
• Multi-language support

Created with ❤️ for the music community

GitHub: github.com/lucmuss/musiclist-for-soundiiz
License: MIT""",
    },
    
    "de": {
        # Window
        "window_title": "MusicList für Soundiiz",
        "subtitle": "Musik-Metadaten extrahieren und Playlists erstellen",
        
        # Sections
        "input_directories": "📁 Eingabe-Verzeichnisse",
        "output": "📄 Ausgabe",
        "options": "⚙️ Optionen",
        "progress": "📊 Fortschritt",
        
        # Input section
        "add_directory": "Verzeichnis hinzufügen",
        "remove_selected": "Ausgewählte entfernen",
        "clear_all": "Alle löschen",
        "tip_add_directory": "💡 Tipp: Klicke 'Verzeichnis hinzufügen' oder ziehe Ordner hierher",
        
        # Output section
        "output_file": "Ausgabedatei:",
        "browse": "Durchsuchen",
        "format": "Format:",
        "max_songs": "Max. Songs pro Datei:",
        
        # Options
        "scan_recursive": "Unterverzeichnisse rekursiv scannen",
        "detect_duplicates": "Duplikate erkennen",
        "remove_duplicates": "Duplikate entfernen",
        "strategy": "Strategie:",
        
        # Buttons
        "process_files": "🚀 Dateien verarbeiten",
        "clear_log": "Log löschen",
        "help": "Hilfe",
        "about": "Über",
        "language": "Sprache:",
        
        # Status
        "ready": "Bereit",
        "ready_to_process": "Bereit zur Verarbeitung von Musikdateien",
        "processing": "Verarbeite...",
        "completed": "Erfolgreich abgeschlossen!",
        "error_occurred": "Fehler aufgetreten",
        
        # Messages
        "info": "Info",
        "warning": "Warnung",
        "error": "Fehler",
        "success": "Erfolg",
        "already_added": "Verzeichnis bereits hinzugefügt",
        "processing_in_progress": "Verarbeitung bereits im Gang!",
        "no_input_dir": "Bitte füge mindestens ein Eingabeverzeichnis hinzu",
        "no_output_file": "Bitte gib eine Ausgabedatei an",
        "no_files_found": "Keine Musikdateien in den ausgewählten Verzeichnissen gefunden",
        "success_message": "Erfolgreich {count} Songs verarbeitet!\\n\\nAusgabe: {file}",
        "error_message": "Ein Fehler ist aufgetreten:\\n{error}",
        
        # Log messages
        "added": "Hinzugefügt:",
        "removed": "Entfernt:",
        "cleared": "Alle Verzeichnisse gelöscht",
        "starting_processing": "Starte Verarbeitung...",
        "scanning": "Scanne:",
        "found_files": "{count} Dateien gefunden",
        "total_found": "✓ Insgesamt gefunden: {count}",
        "no_music_files": "⚠️  Keine Musikdateien gefunden!",
        "checking_duplicates": "\\nPrüfe auf Duplikate...",
        "found_duplicates": "⚠️  {groups} Duplikat-Gruppen gefunden ({total} Dateien insgesamt)",
        "removed_duplicates": "✓ {count} Duplikate entfernt",
        "unique_remaining": "✓ {count} eindeutige Songs verbleiben",
        "no_duplicates": "✓ Keine Duplikate gefunden",
        "exporting_to": "\\nExportiere nach {format}...",
        "export_completed": "✓ Export abgeschlossen: {file}",
        
        # Help
        "help_title": "MusicList für Soundiiz - Hilfe",
        "help_text": """1. Verzeichnisse hinzufügen:
   Klicke 'Verzeichnis hinzufügen' um Musikordner auszuwählen.
   Du kannst mehrere Verzeichnisse hinzufügen.

2. Ausgabe wählen:
   Wähle Ausgabedatei und Format (CSV, JSON, M3U, TXT).

3. Optionen:
   - Rekursiv: Unterverzeichnisse scannen
   - Duplikate erkennen/entfernen: Doppelte Songs finden
   - Max Songs: In mehrere Dateien aufteilen
   
4. Verarbeiten:
   Klicke 'Dateien verarbeiten' zum Starten.
   
Unterstützte Formate:
AAC, AU, FLAC, MP3, OGG, M4A, WAV, WMA

Mehr Infos:
https://github.com/lucmuss/musiclist-for-soundiiz""",
        
        # About
        "about_title": "Über",
        "about_text": """MusicList für Soundiiz
Version 1.0.0

Professionelles Tool zum Extrahieren von Musik-Metadaten
und Erstellen von Soundiiz-kompatiblen Playlists.

Features:
• Multi-Format-Unterstützung
• Duplikat-Erkennung
• Batch-Verarbeitung
• Mehrere Export-Formate
• Mehrsprachig

Erstellt mit ❤️ für die Musik-Community

GitHub: github.com/lucmuss/musiclist-for-soundiiz
Lizenz: MIT""",
    },
    
    "es": {
        "window_title": "MusicList para Soundiiz",
        "subtitle": "Extraer metadatos de música y crear listas de reproducción",
        "input_directories": "📁 Directorios de entrada",
        "output": "📄 Salida",
        "options": "⚙️ Opciones",
        "progress": "📊 Progreso",
        "add_directory": "Añadir directorio",
        "remove_selected": "Eliminar seleccionados",
        "clear_all": "Limpiar todo",
        "tip_add_directory": "💡 Consejo: Haz clic en 'Añadir directorio' o arrastra carpetas aquí",
        "output_file": "Archivo de salida:",
        "browse": "Examinar",
        "format": "Formato:",
        "max_songs": "Máx. canciones por archivo:",
        "scan_recursive": "Escanear subdirectorios recursivamente",
        "detect_duplicates": "Detectar duplicados",
        "remove_duplicates": "Eliminar duplicados",
        "strategy": "Estrategia:",
        "process_files": "🚀 Procesar archivos",
        "clear_log": "Limpiar registro",
        "help": "Ayuda",
        "about": "Acerca de",
        "language": "Idioma:",
        "ready": "Listo",
        "ready_to_process": "Listo para procesar archivos de música",
        "processing": "Procesando...",
        "completed": "¡Completado con éxito!",
        "success_message": "¡{count} canciones procesadas con éxito!\\n\\nSalida: {file}",
    },
    
    "fr": {
        "window_title": "MusicList pour Soundiiz",
        "subtitle": "Extraire les métadonnées musicales et créer des listes de lecture",
        "input_directories": "📁 Répertoires d'entrée",
        "output": "📄 Sortie",
        "options": "⚙️ Options",
        "progress": "📊 Progrès",
        "add_directory": "Ajouter un répertoire",
        "remove_selected": "Supprimer sélectionnés",
        "clear_all": "Tout effacer",
        "tip_add_directory": "💡 Conseil : Cliquez sur 'Ajouter un répertoire' ou glissez des dossiers ici",
        "output_file": "Fichier de sortie :",
        "browse": "Parcourir",
        "format": "Format :",
        "max_songs": "Max. chansons par fichier :",
        "scan_recursive": "Scanner les sous-répertoires récursivement",
        "detect_duplicates": "Détecter les doublons",
        "remove_duplicates": "Supprimer les doublons",
        "strategy": "Stratégie :",
        "process_files": "🚀 Traiter les fichiers",
        "clear_log": "Effacer le journal",
        "help": "Aide",
        "about": "À propos",
        "language": "Langue :",
        "ready": "Prêt",
        "ready_to_process": "Prêt à traiter les fichiers musicaux",
        "processing": "Traitement...",
        "completed": "Terminé avec succès !",
        "success_message": "{count} chansons traitées avec succès !\\n\\nSortie : {file}",
    },
    
    "pt": {
        "window_title": "MusicList para Soundiiz",
        "subtitle": "Extrair metadados de música e criar playlists",
        "input_directories": "📁 Diretórios de entrada",
        "output": "📄 Saída",
        "options": "⚙️ Opções",
        "progress": "📊 Progresso",
        "add_directory": "Adicionar diretório",
        "remove_selected": "Remover selecionados",
        "clear_all": "Limpar tudo",
        "tip_add_directory": "💡 Dica: Clique em 'Adicionar diretório' ou arraste pastas aqui",
        "output_file": "Arquivo de saída:",
        "browse": "Procurar",
        "format": "Formato:",
        "max_songs": "Máx. músicas por arquivo:",
        "scan_recursive": "Escanear subdiretórios recursivamente",
        "detect_duplicates": "Detectar duplicados",
        "remove_duplicates": "Remover duplicados",
        "strategy": "Estratégia:",
        "process_files": "🚀 Processar arquivos",
        "clear_log": "Limpar log",
        "help": "Ajuda",
        "about": "Sobre",
        "language": "Idioma:",
        "ready": "Pronto",
        "ready_to_process": "Pronto para processar arquivos de música",
        "processing": "Processando...",
        "completed": "Concluído com sucesso!",
        "success_message": "{count} músicas processadas com sucesso!\\n\\nSaída: {file}",
    },
    
    "ja": {
        "window_title": "MusicList for Soundiiz",
        "subtitle": "音楽メタデータの抽出とプレイリストの作成",
        "input_directories": "📁 入力ディレクトリ",
        "output": "📄 出力",
        "options": "⚙️ オプション",
        "progress": "📊 進行状況",
        "add_directory": "ディレクトリを追加",
        "remove_selected": "選択を削除",
        "clear_all": "すべてクリア",
        "output_file": "出力ファイル：",
        "browse": "参照",
        "format": "形式：",
        "max_songs": "ファイルあたりの最大曲数：",
        "scan_recursive": "サブディレクトリを再帰的にスキャン",
        "detect_duplicates": "重複を検出",
        "remove_duplicates": "重複を削除",
        "strategy": "戦略：",
        "process_files": "🚀 ファイルを処理",
        "clear_log": "ログをクリア",
        "help": "ヘルプ",
        "about": "について",
        "language": "言語：",
        "ready": "準備完了",
        "ready_to_process": "音楽ファイルの処理準備完了",
        "processing": "処理中...",
        "completed": "正常に完了しました！",
        "success_message": "{count}曲が正常に処理されました！\\n\\n出力：{file}",
    },
    
    "zh": {
        "window_title": "MusicList for Soundiiz",
        "subtitle": "提取音乐元数据并创建播放列表",
        "input_directories": "📁 输入目录",
        "output": "📄 输出",
        "options": "⚙️ 选项",
        "progress": "📊 进度",
        "add_directory": "添加目录",
        "remove_selected": "删除选中",
        "clear_all": "全部清除",
        "output_file": "输出文件：",
        "browse": "浏览",
        "format": "格式：",
        "max_songs": "每个文件最大歌曲数：",
        "scan_recursive": "递归扫描子目录",
        "detect_duplicates": "检测重复",
        "remove_duplicates": "删除重复",
        "strategy": "策略：",
        "process_files": "🚀 处理文件",
        "clear_log": "清除日志",
        "help": "帮助",
        "about": "关于",
        "language": "语言：",
        "ready": "就绪",
        "ready_to_process": "准备处理音乐文件",
        "processing": "处理中...",
        "completed": "成功完成！",
        "success_message": "成功处理了{count}首歌曲！\\n\\n输出：{file}",
    },
    
    "it": {
        "window_title": "MusicList per Soundiiz",
        "subtitle": "Estrai metadati musicali e crea playlist",
        "input_directories": "📁 Directory di input",
        "output": "📄 Output",
        "options": "⚙️ Opzioni",
        "progress": "📊 Progresso",
        "add_directory": "Aggiungi directory",
        "remove_selected": "Rimuovi selezionati",
        "clear_all": "Cancella tutto",
        "tip_add_directory": "💡 Suggerimento: Fai clic su 'Aggiungi directory' o trascina cartelle qui",
        "output_file": "File di output:",
        "browse": "Sfoglia",
        "format": "Formato:",
        "max_songs": "Max canzoni per file:",
        "scan_recursive": "Scansiona sottodirectory ricorsivamente",
        "detect_duplicates": "Rileva duplicati",
        "remove_duplicates": "Rimuovi duplicati",
        "strategy": "Strategia:",
        "process_files": "🚀 Elabora file",
        "clear_log": "Cancella log",
        "help": "Aiuto",
        "about": "Informazioni",
        "language": "Lingua:",
        "ready": "Pronto",
        "ready_to_process": "Pronto per elaborare file musicali",
        "processing": "Elaborazione...",
        "completed": "Completato con successo!",
        "success_message": "Elaborate {count} canzoni con successo!\\n\\nOutput: {file}",
    },
    
    "nl": {
        "window_title": "MusicList voor Soundiiz",
        "subtitle": "Muziekmetadata extraheren en afspeellijsten maken",
        "input_directories": "📁 Invoermappen",
        "output": "📄 Uitvoer",
        "options": "⚙️ Opties",
        "progress": "📊 Voortgang",
        "add_directory": "Map toevoegen",
        "remove_selected": "Geselecteerde verwijderen",
        "clear_all": "Alles wissen",
        "tip_add_directory": "💡 Tip: Klik op 'Map toevoegen' of sleep mappen hierheen",
        "output_file": "Uitvoerbestand:",
        "browse": "Bladeren",
        "format": "Formaat:",
        "max_songs": "Max. nummers per bestand:",
        "scan_recursive": "Submappen recursief scannen",
        "detect_duplicates": "Duplicaten detecteren",
        "remove_duplicates": "Duplicaten verwijderen",
        "strategy": "Strategie:",
        "process_files": "🚀 Bestanden verwerken",
        "clear_log": "Log wissen",
        "help": "Help",
        "about": "Over",
        "language": "Taal:",
        "ready": "Gereed",
        "ready_to_process": "Gereed om muziekbestanden te verwerken",
        "processing": "Verwerken...",
        "completed": "Met succes voltooid!",
        "success_message": "{count} nummers succesvol verwerkt!\\n\\nUitvoer: {file}",
    },
    
    "ru": {
        "window_title": "MusicList для Soundiiz",
        "subtitle": "Извлечение музыкальных метаданных и создание плейлистов",
        "input_directories": "📁 Входные каталоги",
        "output": "📄 Вывод",
        "options": "⚙️ Настройки",
        "progress": "📊 Прогресс",
        "add_directory": "Добавить каталог",
        "remove_selected": "Удалить выбранное",
        "clear_all": "Очистить всё",
        "tip_add_directory": "💡 Совет: Нажмите 'Добавить каталог' или перетащите папки сюда",
        "output_file": "Выходной файл:",
        "browse": "Обзор",
        "format": "Формат:",
        "max_songs": "Макс. песен на файл:",
        "scan_recursive": "Сканировать подкаталоги рекурсивно",
        "detect_duplicates": "Обнаружить дубликаты",
        "remove_duplicates": "Удалить дубликаты",
        "strategy": "Стратегия:",
        "process_files": "🚀 Обработать файлы",
        "clear_log": "Очистить журнал",
        "help": "Помощь",
        "about": "О программе",
        "language": "Язык:",
        "ready": "Готово",
        "ready_to_process": "Готово к обработке музыкальных файлов",
        "processing": "Обработка...",
        "completed": "Успешно завершено!",
        "success_message": "Успешно обработано {count} песен!\\n\\nВывод: {file}",
    },
    
    "ko": {
        "window_title": "MusicList for Soundiiz",
        "subtitle": "음악 메타데이터 추출 및 재생목록 생성",
        "input_directories": "📁 입력 디렉토리",
        "output": "📄 출력",
        "options": "⚙️ 옵션",
        "progress": "📊 진행 상황",
        "add_directory": "디렉토리 추가",
        "remove_selected": "선택 항목 제거",
        "clear_all": "모두 지우기",
        "tip_add_directory": "💡 팁: '디렉토리 추가'를 클릭하거나 폴더를 여기로 드래그하세요",
        "output_file": "출력 파일:",
        "browse": "찾아보기",
        "format": "형식:",
        "max_songs": "파일당 최대 곡 수:",
        "scan_recursive": "하위 디렉토리 재귀적으로 스캔",
        "detect_duplicates": "중복 감지",
        "remove_duplicates": "중복 제거",
        "strategy": "전략:",
        "process_files": "🚀 파일 처리",
        "clear_log": "로그 지우기",
        "help": "도움말",
        "about": "정보",
        "language": "언어:",
        "ready": "준비됨",
        "ready_to_process": "음악 파일 처리 준비 완료",
        "processing": "처리 중...",
        "completed": "성공적으로 완료!",
        "success_message": "{count}곡이 성공적으로 처리되었습니다!\\n\\n출력: {file}",
    },
    
    "ar": {
        "window_title": "MusicList لـ Soundiiz",
        "subtitle": "استخراج بيانات الموسيقى وإنشاء قوائم التشغيل",
        "input_directories": "📁 مجلدات الإدخال",
        "output": "📄 الإخراج",
        "options": "⚙️ الخيارات",
        "progress": "📊 التقدم",
        "add_directory": "إضافة مجلد",
        "remove_selected": "إزالة المحدد",
        "clear_all": "مسح الكل",
        "tip_add_directory": "💡 نصيحة: انقر فوق 'إضافة مجلد' أو اسحب المجلدات هنا",
        "output_file": "ملف الإخراج:",
        "browse": "استعراض",
        "format": "التنسيق:",
        "max_songs": "الحد الأقصى للأغاني لكل ملف:",
        "scan_recursive": "فحص المجلدات الفرعية بشكل متكرر",
        "detect_duplicates": "كشف التكرارات",
        "remove_duplicates": "إزالة التكرارات",
        "strategy": "الاستراتيجية:",
        "process_files": "🚀 معالجة الملفات",
        "clear_log": "مسح السجل",
        "help": "مساعدة",
        "about": "حول",
        "language": "اللغة:",
        "ready": "جاهز",
        "ready_to_process": "جاهز لمعالجة ملفات الموسيقى",
        "processing": "جاري المعالجة...",
        "completed": "اكتمل بنجاح!",
        "success_message": "تمت معالجة {count} أغنية بنجاح!\\n\\nالإخراج: {file}",
    },
}

# Language names for display
LANGUAGE_NAMES = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "pt": "Português",
    "it": "Italiano",
    "nl": "Nederlands",
    "ru": "Русский",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
    "ar": "العربية",
}


class I18n:
    """Simple internationalization class."""
    
    def __init__(self, language="en"):
        """Initialize with default language."""
        self.set_language(language)
    
    def set_language(self, language):
        """Set the current language."""
        if language in TRANSLATIONS:
            self.current_lang = language
            self.trans = TRANSLATIONS[language]
        else:
            self.current_lang = "en"
            self.trans = TRANSLATIONS["en"]
    
    def get(self, key, **kwargs):
        """Get translated string, fall back to English if not found."""
        # Try current language
        text = self.trans.get(key)
        
        # Fall back to English
        if text is None:
            text = TRANSLATIONS["en"].get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
                
        return text
    
    def __call__(self, key, **kwargs):
        """Shortcut for get()."""
        return self.get(key, **kwargs)
