import pandas as pd
import re
import csv

# Список команди підтримки
SUPPORT_TEAM = [
    'peperohka', 'nihigos', 'smilekname', 'marhaba7177', 'oleg_93830'
]


def parse_raw_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = re.split(r",\s*\{'type':", text)
    parsed_messages = []

    for block in blocks:
        if not block.strip().startswith("{'type':"):
            block = "{'type':" + block

        content_match = re.search(
            r"'content':\s*'(.*?)',\s*'mentions'", block, re.DOTALL)
        content = content_match.group(1) if content_match else ""

        # --- ОЧИСТКА ВІД ТЕГІВ ---
        # Видаляємо конструкції типу <@&12345...> або <@12345...> та пробіли після них
        if content:
            content = re.sub(r'<@&?\d+>\s*', '', content)

        author_match = re.search(r"'username':\s*'(.*?)'", block)
        author = author_match.group(1) if author_match else "Unknown"

        time_match = re.search(r"'timestamp':\s*'(.*?)'", block)
        timestamp = time_match.group(1) if time_match else ""

        # Перевірка на наявність треду
        thread_match = re.search(
            r"'thread':\s*\{.*?'name':\s*'(.*?)'", block, re.DOTALL)
        thread_name = thread_match.group(1) if thread_match else None

        # Перевірка на реакції (Done/Resolved)
        is_resolved = False
        reactions_match = re.search(
            r"'reactions':\s*\[(.*?)\]", block, re.DOTALL)
        if reactions_match:
            if any(x in reactions_match.group(1).lower() for x in ['done', 'check', 'plus', 'white_check_mark']):
                is_resolved = True

        # --- ЛОГІКА OCCURRENCE (СТАТУСУ) ---
        if is_resolved:
            occurrence = "Resolved"
        elif thread_name:
            occurrence = "In Thread"
        else:
            occurrence = "Pending"

        if content:
            parsed_messages.append({
                'content': content.replace('\\n', ' ').replace('\n', ' '),
                'author': author,
                'timestamp': timestamp,
                'thread_name': thread_name if thread_name else "No Thread",
                'occurrence': occurrence
            })
    return parsed_messages


def analyze_message_content(content, author):
    content_lower = content.lower()

    # --- 1. ACTION (Визначення дії) ---
    actions_map = {
        'add': 'Add', 'remove': 'Remove', 'delete': 'Remove',
        'check': 'Check', 'test': 'Test', 'block': 'Block',
        'send': 'Send', 'ask': 'Ask', 'raise': 'Raise',
        'assign': 'Assign', 'share': 'Share', 'migration': 'Migration',
        'give': 'Ask', 'whitelist': 'Add', 'allow': 'Add'
    }

    action = "Other"
    for key, val in actions_map.items():
        if key in content_lower:
            action = val
            break

    # --- СПЕЦІАЛЬНЕ ПРАВИЛО ДЛЯ SS7 ---
    if 'ss7' in content_lower:
        action = "Testing"

    # --- 2. OBJECT (Визначення об'єкта) ---
    obj = "N/A"

    has_email = bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', content))
    has_phone = bool(re.search(r'\b\d{7,}\b', content))

    # 2.1 Спец. правило для Support Maintenance
    if author in SUPPORT_TEAM and ('maintenance' in content_lower or 'notification' in content_lower):
        action = "Maintenance Notification"
        obj = "Ticket"

    # 2.2 Жорсткі правила для об'єктів
    elif action == 'Add' and has_email:
        obj = "Email"
    elif action in ['Send', 'Check'] and 'tt' not in content_lower and 'ticket' not in content_lower:
        obj = "Samples"
    elif action in ['Assign', 'Block']:
        obj = "Carriers"
    elif ' ss ' in content_lower or 'screenshot' in content_lower or content_lower.endswith(' ss'):
        obj = "Screenshot"
    elif 'prefix' in content_lower:
        obj = "Prefix"
    elif 'route' in content_lower:
        obj = "Route"
    elif 'rate' in content_lower or 'price' in content_lower:
        obj = "Rate"
    elif 'sender' in content_lower or 'sid' in content_lower:
        obj = "SenderID"
    elif has_phone and obj == "N/A":
        obj = "Phone Number"

    # 2.3 Пошук країни/партнера
    if obj == "N/A":
        match_context = re.search(
            r'\b(for|on|to|with|about)\s+([a-zA-Z0-9\s]+?)(?:\s+email|\s+route|\s+sim|\n|$)', content, re.IGNORECASE)
        if match_context:
            candidate = match_context.group(2).strip()
            if candidate.lower() not in ['me', 'us', 'all', 'samples']:
                obj = candidate

        # Fallback
        if obj == "N/A" and len(content) < 30:
            obj = content.split('-')[0].strip()

    # 2.4 Якщо все ще N/A і це сапорт
    if obj == "N/A" and author in SUPPORT_TEAM:
        obj = "General Support"

    # --- 3. CASE (Деталізація) ---
    case_str = "General Request"

    if author in SUPPORT_TEAM and action != "Maintenance Notification":
        case_str = "Support"
    elif action == "Maintenance Notification":
        case_str = "Notification"
    else:
        # Уніфікація кейсів
        if 'fake' in content_lower:
            case_str = "Fake"
        elif 'dlr' in content_lower:
            case_str = "DLR"
        elif 'tt' in content_lower or 'ticket' in content_lower:
            case_str = "Ticket"
        elif 'ss7' in content_lower:
            case_str = "SS7"
        elif 'route' in content_lower:
            case_str = "Route"
        elif 'rate' in content_lower or 'price' in content_lower or 'cost' in content_lower:
            case_str = "Rate"
        elif 'spam' in content_lower or 'block' in content_lower:
            case_str = "Spam/Block"
        elif 'sim' in content_lower:
            case_str = "SIM"
        elif 'prefix' in content_lower:
            case_str = "Prefix"
        elif 'sender' in content_lower:
            case_str = "SenderID"
        elif any(x in content_lower for x in ['balance', 'credit', 'payment', 'paid']):
            case_str = "Finance"
        elif any(x in content_lower for x in ['bind', 'ip', 'whitelist', 'connect', 'smpp']):
            case_str = "Connectivity"
        elif any(x in content_lower for x in ['quality', 'fas', 'cli', 'ncli']):
            case_str = "Quality"
        elif 'test' in content_lower:
            case_str = "Testing"

        # Уточнення для Check -> Quality
        if case_str == "General Request" and action == "Check":
            case_str = "Quality Check"

    return action, obj, case_str


# --- Виконання ---
file_name = 'messages.json'

try:
    messages = parse_raw_data(file_name)
    rows = []

    for msg in messages:
        action, obj, case = analyze_message_content(
            msg['content'], msg['author'])

        rows.append({
            'Date': msg['timestamp'][:10],
            'Author': msg['author'],
            'Action': action,
            'Object': obj,
            'Case': case,
            'Following request (Thread Context)': msg['thread_name'],
            'Occurrence (Status)': msg['occurrence'],
            'Original Message': msg['content'][:100] + '...'
        })

    df = pd.DataFrame(rows)
    output_filename = 'discord_analytics_clean_v6.csv'
    df.to_csv(output_filename, index=False, quoting=csv.QUOTE_ALL)
    print(f"Готово! Файл збережено як {output_filename}")

except FileNotFoundError:
    print(f"Файл {file_name} не знайдено.")
