"""Internationalized error messages for 15 languages.

This module provides a centralized error message catalog supporting
15 languages to match the report i18n system.

Usage:
    from truthound_dashboard.core.i18n import get_message, SupportedLocale

    message = get_message("source_not_found", SupportedLocale.KOREAN)
    # Returns: "데이터 소스를 찾을 수 없습니다"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truthound_dashboard.core.reporters.i18n.base import SupportedLocale

# Error message catalog for 15 languages
# Keys are error codes, values are dicts mapping locale codes to messages
ERROR_MESSAGES: dict[str, dict[str, str]] = {
    # Source errors
    "source_not_found": {
        "en": "Data source not found",
        "ko": "데이터 소스를 찾을 수 없습니다",
        "ja": "データソースが見つかりません",
        "zh": "找不到数据源",
        "de": "Datenquelle nicht gefunden",
        "fr": "Source de données introuvable",
        "es": "Fuente de datos no encontrada",
        "pt": "Fonte de dados não encontrada",
        "it": "Origine dati non trovata",
        "ru": "Источник данных не найден",
        "ar": "مصدر البيانات غير موجود",
        "th": "ไม่พบแหล่งข้อมูล",
        "vi": "Không tìm thấy nguồn dữ liệu",
        "id": "Sumber data tidak ditemukan",
        "tr": "Veri kaynağı bulunamadı",
    },
    "source_already_exists": {
        "en": "Data source already exists",
        "ko": "데이터 소스가 이미 존재합니다",
        "ja": "データソースは既に存在します",
        "zh": "数据源已存在",
        "de": "Datenquelle existiert bereits",
        "fr": "La source de données existe déjà",
        "es": "La fuente de datos ya existe",
        "pt": "A fonte de dados já existe",
        "it": "L'origine dati esiste già",
        "ru": "Источник данных уже существует",
        "ar": "مصدر البيانات موجود بالفعل",
        "th": "แหล่งข้อมูลมีอยู่แล้ว",
        "vi": "Nguồn dữ liệu đã tồn tại",
        "id": "Sumber data sudah ada",
        "tr": "Veri kaynağı zaten mevcut",
    },
    "source_connection_failed": {
        "en": "Failed to connect to data source",
        "ko": "데이터 소스에 연결할 수 없습니다",
        "ja": "データソースへの接続に失敗しました",
        "zh": "无法连接到数据源",
        "de": "Verbindung zur Datenquelle fehlgeschlagen",
        "fr": "Échec de connexion à la source de données",
        "es": "Error al conectar con la fuente de datos",
        "pt": "Falha ao conectar à fonte de dados",
        "it": "Connessione all'origine dati fallita",
        "ru": "Не удалось подключиться к источнику данных",
        "ar": "فشل الاتصال بمصدر البيانات",
        "th": "ไม่สามารถเชื่อมต่อกับแหล่งข้อมูลได้",
        "vi": "Không thể kết nối với nguồn dữ liệu",
        "id": "Gagal terhubung ke sumber data",
        "tr": "Veri kaynağına bağlanılamadı",
    },
    # Validation errors
    "validation_failed": {
        "en": "Validation failed",
        "ko": "검증에 실패했습니다",
        "ja": "検証に失敗しました",
        "zh": "验证失败",
        "de": "Validierung fehlgeschlagen",
        "fr": "Échec de la validation",
        "es": "La validación falló",
        "pt": "A validação falhou",
        "it": "Validazione fallita",
        "ru": "Проверка не пройдена",
        "ar": "فشل التحقق",
        "th": "การตรวจสอบล้มเหลว",
        "vi": "Xác thực thất bại",
        "id": "Validasi gagal",
        "tr": "Doğrulama başarısız",
    },
    "validation_in_progress": {
        "en": "Validation is already in progress",
        "ko": "검증이 이미 진행 중입니다",
        "ja": "検証は既に進行中です",
        "zh": "验证已在进行中",
        "de": "Validierung läuft bereits",
        "fr": "La validation est déjà en cours",
        "es": "La validación ya está en progreso",
        "pt": "A validação já está em andamento",
        "it": "La validazione è già in corso",
        "ru": "Проверка уже выполняется",
        "ar": "التحقق قيد التنفيذ بالفعل",
        "th": "การตรวจสอบกำลังดำเนินการอยู่แล้ว",
        "vi": "Quá trình xác thực đang được thực hiện",
        "id": "Validasi sudah berjalan",
        "tr": "Doğrulama zaten devam ediyor",
    },
    "validator_not_found": {
        "en": "Validator not found",
        "ko": "검증기를 찾을 수 없습니다",
        "ja": "バリデーターが見つかりません",
        "zh": "找不到验证器",
        "de": "Validator nicht gefunden",
        "fr": "Validateur introuvable",
        "es": "Validador no encontrado",
        "pt": "Validador não encontrado",
        "it": "Validatore non trovato",
        "ru": "Валидатор не найден",
        "ar": "أداة التحقق غير موجودة",
        "th": "ไม่พบตัวตรวจสอบ",
        "vi": "Không tìm thấy trình xác thực",
        "id": "Validator tidak ditemukan",
        "tr": "Doğrulayıcı bulunamadı",
    },
    # Schema errors
    "schema_not_found": {
        "en": "Schema not found",
        "ko": "스키마를 찾을 수 없습니다",
        "ja": "スキーマが見つかりません",
        "zh": "找不到模式",
        "de": "Schema nicht gefunden",
        "fr": "Schéma introuvable",
        "es": "Esquema no encontrado",
        "pt": "Schema não encontrado",
        "it": "Schema non trovato",
        "ru": "Схема не найдена",
        "ar": "المخطط غير موجود",
        "th": "ไม่พบ Schema",
        "vi": "Không tìm thấy lược đồ",
        "id": "Schema tidak ditemukan",
        "tr": "Şema bulunamadı",
    },
    "schema_invalid": {
        "en": "Invalid schema format",
        "ko": "잘못된 스키마 형식입니다",
        "ja": "無効なスキーマ形式です",
        "zh": "无效的模式格式",
        "de": "Ungültiges Schema-Format",
        "fr": "Format de schéma invalide",
        "es": "Formato de esquema inválido",
        "pt": "Formato de schema inválido",
        "it": "Formato schema non valido",
        "ru": "Недопустимый формат схемы",
        "ar": "تنسيق المخطط غير صالح",
        "th": "รูปแบบ Schema ไม่ถูกต้อง",
        "vi": "Định dạng lược đồ không hợp lệ",
        "id": "Format schema tidak valid",
        "tr": "Geçersiz şema formatı",
    },
    # Schedule errors
    "schedule_not_found": {
        "en": "Schedule not found",
        "ko": "스케줄을 찾을 수 없습니다",
        "ja": "スケジュールが見つかりません",
        "zh": "找不到计划",
        "de": "Zeitplan nicht gefunden",
        "fr": "Planification introuvable",
        "es": "Programación no encontrada",
        "pt": "Agendamento não encontrado",
        "it": "Pianificazione non trovata",
        "ru": "Расписание не найдено",
        "ar": "الجدول غير موجود",
        "th": "ไม่พบตารางเวลา",
        "vi": "Không tìm thấy lịch trình",
        "id": "Jadwal tidak ditemukan",
        "tr": "Zamanlama bulunamadı",
    },
    "schedule_invalid_cron": {
        "en": "Invalid cron expression",
        "ko": "잘못된 cron 표현식입니다",
        "ja": "無効なcron式です",
        "zh": "无效的cron表达式",
        "de": "Ungültiger Cron-Ausdruck",
        "fr": "Expression cron invalide",
        "es": "Expresión cron inválida",
        "pt": "Expressão cron inválida",
        "it": "Espressione cron non valida",
        "ru": "Недопустимое cron-выражение",
        "ar": "تعبير cron غير صالح",
        "th": "นิพจน์ cron ไม่ถูกต้อง",
        "vi": "Biểu thức cron không hợp lệ",
        "id": "Ekspresi cron tidak valid",
        "tr": "Geçersiz cron ifadesi",
    },
    # Notification errors
    "notification_channel_not_found": {
        "en": "Notification channel not found",
        "ko": "알림 채널을 찾을 수 없습니다",
        "ja": "通知チャンネルが見つかりません",
        "zh": "找不到通知渠道",
        "de": "Benachrichtigungskanal nicht gefunden",
        "fr": "Canal de notification introuvable",
        "es": "Canal de notificación no encontrado",
        "pt": "Canal de notificação não encontrado",
        "it": "Canale di notifica non trovato",
        "ru": "Канал уведомлений не найден",
        "ar": "قناة الإشعارات غير موجودة",
        "th": "ไม่พบช่องทางการแจ้งเตือน",
        "vi": "Không tìm thấy kênh thông báo",
        "id": "Saluran notifikasi tidak ditemukan",
        "tr": "Bildirim kanalı bulunamadı",
    },
    "notification_send_failed": {
        "en": "Failed to send notification",
        "ko": "알림 전송에 실패했습니다",
        "ja": "通知の送信に失敗しました",
        "zh": "发送通知失败",
        "de": "Benachrichtigung konnte nicht gesendet werden",
        "fr": "Échec de l'envoi de la notification",
        "es": "Error al enviar la notificación",
        "pt": "Falha ao enviar notificação",
        "it": "Invio notifica fallito",
        "ru": "Не удалось отправить уведомление",
        "ar": "فشل إرسال الإشعار",
        "th": "ไม่สามารถส่งการแจ้งเตือนได้",
        "vi": "Gửi thông báo thất bại",
        "id": "Gagal mengirim notifikasi",
        "tr": "Bildirim gönderilemedi",
    },
    # Report errors
    "report_generation_failed": {
        "en": "Report generation failed",
        "ko": "리포트 생성에 실패했습니다",
        "ja": "レポート生成に失敗しました",
        "zh": "报告生成失败",
        "de": "Berichterstellung fehlgeschlagen",
        "fr": "Échec de la génération du rapport",
        "es": "Error al generar el informe",
        "pt": "Falha na geração do relatório",
        "it": "Generazione report fallita",
        "ru": "Не удалось создать отчет",
        "ar": "فشل إنشاء التقرير",
        "th": "การสร้างรายงานล้มเหลว",
        "vi": "Tạo báo cáo thất bại",
        "id": "Pembuatan laporan gagal",
        "tr": "Rapor oluşturma başarısız",
    },
    "report_format_unsupported": {
        "en": "Unsupported report format",
        "ko": "지원하지 않는 리포트 형식입니다",
        "ja": "サポートされていないレポート形式です",
        "zh": "不支持的报告格式",
        "de": "Nicht unterstütztes Berichtsformat",
        "fr": "Format de rapport non pris en charge",
        "es": "Formato de informe no compatible",
        "pt": "Formato de relatório não suportado",
        "it": "Formato report non supportato",
        "ru": "Неподдерживаемый формат отчета",
        "ar": "تنسيق التقرير غير مدعوم",
        "th": "รูปแบบรายงานไม่รองรับ",
        "vi": "Định dạng báo cáo không được hỗ trợ",
        "id": "Format laporan tidak didukung",
        "tr": "Desteklenmeyen rapor formatı",
    },
    # General errors
    "internal_error": {
        "en": "An internal error occurred",
        "ko": "내부 오류가 발생했습니다",
        "ja": "内部エラーが発生しました",
        "zh": "发生内部错误",
        "de": "Ein interner Fehler ist aufgetreten",
        "fr": "Une erreur interne s'est produite",
        "es": "Se produjo un error interno",
        "pt": "Ocorreu um erro interno",
        "it": "Si è verificato un errore interno",
        "ru": "Произошла внутренняя ошибка",
        "ar": "حدث خطأ داخلي",
        "th": "เกิดข้อผิดพลาดภายใน",
        "vi": "Đã xảy ra lỗi nội bộ",
        "id": "Terjadi kesalahan internal",
        "tr": "Dahili bir hata oluştu",
    },
    "invalid_request": {
        "en": "Invalid request",
        "ko": "잘못된 요청입니다",
        "ja": "無効なリクエストです",
        "zh": "无效请求",
        "de": "Ungültige Anfrage",
        "fr": "Requête invalide",
        "es": "Solicitud inválida",
        "pt": "Requisição inválida",
        "it": "Richiesta non valida",
        "ru": "Недопустимый запрос",
        "ar": "طلب غير صالح",
        "th": "คำขอไม่ถูกต้อง",
        "vi": "Yêu cầu không hợp lệ",
        "id": "Permintaan tidak valid",
        "tr": "Geçersiz istek",
    },
    "unauthorized": {
        "en": "Unauthorized access",
        "ko": "권한이 없습니다",
        "ja": "アクセス権限がありません",
        "zh": "未授权访问",
        "de": "Unbefugter Zugriff",
        "fr": "Accès non autorisé",
        "es": "Acceso no autorizado",
        "pt": "Acesso não autorizado",
        "it": "Accesso non autorizzato",
        "ru": "Несанкционированный доступ",
        "ar": "وصول غير مصرح به",
        "th": "ไม่ได้รับอนุญาต",
        "vi": "Truy cập trái phép",
        "id": "Akses tidak sah",
        "tr": "Yetkisiz erişim",
    },
    "not_found": {
        "en": "Resource not found",
        "ko": "리소스를 찾을 수 없습니다",
        "ja": "リソースが見つかりません",
        "zh": "找不到资源",
        "de": "Ressource nicht gefunden",
        "fr": "Ressource introuvable",
        "es": "Recurso no encontrado",
        "pt": "Recurso não encontrado",
        "it": "Risorsa non trovata",
        "ru": "Ресурс не найден",
        "ar": "المورد غير موجود",
        "th": "ไม่พบทรัพยากร",
        "vi": "Không tìm thấy tài nguyên",
        "id": "Sumber daya tidak ditemukan",
        "tr": "Kaynak bulunamadı",
    },
    "rate_limited": {
        "en": "Rate limit exceeded",
        "ko": "요청 한도를 초과했습니다",
        "ja": "レート制限を超過しました",
        "zh": "超出速率限制",
        "de": "Ratenlimit überschritten",
        "fr": "Limite de requêtes dépassée",
        "es": "Límite de solicitudes excedido",
        "pt": "Limite de requisições excedido",
        "it": "Limite di richieste superato",
        "ru": "Превышен лимит запросов",
        "ar": "تم تجاوز حد المعدل",
        "th": "เกินขีดจำกัดการร้องขอ",
        "vi": "Vượt quá giới hạn yêu cầu",
        "id": "Batas permintaan terlampaui",
        "tr": "İstek limiti aşıldı",
    },
    # Drift detection errors
    "drift_comparison_failed": {
        "en": "Drift comparison failed",
        "ko": "드리프트 비교에 실패했습니다",
        "ja": "ドリフト比較に失敗しました",
        "zh": "漂移比较失败",
        "de": "Drift-Vergleich fehlgeschlagen",
        "fr": "Échec de la comparaison de dérive",
        "es": "Error en la comparación de deriva",
        "pt": "Falha na comparação de drift",
        "it": "Confronto drift fallito",
        "ru": "Сравнение дрейфа не удалось",
        "ar": "فشل مقارنة الانحراف",
        "th": "การเปรียบเทียบ Drift ล้มเหลว",
        "vi": "So sánh drift thất bại",
        "id": "Perbandingan drift gagal",
        "tr": "Drift karşılaştırması başarısız",
    },
    # Anomaly detection errors
    "anomaly_detection_failed": {
        "en": "Anomaly detection failed",
        "ko": "이상 탐지에 실패했습니다",
        "ja": "異常検出に失敗しました",
        "zh": "异常检测失败",
        "de": "Anomalieerkennung fehlgeschlagen",
        "fr": "Échec de la détection d'anomalies",
        "es": "Error en la detección de anomalías",
        "pt": "Falha na detecção de anomalias",
        "it": "Rilevamento anomalie fallito",
        "ru": "Обнаружение аномалий не удалось",
        "ar": "فشل اكتشاف الشذوذ",
        "th": "การตรวจจับความผิดปกติล้มเหลว",
        "vi": "Phát hiện bất thường thất bại",
        "id": "Deteksi anomali gagal",
        "tr": "Anomali tespiti başarısız",
    },
    # Profile errors
    "profile_not_found": {
        "en": "Profile not found",
        "ko": "프로파일을 찾을 수 없습니다",
        "ja": "プロファイルが見つかりません",
        "zh": "找不到配置文件",
        "de": "Profil nicht gefunden",
        "fr": "Profil introuvable",
        "es": "Perfil no encontrado",
        "pt": "Perfil não encontrado",
        "it": "Profilo non trovato",
        "ru": "Профиль не найден",
        "ar": "الملف الشخصي غير موجود",
        "th": "ไม่พบโปรไฟล์",
        "vi": "Không tìm thấy hồ sơ",
        "id": "Profil tidak ditemukan",
        "tr": "Profil bulunamadı",
    },
    # Plugin errors
    "plugin_not_found": {
        "en": "Plugin not found",
        "ko": "플러그인을 찾을 수 없습니다",
        "ja": "プラグインが見つかりません",
        "zh": "找不到插件",
        "de": "Plugin nicht gefunden",
        "fr": "Plugin introuvable",
        "es": "Plugin no encontrado",
        "pt": "Plugin não encontrado",
        "it": "Plugin non trovato",
        "ru": "Плагин не найден",
        "ar": "البرنامج المساعد غير موجود",
        "th": "ไม่พบปลั๊กอิน",
        "vi": "Không tìm thấy plugin",
        "id": "Plugin tidak ditemukan",
        "tr": "Eklenti bulunamadı",
    },
    "plugin_install_failed": {
        "en": "Plugin installation failed",
        "ko": "플러그인 설치에 실패했습니다",
        "ja": "プラグインのインストールに失敗しました",
        "zh": "插件安装失败",
        "de": "Plugin-Installation fehlgeschlagen",
        "fr": "Échec de l'installation du plugin",
        "es": "Error al instalar el plugin",
        "pt": "Falha na instalação do plugin",
        "it": "Installazione plugin fallita",
        "ru": "Установка плагина не удалась",
        "ar": "فشل تثبيت البرنامج المساعد",
        "th": "การติดตั้งปลั๊กอินล้มเหลว",
        "vi": "Cài đặt plugin thất bại",
        "id": "Instalasi plugin gagal",
        "tr": "Eklenti kurulumu başarısız",
    },
    # Lineage errors
    "lineage_not_found": {
        "en": "Lineage information not found",
        "ko": "리니지 정보를 찾을 수 없습니다",
        "ja": "リネージ情報が見つかりません",
        "zh": "找不到血统信息",
        "de": "Abstammungsinformationen nicht gefunden",
        "fr": "Informations de lignage introuvables",
        "es": "Información de linaje no encontrada",
        "pt": "Informações de linhagem não encontradas",
        "it": "Informazioni di lineage non trovate",
        "ru": "Информация о происхождении не найдена",
        "ar": "معلومات النسب غير موجودة",
        "th": "ไม่พบข้อมูล Lineage",
        "vi": "Không tìm thấy thông tin lineage",
        "id": "Informasi lineage tidak ditemukan",
        "tr": "Köken bilgisi bulunamadı",
    },
    # Trigger errors
    "trigger_not_found": {
        "en": "Trigger not found",
        "ko": "트리거를 찾을 수 없습니다",
        "ja": "トリガーが見つかりません",
        "zh": "找不到触发器",
        "de": "Trigger nicht gefunden",
        "fr": "Déclencheur introuvable",
        "es": "Disparador no encontrado",
        "pt": "Gatilho não encontrado",
        "it": "Trigger non trovato",
        "ru": "Триггер не найден",
        "ar": "المشغل غير موجود",
        "th": "ไม่พบทริกเกอร์",
        "vi": "Không tìm thấy trigger",
        "id": "Trigger tidak ditemukan",
        "tr": "Tetikleyici bulunamadı",
    },
    "trigger_execution_failed": {
        "en": "Trigger execution failed",
        "ko": "트리거 실행에 실패했습니다",
        "ja": "トリガーの実行に失敗しました",
        "zh": "触发器执行失败",
        "de": "Trigger-Ausführung fehlgeschlagen",
        "fr": "Échec de l'exécution du déclencheur",
        "es": "Error en la ejecución del disparador",
        "pt": "Falha na execução do gatilho",
        "it": "Esecuzione trigger fallita",
        "ru": "Выполнение триггера не удалось",
        "ar": "فشل تنفيذ المشغل",
        "th": "การดำเนินการทริกเกอร์ล้มเหลว",
        "vi": "Thực thi trigger thất bại",
        "id": "Eksekusi trigger gagal",
        "tr": "Tetikleyici yürütme başarısız",
    },
}


def get_message(
    key: str,
    locale: SupportedLocale | str,
    default: str | None = None,
) -> str:
    """Get localized error message.

    Args:
        key: Error message key (e.g., "source_not_found")
        locale: Target locale (SupportedLocale enum or string code)
        default: Default message if key not found

    Returns:
        Localized error message string.

    Example:
        >>> from truthound_dashboard.core.i18n import get_message, SupportedLocale
        >>> get_message("source_not_found", SupportedLocale.KOREAN)
        '데이터 소스를 찾을 수 없습니다'
        >>> get_message("source_not_found", "ja")
        'データソースが見つかりません'
    """
    # Convert enum to string if needed
    locale_code = locale.value if hasattr(locale, "value") else str(locale)

    messages = ERROR_MESSAGES.get(key)
    if not messages:
        return default or key

    # Try exact locale match
    if locale_code in messages:
        return messages[locale_code]

    # Fallback to English
    if "en" in messages:
        return messages["en"]

    return default or key


def get_all_messages(locale: SupportedLocale | str) -> dict[str, str]:
    """Get all error messages for a locale.

    Args:
        locale: Target locale (SupportedLocale enum or string code)

    Returns:
        Dictionary mapping error keys to localized messages.

    Example:
        >>> from truthound_dashboard.core.i18n import get_all_messages
        >>> messages = get_all_messages("ko")
        >>> messages["source_not_found"]
        '데이터 소스를 찾을 수 없습니다'
    """
    locale_code = locale.value if hasattr(locale, "value") else str(locale)

    result = {}
    for key, messages in ERROR_MESSAGES.items():
        if locale_code in messages:
            result[key] = messages[locale_code]
        elif "en" in messages:
            result[key] = messages["en"]
        else:
            result[key] = key

    return result
