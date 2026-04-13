# i18n.py - Gestion des langues (Français / English)

TEXTS = {
    "fr": {
        "start": "🐻 *Bitsure Teddy* – Analyse de marché pro\n\nStatut : {status}\nCommandes : /help\nOffres : /upgrade",
        "help_title": "🧸 Commandes disponibles :\n\n",
        "help_admin": "\n\nAdmin : /broadcast, /reload, /stats, /setrole",
        "support": "📞 *Besoin d'aide ?*\n\nContactez l'administrateur : @btsr_teddy09",
        "upgrade_title": "💳 *Choisissez votre offre :*\n\n• PRO : illimité, scalping\n• ELITE : PRO + groupe privé\n• LIFETIME : ELITE à vie (50 places)",
        "invoice_title": "Bitsure Teddy Premium",
        "payment_success": "✅ *Paiement réussi !*\n\nVotre compte est maintenant *{role}*.\nMerci de soutenir Bitsure Teddy ! 🧸💸",
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO et ELITE.\nUtilisez /upgrade pour découvrir nos offres.",
        "limit_reached": "❌ Vous avez atteint votre limite quotidienne de requêtes. Passez premium pour un accès illimité.",
        "symbole_invalide": "Symbole invalide.",
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix non disponible pour {symbol}.",
        "watchlist_limit": "❌ Vous avez atteint la limite de 3 symboles en mode gratuit.\nPassez Premium pour en ajouter plus : /upgrade",
        "watchlist_added": "✅ {symbol} ajouté à votre watchlist.",
        "alerts_empty": "Aucune alerte active.",
        "alerts_cleared": "✅ Toutes vos alertes ont été supprimées.",
        "broadcast_admin_only": "⛔ Commande réservée à l'administrateur.",
        "broadcast_sent": "✅ Broadcast envoyé à {success}/{total} utilisateurs.",
        "settings_info": "⚙️ *Paramètres*\nTimeframe: {tf}\nRisque: {risk}\nLangue: {lang}\nRôle: {role}\nPremium: {prem}",
        "stats_info": "📊 *STATISTIQUES BITSURE TEDDY*\n👥 Utilisateurs totaux : {total}\n🆓 FREE : {free}\n💪 PRO : {pro}\n👑 ELITE : {elite}\n🚀 LIFETIME vendus : {lifetime}/50",
        "usage_info": "📊 Requêtes restantes aujourd'hui: {rem}",
        "usage_unlimited": "✅ Premium: requêtes illimitées.",
        "language_set": "✅ Langue définie sur Français.",
        "symboles_list": "📊 *SYMBOLES POPULAIRES*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Exemple : /analyse BTCUSD",
    },
    "en": {
        "start": "🐻 *Bitsure Teddy* – Professional Market Analysis\n\nStatus: {status}\nCommands: /help\nOffers: /upgrade",
        "help_title": "🧸 Available commands:\n\n",
        "help_admin": "\n\nAdmin: /broadcast, /reload, /stats, /setrole",
        "support": "📞 *Need help?*\n\nContact admin: @btsr_teddy09",
        "upgrade_title": "💳 *Choose your plan:*\n\n• PRO: unlimited, scalping\n• ELITE: PRO + private group\n• LIFETIME: ELITE for life (50 spots)",
        "invoice_title": "Bitsure Teddy Premium",
        "payment_success": "✅ *Payment successful!*\n\nYour account is now *{role}*.\nThank you for supporting Bitsure Teddy! 🧸💸",
        "premium_required": "🔒 *Premium Feature*\n\nThis command is reserved for PRO and ELITE members.\nUse /upgrade to discover our offers.",
        "limit_reached": "❌ You have reached your daily request limit. Upgrade to premium for unlimited access.",
        "symbole_invalide": "Invalid symbol.",
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "price_usage": "Usage: /price SYMBOL",
        "price_error": "❌ Price not available for {symbol}.",
        "watchlist_limit": "❌ You have reached the limit of 3 symbols in free mode.\nUpgrade to Premium to add more: /upgrade",
        "watchlist_added": "✅ {symbol} added to your watchlist.",
        "alerts_empty": "No active alerts.",
        "alerts_cleared": "✅ All your alerts have been deleted.",
        "broadcast_admin_only": "⛔ Admin only command.",
        "broadcast_sent": "✅ Broadcast sent to {success}/{total} users.",
        "settings_info": "⚙️ *Settings*\nTimeframe: {tf}\nRisk: {risk}\nLanguage: {lang}\nRole: {role}\nPremium: {prem}",
        "stats_info": "📊 *BITSURE TEDDY STATISTICS*\n👥 Total users: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}\n👑 ELITE: {elite}\n🚀 LIFETIME sold: {lifetime}/50",
        "usage_info": "📊 Requests remaining today: {rem}",
        "usage_unlimited": "✅ Premium: unlimited requests.",
        "language_set": "✅ Language set to English.",
        "symboles_list": "📊 *POPULAR SYMBOLS*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Example: /analyse BTCUSD",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Retourne le texte dans la langue demandée, avec formatage optionnel."""
    texts = TEXTS.get(lang, TEXTS["fr"])
    text = texts.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text