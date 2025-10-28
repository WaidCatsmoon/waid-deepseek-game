import streamlit as st
import requests
import random

st.set_page_config(page_title="Вейд Кетсмун", layout="wide")

DEEPSEEK_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-coder-6.7b-instruct"
HF_TOKEN = st.secrets["HF_TOKEN"] 

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

universes = ["волшебный лес", "кибер-город", "драконья пещера", "подземный мир"]
creatures = ['slime', 'succubus', 'fairy', 'dragon', 'elf']

if 'session' not in st.session_state:
    st.session_state.session = {
        'universe': random.choice(universes),
        'creature': random.choice(creatures),
        'party': [],
        'names': {}
    }

def call_deepseek(prompt):
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 1.0}}
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()[0]['generated_text']
    except:
        pass
    return "ИИ думает..."

def get_name(creature):
    if creature not in st.session_state.session['names']:
        prompt = f"Придумай уникальное фэнтезийное имя для {creature} в {st.session_state.session['universe']}. Только имя."
        name = call_deepseek(prompt)
        st.session_state.session['names'][creature] = name or creature.capitalize()
    return st.session_state.session['names'][creature]

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"### Вселенная: **{st.session_state.session['universe']}**")
    current_name = get_name(st.session_state.session['creature'])
    st.markdown(f"### Существо: **{current_name}**")

    chat = st.container()
    with chat:
        for msg in st.session_state.get('chat', []):
            if msg['role'] == 'user':
                st.markdown(f"<div style='text-align: right; background: #e94560; color: white; padding: 10px; border-radius: 10px; margin: 5px; display: inline-block;'>Ты: {msg['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background: #0f3460; color: white; padding: 10px; border-radius: 10px; margin: 5px; display: inline-block;'>{msg['text']}</div>", unsafe_allow_html=True)

    user_input = st.chat_input("Что скажешь?")
    if user_input:
        st.session_state.setdefault('chat', []).append({'role': 'user', 'text': user_input})

        prompt = f"""Ты — {current_name}, спутник Вейда.
Вселенная: {st.session_state.session['universe']}.
Группа: {', '.join([get_name(p) for p in st.session_state.session['party']]) or 'никого'}.
Ответь от первого лица, живо, 2-3 предложения.
Пользователь: {user_input}"""
        reply = call_deepseek(prompt)
        st.session_state['chat'].append({'role': 'ai', 'text': f"**{current_name}:** {reply}"})

        if "присоединиться" in user_input.lower():
            if st.session_state.session['creature'] not in st.session_state.session['party']:
                st.session_state.session['party'].append(st.session_state.session['creature'])
        if "новая вселенная" in user_input.lower():
            st.session_state.session['universe'] = random.choice(universes)
            st.session_state.session['creature'] = random.choice([c for c in creatures if c not in st.session_state.session['party']])
            st.session_state.session['names'] = {}

        st.rerun()

with col2:
    st.markdown("### Группа")
    for p in st.session_state.session['party']:
        st.markdown(f"- {get_name(p)}")
