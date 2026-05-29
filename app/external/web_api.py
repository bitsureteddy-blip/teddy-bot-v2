import streamlit as st
import asyncio
import pandas as pd
import plotly.graph_objects as go
import nest_asyncio
import time

from data_fetcher import DataFetcher
from signal_engine import SignalEngine
from utils import format_number, load_json, save_json

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Bitsure Teddy",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="expanded"
)

nest_asyncio.apply()

fetcher = DataFetcher.get_instance()
WATCHLIST_FILE = "data/watchlist.json"
ALERTS_FILE = "data/web_alerts.json"

# =========================
# ASYNC SAFE RUNNER
# =========================
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

# =========================
# CACHE PERFORMANCE
# =========================
@st.cache_data(ttl=300)
def get_cached_historical_data(symbol: str, timeframe: str = "1d"):
    return run_async(fetcher.get_historical_data(symbol, timeframe=timeframe))

@st.cache_data(ttl=15)
def get_cached_realtime_price(symbol: str):
    return run_async(fetcher.get_realtime_price(symbol))

# =========================
# GESTION DES RÔLES (SESSION)
# =========================
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = "free"

def set_user_role(user_id: str):
    # Simulation – à connecter à user_manager plus tard
    if user_id == "8376348929":  # Admin
        st.session_state.user_role = "elite"
    elif user_id.startswith("PRO"):
        st.session_state.user_role = "pro"
    else:
        st.session_state.user_role = "free"

# =========================
# WATCHLIST STORAGE
# =========================
def load_watchlist():
    data = load_json(WATCHLIST_FILE)
    return data.get("watchlist", ["EURUSD", "BTCUSD", "XAUUSD"])

def save_watchlist(list_data):
    save_json(WATCHLIST_FILE, {"watchlist": list_data})

if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()

# =========================
# ALERTES STORAGE
# =========================
def load_alerts():
    data = load_json(ALERTS_FILE)
    return data.get("alerts", [])

def save_alerts(alerts_list):
    save_json(ALERTS_FILE, {"alerts": alerts_list})

if "alerts" not in st.session_state:
    st.session_state.alerts = load_alerts()

# =========================
# UI STYLE - THÈME TRADING PRO
# =========================
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #EAEAEA;
        font-family: 'Inter', sans-serif;
    }
    .css-1d391kg {
        background-color: #1A1C23;
    }
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    .stMetric {
        background-color: #1E222D;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #2A2E3D;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stMetric label {
        color: #9A9FB0 !important;
        font-size: 0.9rem;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2rem !important;
        font-weight: 700;
    }
    .stTextInput > div > div > input {
        background-color: #1E222D;
        color: white;
        border: 1px solid #2A2E3D;
        border-radius: 8px;
    }
    .stButton > button {
        background-color: #2A2E3D;
        color: white;
        border: 1px solid #3A4055;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #3A4055;
        border-color: #5A6A8B;
    }
    div[data-testid="stButton"] > button:has(div:contains("Analyser")) {
        background-color: #00A67E !important;
        border-color: #00A67E !important;
        color: white !important;
    }
    .stDataFrame {
        background-color: #1E222D;
        border-radius: 8px;
        border: 1px solid #2A2E3D;
    }
    .stDataFrame th {
        background-color: #2A2E3D !important;
        color: white !important;
        font-weight: 600;
    }
    .stProgress > div > div {
        background-color: #00A67E !important;
    }
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio label {
        background-color: #1A1C23;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border: 1px solid #2A2E3D;
        transition: all 0.2s;
    }
    .stRadio label:hover {
        background-color: #2A2E3D;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🐻 Bitsure Teddy")
st.sidebar.markdown("---")

# Connexion utilisateur (simulée)
user_id_input = st.sidebar.text_input("🔑 Ton ID Telegram", value=st.session_state.user_id, placeholder="ex: 123456789")
if user_id_input != st.session_state.user_id:
    st.session_state.user_id = user_id_input
    set_user_role(user_id_input)
    st.rerun()

if st.session_state.user_id:
    st.sidebar.success(f"Connecté (ID: {st.session_state.user_id})")
    st.sidebar.info(f"Statut : **{st.session_state.user_role.upper()}**")
else:
    st.sidebar.warning("Entre ton ID Telegram pour débloquer les fonctions Premium")

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "📌 MENU PRINCIPAL",
    ["📊 Dashboard", "⚡ Scalping", "🚨 Alertes", "📈 Analyse Avancée", "🔥 Scanner", "📋 Watchlist", "⚙️ Paramètres", "💎 Premium"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.caption("🧸 *Built in Burundi. Used worldwide.*")

# =========================
# DASHBOARD
# =========================
if page == "📊 Dashboard":
    st.title("📊 Dashboard Trading")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        symbol = st.text_input("Symbole", "EURUSD").upper()
    with col2:
        timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h"], index=0)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze = st.button("🔍 Analyser")

    if analyze:
        with st.spinner("Analyse en cours..."):
            df = get_cached_historical_data(symbol, timeframe)
            price = get_cached_realtime_price(symbol)

            if df is None or df.empty:
                st.error("Données indisponibles")
            else:
                result = SignalEngine.analyze(df)
                ind = result["indicators"]

                c1, c2, c3, c4 = st.columns(4)
                if result["signal"] == "ACHETER":
                    c1.success("🟢 ACHETER")
                elif result["signal"] == "VENDRE":
                    c1.error("🔴 VENDRE")
                else:
                    c1.warning("🟠 ATTENDRE")

                c2.metric("Teddy Score", f"{result['teddy_score']}/100")
                c3.metric("Prix", format_number(ind["price"]) if ind["price"] else "N/A")
                if price:
                    spread = price['ask'] - price['bid']
                    c4.metric("Spread", format_number(spread, 5))
                else:
                    c4.metric("RSI", f"{ind['rsi']:.2f}" if ind['rsi'] else "N/A")

                st.progress(result["teddy_score"] / 100)
                st.subheader("Analyse")
                st.write(result["reason"])
                st.write(result["risk_advice"])

                st.subheader("Graphique")
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['SMA50'] = df['Close'].rolling(window=50).mean()
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Prix"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.5), name="SMA20"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='cyan', width=1.5), name="SMA50"))
                fig.update_layout(template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("💰 Prix en temps réel")
                if price:
                    col_bid, col_ask, col_spread = st.columns(3)
                    col_bid.metric("Bid", format_number(price['bid'], 5))
                    col_ask.metric("Ask", format_number(price['ask'], 5))
                    col_spread.metric("Spread", format_number(price['ask'] - price['bid'], 5))
                else:
                    st.warning("Prix temps réel indisponible")

# =========================
# SCALPING
# =========================
elif page == "⚡ Scalping":
    st.title("⚡ Scalping (Premium)")
    if st.session_state.user_role not in ["pro", "elite"]:
        st.warning("🔒 Fonctionnalité réservée aux membres PRO et ELITE. Passez à l'offre Premium dans l'onglet dédié.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            symbol = st.text_input("Symbole", "EURUSD").upper()
        with col2:
            duration = st.selectbox("Durée", ["3", "5", "10", "20"], index=1)
        if st.button("⚡ Lancer le scalping"):
            with st.spinner(f"Scalping {symbol} ({duration}s)..."):
                fetcher.subscribe_twelvedata(symbol)
                time.sleep(1)
                price = get_cached_realtime_price(symbol)
                if price:
                    spread = price['ask'] - price['bid']
                    volatility = (spread / price['price']) * 100
                    if volatility < 0.05:
                        signal = "ATTENDRE"
                        reason = "Volatilité très faible"
                    elif volatility < 0.2:
                        signal = "ACHETER" if price['bid'] > price['ask'] * 0.999 else "VENDRE"
                        reason = "Scalping sur micro-spread"
                    else:
                        signal = "ATTENDRE"
                        reason = "Volatilité élevée"
                    st.metric("Signal", signal)
                    st.write(f"**Raison :** {reason}")
                    st.write(f"Prix : {format_number(price['price'])} | Bid : {format_number(price['bid'], 5)} | Ask : {format_number(price['ask'], 5)} | Volatilité : {volatility:.4f}%")
                else:
                    st.error("Impossible d'obtenir les données temps réel.")

# =========================
# ALERTES
# =========================
elif page == "🚨 Alertes":
    st.title("🚨 Alertes de prix")
    st.markdown("Créez et gérez vos alertes de prix.")
    with st.form("alert_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Symbole", "EURUSD").upper()
        with col2:
            condition = st.selectbox("Condition", ["above", "below"])
        with col3:
            price = st.number_input("Prix cible", min_value=0.0, step=0.0001, format="%.5f")
        if st.form_submit_button("➕ Créer l'alerte"):
            new_alert = {"symbol": symbol, "condition": condition, "price": price, "triggered": False}
            st.session_state.alerts.append(new_alert)
            save_alerts(st.session_state.alerts)
            st.success(f"Alerte créée : {symbol} {condition} {price}")
            st.rerun()

    st.subheader("📋 Vos alertes actives")
    if not st.session_state.alerts:
        st.info("Aucune alerte active.")
    else:
        for i, alert in enumerate(st.session_state.alerts):
            col1, col2 = st.columns([4, 1])
            status = "✅" if alert['triggered'] else "⏳"
            col1.write(f"{status} {alert['symbol']} {alert['condition']} {alert['price']}")
            if col2.button("🗑️", key=f"del_alert_{i}"):
                del st.session_state.alerts[i]
                save_alerts(st.session_state.alerts)
                st.rerun()

# =========================
# ANALYSE AVANCÉE
# =========================
elif page == "📈 Analyse Avancée":
    st.title("📈 Analyse Avancée")
    symbol = st.text_input("Symbole", "EURUSD").upper()
    timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h"], index=0)
    if st.button("Analyser"):
        df = get_cached_historical_data(symbol, timeframe)
        if df is not None and not df.empty:
            result = SignalEngine.analyze(df)
            ind = result["indicators"]
            st.subheader("📊 Indicateurs techniques")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("RSI", f"{ind['rsi']:.2f}")
            col2.metric("SMA 20", format_number(ind['sma20']))
            col3.metric("SMA 50", format_number(ind['sma50']))
            col4.metric("MACD", format_number(ind['macd'], 5))
            st.subheader("📈 Niveaux clés")
            col1, col2 = st.columns(2)
            col1.metric("Support", format_number(ind['support']) if ind['support'] else "N/A")
            col2.metric("Résistance", format_number(ind['resistance']) if ind['resistance'] else "N/A")
            st.subheader("🧭 Tendance")
            st.info(ind.get('trend', 'N/A'))
        else:
            st.error("Données indisponibles")

# =========================
# SCANNER (VERSION AMÉLIORÉE)
# =========================
elif page == "🔥 Scanner":
    st.title("🔥 Scanner de Marché")
    st.markdown("Analyse multi-actifs en temps réel avec signaux et scores.")

    # Liste étendue de symboles
    symbols = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
        "BTCUSD", "ETHUSD", "XRPUSD", "SOLUSD", "ADAUSD", "BNBUSD",
        "XAUUSD", "XAGUSD", "USOIL", "UKOIL",
        "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "NVDA"
    ]

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Lancer le Scan Complet", type="primary"):
            with st.spinner("Scan des marchés en cours... Veuillez patienter."):
                results = []
                progress = st.progress(0)
                status_text = st.empty()

                for i, sym in enumerate(symbols):
                    status_text.text(f"Analyse de {sym} ({i+1}/{len(symbols)})")
                    df = get_cached_historical_data(sym)
                    if df is not None and not df.empty:
                        res = SignalEngine.analyze(df)
                        results.append({
                            "Symbole": sym,
                            "Signal": res["signal"],
                            "Score": res["teddy_score"],
                            "Prix": res["indicators"]["price"],
                            "RSI": res["indicators"]["rsi"],
                            "SMA20": res["indicators"]["sma20"]
                        })
                    progress.progress((i + 1) / len(symbols))
                
                status_text.empty()
                progress.empty()

                if results:
                    df_res = pd.DataFrame(results).sort_values("Score", ascending=False)
                    st.session_state['scan_results'] = df_res
                else:
                    st.error("Aucun résultat disponible.")

    # Affichage des résultats (avec mise en cache de session)
    if 'scan_results' in st.session_state and not st.session_state['scan_results'].empty:
        df_display = st.session_state['scan_results'].copy()
        
        # Filtres
        with st.expander("🔽 Filtres et Options", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                signal_filter = st.multiselect("Signaux", ["ACHETER", "VENDRE", "ATTENDRE"], default=["ACHETER", "VENDRE", "ATTENDRE"])
            with col_f2:
                min_score = st.slider("Score minimum", 0, 100, 0)
            with col_f3:
                search_symbol = st.text_input("🔍 Rechercher un symbole").upper()
        
        # Application des filtres
        if signal_filter:
            df_display = df_display[df_display['Signal'].isin(signal_filter)]
        df_display = df_display[df_display['Score'] >= min_score]
        if search_symbol:
            df_display = df_display[df_display['Symbole'].str.contains(search_symbol)]

        st.subheader(f"📋 Résultats ({len(df_display)} actifs)")
        
        # Fonction de coloration des signaux
        def color_signal(val):
            if val == "ACHETER":
                return 'background-color: #006633; color: white; font-weight: bold'
            elif val == "VENDRE":
                return 'background-color: #993333; color: white; font-weight: bold'
            else:
                return 'background-color: #555555; color: white'
        
        # Fonction de barre de progression pour le score
        def score_bar(val):
            return f'⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤'[:int(val/10)] + f'⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤'[int(val/10):]  # simulation simple

        # Application du style
        styled_df = df_display.style.applymap(color_signal, subset=['Signal'])
        styled_df = styled_df.format({
            'Prix': lambda x: format_number(x, 5) if x < 1000 else format_number(x, 2),
            'RSI': '{:.1f}',
            'SMA20': lambda x: format_number(x, 5)
        })
        styled_df = styled_df.background_gradient(subset=['Score'], cmap='RdYlGn', low=0.4, high=0.6)
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Bouton d'export
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exporter en CSV",
            data=csv,
            file_name='bitsure_scan.csv',
            mime='text/csv'
        )
# =========================
# WATCHLIST
# =========================
elif page == "📋 Watchlist":
    st.title("📋 Watchlist")
    new_sym = st.text_input("Ajouter symbole").upper()
    if st.button("Ajouter") and new_sym:
        if new_sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_sym)
            save_watchlist(st.session_state.watchlist)
            st.rerun()
    st.subheader("Tes actifs")
    for sym in st.session_state.watchlist:
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.write(sym)
        if col2.button("📊 Analyser", key=f"wl_analyze_{sym}"):
            df = get_cached_historical_data(sym)
            if df is not None and not df.empty:
                res = SignalEngine.analyze(df)
                st.info(f"{sym} → {res['signal']} ({res['teddy_score']}/100)")
        if col3.button("🗑️", key=f"wl_del_{sym}"):
            st.session_state.watchlist.remove(sym)
            save_watchlist(st.session_state.watchlist)
            st.rerun()

# =========================
# PARAMÈTRES
# =========================
elif page == "⚙️ Paramètres":
    st.title("⚙️ Paramètres")
    st.markdown("Personnalisez votre expérience de trading.")
    risk = st.selectbox("Profil de risque", ["low", "medium", "high"], index=1)
    st.success(f"Profil de risque défini sur : **{risk}**")
    st.markdown("---")
    st.markdown("### 🔔 Notifications")
    st.checkbox("Activer les notifications d'alertes", value=True)

# =========================
# PREMIUM
# =========================
elif page == "💎 Premium":
    st.title("💎 Offres Premium")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🆓 FREE")
        st.markdown("**0€ / mois**")
        st.markdown("- 5 analyses / jour")
        st.markdown("- Watchlist 3 symboles")
        st.markdown("- Timeframe 1d")
    with col2:
        st.markdown("### 💎 PRO")
        st.markdown("**9,99€ / mois** (Stripe)")
        st.markdown("**15,99€ / mois** (Stars)")
        st.markdown("- ✅ Illimité")
        st.markdown("- ✅ Scalping & WebSocket")
        st.markdown("- ✅ Watchlist illimitée")
    with col3:
        st.markdown("### 👑 ELITE")
        st.markdown("**24,99€ / mois** (Stripe)")
        st.markdown("**39,99€ / mois** (Stars)")
        st.markdown("- ✅ Tout PRO")
        st.markdown("- ✅ Groupe privé")
        st.markdown("- ✅ Support prioritaire")
    st.markdown("---")
    st.info("💡 Paiement via notre bot Telegram : @BitsureTeddyBot (/upgrade)")
    st.button("🚀 Passer PRO", help="Ouvre Telegram pour passer à l'offre Premium")