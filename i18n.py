# i18n.py - Traductions complètes FR / EN pour Bitsure Teddy

TEXTS = {
    "fr": {
        "start": "🐻 *Bitsure Teddy* – Analyse de marché pro\n\nStatut : {status}\nCommandes : /help\nOffres : /upgrade",
        "start_disclaimer": "\n\n⚠️ *Version Beta – Merci de votre soutien !*\nCe bot est en cours d'amélioration. L'anglais peut contenir des erreurs et les données des actions ne sont pas encore toutes disponibles. Ces points seront corrigés progressivement grâce à vos retours et aux futurs financements. Merci de faire partie de l'aventure Bitsure Teddy ! 🧸",
        "status_free_trial": "🆓 Essai gratuit (3 jours)",
        "status_free_ended": "🆓 Gratuit (essai terminé)",
        "status_pro": "💎 PRO",
        "status_elite": "👑 ELITE",
        "international_payment_info": "\n\n🌍 *Vous êtes dans un pays où les paiements internationaux sont difficiles ?*\nPas de problème. Contactez l'administrateur pour un arrangement manuel : /support",

        "help_full": (
            "🧸 *Commandes disponibles :*\n\n"
            "/analyse SYMBOLE – Analyse complète\n"
            "/price SYMBOLE – Prix actuel\n"
            "/scalp SYMBOLE DUREE – Scalping (Premium)\n"
            "/tick SYMBOLE – Dernier tick\n"
            "/spread SYMBOLE – Spread bid/ask\n"
            "/alert SYMBOLE above/below PRIX – Créer alerte\n"
            "/alerts – Lister alertes\n"
            "/delalert ID – Supprimer alerte\n"
            "/clearalerts – Tout supprimer\n"
            "/watchlist – Voir liste\n"
            "/addwatch SYMBOLE – Ajouter symbole\n"
            "/removewatch SYMBOLE – Retirer\n"
            "/scan – Scanner watchlist\n"
            "/trend SYMBOLE – Tendance\n"
            "/volatility SYMBOLE – Volatilité\n"
            "/correlation S1 S2 – Corrélation\n"
            "/levels SYMBOLE – Supports/Résistances\n"
            "/settings – Paramètres\n"
            "/settimeframe TF – 1h/4h/1d\n"
            "/setrisk PROFIL – low/medium/high\n"
            "/setlanguage LANG – en/fr\n"
            "/usage – Requêtes restantes\n"
            "/status – État du bot\n"
            "/about – Version\n"
            "/symbolinfo SYMBOLE – Infos\n"
            "/myid – Votre ID\n"
            "/upgrade – Offres Premium\n"
            "/support – Contacter admin\n"
            "/symboles – Symboles populaires\n"
            "/redeem CODE – Utiliser un code promo"
        ),
        "help_admin": "\n\nAdmin : /broadcast, /reload, /stats, /setrole, /gift, /revoke",

        "support": "📞 Besoin d'aide ?\n\nContactez l'administrateur : @btsr_teddy09",

        "upgrade_title": "💳 *Choisissez votre offre :*\n\n• PRO : 9,99€/mois – illimité, scalping\n• ELITE : 24,99€/mois – PRO + groupe privé + support prioritaire\n\n⚠️ Les prix en Telegram Stars sont majorés en raison des commissions.",
"button_pro_stars": "💎 PRO – 15,99€/mois (Stars)",
"button_elite_stars": "👑 ELITE – 39,99€/mois (Stars)",
"button_pro_stripe": "💳 PRO – 9,99€/mois (Stripe bientôt)",
"button_elite_stripe": "💳 ELITE – 24,99€/mois (Stripe bientôt)",
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO et ELITE.\nUtilisez /upgrade pour découvrir nos offres.",

        "limit_reached": "❌ Vous avez atteint votre limite quotidienne de requêtes. Passez premium pour un accès illimité.",
        "watchlist_limit": "❌ Vous avez atteint la limite de 3 symboles en mode gratuit.\nPassez Premium pour en ajouter plus : /upgrade",
        "watchlist_added": "✅ {symbol} ajouté à votre watchlist.",
        "watchlist_removed": "✅ {symbol} retiré de votre watchlist.",
        "watchlist_empty": "Votre watchlist est vide.",
        "watchlist_scan_empty": "Watchlist vide.",
        "watchlist_scan_result": "📊 *Scan watchlist:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",

        "alert_usage": "Usage: /alert SYMBOLE above/below PRIX",
        "alert_invalid_price": "Prix invalide.",
        "alert_invalid_cond": "Condition doit être 'above' ou 'below'.",
        "alert_created": "✅ Alerte #{id} créée : {symbol} {cond} {price}",
        "alerts_empty": "Aucune alerte active.",
        "alerts_list_title": "*Vos alertes :*\n",
        "alert_deleted": "✅ Alerte #{id} supprimée.",
        "alert_not_found": "❌ Alerte non trouvée.",
        "alerts_cleared": "✅ Toutes vos alertes ont été supprimées.",

        "symbole_invalide": "Symbole invalide.",
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix non disponible pour {symbol}.",
        "price_format": "*{symbol}*\n💰 Prix: {price}\n📊 Bid: {bid} / Ask: {ask}",

        "tick_usage": "Usage: /tick SYMBOLE",
        "tick_none": "❌ Aucun tick récent.",
        "tick_current": "🕒 Dernier tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOLE",
        "spread_format": "*{symbol}* Spread: {spread}",
        "spread_unavailable": "❌ Spread non disponible.",

        "scalp_usage": "Usage: /scalp SYMBOLE DURÉE (3,5,10,20)",
        "scalp_invalid_duration": "Durée invalide. Choisissez 3, 5, 10 ou 20 secondes.",
        "scalp_signal_buy": "ACHETER",
        "scalp_signal_sell": "VENDRE",
        "scalp_signal_wait": "ATTENDRE",
        "scalp_result": "⚡ *Scalping {symbol} ({duration}s)*\nSignal: *{signal}*\nPrix: {price}\nBid: {bid} / Ask: {ask}\nVolatilité: {volatility}%\n\n{reason}",

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

        "status_ok": "✅ Bot opérationnel. APIs: Twelve Data, Yahoo, RealMarket.",
        "about": "Teddy Trading Bot v1.0 – Bitsure Teddy\nDéveloppé pour trading professionnel.",
        "symbolinfo": "ℹ️ Utilisez /analyse pour les infos détaillées.",
        "myid": "Votre ID Telegram: `{user_id}`",
        "broadcast_admin_only": "⛔ Commande réservée à l'administrateur.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast envoyé à {success}/{total} utilisateurs.",
        "reload_success": "✅ Configuration rechargée.",
        "stats_info": "📊 *STATISTIQUES BITSURE TEDDY*\n👥 Utilisateurs totaux : {total}\n🆓 FREE : {free}\n💪 PRO : {pro}\n👑 ELITE : {elite}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro/elite)",
        "setrole_invalid_id": "❌ USER_ID invalide.",
        "setrole_invalid_role": "❌ Rôle invalide. Utilisez free, pro, ou elite.",
        "setrole_success": "✅ Rôle de l'utilisateur {target_id} mis à jour : *{role}*",

        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro/elite)",
        "gift_success": "✅ Rôle {role} offert à {target_id} pour {days} jours.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ Rôle de l'utilisateur {target_id} révoqué (free).",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Code promo appliqué : {message}",
        "redeem_invalid": "❌ Code promo invalide ou expiré.",

        "symboles_list": "📊 *SYMBOLES POPULAIRES*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Exemple : /analyse BTCUSD",
    },
    "en": {
        "start": "🐻 *Bitsure Teddy* – Professional Market Analysis\n\nStatus: {status}\nCommands: /help\nOffers: /upgrade",
        "start_disclaimer": "\n\n⚠️ *Beta Version – Thank you for your support!*\nThis bot is a work in progress. English may contain errors and stock data is not fully available yet. These issues will be fixed over time as we secure more funding. Thank you for being part of the Bitsure Teddy journey! 🧸",
        "status_free_trial": "🆓 Free trial (3 days)",
        "status_free_ended": "🆓 Free (trial ended)",
        "status_pro": "💎 PRO",
        "status_elite": "👑 ELITE",
        "international_payment_info": "\n\n🌍 *Are you in a country where international payments are difficult?*\nNo problem. Contact the administrator for a manual arrangement: /support",

        "help_full": (
            "🧸 *Available commands:*\n\n"
            "/analyse SYMBOL – Full analysis\n"
            "/price SYMBOL – Current price\n"
            "/scalp SYMBOL DURATION – Scalping (Premium)\n"
            "/tick SYMBOL – Latest tick\n"
            "/spread SYMBOL – Bid/ask spread\n"
            "/alert SYMBOL above/below PRICE – Create price alert\n"
            "/alerts – List your alerts\n"
            "/delalert ID – Delete an alert\n"
            "/clearalerts – Delete all alerts\n"
            "/watchlist – View your watchlist\n"
            "/addwatch SYMBOL – Add a symbol\n"
            "/removewatch SYMBOL – Remove a symbol\n"
            "/scan – Scan your watchlist\n"
            "/trend SYMBOL – Global trend\n"
            "/volatility SYMBOL – Volatility (ATR)\n"
            "/correlation S1 S2 – 30‑day correlation\n"
            "/levels SYMBOL – Support/resistance levels\n"
            "/settings – View your settings\n"
            "/settimeframe TF – 1h,4h,1d\n"
            "/setrisk PROFILE – low, medium, high\n"
            "/setlanguage LANG – en/fr\n"
            "/usage – Remaining requests\n"
            "/status – Bot status\n"
            "/about – Version & credits\n"
            "/symbolinfo SYMBOL – Symbol info\n"
            "/myid – Get your Telegram ID\n"
            "/upgrade – Premium offers\n"
            "/support – Contact admin\n"
            "/symboles – Popular symbols\n"
            "/redeem CODE – Use a promo code"
        ),
        "help_admin": "\n\nAdmin: /broadcast, /reload, /stats, /setrole, /gift, /revoke",

        "support": "📞 Need help?\n\nContact admin: @btsr_teddy09",

       "upgrade_title": "💳 *Choose your plan:*\n\n• PRO: 9.99€/month – unlimited, scalping\n• ELITE: 24.99€/month – PRO + private group + priority support\n\n⚠️ Telegram Stars prices are higher due to platform fees.",
"button_pro_stars": "💎 PRO – 15.99€/month (Stars)",
"button_elite_stars": "👑 ELITE – 39.99€/month (Stars)",
"button_pro_stripe": "💳 PRO – 9.99€/month (Stripe soon)",
"button_elite_stripe": "💳 ELITE – 24.99€/month (Stripe soon)",
        "premium_required": "🔒 *Premium Feature*\n\nThis command is reserved for PRO and ELITE members.\nUse /upgrade to discover our offers.",

        "limit_reached": "❌ You have reached your daily request limit. Upgrade to premium for unlimited access.",
        "watchlist_limit": "❌ You have reached the limit of 3 symbols in free mode.\nUpgrade to Premium to add more: /upgrade",
        "watchlist_added": "✅ {symbol} added to your watchlist.",
        "watchlist_removed": "✅ {symbol} removed from your watchlist.",
        "watchlist_empty": "Your watchlist is empty.",
        "watchlist_scan_empty": "Watchlist empty.",
        "watchlist_scan_result": "📊 *Watchlist scan:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",

        "alert_usage": "Usage: /alert SYMBOL above/below PRICE",
        "alert_invalid_price": "Invalid price.",
        "alert_invalid_cond": "Condition must be 'above' or 'below'.",
        "alert_created": "✅ Alert #{id} created: {symbol} {cond} {price}",
        "alerts_empty": "No active alerts.",
        "alerts_list_title": "*Your alerts:*\n",
        "alert_deleted": "✅ Alert #{id} deleted.",
        "alert_not_found": "❌ Alert not found.",
        "alerts_cleared": "✅ All your alerts have been deleted.",

        "symbole_invalide": "Invalid symbol.",
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "price_usage": "Usage: /price SYMBOL",
        "price_error": "❌ Price not available for {symbol}.",
        "price_format": "*{symbol}*\n💰 Price: {price}\n📊 Bid: {bid} / Ask: {ask}",

        "tick_usage": "Usage: /tick SYMBOL",
        "tick_none": "❌ No recent tick.",
        "tick_current": "🕒 Last tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOL",
        "spread_format": "*{symbol}* Spread: {spread}",
        "spread_unavailable": "❌ Spread unavailable.",

        "scalp_usage": "Usage: /scalp SYMBOL DURATION (3,5,10,20)",
        "scalp_invalid_duration": "Invalid duration. Choose 3, 5, 10 or 20 seconds.",
        "scalp_signal_buy": "BUY",
        "scalp_signal_sell": "SELL",
        "scalp_signal_wait": "WAIT",
        "scalp_result": "⚡ *Scalping {symbol} ({duration}s)*\nSignal: *{signal}*\nPrice: {price}\nBid: {bid} / Ask: {ask}\nVolatility: {volatility}%\n\n{reason}",

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

        "status_ok": "✅ Bot operational. APIs: Twelve Data, Yahoo, RealMarket.",
        "about": "Teddy Trading Bot v1.0 – Bitsure Teddy\nDeveloped for professional trading.",
        "symbolinfo": "ℹ️ Use /analyse for detailed info.",
        "myid": "Your Telegram ID: `{user_id}`",
        "broadcast_admin_only": "⛔ Admin only command.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast sent to {success}/{total} users.",
        "reload_success": "✅ Configuration reloaded.",
        "stats_info": "📊 *BITSURE TEDDY STATISTICS*\n👥 Total users: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}\n👑 ELITE: {elite}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro/elite)",
        "setrole_invalid_id": "❌ Invalid USER_ID.",
        "setrole_invalid_role": "❌ Invalid role. Use free, pro, or elite.",
        "setrole_success": "✅ User {target_id} role updated: *{role}*",

        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro/elite)",
        "gift_success": "✅ {role} role granted to {target_id} for {days} days.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ User {target_id} role revoked (free).",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Promo code applied: {message}",
        "redeem_invalid": "❌ Invalid or expired promo code.",

        "symboles_list": "📊 *POPULAR SYMBOLS*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Example: /analyse BTCUSD",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    texts = TEXTS.get(lang, TEXTS["en"])
    text = texts.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text