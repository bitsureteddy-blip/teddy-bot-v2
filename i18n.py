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
            "/challenge – Défi scalping (5 trades)\n"
            "/snapshot – Image pour Instagram\n"
            "/verify ID – Vérifier un signal\n"
            "/redeem CODE – Utiliser un code promo\n"
            "/ask QUESTION – Poser une question à l'IA\n"
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
        "alert_triggered": "🚨 *Alerte déclenchée* : {symbol} a atteint {condition} {price}\nPrix actuel : {current_price}",

        "symbole_invalide": "Symbole invalide.",
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "analyse_caption": "*{symbol}* – Signal: *{signal}*\n{reason}\n{risk_advice}\n\n💰 Prix: {price}\n📊 RSI: {rsi:.2f}\n📈 SMA20: {sma20}, SMA50: {sma50}\n🧸 Score Teddy: {teddy_score}/100",
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
        "volatility_usage": "Usage: /volatility SYMBOLE",
        "volatility_wait": "⚙️ Calcul de la volatilité pour {symbol}...",
        "volatility_error": "❌ Impossible de calculer la volatilité pour {symbol}.",
        "volatility_result": "📊 *{symbol}* – Volatilité (ATR 14): {atr}","correlation_usage": "Usage: /correlation SYMBOLE1 SYMBOLE2",
        "correlation_wait": "⚙️ Calcul de la corrélation entre {sym1} et {sym2}...",
        "correlation_error": "❌ Impossible de calculer la corrélation.",
        "correlation_insufficient_data": "❌ Données insuffisantes pour calculer la corrélation.",
        "correlation_result": "📈 *Corrélation 30 jours*\n{sym1} ↔ {sym2} : {corr}",
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
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nL'application pour Android et iOS est en cours de développement. Elle vous permettra d'accéder à toutes les analyses sans passer par Telegram. Restez à l'écoute ! 🧸",
        "symboles_list": "📊 *SYMBOLES POPULAIRES*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Exemple : /analyse BTCUSD",
        "gift_notification": "🎁 Vous avez reçu un accès {role} gratuit pour {days} jours ! Profitez-en !",
        "ask_usage": "Usage : /ask <votre question>\nExemple : /ask Qu'est-ce que le RSI ?",
        "ask_thinking": "🤔 Je réfléchis...",
        "ask_error": "❌ Erreur IA : {error}", 

        # --- Signal Engine (Français) ---
        "signal_insufficient_data": "Données insuffisantes",
        "signal_buy_reason": "📈 Signaux haussiers détectés",
        "signal_buy_advice": "⚠️ Entrée progressive conseillée",
        "signal_sell_reason": "📉 Signaux baissiers détectés",
        "signal_sell_advice": "⚠️ Risque de continuation",
        "signal_wait_overbought": "Marché suracheté, attendez une correction",
        "signal_wait_oversold": "Marché survendu, attendez un rebond",
        "signal_wait_neutral": "Aucun signal clair – phase de consolidation",
        "signal_wait_advice": "⏳ Attendre une confirmation",
        # Dans "fr"
"challenge_start": "🔥 *DÉFI SCALPING LANCÉ* 🔥\nAnalyse de 5 trades consécutifs sur EURUSD en cours...",
"challenge_trade": "📊 *Trade {n}/5* – {signal} à {price}\nRésultat : {result} ({pips} pips)",
"challenge_score": "🏆 *SCORE FINAL* : {wins}/5 gagnés\n{summary}",
"snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nScore Teddy: {score}/100\nPrix: {price}",
"verify_not_found": "❌ Aucun signal trouvé avec l'ID `{signal_id}`.",
"verify_result": "🔍 *Signal #{signal_id}*\nÉmis le : {timestamp}\nSymbole : {symbol}\nSignal : {signal}\nPrix : {price}\nScore : {score}/100",

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
            "/challenge – Scalping challenge (5 trades)\n"
            "/snapshot – Instagram-ready image\n"
            "/verify ID – Verify a signal\n" 
            "/redeem CODE – Use a promo code\n"
            "/ask QUESTION – Ask the AI a question\n"
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
        "alert_triggered": "🚨 *Alert triggered*: {symbol} reached {condition} {price}\nCurrent price: {current_price}",

        "symbole_invalide": "Invalid symbol.",
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "analyse_caption": "*{symbol}* – Signal: *{signal}*\n{reason}\n{risk_advice}\n\n💰 Price: {price}\n📊 RSI: {rsi:.2f}\n📈 SMA20: {sma20}, SMA50: {sma50}\n🧸 Teddy Score: {teddy_score}/100",
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
        "volatility_usage": "Usage: /volatility SYMBOL",
        "volatility_wait": "⚙️ Calculating volatility for {symbol}...",
        "volatility_error": "❌ Could not calculate volatility for {symbol}.",
        "volatility_result": "📊 *{symbol}* – Volatility (ATR 14): {atr}","correlation_usage": "Usage: /correlation SYMBOL1 SYMBOL2",
        "correlation_wait": "⚙️ Calculating correlation between {sym1} and {sym2}...",
        "correlation_error": "❌ Could not calculate correlation.",
        "correlation_insufficient_data": "❌ Insufficient data to calculate correlation.",
        "correlation_result": "📈 *30-day Correlation*\n{sym1} ↔ {sym2}: {corr}",
 
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
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nThe Android and iOS app is currently in development. It will allow you to access all analyses without using Telegram. Stay tuned! 🧸",
        "symboles_list": "📊 *POPULAR SYMBOLS*\n\n🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n💡 Example: /analyse BTCUSD",
        "gift_notification": "🎁 You have been granted free {role} access for {days} days! Enjoy!",
        "ask_usage": "Usage: /ask <your question>\nExample: /ask What is RSI?",
        "ask_thinking": "🤔 Thinking...",
        "ask_error": "❌ AI Error: {error}", 

        # --- Signal Engine (English) ---
        "signal_insufficient_data": "Insufficient data",
        "signal_buy_reason": "📈 Bullish signals detected",
        "signal_buy_advice": "⚠️ Consider gradual entry",
        "signal_sell_reason": "📉 Bearish signals detected",
        "signal_sell_advice": "⚠️ Continuation risk",
        "signal_wait_overbought": "Market overbought, wait for pullback",
        "signal_wait_oversold": "Market oversold, wait for bounce",
        "signal_wait_neutral": "No clear signal – consolidation phase",
        "signal_wait_advice": "⏳ Wait for confirmation",
# Dans "en"
"challenge_start": "🔥 *SCALPING CHALLENGE STARTED* 🔥\nAnalyzing 5 consecutive trades on EURUSD...",
"challenge_trade": "📊 *Trade {n}/5* – {signal} at {price}\nResult: {result} ({pips} pips)",
"challenge_score": "🏆 *FINAL SCORE*: {wins}/5 won\n{summary}",
"snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nTeddy Score: {score}/100\nPrice: {price}",
"verify_not_found": "❌ No signal found with ID `{signal_id}`.",
"verify_result": "🔍 *Signal #{signal_id}*\nIssued on: {timestamp}\nSymbol: {symbol}\nSignal: {signal}\nPrice: {price}\nScore: {score}/100",
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