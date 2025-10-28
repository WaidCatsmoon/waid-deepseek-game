import streamlit as st
import requests
import random

st.set_page_config(page_title="Вейд: Семья и Счастье", layout="wide")

# === DEEPSEEK ===
DEEPSEEK_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-coder-6.7b-instruct"
HF_TOKEN = st.secrets["HF_TOKEN"]
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

universes = ["волшебный лес", "кибер-город", "драконья пещера", "подземный мир"]
creatures = ['slime', 'succubus', 'fairy', 'dragon', 'elf', 'ghoul']

# === ИНИЦИАЛИЗАЦИЯ ===
if 'waid' not in st.session_state:
    st.session_state.waid = {
        'happiness': 100, 'max_happiness': 100,
        'atk': 20, 'def': 10, 'mana': 50, 'max_mana': 50,
        'spouse': None, 'children': [], 'turns_since_child': 0
    }
if 'party' not in st.session_state:
    st.session_state.party = []
if 'enemy' not in st.session_state:
    st.session_state.enemy = None
if 'in_battle' not in st.session_state:
    st.session_state.in_battle = False
if 'chat' not in st.session_state:
    st.session_state.chat = []
if 'names' not in st.session_state:
    st.session_state.names = {}

# === DEEPSEEK ===
def call_deepseek(prompt):
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 120, "temperature": 0.9}}
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()[0]['generated_text'].strip()
    except:
        return "…"

# === ИМЯ ===
def get_name(creature):
    if creature not in st.session_state.names:
        prompt = f"Придумай красивое имя для {creature} в {st.session_state.get('universe', 'мире')}. Только имя."
        name = call_deepseek(prompt)
        st.session_state.names[creature] = name or creature.capitalize()
    return st.session_state.names[creature]

# === ВРАГ ===
def spawn_enemy():
    creature = random.choice(creatures)
    name = get_name(creature)
    return {
        'name': name, 'creature': creature,
        'hp': random.randint(70, 140), 'max_hp': random.randint(70, 140),
        'atk': random.randint(12, 28), 'def': 6
    }

# === УРОН ПО СЧАСТЬЮ ===
def damage_happiness(amount):
    st.session_state.waid['happiness'] = max(0, st.session_state.waid['happiness'] - amount)
    if st.session_state.waid['happiness'] == 0:
        st.session_state.chat.append({'role': 'system', 'text': "**Ты сломлен... мир поглотил тебя.**"})
        st.session_state.in_battle = False

# === АТАКА ВРАГА ===
def enemy_attack():
    dmg = random.randint(10, 25)
    st.session_state.chat.append({'role': 'system', 'text': f"**{st.session_state.enemy['name']}** наносит удар..."})
    damage_happiness(dmg)
    st.session_state.chat.append({'role': 'system', 'text': f"**Счастье: -{dmg}** → {st.session_state.waid['happiness']}/100"})

# === СЕМЬЯ ===
def marry(partner_name):
    st.session_state.waid['spouse'] = partner_name
    st.session_state.waid['happiness'] = min(100, st.session_state.waid['happiness'] + 20)
    st.session_state.chat.append({'role': 'system', 'text': f"**{partner_name} — твоя супруга!** Счастье +20"})

def have_child():
    if not st.session_state.waid['spouse']:
        st.session_state.chat.append({'role': 'system', 'text': "Сначала нужна семья..."})
        return
    child_name = call_deepseek(f"Придумай имя ребёнку Вейда и {st.session_state.waid['spouse']}. Только имя.")
    child = {'name': child_name.strip(), 'age': 0}
    st.session_state.waid['children'].append(child)
    st.session_state.waid['turns_since_child'] = 0
    st.session_state.chat.append({'role': 'system', 'text': f"**Рождается: {child_name}!!}**"})

# === UI ===
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### Вселенная: **{st.session_state.get('universe', '???')}**")

    if st.session_state.in_battle and st.session_state.enemy:
        enemy = st.session_state.enemy
        st.markdown(f"### Враг: **{enemy['name']}** ❤️ {enemy['hp']}/{enemy['max_hp']}")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Атаковать"):
                damage = max(1, st.session_state.waid['atk'] - enemy['def'] // 2)
                enemy['hp'] -= damage
                st.session_state.chat.append({'role': 'system', 'text': f"Ты нанёс **{damage}** урона!"})
                if enemy['hp'] <= 0:
                    st.session_state.chat.append({'role': 'system', 'text': f"**{enemy['name']} повержен!**"})
                    st.session_state.waid['happiness'] = min(100, st.session_state.waid['happiness'] + 10)
                    st.session_state.in_battle = False
                else:
                    enemy_attack()
                st.rerun()

        with col_btn2:
            if st.button("Поговорить"):
                prompt = f"Ты — {enemy['name']}, враг Вейда. Он пытается поговорить. Может, сдашься?"
                reply = call_deepseek(prompt)
                st.session_state.chat.append({'role': 'enemy', 'text': f"**{enemy['name']}:** {reply}"})
                if any(w in reply.lower() for w in ["не хочу", "сдаюсь", "мир", "друг"]):
                    st.session_state.chat.append({'role': 'system', 'text': f"**{enemy['name']} присоединяется!** Счастье +15"})
                    member = {'name': enemy['name'], 'creature': enemy['creature'], 'hp': 100, 'max_hp': 100, 'atk': 18, 'def': 8}
                    st.session_state.party.append(member)
                    st.session_state.waid['happiness'] = min(100, st.session_state.waid['happiness'] + 15)
                    st.session_state.in_battle = False
                st.rerun()

    else:
        current = st.session_state.get('current_creature')
        if current:
            name = get_name(current)
            st.markdown(f"### Существо: **{name}**")

        user_input = st.chat_input("Что скажешь? (привет, атаковать, жениться на [имя], родить ребёнка, новая вселенная)")
        if user_input:
            st.session_state.chat.append({'role': 'user', 'text': user_input})

            if "привет" in user_input.lower():
                prompt = f"Ты — {name}, встречаешь Вейда. Приветствие."
                reply = call_deepseek(prompt)
                st.session_state.chat.append({'role': 'ai', 'text': f"**{name}:** {reply}"})

            elif any(w in user_input.lower() for w in ["атаковать", "бой"]):
                st.session_state.enemy = spawn_enemy()
                st.session_state.in_battle = True
                st.session_state.chat.append({'role': 'system', 'text': f"**{st.session_state.enemy['name']} появляется!**"})
                st.rerun()

            elif "присоединиться" in user_input.lower():
                if current and current not in [p['creature'] for p in st.session_state.party]:
                    member = {'name': name, 'creature': current, 'hp': 100, 'max_hp': 100, 'atk': 18, 'def': 8}
                    st.session_state.party.append(member)
                    st.session_state.chat.append({'role': 'system', 'text': f"**{name} в группе!**"})

            elif "жениться" in user_input.lower() or "выйти замуж" in user_input.lower():
                partner = user_input.split("на")[-1].strip() if "на" in user_input else name
                marry(partner)

            elif "родить ребёнка" in user_input.lower():
                have_child()

            elif "новая вселенная" in user_input.lower():
                st.session_state.universe = random.choice(universes)
                st.session_state.current_creature = random.choice([c for c in creatures if c not in [p['creature'] for p in st.session_state.party]])
                st.session_state.chat.append({'role': 'system', 'text': f"Портал открыт! Новая вселенная: **{st.session_state.universe}**"})
                st.session_state.names = {}

            st.rerun()

    # Чат
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.chat[-15:]:
            if msg['role'] == 'user':
                st.markdown(f"<div style='text-align: right; background: #e94560; color: white; padding: 8px; border-radius: 10px; margin: 5px;'>Ты: {msg['text']}</div>", unsafe_allow_html=True)
            elif msg['role'] == 'ai':
                st.markdown(f"<div style='background: #0f3460; color: white; padding: 8px; border-radius: 10px; margin: 5px;'>{msg['text']}</div>", unsafe_allow_html=True)
            elif msg['role'] == 'enemy':
                st.markdown(f"<div style='background: #8B0000; color: white; padding: 8px; border-radius: 10px; margin: 5px;'>{msg['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; color: #888; font-style: italic;'>{msg['text']}</div>", unsafe_allow_html=True)

    # Рост детей (только счастье)
    if st.session_state.waid['turns_since_child'] is not None:
        st.session_state.waid['turns_since_child'] += 1
        for child in st.session_state.waid['children']:
            if child['age'] < 5 and st.session_state.waid['turns_since_child'] % 4 == 0:
                child['age'] += 1
                st.session_state.waid['happiness'] = min(100, st.session_state.waid['happiness'] + 5)
                st.session_state.chat.append({'role': 'system', 'text': f"**{child['name']}** сказал первое слово! Счастье +5"})

with col2:
    st.markdown("### Вейд Кетсмун")
    happiness = st.session_state.waid['happiness']
    st.progress(happiness / 100)
    color = "green" if happiness > 50 else "orange" if happiness > 25 else "red"
    st.markdown(f"<p style='color:{color}; font-weight:bold;'>Счастье: {happiness}/100</p>", unsafe_allow_html=True)

    if st.session_state.waid['spouse']:
        st.markdown(f"**Супруг(а):** {st.session_state.waid['spouse']}")

    st.markdown("### Дети (дома)")
    for child in st.session_state.waid['children']:
        st.write(f"**{child['name']}** (возраст: {child['age']})")

    st.markdown("### Группа (в бою)")
    for member in st.session_state.party:
        st.progress(member['hp'] / member['max_hp'])
        st.write(f"**{member['name']}** ❤️ {member['hp']}/{member['max_hp']}")

# === СТАРТ ===
if not st.session_state.get('universe'):
    st.session_state.universe = random.choice(universes)
    st.session_state.current_creature = random.choice(creatures)
    st.rerun()