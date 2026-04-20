# i18n.py - Traductions complètes FR / EN pour Bitsure Teddy

TEXTS = {
    "fr": {
        # ----- Accueil / Statuts -----
        "start": (
            "🐻 *Bitsure Teddy* – Votre assistant trading intelligent\n\n"
            "📊 Analyses techniques avancées (crypto, forex, actions, matières premières)\n"
            "⚡ Signaux scalping en temps réel\n"
            "🚨 Alertes de prix personnalisées\n"
            "🧸 Challenge scalping & historique vérifiable\n\n"
            "*Statut actuel :* {status}\n\n"
            "🔹 /menu – Menu principal\n"
            "🔹 /help – Liste des commandes\n"
            "🔹 /upgrade – Passer à PRO\n\n"
            "Bons trades ! 🧸"
        ),
        "start_disclaimer": (
            "\n\n⚠️ *Version Beta – Merci de votre soutien !*\n"
            "Ce bot est en cours d'amélioration. L'anglais peut contenir des erreurs et les données des actions "
            "ne sont pas encore toutes disponibles. Ces points seront corrigés progressivement grâce à vos retours "
            "et aux futurs financements. Merci de faire partie de l'aventure Bitsure Teddy ! 🧸"
        ),
        "status_free_trial": "🆓 Essai gratuit (3 jours)",
        "status_free_ended": "🆓 Gratuit (essai terminé)",
        "status_pro": "💎 PRO",
        "international_payment_info": (
            "\n\n🌍 *Vous êtes dans un pays où les paiements internationaux sont difficiles ?*\n"
            "Pas de problème. Contactez l'administrateur pour un arrangement manuel : /support"
        ),

        # ----- Aide -----
        "help_full": (
            "🧸 *Commandes disponibles :*\n\n"
            "/menu – Menu principal interactif\n"
            "/analyse SYMBOLE – Analyse complète\n"
            "/price SYMBOLE – Prix actuel\n"
            "/scalp SYMBOLE DURÉE – Scalping (Premium)\n"
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
            "/trend SYMBOLE – Tendance globale\n"
            "/volatility SYMBOLE – Volatilité (ATR)\n"
            "/correlation S1 S2 – Corrélation 30 jours\n"
            "/levels SYMBOLE – Supports/Résistances\n"
            "/sentiment – Fear & Greed Index crypto\n"
            "/compare SYM1 SYM2 – Comparaison rapide\n"
            "/top crypto – Top 5 crypto en hausse\n"
            "/fav add/remove/list – Symboles favoris\n"
            "/learn [terme] – Mini centre de formation\n"
            "/settings – Paramètres\n"
            "/settimeframe TF – 1h/4h/1d\n"
            "/setrisk PROFIL – low/medium/high\n"
            "/setlanguage LANG – en/fr\n"
            "/usage – Requêtes restantes\n"
            "/status – État du bot\n"
            "/about – Version\n"
            "/symbolinfo SYMBOLE – Infos symbole\n"
            "/myid – Votre ID Telegram\n"
            "/upgrade – Offre PRO\n"
            "/support – Contacter admin\n"
            "/symboles – Symboles populaires\n"
            "/challenge – Défi scalping (5 trades)\n"
            "/historique – Historique des signaux\n"
            "/snapshot – Image pour partage\n"
            "/verify ID – Vérifier un signal\n"
            "/redeem CODE – Utiliser un code promo"
        ),
        "help_admin": "\n\nAdmin : /broadcast, /reload, /stats, /setrole, /gift, /revoke",

        # ----- Support / Upgrade -----
        "support": "📞 Besoin d'aide ?\n\nContactez l'administrateur : @btsr_teddy09",
        "upgrade_title": (
            "💳 *Passez à Bitsure Teddy PRO*\n\n"
            "• Analyses illimitées\n"
            "• Scalping temps réel\n"
            "• Watchlist étendue\n"
            "• Support prioritaire\n\n"
            "*Choisissez votre mode de paiement :*"
        ),
        "button_pro_stars": "⭐ PRO – 14,99€/mois (Telegram Stars)",
        "button_pro_stripe": "💳 PRO – 15,99€/mois (Carte bancaire)",
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO.\nUtilisez /upgrade pour découvrir l'offre.",
        "payment_success": "✅ *Paiement réussi !*\nVous êtes maintenant *PRO*.\nMerci de votre confiance ! 🧸",
        "stripe_soon": "💳 Le paiement par carte bancaire sera disponible très prochainement. En attendant, vous pouvez utiliser les Telegram Stars ou contacter le support.",

        # ----- Limites -----
        "limit_reached": "❌ Vous avez atteint votre limite quotidienne de requêtes. Passez PRO pour un accès illimité : /upgrade",
        "watchlist_limit": "❌ Vous avez atteint la limite de 3 symboles en mode gratuit.\nPassez PRO pour en ajouter plus : /upgrade",

        # ----- Watchlist -----
        "watchlist_added": "✅ {symbol} ajouté à votre watchlist.",
        "watchlist_removed": "✅ {symbol} retiré de votre watchlist.",
        "watchlist_empty": "Votre watchlist est vide.",
        "watchlist_scan_empty": "Watchlist vide.",
        "watchlist_scan_result": "📊 *Scan watchlist:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",

        # ----- Alertes -----
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
        "clearalerts_confirm": "⚠️ Êtes-vous sûr de vouloir supprimer TOUTES vos alertes ?",
        "confirm_yes": "✅ Oui",
        "confirm_no": "❌ Non",

        # ----- Symboles -----
        "symbole_invalide": "Symbole invalide.",
        "symboles_list": (
            "📊 *SYMBOLES POPULAIRES*\n\n"
            "🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n"
            "💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n"
            "✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n"
            "📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n"
            "💡 Exemple : /analyse BTCUSD"
        ),

        # ----- Analyse -----
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "analyse_caption": (
            "*{symbol}* – *{signal}*  [CONFIANCE: {confidence}]\n"
            "💰 Prix: {price} | SL: {sl} | TP: {tp} | Ratio R/R: {rr_ratio}\n"
            "{reason}\n{risk_advice}\n\n"
            "📊 RSI: {rsi:.2f} | Stoch: {stoch_k:.1f}/{stoch_d:.1f} | ADX: {adx:.1f}\n"
            "📈 SMA20: {sma20} | SMA50: {sma50}\n"
            "🧸 Teddy Score: {teddy_score}/100"
        ),
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix non disponible pour {symbol}.",
        "price_format": "*{symbol}*\n💰 Prix: {price}\n📊 Bid: {bid} / Ask: {ask}",

        # ----- Scalping -----
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
        "scalp_result": (
            "⚡ *Scalping {symbol} ({duration}s)*\n"
            "Signal: *{signal}*\n"
            "Prix: {price}\n"
            "Bid: {bid} / Ask: {ask}\n"
            "Spread: {spread} ({spread_pct}%)\n"
            "RSI: {rsi:.1f}\n"
            "{reason}"
        ),

        # ----- Tendance / Volatilité / Corrélation / Niveaux -----
        "trend_usage": "Usage: /trend SYMBOLE",
        "trend_no_data": "Données non disponibles.",
        "trend_haussiere": "Haussière",
        "trend_baissiere": "Baissière",
        "trend_neutre": "Neutre",
        "trend_result": "*{symbol}* Tendance: {tend}",
        "volatility_usage": "Usage: /volatility SYMBOLE",
        "volatility_result": "*{symbol}* Volatilité (ATR 14): {atr}",
        "correlation_usage": "Usage: /correlation SYMBOLE1 SYMBOLE2",
        "correlation_result": "*{symbol1} vs {symbol2}* Corrélation 30j: {corr:.2f}",
        "levels_usage": "Usage: /levels SYMBOLE",
        "levels_no_data": "Données non disponibles.",
        "levels_result": (
            "*{symbol}* Niveaux:\n"
            "Support: {support}\n"
            "Résistance: {resistance}\n"
            "Fibonacci (dernier swing):\n"
            "• 0.382: {fib382}\n"
            "• 0.500: {fib500}\n"
            "• 0.618: {fib618}"
        ),

        # ----- Sentiment / Compare / Top / Fav -----
        "sentiment_result": "📊 *Fear & Greed Index Crypto*\n\nValeur actuelle: {value}\nClassification: {classification}\n\nMise à jour: {timestamp}",
        "compare_result": "*{symbol1} vs {symbol2}*\n\n{price1} | {change1}\n{price2} | {change2}\nRSI: {rsi1} vs {rsi2}\nTendance: {trend1} vs {trend2}",
        "top_crypto": "🚀 *Top 5 Crypto en hausse (24h)*\n\n{list}",
        "fav_usage": "Usage: /fav add|remove|list [symbole]",
        "fav_added": "✅ {symbol} ajouté aux favoris.",
        "fav_removed": "✅ {symbol} retiré des favoris.",
        "fav_list": "⭐ *Vos favoris:*\n{symbols}",
        "fav_empty": "Aucun favori enregistré.",

        # ----- Learn -----
        "learn_usage": "Usage: /learn [terme]\nTermes disponibles: rsi, macd, sma, support, resistance, fibonacci, atr, adx, stochastic, spread",
        "learn_rsi": "*RSI (Relative Strength Index)*\nIndicateur de momentum mesurant la vitesse et l'ampleur des mouvements de prix. Valeurs extrêmes >70 (surachat) et <30 (survente).",
        "learn_macd": "*MACD*\nMoving Average Convergence Divergence. Suit la relation entre deux moyennes mobiles. Croisements utilisés pour signaux d'achat/vente.",
        "learn_sma": "*SMA (Simple Moving Average)*\nMoyenne des prix sur une période donnée. SMA20 et SMA50 sont des références courantes de tendance court/moyen terme.",
        "learn_support": "*Support*\nNiveau de prix où la demande est historiquement suffisante pour stopper une baisse.",
        "learn_resistance": "*Résistance*\nNiveau de prix où l'offre est historiquement suffisante pour stopper une hausse.",
        "learn_fibonacci": "*Fibonacci*\nNiveaux de retracement (38.2%, 50%, 61.8%) utilisés pour identifier des zones potentielles de support/résistance.",
        "learn_atr": "*ATR (Average True Range)*\nMesure de la volatilité moyenne sur une période. Utilisé pour placer des stop-loss.",
        "learn_adx": "*ADX (Average Directional Index)*\nMesure la force d'une tendance (valeurs >25 indiquent une tendance forte).",
        "learn_stochastic": "*Stochastic Oscillator*\nCompare le prix de clôture à la fourchette de prix sur une période. Zones >80 surachat, <20 survente.",
        "learn_spread": "*Spread*\nDifférence entre le prix acheteur (bid) et vendeur (ask). Un spread serré indique une bonne liquidité.",

        # ----- Paramètres -----
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

        # ----- Infos -----
        "status_ok": "✅ Bot opérationnel. APIs: Twelve Data, Yahoo Finance.",
        "about": "Teddy Trading Bot v2.0 – Bitsure Teddy\nDéveloppé pour trading professionnel.",
        "symbolinfo": "ℹ️ Utilisez /analyse pour les infos détaillées.",
        "myid": "Votre ID Telegram: `{user_id}`",

        # ----- Admin -----
        "broadcast_admin_only": "⛔ Commande réservée à l'administrateur.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast envoyé à {success}/{total} utilisateurs.",
        "reload_success": "✅ Configuration rechargée.",
        "stats_info": "📊 *STATISTIQUES BITSURE TEDDY*\n👥 Utilisateurs totaux : {total}\n🆓 FREE : {free}\n💪 PRO : {pro}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro)",
        "setrole_invalid_id": "❌ USER_ID invalide.",
        "setrole_invalid_role": "❌ Rôle invalide. Utilisez free ou pro.",
        "setrole_success": "✅ Rôle de l'utilisateur {target_id} mis à jour : *{role}*",
        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro)",
        "gift_success": "✅ Rôle {role} offert à {target_id} pour {days} jours.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ Rôle de l'utilisateur {target_id} révoqué (free).",
        "revoke_confirm": "⚠️ Révoquer l'accès de {target_id} ?",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Code promo appliqué : {message}",
        "redeem_invalid": "❌ Code promo invalide ou expiré.",
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nL'application pour Android et iOS est en cours de développement. Elle vous permettra d'accéder à toutes les analyses sans passer par Telegram. Restez à l'écoute ! 🧸",
        "gift_notification": "🎁 Vous avez reçu un accès {role} gratuit pour {days} jours ! Profitez-en !",

        # ----- Challenge / Snapshot / Verify -----
        "challenge_start": "🔥 *DÉFI SCALPING LANCÉ* 🔥\nAnalyse de 5 trades consécutifs sur EURUSD en cours...",
        "challenge_trade": "📊 *Trade {n}/5* – {signal} à {price}\nRésultat : {result} ({pips} pips)",
        "challenge_score": "🏆 *SCORE FINAL* : {wins}/5 gagnés\n{summary}",
        "snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nTeddy Score: {score}/100\nPrix: {price}",
        "verify_not_found": "❌ Aucun signal trouvé avec l'ID `{signal_id}`.",
        "verify_result": "🔍 *Signal #{signal_id}*\nÉmis le : {timestamp}\nSymbole : {symbol}\nSignal : {signal}\nPrix d'entrée : {price}\nRésultat : {result}",
        "history_title": "📜 *Historique des signaux*\n",
        "history_empty": "Aucun signal enregistré.",

        # ----- Signal Engine (confiance, SL/TP) -----
        "signal_insufficient_data": "Données insuffisantes",
        "signal_buy_reason": "📈 Signaux haussiers détectés",
        "signal_buy_advice": "⚠️ Entrée progressive conseillée",
        "signal_sell_reason": "📉 Signaux baissiers détectés",
        "signal_sell_advice": "⚠️ Risque de continuation",
        "signal_wait_overbought": "Marché suracheté, attendez une correction",
        "signal_wait_oversold": "Marché survendu, attendez un rebond",
        "signal_wait_neutral": "Aucun signal clair – phase de consolidation",
        "signal_wait_advice": "⏳ Attendre une confirmation",
        "confidence_high": "FORTE",
        "confidence_medium": "MOYENNE",
        "confidence_low": "FAIBLE",

        # ----- Menu interactif -----
        "menu_title": "🧸 *MENU PRINCIPAL*\nSélectionnez une catégorie :",
        "menu_analyse": "📊 Analyse",
        "menu_scalping": "⚡ Scalping",
        "menu_alertes": "🚨 Alertes",
        "menu_watchlist": "📋 Watchlist",
        "menu_parametres": "⚙️ Paramètres",
        "menu_challenge": "🧸 Challenge",
        "menu_aide": "ℹ️ Aide",
        "back": "⬅️ Retour",

        # ----- Sélection de symboles -----
        "select_symbol": "Sélectionnez un symbole :",
        "category_crypto": "🪙 Cryptos",
        "category_forex": "💱 Forex",
        "category_commodities": "✨ Matières premières",
        "category_stocks": "📈 Actions",
        "category_fav": "⭐ Favoris",
        "prev_page": "⬅️",
        "next_page": "➡️"
    },

    "en": {
        # ----- Welcome / Status -----
        "start": (
            "🐻 *Bitsure Teddy* – Your smart trading assistant\n\n"
            "📊 Advanced technical analysis (crypto, forex, stocks, commodities)\n"
            "⚡ Real‑time scalping signals\n"
            "🚨 Custom price alerts\n"
            "🧸 Scalping challenge & verifiable history\n\n"
            "*Current status:* {status}\n\n"
            "🔹 /menu – Main menu\n"
            "🔹 /help – Command list\n"
            "🔹 /upgrade – Upgrade to PRO\n\n"
            "Happy trading! 🧸"
        ),
        "start_disclaimer": (
            "\n\n⚠️ *Beta Version – Thank you for your support!*\n"
            "This bot is a work in progress. English may contain errors and stock data is not fully available yet. "
            "These issues will be fixed over time as we secure more funding. Thank you for being part of the Bitsure Teddy journey! 🧸"
        ),
        "status_free_trial": "🆓 Free trial (3 days)",
        "status_free_ended": "🆓 Free (trial ended)",
        "status_pro": "💎 PRO",
        "international_payment_info": (
            "\n\n🌍 *Are you in a country where international payments are difficult?*\n"
            "No problem. Contact the administrator for a manual arrangement: /support"
        ),

        # ----- Help -----
        "help_full": (
            "🧸 *Available commands:*\n\n"
            "/menu – Interactive main menu\n"
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
            "/sentiment – Fear & Greed Index (crypto)\n"
            "/compare SYM1 SYM2 – Quick comparison\n"
            "/top crypto – Top 5 gainers (24h)\n"
            "/fav add/remove/list – Favorite symbols\n"
            "/learn [term] – Mini education center\n"
            "/settings – View your settings\n"
            "/settimeframe TF – 1h/4h/1d\n"
            "/setrisk PROFILE – low, medium, high\n"
            "/setlanguage LANG – en/fr\n"
            "/usage – Remaining requests\n"
            "/status – Bot status\n"
            "/about – Version & credits\n"
            "/symbolinfo SYMBOL – Symbol info\n"
            "/myid – Get your Telegram ID\n"
            "/upgrade – PRO offer\n"
            "/support – Contact admin\n"
            "/symboles – Popular symbols\n"
            "/challenge – Scalping challenge (5 trades)\n"
            "/historique – Signal history\n"
            "/snapshot – Instagram‑ready image\n"
            "/verify ID – Verify a signal\n"
            "/redeem CODE – Use a promo code"
        ),
        "help_admin": "\n\nAdmin: /broadcast, /reload, /stats, /setrole, /gift, /revoke",

        # ----- Support / Upgrade -----
        "support": "📞 Need help?\n\nContact admin: @btsr_teddy09",
        "upgrade_title": (
            "💳 *Upgrade to Bitsure Teddy PRO*\n\n"
            "• Unlimited analyses\n"
            "• Real‑time scalping\n"
            "• Extended watchlist\n"
            "• Priority support\n\n"
            "*Choose your payment method:*"
        ),
        "button_pro_stars": "⭐ PRO – €14.99/month (Telegram Stars)",
        "button_pro_stripe": "💳 PRO – €15.99/month (Credit Card)",
        "premium_required": "🔒 *Premium Feature*\n\nThis command is reserved for PRO members.\nUse /upgrade to discover the offer.",
        "payment_success": "✅ *Payment successful!*\nYou are now *PRO*.\nThank you for your trust! 🧸",
        "stripe_soon": "💳 Credit card payment will be available very soon. In the meantime, you can use Telegram Stars or contact support.",

        # ----- Limits -----
        "limit_reached": "❌ You have reached your daily request limit. Upgrade to PRO for unlimited access: /upgrade",
        "watchlist_limit": "❌ You have reached the limit of 3 symbols in free mode.\nUpgrade to PRO to add more: /upgrade",

        # ----- Watchlist -----
        "watchlist_added": "✅ {symbol} added to your watchlist.",
        "watchlist_removed": "✅ {symbol} removed from your watchlist.",
        "watchlist_empty": "Your watchlist is empty.",
        "watchlist_scan_empty": "Watchlist empty.",
        "watchlist_scan_result": "📊 *Watchlist scan:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",

        # ----- Alerts -----
        "alert_usage": "Usage: /alert SYMBOL above/below PRICE",
        "alert_invalid_price": "Invalid price format.",
        "alert_invalid_cond": "Condition must be 'above' or 'below'.",
        "alert_created": "✅ Alert #{id} created: {symbol} {cond} {price}",
        "alerts_empty": "No active alerts.",
        "alerts_list_title": "*Your alerts:*\n",
        "alert_deleted": "✅ Alert #{id} deleted.",
        "alert_not_found": "❌ Alert not found.",
        "alerts_cleared": "✅ All your alerts have been deleted.",
        "alert_triggered": "🚨 *Alert triggered*: {symbol} reached {condition} {price}\nCurrent price: {current_price}",
        "clearalerts_confirm": "⚠️ Are you sure you want to delete ALL your alerts?",
        "confirm_yes": "✅ Yes",
        "confirm_no": "❌ No",

        # ----- Symbols -----
        "symbole_invalide": "Invalid symbol.",
        "symboles_list": (
            "📊 *POPULAR SYMBOLS*\n\n"
            "🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n"
            "💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n"
            "✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n"
            "📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n"
            "💡 Example: /analyse BTCUSD"
        ),

        # ----- Analysis -----
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "analyse_caption": (
            "*{symbol}* – *{signal}*  [CONFIDENCE: {confidence}]\n"
            "💰 Price: {price} | SL: {sl} | TP: {tp} | R/R Ratio: {rr_ratio}\n"
            "{reason}\n{risk_advice}\n\n"
            "📊 RSI: {rsi:.2f} | Stoch: {stoch_k:.1f}/{stoch_d:.1f} | ADX: {adx:.1f}\n"
            "📈 SMA20: {sma20} | SMA50: {sma50}\n"
            "🧸 Teddy Score: {teddy_score}/100"
        ),
        "price_usage": "Usage: /price SYMBOL",
        "price_error": "❌ Price not available for {symbol}.",
        "price_format": "*{symbol}*\n💰 Price: {price}\n📊 Bid: {bid} / Ask: {ask}",

        # ----- Scalping -----
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
        "scalp_result": (
            "⚡ *Scalping {symbol} ({duration}s)*\n"
            "Signal: *{signal}*\n"
            "Price: {price}\n"
            "Bid: {bid} / Ask: {ask}\n"
            "Spread: {spread} ({spread_pct}%)\n"
            "RSI: {rsi:.1f}\n"
            "{reason}"
        ),

        # ----- Trend / Volatility / Correlation / Levels -----
        "trend_usage": "Usage: /trend SYMBOL",
        "trend_no_data": "No data available.",
        "trend_haussiere": "Bullish",
        "trend_baissiere": "Bearish",
        "trend_neutre": "Neutral",
        "trend_result": "*{symbol}* Trend: {tend}",
        "volatility_usage": "Usage: /volatility SYMBOL",
        "volatility_result": "*{symbol}* Volatility (ATR 14): {atr}",
        "correlation_usage": "Usage: /correlation SYMBOL1 SYMBOL2",
        "correlation_result": "*{symbol1} vs {symbol2}* 30d Correlation: {corr:.2f}",
        "levels_usage": "Usage: /levels SYMBOL",
        "levels_no_data": "No data available.",
        "levels_result": (
            "*{symbol}* Levels:\n"
            "Support: {support}\n"
            "Resistance: {resistance}\n"
            "Fibonacci (last swing):\n"
            "• 0.382: {fib382}\n"
            "• 0.500: {fib500}\n"
            "• 0.618: {fib618}"
        ),

        # ----- Sentiment / Compare / Top / Fav -----
        "sentiment_result": "📊 *Crypto Fear & Greed Index*\n\nCurrent value: {value}\nClassification: {classification}\n\nLast updated: {timestamp}",
        "compare_result": "*{symbol1} vs {symbol2}*\n\n{price1} | {change1}\n{price2} | {change2}\nRSI: {rsi1} vs {rsi2}\nTrend: {trend1} vs {trend2}",
        "top_crypto": "🚀 *Top 5 Crypto Gainers (24h)*\n\n{list}",
        "fav_usage": "Usage: /fav add|remove|list [symbol]",
        "fav_added": "✅ {symbol} added to favorites.",
        "fav_removed": "✅ {symbol} removed from favorites.",
        "fav_list": "⭐ *Your favorites:*\n{symbols}",
        "fav_empty": "No favorites saved.",

        # ----- Learn -----
        "learn_usage": "Usage: /learn [term]\nAvailable terms: rsi, macd, sma, support, resistance, fibonacci, atr, adx, stochastic, spread",
        "learn_rsi": "*RSI (Relative Strength Index)*\nMomentum indicator measuring speed and magnitude of price moves. Extreme values >70 (overbought) and <30 (oversold).",
        "learn_macd": "*MACD*\nMoving Average Convergence Divergence. Tracks relationship between two moving averages. Crossovers used for buy/sell signals.",
        "learn_sma": "*SMA (Simple Moving Average)*\nAverage price over a given period. SMA20 and SMA50 are common short/medium term trend references.",
        "learn_support": "*Support*\nPrice level where demand has historically been strong enough to stop a decline.",
        "learn_resistance": "*Resistance*\nPrice level where supply has historically been strong enough to stop a rally.",
        "learn_fibonacci": "*Fibonacci*\nRetracement levels (38.2%, 50%, 61.8%) used to identify potential support/resistance zones.",
        "learn_atr": "*ATR (Average True Range)*\nMeasures average volatility over a period. Used to set stop‑losses.",
        "learn_adx": "*ADX (Average Directional Index)*\nMeasures trend strength (values >25 indicate a strong trend).",
        "learn_stochastic": "*Stochastic Oscillator*\nCompares closing price to the price range over a period. Zones >80 overbought, <20 oversold.",
        "learn_spread": "*Spread*\nDifference between bid and ask price. A tight spread indicates good liquidity.",

        # ----- Settings -----
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

        # ----- Info -----
        "status_ok": "✅ Bot operational. APIs: Twelve Data, Yahoo Finance.",
        "about": "Teddy Trading Bot v2.0 – Bitsure Teddy\nDeveloped for professional trading.",
        "symbolinfo": "ℹ️ Use /analyse for detailed info.",
        "myid": "Your Telegram ID: `{user_id}`",

        # ----- Admin -----
        "broadcast_admin_only": "⛔ Admin only command.",
        "broadcast_usage": "Usage: /broadcast MESSAGE",
        "broadcast_sent": "✅ Broadcast sent to {success}/{total} users.",
        "reload_success": "✅ Configuration reloaded.",
        "stats_info": "📊 *BITSURE TEDDY STATISTICS*\n👥 Total users: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro)",
        "setrole_invalid_id": "❌ Invalid USER_ID.",
        "setrole_invalid_role": "❌ Invalid role. Use free or pro.",
        "setrole_success": "✅ User {target_id} role updated: *{role}*",
        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro)",
        "gift_success": "✅ {role} role granted to {target_id} for {days} days.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ User {target_id} role revoked (free).",
        "revoke_confirm": "⚠️ Revoke access for {target_id}?",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Promo code applied: {message}",
        "redeem_invalid": "❌ Invalid or expired promo code.",
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nThe Android and iOS app is currently in development. It will allow you to access all analyses without using Telegram. Stay tuned! 🧸",
        "gift_notification": "🎁 You have been granted free {role} access for {days} days! Enjoy!",

        # ----- Challenge / Snapshot / Verify -----
        "challenge_start": "🔥 *SCALPING CHALLENGE STARTED* 🔥\nAnalyzing 5 consecutive trades on EURUSD...",
        "challenge_trade": "📊 *Trade {n}/5* – {signal} at {price}\nResult: {result} ({pips} pips)",
        "challenge_score": "🏆 *FINAL SCORE*: {wins}/5 won\n{summary}",
        "snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nTeddy Score: {score}/100\nPrice: {price}",
        "verify_not_found": "❌ No signal found with ID `{signal_id}`.",
        "verify_result": "🔍 *Signal #{signal_id}*\nIssued on: {timestamp}\nSymbol: {symbol}\nSignal: {signal}\nEntry Price: {price}\nResult: {result}",
        "history_title": "📜 *Signal History*\n",
        "history_empty": "No signals recorded.",

        # ----- Signal Engine (confidence, SL/TP) -----
        "signal_insufficient_data": "Insufficient data",
        "signal_buy_reason": "📈 Bullish signals detected",
        "signal_buy_advice": "⚠️ Consider gradual entry",
        "signal_sell_reason": "📉 Bearish signals detected",
        "signal_sell_advice": "⚠️ Continuation risk",
        "signal_wait_overbought": "Market overbought, wait for pullback",
        "signal_wait_oversold": "Market oversold, wait for bounce",
        "signal_wait_neutral": "No clear signal – consolidation phase",
        "signal_wait_advice": "⏳ Wait for confirmation",
        "confidence_high": "HIGH",
        "confidence_medium": "MEDIUM",
        "confidence_low": "LOW",

        # ----- Interactive Menu -----
        "menu_title": "🧸 *MAIN MENU*\nSelect a category:",
        "menu_analyse": "📊 Analysis",
        "menu_scalping": "⚡ Scalping",
        "menu_alertes": "🚨 Alerts",
        "menu_watchlist": "📋 Watchlist",
        "menu_parametres": "⚙️ Settings",
        "menu_challenge": "🧸 Challenge",
        "menu_aide": "ℹ️ Help",
        "back": "⬅️ Back",

        # ----- Symbol Selection -----
        "select_symbol": "Select a symbol:",
        "category_crypto": "🪙 Crypto",
        "category_forex": "💱 Forex",
        "category_commodities": "✨ Commodities",
        "category_stocks": "📈 Stocks",
        "category_fav": "⭐ Favorites",
        "prev_page": "⬅️",
        "next_page": "➡️"
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