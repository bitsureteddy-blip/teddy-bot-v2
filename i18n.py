# i18n.py - Traductions exhaustives pour Bitsure Teddy

TEXTS = {
    "fr": {
        # ---- Start & Bienvenue ----
        "start": "🐻 *Bitsure Teddy* – Analyse de marché pro\n\nStatut : {status}\nCommandes : /help\nOffres : /upgrade",
        "start_disclaimer": "\n\n⚠️ *Version Beta – Merci de votre soutien !*\nCe bot est en cours d'amélioration. L'anglais peut contenir des erreurs et les données des actions ne sont pas encore toutes disponibles. Ces points seront corrigés progressivement grâce à vos retours et aux futurs financements. Merci de faire partie de l'aventure Bitsure Teddy ! 🧸",
        "status_free_trial": "🆓 Essai gratuit (3 jours)",
        "status_free_ended": "🆓 Gratuit (essai terminé)",
        "status_pro": "💎 PRO",
        "status_elite": "👑 ELITE",
        
        # ---- Help ----
        "help_title": "🧸 Commandes disponibles :\n\n",
        "help_admin": "\n\nAdmin : /broadcast, /reload, /stats, /setrole",
        
        # ---- Support ----
        "support": "📞 *Besoin d'aide ?*\n\nContactez l'administrateur : @btsr_teddy09",
        
        # ---- Upgrade ----
        "upgrade_title": "💳 *Choisissez votre offre :*\n\n• PRO : illimité, scalping\n• ELITE : PRO + groupe privé\n• LIFETIME : ELITE à vie (50 places)",
        "invoice_title": "Bitsure Teddy Premium",
        "payment_success": "✅ *Paiement réussi !*\n\nVotre compte est maintenant *{role}*.\nMerci de soutenir Bitsure Teddy ! 🧸💸",
        "stripe_soon": "ℹ️ Paiement Stripe bientôt disponible.",
        
        # ---- Premium requis ----
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO et ELITE.\nUtilisez /upgrade pour découvrir nos offres.",
        
        # ---- Limites & Quotas ----
        "limit_reached": "❌ Vous avez atteint votre limite quotidienne de requêtes. Passez premium pour un accès illimité.",
        "watchlist_limit": "❌ Vous avez atteint la limite de 3 symboles en mode gratuit.\nPassez Premium pour en ajouter plus : /upgrade",
        "watchlist_added": "✅ {symbol} ajouté à votre watchlist.",
        "watchlist_removed": "✅ {symbol} retiré de votre watchlist.",
        "watchlist_empty": "Votre watchlist est vide.",
        "watchlist_scan_empty": "Watchlist vide.",
        "watchlist_scan_result": "📊 *Scan watchlist:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",
        
        # ---- Alertes ----
        "alert_usage": "Usage: /alert SYMBOLE above/below PRIX",
        "alert_invalid_price": "Prix invalide.",
        "alert_invalid_cond": "Condition doit être 'above' ou 'below'.",
        "alert_created": "✅ Alerte #{id} créée : {symbol} {cond} {price}",
        "alerts_empty": "Aucune alerte active.",
        "alerts_list_title": "*Vos alertes :*\n",
        "alert_deleted": "✅ Alerte #{id} supprimée.",
        "alert_not_found": "❌ Alerte non trouvée.",
        "alerts_cleared": "✅ Toutes vos alertes ont été supprimées.",
        
        # ---- Analyse & Prix ----
        "symbole_invalide": "Symbole invalide.",
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix non disponible pour {symbol}.",
        "price_format": "*{symbol}*\n💰 Prix: {price}\n📊 Bid: {bid} / Ask: {ask}",
        
        # ---- Tick / Spread ----
        "tick_usage": "Usage: /tick SYMBOLE",
        "tick_none": "❌ Aucun tick récent.",
        "tick_current": "🕒 Dernier tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOLE",
        "spread_format": "*{symbol}* Spread: {spread}",
        "spread_unavailable": "❌ Spread non disponible.",
        
        # ---- Scalping (Premium) ----
        "scalp_dev": "⚡ Scalping en développement (Premium).",
        
        # ---- Tendance & Volatilité ----
        "trend_usage": "Usage: /trend SYMBOLE",
        "trend_no_data": "Données non disponibles.",
        "trend_haussiere": "Haussière",
        "trend_baissiere": "Baissière",
        "trend_neutre": "Neutre",
        "trend_result": "*{symbol}* Tendance: {tend}",
        "volatility_wip": "Calcul de la volatilité (ATR) en cours...",
        "correlation_wip": "Corrélation en développement.",
        "levels_usage": "Usage: /levels SYMBOLE",
        "levels_no_data": "Données non disponibles.",
        "levels_result": "*{symbol}* Niveaux:\nSupport: {support}\nRésistance: {resistance}",
        
        # ---- Paramètres ----
        "settings_info": "⚙️ *Paramètres*\nTimeframe: {tf}\nRisque: {risk}\nLangue: {lang_name}\nRôle: {role}\nPremium: {prem}",
        "settimeframe_usage": "Usage: /settimeframe 1h|4h|1d",
        "settimeframe_invalid": "Timeframe invalide.",
        "settimeframe_success": "✅ Timeframe par défaut: {tf}",
        "setrisk_usage": "Usage: /setrisk low|medium|high",
        "setrisk_invalid": "Risque invalide.",
        "setrisk_success": "✅ Profil de risque: {risk}",
        "setlanguage_usage": "Usage: /setlanguage en|fr",
        "setlanguage_invalid": "Langue invalide. Utilisez 'en' ou 'fr'.",
        "setlanguage_success_fr": "✅ Langue définie sur Français.",
        "setlanguage_success_en": "✅ Language set to English.",
        "usage_requests_remaining": "📊 Requêtes restantes aujourd'hui: {rem}",
        "usage_unlimited": "✅ Premium: requêtes illimitées.",
        
        # ---- Infos & Admin ----
        "status_ok": "✅ Bot opérationnel. APIs: Twelve Data, Yahoo, RealMarket.",
        "about": "Teddy Trading Bot v1.0 – Bitsure Teddy\nDéveloppé pour trading professionnel.",
        "symbolinfo": "ℹ️ Utilisez /analyse pour les infos détaillées.",
        "myid": "Votre ID Telegram: `{user_id}`",
        "broadcast_admin_only": "⛔ Commande réservée à l'administrateur.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast envoyé à {success}/{total} utilisateurs.",
        "reload_success": "✅ Configuration rechargée.",
        "stats_info": "📊 *STATISTIQUES BITSURE TEDDY*\n👥 Utilisateurs totaux : {total}\n🆓 FREE : {free}\n💪 PRO : {pro}\n👑 ELITE : {elite}\n🚀 LIFETIME vendus : {lifetime}/50",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro/elite)",
        "setrole_invalid_id": "❌ USER_ID invalide.",
        "setrole_invalid_role": "❌ Rôle invalide. Utilisez free, pro, ou elite.",
        "setrole_success": "✅ Rôle de l'utilisateur {target_id} mis à jour : *{role}*",
        
        # ---- Symboles populaires ----
        "symboles_list": "📊 *SYMBOLES POPULAIRES*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Exemple : /analyse BTCUSD",
    },
    "en": {
        # ---- Start & Welcome ----
        "start": "🐻 *Bitsure Teddy* – Professional Market Analysis\n\nStatus: {status}\nCommands: /help\nOffers: /upgrade",
        "start_disclaimer": "\n\n⚠️ *Beta Version – Thank you for your support!*\nThis bot is a work in progress. English may contain errors and stock data is not fully available yet. These issues will be fixed over time as we secure more funding. Thank you for being part of the Bitsure Teddy journey! 🧸",
        "status_free_trial": "🆓 Free trial (3 days)",
        "status_free_ended": "🆓 Free (trial ended)",
        "status_pro": "💎 PRO",
        "status_elite": "👑 ELITE",
        
        # ---- Help ----
        "help_title": "🧸 Available commands:\n\n",
        "help_admin": "\n\nAdmin: /broadcast, /reload, /stats, /setrole",
        
        # ---- Support ----
        "support": "📞 *Need help?*\n\nContact admin: @btsr_teddy09",
        
        # ---- Upgrade ----
        "upgrade_title": "💳 *Choose your plan:*\n\n• PRO: unlimited, scalping\n• ELITE: PRO + private group\n• LIFETIME: ELITE for life (50 spots)",
        "invoice_title": "Bitsure Teddy Premium",
        "payment_success": "✅ *Payment successful!*\n\nYour account is now *{role}*.\nThank you for supporting Bitsure Teddy! 🧸💸",
        "stripe_soon": "ℹ️ Stripe payment coming soon.",
        
        # ---- Premium required ----
        "premium_required": "🔒 *Premium Feature*\n\nThis command is reserved for PRO and ELITE members.\nUse /upgrade to discover our offers.",
        
        # ---- Limits & Quotas ----
        "limit_reached": "❌ You have reached your daily request limit. Upgrade to premium for unlimited access.",
        "watchlist_limit": "❌ You have reached the limit of 3 symbols in free mode.\nUpgrade to Premium to add more: /upgrade",
        "watchlist_added": "✅ {symbol} added to your watchlist.",
        "watchlist_removed": "✅ {symbol} removed from your watchlist.",
        "watchlist_empty": "Your watchlist is empty.",
        "watchlist_scan_empty": "Watchlist empty.",
        "watchlist_scan_result": "📊 *Watchlist scan:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",
        
        # ---- Alerts ----
        "alert_usage": "Usage: /alert SYMBOL above/below PRICE",
        "alert_invalid_price": "Invalid price.",
        "alert_invalid_cond": "Condition must be 'above' or 'below'.",
        "alert_created": "✅ Alert #{id} created: {symbol} {cond} {price}",
        "alerts_empty": "No active alerts.",
        "alerts_list_title": "*Your alerts:*\n",
        "alert_deleted": "✅ Alert #{id} deleted.",
        "alert_not_found": "❌ Alert not found.",
        "alerts_cleared": "✅ All your alerts have been deleted.",
        
        # ---- Analysis & Price ----
        "symbole_invalide": "Invalid symbol.",
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "price_usage": "Usage: /price SYMBOL",
        "price_error": "❌ Price not available for {symbol}.",
        "price_format": "*{symbol}*\n💰 Price: {price}\n📊 Bid: {bid} / Ask: {ask}",
        
        # ---- Tick / Spread ----
        "tick_usage": "Usage: /tick SYMBOL",
        "tick_none": "❌ No recent tick.",
        "tick_current": "🕒 Last tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOL",
        "spread_format": "*{symbol}* Spread: {spread}",
        "spread_unavailable": "❌ Spread unavailable.",
        
        # ---- Scalping (Premium) ----
        "scalp_dev": "⚡ Scalping in development (Premium).",
        
        # ---- Trend & Volatility ----
        "trend_usage": "Usage: /trend SYMBOL",
        "trend_no_data": "No data available.",
        "trend_haussiere": "Bullish",
        "trend_baissiere": "Bearish",
        "trend_neutre": "Neutral",
        "trend_result": "*{symbol}* Trend: {tend}",
        "volatility_wip": "Volatility calculation (ATR) in progress...",
        "correlation_wip": "Correlation in development.",
        "levels_usage": "Usage: /levels SYMBOL",
        "levels_no_data": "No data available.",
        "levels_result": "*{symbol}* Levels:\nSupport: {support}\nResistance: {resistance}",
        
        # ---- Settings ----
        "settings_info": "⚙️ *Settings*\nTimeframe: {tf}\nRisk: {risk}\nLanguage: {lang_name}\nRole: {role}\nPremium: {prem}",
        "settimeframe_usage": "Usage: /settimeframe 1h|4h|1d",
        "settimeframe_invalid": "Invalid timeframe.",
        "settimeframe_success": "✅ Default timeframe: {tf}",
        "setrisk_usage": "Usage: /setrisk low|medium|high",
        "setrisk_invalid": "Invalid risk.",
        "setrisk_success": "✅ Risk profile: {risk}",
        "setlanguage_usage": "Usage: /setlanguage en|fr",
        "setlanguage_invalid": "Invalid language. Use 'en' or 'fr'.",
        "setlanguage_success_fr": "✅ Langue définie sur Français.",
        "setlanguage_success_en": "✅ Language set to English.",
        "usage_requests_remaining": "📊 Requests remaining today: {rem}",
        "usage_unlimited": "✅ Premium: unlimited requests.",
        
        # ---- Info & Admin ----
        "status_ok": "✅ Bot operational. APIs: Twelve Data, Yahoo, RealMarket.",
        "about": "Teddy Trading Bot v1.0 – Bitsure Teddy\nDeveloped for professional trading.",
        "symbolinfo": "ℹ️ Use /analyse for detailed info.",
        "myid": "Your Telegram ID: `{user_id}`",
        "broadcast_admin_only": "⛔ Admin only command.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast sent to {success}/{total} users.",
        "reload_success": "✅ Configuration reloaded.",
        "stats_info": "📊 *BITSURE TEDDY STATISTICS*\n👥 Total users: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}\n👑 ELITE: {elite}\n🚀 LIFETIME sold: {lifetime}/50",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro/elite)",
        "setrole_invalid_id": "❌ Invalid USER_ID.",
        "setrole_invalid_role": "❌ Invalid role. Use free, pro, or elite.",
        "setrole_success": "✅ User {target_id} role updated: *{role}*",
        
        # ---- Popular symbols ----
        "symboles_list": "📊 *POPULAR SYMBOLS*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Example: /analyse BTCUSD",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    texts = TEXTS.get(lang, TEXTS["fr"])
    text = texts.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text