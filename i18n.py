"""
Traduzioni dell'interfaccia. La chiave è il testo italiano; ogni lingua ha la sua versione.
Per aggiungere una lingua: aggiungi il codice a LANGUAGES e una colonna in ogni voce di TEXTS.
Testi senza traduzione restano in italiano.
"""

LANGUAGES = [("it", "Italiano"), ("en", "English"), ("fr", "Français"), ("es", "Español"), ("zh", "中文")]
QT_LOCALES = {"it": "it_IT", "en": "en_US", "fr": "fr_FR", "es": "es_ES", "zh": "zh_CN"}

_lang = "it"


def set_language(code):
    global _lang
    _lang = code if code in dict(LANGUAGES) else "it"


def language():
    return _lang


def _(text, **kw):
    """Traduce `text` nella lingua corrente e riempie i segnaposto {nome}."""
    row = TEXTS.get(text)
    out = row.get(_lang, text) if row else text
    return out.format(**kw) if kw else out


# fmt: off
TEXTS = {
    # --- generali
    "(senza titolo)": {"en": "(untitled)", "fr": "(sans titre)", "es": "(sin título)", "zh": "（无标题）"},
    "tutto il giorno": {"en": "all day", "fr": "toute la journée", "es": "todo el día", "zh": "全天"},
    "Espandi": {"en": "Expand", "fr": "Développer", "es": "Expandir", "zh": "展开"},
    "Riduci": {"en": "Collapse", "fr": "Réduire", "es": "Contraer", "zh": "收起"},
    "Aggiorna": {"en": "Refresh", "fr": "Actualiser", "es": "Actualizar", "zh": "刷新"},
    "Elimina": {"en": "Delete", "fr": "Supprimer", "es": "Eliminar", "zh": "删除"},
    "Non trovo «{path}»": {"en": "Can't find “{path}”", "fr": "Introuvable : « {path} »",
                           "es": "No encuentro «{path}»", "zh": "找不到“{path}”"},
    "Dati non disponibili": {"en": "No data available", "fr": "Données indisponibles",
                             "es": "Datos no disponibles", "zh": "暂无数据"},

    # --- app / lanciatore
    "App": {"en": "Apps", "fr": "Apps", "es": "Apps", "zh": "应用"},
    "Tocca una tua app per modificarla": {"en": "Tap one of your apps to edit it",
                                          "fr": "Touchez une de vos apps pour la modifier",
                                          "es": "Toca una de tus apps para editarla", "zh": "点击你的应用以编辑"},
    "+ Programma": {"en": "+ Program", "fr": "+ Programme", "es": "+ Programa", "zh": "+ 程序"},
    "+ Link": {"en": "+ Link", "fr": "+ Lien", "es": "+ Enlace", "zh": "+ 链接"},
    "Aggiungi un programma o un file": {"en": "Add a program or a file", "fr": "Ajouter un programme ou un fichier",
                                        "es": "Añadir un programa o un archivo", "zh": "添加程序或文件"},
    "Aggiungi un sito o un link": {"en": "Add a website or a link", "fr": "Ajouter un site ou un lien",
                                   "es": "Añadir un sitio o un enlace", "zh": "添加网站或链接"},
    "Nessuna app. Premi la rotella ⚙ in alto per aggiungerne.": {
        "en": "No apps yet. Press the ⚙ gear at the top to add some.",
        "fr": "Aucune app. Appuyez sur la roue ⚙ en haut pour en ajouter.",
        "es": "No hay apps. Pulsa el engranaje ⚙ arriba para añadir.",
        "zh": "还没有应用。点击顶部的 ⚙ 添加。"},
    "{name}: non trovato su questo computer": {"en": "{name}: not found on this computer",
                                               "fr": "{name} : introuvable sur cet ordinateur",
                                               "es": "{name}: no encontrado en este equipo",
                                               "zh": "{name}：此电脑上未找到"},
    "Non trovo {name} su questo computer.": {"en": "Can't find {name} on this computer.",
                                             "fr": "{name} est introuvable sur cet ordinateur.",
                                             "es": "No encuentro {name} en este equipo.",
                                             "zh": "此电脑上找不到 {name}。"},
    "Apri {name}": {"en": "Open {name}", "fr": "Ouvrir {name}", "es": "Abrir {name}", "zh": "打开 {name}"},
    "Scegli cosa aprire": {"en": "Choose what to open", "fr": "Choisissez quoi ouvrir", "es": "Elige qué abrir",
                           "zh": "选择要打开的项目"},
    "non trovato": {"en": "not found", "fr": "introuvable", "es": "no encontrado", "zh": "未找到"},
    "Non riesco ad aprirlo.": {"en": "Can't open it.", "fr": "Impossible de l’ouvrir.", "es": "No puedo abrirlo.",
                               "zh": "无法打开。"},
    "Sposta prima": {"en": "Move earlier", "fr": "Déplacer avant", "es": "Mover antes", "zh": "前移"},
    "Sposta dopo": {"en": "Move later", "fr": "Déplacer après", "es": "Mover después", "zh": "后移"},
    "Rinomina…": {"en": "Rename…", "fr": "Renommer…", "es": "Renombrar…", "zh": "重命名…"},
    "Rinomina": {"en": "Rename", "fr": "Renommer", "es": "Renombrar", "zh": "重命名"},
    "Rimuovi": {"en": "Remove", "fr": "Retirer", "es": "Quitar", "zh": "移除"},
    "Nome:": {"en": "Name:", "fr": "Nom :", "es": "Nombre:", "zh": "名称："},
    "Nome": {"en": "Name", "fr": "Nom", "es": "Nombre", "zh": "名称"},
    "Come lo chiamo?": {"en": "What should I call it?", "fr": "Quel nom lui donner ?", "es": "¿Cómo lo llamo?",
                        "zh": "叫什么名字？"},
    "Scegli un'app": {"en": "Choose an app", "fr": "Choisir une app", "es": "Elige una app", "zh": "选择应用"},
    "Scegli un file": {"en": "Choose a file", "fr": "Choisir un fichier", "es": "Elige un archivo", "zh": "选择文件"},
    "Scegli il programma (anche collegamenti .lnk)": {
        "en": "Choose the program (.lnk shortcuts work too)", "fr": "Choisir le programme (raccourcis .lnk acceptés)",
        "es": "Elige el programa (también accesos .lnk)", "zh": "选择程序（也支持 .lnk 快捷方式）"},
    "Sito o link": {"en": "Website or link", "fr": "Site ou lien", "es": "Sitio o enlace", "zh": "网站或链接"},
    "Indirizzo (es. https://mail.google.com, spotify:, discord://, steam://open/main):": {
        "en": "Address (e.g. https://mail.google.com, spotify:, discord://, steam://open/main):",
        "fr": "Adresse (ex. https://mail.google.com, spotify:, discord://, steam://open/main) :",
        "es": "Dirección (p. ej. https://mail.google.com, spotify:, discord://, steam://open/main):",
        "zh": "地址（例如 https://mail.google.com、spotify:、discord://、steam://open/main）："},

    # --- S&P 500
    "Scarico i dati…": {"en": "Downloading data…", "fr": "Téléchargement…", "es": "Descargando datos…",
                        "zh": "正在下载数据…"},
    "3 giorni": {"en": "3 days", "fr": "3 jours", "es": "3 días", "zh": "3 天"},
    "Questo mese": {"en": "This month", "fr": "Ce mois-ci", "es": "Este mes", "zh": "本月"},
    "1 anno": {"en": "1 year", "fr": "1 an", "es": "1 año", "zh": "1 年"},
    "5 anni": {"en": "5 years", "fr": "5 ans", "es": "5 años", "zh": "5 年"},
    "punti": {"en": "points", "fr": "points", "es": "puntos", "zh": "点"},
    "Mercati": {"en": "Markets", "fr": "Marchés", "es": "Mercados", "zh": "市场"},
    "Oro": {"en": "Gold", "fr": "Or", "es": "Oro", "zh": "黄金"},
    "Nomi nelle schede": {"en": "Tab labels", "fr": "Noms des onglets", "es": "Nombres de las pestañas",
                          "zh": "标签名称"},
    "Sigla": {"en": "Symbol", "fr": "Symbole", "es": "Símbolo", "zh": "代码"},
    "Materie prime": {"en": "Commodities", "fr": "Matières premières", "es": "Materias primas", "zh": "大宗商品"},
    "S&P 500 senza tech": {"en": "S&P 500 ex-tech", "fr": "S&P 500 hors tech", "es": "S&P 500 sin tecnología",
                           "zh": "标普500（不含科技）"},
    "Cina (Shanghai)": {"en": "China (Shanghai)", "fr": "Chine (Shanghai)", "es": "China (Shanghái)", "zh": "中国（上证）"},
    "Paesi emergenti": {"en": "Emerging markets", "fr": "Marchés émergents", "es": "Mercados emergentes",
                        "zh": "新兴市场"},
    "Nessun titolo scelto. Premi la rotella ⚙ e scegline uno in «Mercati».": {
        "en": "No instrument chosen. Press the ⚙ gear and pick one under “Markets”.",
        "fr": "Aucun titre choisi. Appuyez sur la roue ⚙ et choisissez-en un dans « Marchés ».",
        "es": "Ningún valor elegido. Pulsa la rueda ⚙ y elige uno en «Mercados».",
        "zh": "未选择任何品种。点击 ⚙ 齿轮，在“市场”中选择。"},
    "Fonte: {src}, aggiornato alle {time}": {"en": "Source: {src}, updated at {time}",
                                             "fr": "Source : {src}, mis à jour à {time}",
                                             "es": "Fuente: {src}, actualizado a las {time}",
                                             "zh": "来源：{src}，更新于 {time}"},
    "Non riesco a scaricare {name}. Controlla la connessione; riprovo tra 15 minuti.": {
        "en": "Can't download {name}. Check your connection; retrying in 15 minutes.",
        "fr": "Impossible de télécharger {name}. Vérifiez la connexion ; nouvel essai dans 15 minutes.",
        "es": "No puedo descargar {name}. Revisa la conexión; reintento en 15 minutos.",
        "zh": "无法下载 {name}。请检查网络；15 分钟后重试。"},

    # --- aggiornamenti e ripristino
    "Cerca aggiornamenti": {"en": "Check for updates", "fr": "Rechercher des mises à jour",
                            "es": "Buscar actualizaciones", "zh": "检查更新"},
    "Controlla se c’è una nuova versione su GitHub": {"en": "Check GitHub for a new version",
                                                      "fr": "Vérifier s’il existe une nouvelle version sur GitHub",
                                                      "es": "Comprobar si hay una nueva versión en GitHub",
                                                      "zh": "在 GitHub 上检查新版本"},
    "Ripristina impostazioni": {"en": "Restore settings", "fr": "Rétablir les réglages",
                                "es": "Restablecer ajustes", "zh": "恢复默认设置"},
    "Torna alle impostazioni predefinite (note, task e app restano)": {
        "en": "Go back to the default settings (notes, tasks and apps are kept)",
        "fr": "Revenir aux réglages par défaut (notes, tâches et apps sont conservées)",
        "es": "Volver a los ajustes predeterminados (notas, tareas y apps se conservan)",
        "zh": "恢复默认设置（保留便签、任务和应用）"},
    "Ripristinare le impostazioni predefinite?\nNote, task, app e calendari non vengono toccati.": {
        "en": "Restore the default settings?\nNotes, tasks, apps and calendars are not touched.",
        "fr": "Rétablir les réglages par défaut ?\nLes notes, tâches, apps et agendas ne sont pas modifiés.",
        "es": "¿Restablecer los ajustes predeterminados?\nNotas, tareas, apps y calendarios no se tocan.",
        "zh": "恢复默认设置？\n便签、任务、应用和日历不会改变。"},
    "Scarica e installa la nuova versione": {"en": "Download and install the new version",
                                             "fr": "Télécharger et installer la nouvelle version",
                                             "es": "Descargar e instalar la nueva versión", "zh": "下载并安装新版本"},
    "⬆ Aggiorna a {v}": {"en": "⬆ Update to {v}", "fr": "⬆ Mettre à jour vers {v}", "es": "⬆ Actualizar a {v}",
                         "zh": "⬆ 更新到 {v}"},
    "Hai già l’ultima versione ({v}).": {"en": "You already have the latest version ({v}).",
                                         "fr": "Vous avez déjà la dernière version ({v}).",
                                         "es": "Ya tienes la última versión ({v}).", "zh": "已是最新版本（{v}）。"},
    "Non riesco a controllare gli aggiornamenti.": {"en": "Can't check for updates.",
                                                    "fr": "Impossible de vérifier les mises à jour.",
                                                    "es": "No puedo comprobar las actualizaciones.", "zh": "无法检查更新。"},
    "Scaricare e installare {app} {v}? Il programma si riavvia da solo.": {
        "en": "Download and install {app} {v}? The app restarts by itself.",
        "fr": "Télécharger et installer {app} {v} ? L’app redémarre toute seule.",
        "es": "¿Descargar e instalar {app} {v}? La app se reinicia sola.",
        "zh": "下载并安装 {app} {v}？程序会自动重启。"},
    "Questa è una build personalizzata: gli aggiornamenti automatici sono disattivati.": {
        "en": "This is a custom build: automatic updates are turned off.",
        "fr": "Ceci est une version personnalisée : les mises à jour automatiques sont désactivées.",
        "es": "Esta es una versión personalizada: las actualizaciones automáticas están desactivadas.",
        "zh": "这是自行编译的版本：已关闭自动更新。"},
    "Scarico…": {"en": "Downloading…", "fr": "Téléchargement…", "es": "Descargando…", "zh": "正在下载…"},
    "Aggiornamento non riuscito.": {"en": "Update failed.", "fr": "Échec de la mise à jour.",
                                    "es": "La actualización falló.", "zh": "更新失败。"},
    "Download incompleto.": {"en": "Incomplete download.", "fr": "Téléchargement incomplet.",
                             "es": "Descarga incompleta.", "zh": "下载不完整。"},

    # --- calendario
    "Calendario": {"en": "Calendar", "fr": "Calendrier", "es": "Calendario", "zh": "日历"},
    "Nuovo evento in Google Calendar": {"en": "New event in Google Calendar",
                                        "fr": "Nouvel événement dans Google Agenda",
                                        "es": "Nuevo evento en Google Calendar", "zh": "在 Google 日历中新建活动"},
    "Per vedere i tuoi eventi premi la rotella <b>⚙</b> in alto e poi <b>Collega Google Calendar</b>.": {
        "en": "To see your events press the <b>⚙</b> gear at the top, then <b>Connect Google Calendar</b>.",
        "fr": "Pour voir vos événements, appuyez sur la roue <b>⚙</b> en haut, puis <b>Connecter Google Agenda</b>.",
        "es": "Para ver tus eventos pulsa el engranaje <b>⚙</b> arriba y luego <b>Conectar Google Calendar</b>.",
        "zh": "要查看活动，请点击顶部的 <b>⚙</b>，然后选择<b>连接 Google 日历</b>。"},
    "Collega Google Calendar": {"en": "Connect Google Calendar", "fr": "Connecter Google Agenda",
                                "es": "Conectar Google Calendar", "zh": "连接 Google 日历"},
    "ISTRUZIONI_ICAL": {
        "it": "Su calendar.google.com apri Impostazioni, scegli il calendario a sinistra,\n"
              "vai su «Integra calendario» e copia «Indirizzo segreto in formato iCal».\n"
              "Incollalo qui sotto. Per più calendari, un indirizzo per riga.\n"
              "L’indirizzo è privato: chi lo ha può leggere il calendario.",
        "en": "On calendar.google.com open Settings, pick the calendar on the left,\n"
              "go to “Integrate calendar” and copy “Secret address in iCal format”.\n"
              "Paste it below. For several calendars, one address per line.\n"
              "The address is private: anyone who has it can read the calendar.",
        "fr": "Sur calendar.google.com, ouvrez Paramètres, choisissez l’agenda à gauche,\n"
              "allez dans « Intégrer l’agenda » et copiez « Adresse secrète au format iCal ».\n"
              "Collez-la ci-dessous. Pour plusieurs agendas, une adresse par ligne.\n"
              "L’adresse est privée : quiconque la possède peut lire l’agenda.",
        "es": "En calendar.google.com abre Configuración, elige el calendario a la izquierda,\n"
              "ve a «Integrar el calendario» y copia «Dirección secreta en formato iCal».\n"
              "Pégala abajo. Para varios calendarios, una dirección por línea.\n"
              "La dirección es privada: quien la tenga puede leer el calendario.",
        "zh": "在 calendar.google.com 打开“设置”，在左侧选择日历，\n"
              "进入“集成日历”，复制“iCal 格式的私密地址”。\n"
              "粘贴到下面。多个日历请每行一个地址。\n"
              "该地址是私密的：拥有它的人都能读取你的日历。"},
    "{n} calendari non raggiungibili": {"en": "{n} calendars unreachable", "fr": "{n} agendas inaccessibles",
                                        "es": "{n} calendarios inaccesibles", "zh": "{n} 个日历无法访问"},
    "Sincronizzato alle {time}": {"en": "Synced at {time}", "fr": "Synchronisé à {time}",
                                  "es": "Sincronizado a las {time}", "zh": "同步于 {time}"},
    "Non riesco a leggere il calendario. Controlla la connessione e l’indirizzo iCal (⚙ → <b>Collega Google Calendar</b>). Dettaglio: ": {
        "en": "Can't read the calendar. Check your connection and the iCal address (⚙ → <b>Connect Google Calendar</b>). Details: ",
        "fr": "Impossible de lire l’agenda. Vérifiez la connexion et l’adresse iCal (⚙ → <b>Connecter Google Agenda</b>). Détail : ",
        "es": "No puedo leer el calendario. Revisa la conexión y la dirección iCal (⚙ → <b>Conectar Google Calendar</b>). Detalle: ",
        "zh": "无法读取日历。请检查网络和 iCal 地址（⚙ → <b>连接 Google 日历</b>）。详情："},
    "Niente in programma.": {"en": "Nothing planned.", "fr": "Rien de prévu.", "es": "Nada previsto.", "zh": "暂无安排。"},
    "task": {"en": "task", "fr": "tâche", "es": "tarea", "zh": "任务"},

    # --- task
    "Task": {"en": "Tasks", "fr": "Tâches", "es": "Tareas", "zh": "任务"},
    "Cosa devi fare?": {"en": "What do you need to do?", "fr": "Que devez-vous faire ?", "es": "¿Qué tienes que hacer?",
                        "zh": "要做什么？"},
    "Aggiungi il task": {"en": "Add the task", "fr": "Ajouter la tâche", "es": "Añadir la tarea", "zh": "添加任务"},
    "entro": {"en": "due", "fr": "avant le", "es": "para", "zh": "截止"},
    "Pulisci": {"en": "Clear", "fr": "Nettoyer", "es": "Limpiar", "zh": "清理"},
    "Togli i task completati": {"en": "Remove completed tasks", "fr": "Retirer les tâches terminées",
                                "es": "Quitar las tareas completadas", "zh": "移除已完成的任务"},
    "oggi": {"en": "today", "fr": "aujourd’hui", "es": "hoy", "zh": "今天"},
    "entro il {date}": {"en": "due {date}", "fr": "avant le {date}", "es": "para el {date}", "zh": "{date} 截止"},
    "Nessun task. Scrivine uno qui sopra e premi Invio.": {
        "en": "No tasks. Type one above and press Enter.", "fr": "Aucune tâche. Écrivez-en une ci-dessus et appuyez sur Entrée.",
        "es": "No hay tareas. Escribe una arriba y pulsa Intro.", "zh": "没有任务。在上方输入并按回车。"},
    "Non riesco a leggere le tue impostazioni (il file è bloccato da un altro programma). "
    "Per non perderle, finché non riavvii SiDD le modifiche non verranno salvate.": {
        "en": "I can't read your settings (the file is locked by another program). To keep them safe, "
              "changes won't be saved until you restart SiDD.",
        "fr": "Impossible de lire vos réglages (le fichier est bloqué par un autre programme). Pour les protéger, "
              "les modifications ne seront pas enregistrées avant le redémarrage de SiDD.",
        "es": "No puedo leer tus ajustes (otro programa tiene el archivo bloqueado). Para no perderlos, "
              "los cambios no se guardarán hasta que reinicies SiDD.",
        "zh": "无法读取你的设置（文件被其他程序锁定）。为避免丢失，在重启 SiDD 之前不会保存更改。"},
    "Chiudi SiDD": {"en": "Close SiDD", "fr": "Fermer SiDD", "es": "Cerrar SiDD", "zh": "关闭 SiDD"},
    "tutti i giorni": {"en": "every day", "fr": "tous les jours", "es": "todos los días", "zh": "每天"},
    "{n} volte": {"en": "{n} times", "fr": "{n} fois", "es": "{n} veces", "zh": "{n} 次"},
    "orari diversi": {"en": "different times", "fr": "horaires variés", "es": "horarios distintos", "zh": "时间不同"},
    "Collega un calendario dalle impostazioni ⚙.": {
        "en": "Connect a calendar in settings ⚙.", "fr": "Connectez un agenda dans les réglages ⚙.",
        "es": "Conecta un calendario en los ajustes ⚙.", "zh": "在设置 ⚙ 中连接日历。"},
    "Questa settimana": {"en": "This week", "fr": "Cette semaine", "es": "Esta semana", "zh": "本周"},
    "{n} da fare": {"en": "{n} to do", "fr": "{n} à faire", "es": "{n} pendientes", "zh": "{n} 项待办"},
    "Modifica testo…": {"en": "Edit text…", "fr": "Modifier le texte…", "es": "Editar texto…", "zh": "编辑文本…"},
    "Aggiungi a Google Calendar": {"en": "Add to Google Calendar", "fr": "Ajouter à Google Agenda",
                                   "es": "Añadir a Google Calendar", "zh": "添加到 Google 日历"},
    "Modifica task": {"en": "Edit task", "fr": "Modifier la tâche", "es": "Editar tarea", "zh": "编辑任务"},
    "Testo:": {"en": "Text:", "fr": "Texte :", "es": "Texto:", "zh": "文本："},

    # --- note
    "Note": {"en": "Notes", "fr": "Notes", "es": "Notas", "zh": "便签"},
    "Scrivi qui…": {"en": "Write here…", "fr": "Écrivez ici…", "es": "Escribe aquí…", "zh": "在此输入…"},
    "+ Nota": {"en": "+ Note", "fr": "+ Note", "es": "+ Nota", "zh": "+ 便签"},
    "Nuova nota": {"en": "New note", "fr": "Nouvelle note", "es": "Nueva nota", "zh": "新便签"},
    "La bacheca è vuota. Premi «+ Nota» per attaccarne una.": {
        "en": "The board is empty. Press “+ Note” to pin one.", "fr": "Le tableau est vide. Appuyez sur « + Note » pour en épingler une.",
        "es": "El tablón está vacío. Pulsa «+ Nota» para añadir una.", "zh": "便签板是空的。点击“+ 便签”添加。"},
    "Eliminare questa nota?": {"en": "Delete this note?", "fr": "Supprimer cette note ?", "es": "¿Eliminar esta nota?",
                               "zh": "删除这条便签？"},
    "giallo": {"en": "yellow", "fr": "jaune", "es": "amarillo", "zh": "黄色"},
    "rosa": {"en": "pink", "fr": "rose", "es": "rosa", "zh": "粉色"},
    "menta": {"en": "mint", "fr": "menthe", "es": "menta", "zh": "薄荷绿"},
    "azzurro": {"en": "blue", "fr": "bleu", "es": "azul", "zh": "蓝色"},

    # --- impostazioni
    "Impostazioni": {"en": "Settings", "fr": "Réglages", "es": "Ajustes", "zh": "设置"},
    "Fine": {"en": "Done", "fr": "OK", "es": "Listo", "zh": "完成"},
    "Esci dalla modalità configurazione": {"en": "Leave configuration mode", "fr": "Quitter le mode configuration",
                                           "es": "Salir del modo configuración", "zh": "退出配置模式"},
    "Resta sul desktop, sotto le altre finestre": {"en": "Stay on the desktop, below other windows",
                                                   "fr": "Rester sur le bureau, sous les autres fenêtres",
                                                   "es": "Quedarse en el escritorio, bajo las demás ventanas",
                                                   "zh": "停留在桌面，位于其他窗口下方"},
    "Apri all’avvio del computer": {"en": "Open when the computer starts", "fr": "Ouvrir au démarrage de l’ordinateur",
                                    "es": "Abrir al iniciar el equipo", "zh": "开机时自动打开"},
    "Lato dello schermo": {"en": "Screen side", "fr": "Côté de l’écran", "es": "Lado de la pantalla", "zh": "屏幕位置"},
    "Sinistra": {"en": "Left", "fr": "Gauche", "es": "Izquierda", "zh": "左侧"},
    "Destra": {"en": "Right", "fr": "Droite", "es": "Derecha", "zh": "右侧"},
    "Aspetto": {"en": "Appearance", "fr": "Apparence", "es": "Apariencia", "zh": "外观"},
    "Scuro": {"en": "Dark", "fr": "Sombre", "es": "Oscuro", "zh": "深色"},
    "Chiaro": {"en": "Light", "fr": "Clair", "es": "Claro", "zh": "浅色"},
    "Vetro": {"en": "Glass", "fr": "Verre", "es": "Cristal", "zh": "毛玻璃"},
    "Lingua": {"en": "Language", "fr": "Langue", "es": "Idioma", "zh": "语言"},
    "Pannelli visibili": {"en": "Visible panels", "fr": "Panneaux visibles", "es": "Paneles visibles", "zh": "显示的面板"},
    "App predefinite": {"en": "Built-in apps", "fr": "Apps intégrées", "es": "Apps integradas", "zh": "内置应用"},
    "Musica preferita": {"en": "Favourite music app", "fr": "App musicale préférée", "es": "App de música favorita",
                         "zh": "常用音乐应用"},
    "Nessuna": {"en": "None", "fr": "Aucune", "es": "Ninguna", "zh": "无"},
    "Altro": {"en": "Other", "fr": "Autres", "es": "Otros", "zh": "其他"},
    "Imposta i calendari Google": {"en": "Set up Google calendars", "fr": "Configurer les agendas Google",
                                   "es": "Configurar los calendarios de Google", "zh": "设置 Google 日历"},
    "Cartella dati": {"en": "Data folder", "fr": "Dossier des données", "es": "Carpeta de datos", "zh": "数据文件夹"},
    "Apri la cartella dei dati": {"en": "Open the data folder", "fr": "Ouvrir le dossier des données",
                                  "es": "Abrir la carpeta de datos", "zh": "打开数据文件夹"},
    "Chiudi la dashboard": {"en": "Quit the dashboard", "fr": "Quitter le tableau de bord", "es": "Cerrar el panel",
                            "zh": "退出仪表板"},
    "Chiude il programma": {"en": "Closes the program", "fr": "Ferme le programme", "es": "Cierra el programa",
                            "zh": "关闭程序"},
    "Modalità configurazione: aggiungi app e cambia le impostazioni": {
        "en": "Configuration mode: add apps and change settings", "fr": "Mode configuration : ajouter des apps et modifier les réglages",
        "es": "Modo configuración: añade apps y cambia los ajustes", "zh": "配置模式：添加应用并修改设置"},
    "Riduci a icona": {"en": "Minimize", "fr": "Réduire", "es": "Minimizar", "zh": "最小化"},
    "Non riesco a cambiare l’avvio automatico.": {"en": "Can't change the startup setting.",
                                                  "fr": "Impossible de modifier le démarrage automatique.",
                                                  "es": "No puedo cambiar el inicio automático.", "zh": "无法更改开机启动设置。"},

    # --- meteo
    "Meteo": {"en": "Weather", "fr": "Météo", "es": "Tiempo", "zh": "天气"},
    "Sereno": {"en": "Clear", "fr": "Dégagé", "es": "Despejado", "zh": "晴"},
    "Poco nuvoloso": {"en": "Mostly clear", "fr": "Peu nuageux", "es": "Poco nuboso", "zh": "少云"},
    "Parzialmente nuvoloso": {"en": "Partly cloudy", "fr": "Partiellement nuageux", "es": "Parcialmente nuboso",
                              "zh": "多云"},
    "Coperto": {"en": "Overcast", "fr": "Couvert", "es": "Cubierto", "zh": "阴"},
    "Nebbia": {"en": "Fog", "fr": "Brouillard", "es": "Niebla", "zh": "雾"},
    "Pioggerella": {"en": "Drizzle", "fr": "Bruine", "es": "Llovizna", "zh": "毛毛雨"},
    "Pioggia": {"en": "Rain", "fr": "Pluie", "es": "Lluvia", "zh": "雨"},
    "Neve": {"en": "Snow", "fr": "Neige", "es": "Nieve", "zh": "雪"},
    "Rovesci": {"en": "Showers", "fr": "Averses", "es": "Chubascos", "zh": "阵雨"},
    "Rovesci di neve": {"en": "Snow showers", "fr": "Averses de neige", "es": "Chubascos de nieve", "zh": "阵雪"},
    "Temporale": {"en": "Thunderstorm", "fr": "Orage", "es": "Tormenta", "zh": "雷暴"},
    "Oggi": {"en": "Today", "fr": "Auj.", "es": "Hoy", "zh": "今天"},
    "pioggia": {"en": "rain", "fr": "pluie", "es": "lluvia", "zh": "降雨"},
    "Percepita {t}° · vento {w} km/h · umidità {h}%": {
        "en": "Feels like {t}° · wind {w} km/h · humidity {h}%",
        "fr": "Ressenti {t}° · vent {w} km/h · humidité {h} %",
        "es": "Sensación {t}° · viento {w} km/h · humedad {h}%",
        "zh": "体感 {t}° · 风速 {w} km/h · 湿度 {h}%"},
    "Non riesco a scaricare il meteo. Riprovo tra 30 minuti.": {
        "en": "Can't download the weather. Retrying in 30 minutes.",
        "fr": "Impossible de télécharger la météo. Nouvel essai dans 30 minutes.",
        "es": "No puedo descargar el tiempo. Reintento en 30 minutos.", "zh": "无法获取天气。30 分钟后重试。"},
    "Imposta la tua località: premi la rotella ⚙ in alto, sezione «Meteo».": {
        "en": "Set your location: press the ⚙ gear at the top, “Weather” section.",
        "fr": "Choisissez votre lieu : roue ⚙ en haut, section « Météo ».",
        "es": "Elige tu ubicación: pulsa la rueda ⚙ arriba, sección «Tiempo».",
        "zh": "设置你的位置：点击顶部 ⚙ 齿轮，“天气”部分。"},
    "Nessuna località": {"en": "No location", "fr": "Aucun lieu", "es": "Sin ubicación", "zh": "未设置位置"},
    "Cambia località…": {"en": "Change location…", "fr": "Changer de lieu…", "es": "Cambiar ubicación…",
                         "zh": "更改位置…"},
    "Cerca la tua città": {"en": "Search for your city", "fr": "Cherchez votre ville", "es": "Busca tu ciudad",
                           "zh": "搜索你的城市"},
    "Città o località:": {"en": "City or place:", "fr": "Ville ou lieu :", "es": "Ciudad o lugar:", "zh": "城市或地点："},
    "Non trovo «{name}».": {"en": "Can't find “{name}”.", "fr": "« {name} » introuvable.",
                            "es": "No encuentro «{name}».", "zh": "找不到“{name}”。"},
    "Quale intendi?": {"en": "Which one?", "fr": "Lequel ?", "es": "¿Cuál?", "zh": "是哪一个？"},
    "Non riesco a cercare la località.": {"en": "Can't search for the location.",
                                          "fr": "Impossible de chercher le lieu.",
                                          "es": "No puedo buscar la ubicación.", "zh": "无法搜索位置。"},

    # --- scorciatoia
    "Scorciatoia da tastiera": {"en": "Keyboard shortcut", "fr": "Raccourci clavier", "es": "Atajo de teclado",
                                "zh": "快捷键"},
    "Mostra / nascondi la dashboard": {"en": "Show / hide the dashboard", "fr": "Afficher / masquer le tableau de bord",
                                       "es": "Mostrar / ocultar el panel", "zh": "显示 / 隐藏仪表板"},
    "Disattiva la scorciatoia": {"en": "Turn the shortcut off", "fr": "Désactiver le raccourci",
                                 "es": "Desactivar el atajo", "zh": "关闭快捷键"},
    "Non posso usare questa combinazione: serve almeno Ctrl, Alt o Win più una lettera, un numero o un tasto F, e non deve essere già usata da un altro programma.": {
        "en": "Can't use this combination: it needs Ctrl, Alt or Win plus a letter, a number or an F key, and it must not be used by another program.",
        "fr": "Combinaison impossible : il faut Ctrl, Alt ou Win plus une lettre, un chiffre ou une touche F, non utilisée par un autre programme.",
        "es": "No puedo usar esta combinación: necesita Ctrl, Alt o Win más una letra, un número o una tecla F, y no debe usarla otro programa.",
        "zh": "无法使用此组合：需要 Ctrl、Alt 或 Win 加字母、数字或 F 键，且未被其他程序占用。"},

    # --- mercati personalizzati
    "+ Titolo": {"en": "+ Symbol", "fr": "+ Titre", "es": "+ Valor", "zh": "+ 品种"},
    "Aggiungi un titolo, un ETF, una valuta o una crypto": {
        "en": "Add a stock, an ETF, a currency or a crypto", "fr": "Ajouter une action, un ETF, une devise ou une crypto",
        "es": "Añade una acción, un ETF, una divisa o una cripto", "zh": "添加股票、ETF、货币或加密货币"},
    "Rimuovi {name}": {"en": "Remove {name}", "fr": "Retirer {name}", "es": "Quitar {name}", "zh": "移除 {name}"},
    "Nuovo titolo": {"en": "New symbol", "fr": "Nouveau titre", "es": "Nuevo valor", "zh": "新品种"},
    "Simbolo come su Yahoo Finance (es. AAPL, ENI.MI, EURUSD=X, ETH-USD, ^STOXX50E):": {
        "en": "Symbol as on Yahoo Finance (e.g. AAPL, ENI.MI, EURUSD=X, ETH-USD, ^STOXX50E):",
        "fr": "Symbole comme sur Yahoo Finance (ex. AAPL, ENI.MI, EURUSD=X, ETH-USD, ^STOXX50E) :",
        "es": "Símbolo como en Yahoo Finance (p. ej. AAPL, ENI.MI, EURUSD=X, ETH-USD, ^STOXX50E):",
        "zh": "Yahoo Finance 上的代码（如 AAPL、ENI.MI、EURUSD=X、ETH-USD、^STOXX50E）："},
    "Nome da mostrare:": {"en": "Display name:", "fr": "Nom affiché :", "es": "Nombre visible:", "zh": "显示名称："},
    "Non trovo il simbolo «{sym}» su Yahoo Finance.": {"en": "Can't find “{sym}” on Yahoo Finance.",
                                                       "fr": "Symbole « {sym} » introuvable sur Yahoo Finance.",
                                                       "es": "No encuentro «{sym}» en Yahoo Finance.",
                                                       "zh": "在 Yahoo Finance 上找不到“{sym}”。"},

    # --- segnalazione bug
    "Segnala un bug": {"en": "Report a bug", "fr": "Signaler un bug", "es": "Informar de un error", "zh": "报告问题"},
    "Scrivi cosa non funziona": {"en": "Tell us what doesn't work", "fr": "Dites-nous ce qui ne marche pas",
                                 "es": "Cuéntanos qué no funciona", "zh": "告诉我们哪里出了问题"},
    "Cosa non funziona? Descrivi cosa stavi facendo e cosa è successo.": {
        "en": "What doesn't work? Describe what you were doing and what happened.",
        "fr": "Qu’est-ce qui ne marche pas ? Décrivez ce que vous faisiez et ce qui s’est passé.",
        "es": "¿Qué no funciona? Describe qué estabas haciendo y qué pasó.",
        "zh": "哪里出了问题？请描述你当时在做什么以及发生了什么。"},
    "La tua email (facoltativa, per poterti rispondere)": {
        "en": "Your email (optional, so we can reply)", "fr": "Votre e-mail (facultatif, pour vous répondre)",
        "es": "Tu email (opcional, para poder responderte)", "zh": "你的邮箱（可选，便于回复）"},
    "Includi versione e sistema operativo": {"en": "Include version and operating system",
                                             "fr": "Inclure la version et le système",
                                             "es": "Incluir versión y sistema operativo", "zh": "附带版本和操作系统信息"},
    "La segnalazione arriva direttamente allo sviluppatore.": {
        "en": "The report goes straight to the developer.", "fr": "Le signalement arrive directement au développeur.",
        "es": "El informe llega directamente al desarrollador.", "zh": "报告会直接发送给开发者。"},
    "Si apre la pagina delle segnalazioni su GitHub (serve un account GitHub).": {
        "en": "The GitHub issues page opens (you need a GitHub account).",
        "fr": "La page des signalements GitHub s’ouvre (un compte GitHub est nécessaire).",
        "es": "Se abre la página de incidencias de GitHub (necesitas una cuenta de GitHub).",
        "zh": "将打开 GitHub 问题页面（需要 GitHub 账号）。"},
    "Invia": {"en": "Send", "fr": "Envoyer", "es": "Enviar", "zh": "发送"},
    "Annulla": {"en": "Cancel", "fr": "Annuler", "es": "Cancelar", "zh": "取消"},
    "Invio non riuscito. Apro la pagina delle segnalazioni su GitHub?": {
        "en": "Sending failed. Open the GitHub issues page instead?",
        "fr": "Échec de l’envoi. Ouvrir la page des signalements GitHub ?",
        "es": "No se pudo enviar. ¿Abro la página de incidencias de GitHub?", "zh": "发送失败。要打开 GitHub 问题页面吗？"},
    "Grazie! Segnalazione inviata.": {"en": "Thanks! Report sent.", "fr": "Merci ! Signalement envoyé.",
                                      "es": "¡Gracias! Informe enviado.", "zh": "谢谢！报告已发送。"},
}
# fmt: on
