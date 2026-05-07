# i18n.py - Traductions complètes FR / EN pour Bitsure Teddy

TEXTS = {
    "fr": {
        # ----- Accueil / Statuts -----
        "start": (
            "🐻 *Bitsure Teddy* – Votre assistant trading intelligent\n\n"
            "📊 Analyses techniques avancées (crypto, forex, actions, matières premières)\n"
            "⚡ Signaux scalping en temps réel\n"
            "🚨 Alertes de prix personnalisées\n"
            "*Statut actuel :* {status}\n\n"
            "🔹 /menu – Menu principal\n"
            "🔹 /upgrade – Passer à PRO\n\n"
            "Bons trades ! 🧸"
        ),
        "start_disclaimer": "",
        "status_free_trial": "🆓 Essai gratuit (3 jours)",
        "status_free_ended": "🆓 Gratuit (essai terminé)",
        "status_pro": "💎 PRO",
        "international_payment_info": "",
        "terms_title": "📋 Conditions d'utilisation",
        "terms_text": (
            "Avant d'utiliser Bitsure Teddy, tu dois lire et accepter les conditions suivantes :\n\n"
            "1. Ce bot fournit des signaux de trading à titre indicatif uniquement. Aucun conseil financier n'est donné.\n"
            "2. Les performances passées (backtests) ne garantissent pas les résultats futurs.\n"
            "3. Tu es seul responsable de tes décisions de trading. Ne trade jamais plus que ce que tu es prêt à perdre.\n"
            "4. Le trading comporte des risques élevés. Bitsure Teddy et son créateur ne pourront être tenus responsables de tes pertes.\n"
            "5. En utilisant ce bot, tu confirmes avoir compris et accepté ces conditions."
        ),
        "terms_accept": "✅ J'accepte",
        "terms_refuse": "❌ Je refuse",
        "terms_accepted": "✅ Conditions acceptées. Bienvenue sur Bitsure Teddy ! Utilise /menu pour commencer.",
        "terms_refused_msg": "❌ Tu ne peux pas utiliser le bot sans accepter les conditions. Retape /start quand tu seras prêt.",
        "terms_must_accept": "⚠️ Tu dois d'abord accepter les conditions d'utilisation. Tape /start pour les consulter.",
        "terms_button": "📋 Lire les conditions d'utilisation",
        "check_usage": "Usage: /check SYMBOLE BUY|SELL",
        "check_choose_direction": "📊 {symbol} – Choisis la direction :",
        "check": "📊 VALIDATION {symbol}\n━━━━━━━━━━━━━━━━━━━\n✅ Tendance : {trend}\n✅ RSI : {rsi}\n⚠️ Volatilité : {volatility}\n📈 Score : {score}/100 → {light}\n🎯 SL : {sl}\n💰 TP : {tp}",
        "check_green": "🟢 FAVORABLE",
        "check_orange": "🟡 PRUDENT",
        "check_red": "🔴 RISQUÉ",
        "check_vol_high": "Élevée",
        "check_vol_normal": "Normale",
        "history_stats_header": "📊 TON HISTORIQUE\n━━━━━━━━━━━━━━━━━━━\n📈 Signaux reçus : {total}\n✅ Gagnants : {wins} ({win_rate}%)\n❌ Perdants : {losses}\n\n💰 Gain moyen : {avg}%\n📉 Pire : {worst}%\n🏆 Meilleur : {best}%\n\n💡 Conseil : {advice}\n\n📋 DERNIERS SIGNAUX :\n",
        "history_advice_high": "Continue, mais garde une gestion de risque stricte.",
        "history_advice_low": "Réduis le risque et privilégie les scores élevés.",
        "channel_required": "⚠️ Tu dois rejoindre le canal T's World pour utiliser Bitsure Teddy.\n\n👉 https://t.me/+c_xPX-20JAo0MTE0\n\nReviens après avoir rejoint !",
        "channel_verified": "✅ Abonnement vérifié. Bienvenue !",
        "channel_not_joined": "❌ Tu n'as pas encore rejoint le canal. Rejoins-le d'abord.",
        "check_subscription": "✅ J'ai rejoint",
        "ask_usage": "Usage : /ask <ta question>",
        "ask_wait": "🤔 Je réfléchis...",
        "ask_error": "❌ Erreur : {error}",

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
        "button_pro_stars": "⭐ PRO 19,99€/mois (Telegram Stars)",
        "button_binance_usdc": "🟡 Binance USDC",
        "binance_payment_info": (
            "🟡 Paiement Binance (USDC)\n\n"
            "1. Ouvre Binance → Portefeuille → Envoyer\n"
            "2. Entre l'ID Binance : {binance_id}\n"
            "3. Montant : {amount} USDC\n"
            "4. Vérifie que le pseudo affiché est bien le tien\n\n"
            "Ton ID de transaction : {memo}\n\n"
            "⚠️ Copie cet ID et envoie-le à l'admin après avoir payé."
        ),
        "confirm_payment_usage": "Usage: /confirm_payment <user_id>",
        "confirm_payment_ok": "✅ Paiement confirmé pour l'utilisateur {user_id}.",
        "confirm_payment_missing": "❌ Aucun paiement Binance en attente pour {user_id}.",
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO.\nUtilisez /upgrade pour découvrir l'offre.",
        "payment_success": "✅ *Paiement réussi !*\nVous êtes maintenant *PRO*.\nMerci de votre confiance ! 🧸",
        "stripe_soon": "💳 Le paiement par carte bancaire sera disponible très prochainement. En attendant, vous pouvez utiliser les Telegram Stars ou contacter le support.",
        "unavailable_option": "Option non disponible.",

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
        "addwatch_usage": "Usage: /addwatch SYMBOLE",
        "removewatch_usage": "Usage: /removewatch SYMBOLE",

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
        "delalert_usage": "Usage: /delalert ID",

        # ----- Symboles -----
        "symbole_invalide": "Symbole invalide.",
        "invalid_symbol": "Symbole invalide.",
        "symboles_list": (
            "📊 *SYMBOLES POPULAIRES*\n\n"
            "🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n"
            "💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Livre/Dollar\nUSDJPY – Dollar/Yen\n\n"
            "✨ *Matières premières*\nXAUUSD – Or\nXAGUSD – Argent\n\n"
            "📈 *Actions*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n"
            "💡 Exemple : /analyse BTCUSD"
        ),
        "symbol_not_found": "Symbole non trouvé.",
        "symbolinfo_usage": "Usage: /symbolinfo SYMBOLE",
        "symbolinfo_format": "*{symbol}*\nPrix: {price}\nBid/Ask: {bid} / {ask}",

        # ----- Analyse -----
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol} en cours...",
        "analyse_error": "❌ Impossible de récupérer les données pour {symbol}.",
        "analyse_caption": (
            "📊 *ANALYSE {symbol}*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🎯 Signal    : {signal_emoji} {signal}\n"
            "📈 Score     : {teddy_score}/100 ({confidence})\n"
            "💵 Prix      : {price}\n"
            "🛑 SL        : {sl}\n"
            "🎯 TP        : {tp} (RR: {rr_ratio})\n"
            "📊 RSI       : {rsi:.1f}\n"
            "📉 SMA20/50  : {sma20} / {sma50}\n"
            "📏 ADX       : {adx:.1f}\n"
            "💡 Raison    : {reason}\n"
            "⚠️ Conseil   : {risk_advice}\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix non disponible pour {symbol}.",
        "price_format": "💵 *{symbol}*\n━━━━━━━━━━━━━━━━━━━\n💰 Prix : {price}\n📉 Bid  : {bid}\n📈 Ask  : {ask}",
        "price_label": "Prix",

        # ----- Scalping -----
        "tick_usage": "Usage: /tick SYMBOLE",
        "tick_none": "❌ Aucun tick récent.",
        "tick_current": "🕒 *TICK {symbol}*\n━━━━━━━━━━━━━━━━━━━\n💰 Prix : {price}",
        "spread_usage": "Usage: /spread SYMBOLE",
        "spread_format": "📏 *SPREAD {symbol}*\n━━━━━━━━━━━━━━━━━━━\n📉 Bid    : {bid}\n📈 Ask    : {ask}\n📊 Spread : {spread}",
        "spread_unavailable": "❌ Spread non disponible.",
        "scalp_usage": "Usage: /scalp SYMBOLE DURÉE (3,5,10,20)",
        "scalp_invalid_duration": "Durée invalide. Choisissez 3, 5, 10 ou 20 secondes.",
        "scalp_signal_buy": "ACHETER",
        "scalp_signal_sell": "VENDRE",
        "scalp_signal_wait": "ATTENDRE",
        "scalp_result": (
            "⚡ *SCALPING {symbol} · {duration}s*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📊 Signal : {signal_emoji} {signal}\n"
            "💰 Prix    : {price}\n"
            "📉 Bid/Ask : {bid} / {ask}\n"
            "📏 Spread  : {spread} ({spread_pct}%)\n"
            "📈 RSI     : {rsi:.1f}\n"
            "📋 Raison  : {reason}\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "realtime_data_error": "❌ Impossible d'obtenir les données temps réel.",

        # ----- Tendance / Volatilité / Corrélation / Niveaux -----
        "trend_usage": "Usage: /trend SYMBOLE",
        "trend_no_data": "Données non disponibles.",
        "trend_haussiere": "Haussière",
        "trend_baissiere": "Baissière",
        "trend_neutre": "Neutre",
        "trend_bullish": "Haussière",
        "trend_bearish": "Baissière",
        "trend_neutral": "Neutre",
        "trend_result": "*{symbol}* Tendance: {tend}",
        "volatility_usage": "Usage: /volatility SYMBOLE",
        "volatility_result": "*{symbol}* Volatilité (ATR 14): {atr}",
        "correlation_usage": "Usage: /correlation SYMBOLE1 SYMBOLE2",
        "correlation_result": "*{symbol1} vs {symbol2}* Corrélation 30j: {corr:.2f}",
        "levels_usage": "Usage: /levels SYMBOLE",
        "levels_no_data": "Données non disponibles.",
        "levels_result": (
            "📏 *NIVEAUX {symbol}*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🟢 Support    : {support}\n"
            "🔴 Résistance : {resistance}\n"
            "📐 Fib 38.2%  : {fib382}\n"
            "📐 Fib 50.0%  : {fib500}\n"
            "📐 Fib 61.8%  : {fib618}"
        ),

        # ----- Sentiment / Compare / Top / Fav -----
        "sentiment_result": "📊 *Fear & Greed Index Crypto*\n\nValeur actuelle: {value}\nClassification: {classification}",
        "sentiment_error": "Impossible de récupérer le Fear & Greed Index.",
        "compare_usage": "Usage: /compare SYM1 SYM2",
        "compare_result": "*{symbol1} vs {symbol2}*\nTendance: {trend1} vs {trend2}",
        "top_crypto": "🚀 *Top 5 Crypto en hausse (24h)*\n\n{list}",
        "fav_usage": "Usage: /fav add|remove|list [symbole]",
        "fav_add_usage": "Usage: /fav add SYMBOLE",
        "fav_remove_usage": "Usage: /fav remove SYMBOLE",
        "fav_added": "✅ {symbol} ajouté aux favoris.",
        "fav_removed": "✅ {symbol} retiré des favoris.",
        "fav_list": "⭐ *Vos favoris:*\n{symbols}",
        "fav_empty": "Aucun favori enregistré.",
        "insufficient_data": "Données insuffisantes.",
        "insufficient_common_data": "Pas assez de données communes.",
        "data_unavailable": "Données indisponibles.",

        # ----- Learn -----
        "learn_usage": "Usage: /learn [terme]\nTermes disponibles: rsi, macd, sma, support, resistance, fibonacci, atr, adx, stochastic, spread",
        "learn_rsi": "*RSI*\nIndicateur de momentum mesurant vitesse et ampleur des mouvements de prix. >70 surachat, <30 survente.",
        "learn_macd": "*MACD*\nConvergence/divergence de moyennes mobiles. Croisements utilisés pour signaux d'achat/vente.",
        "learn_sma": "*SMA*\nMoyenne mobile simple. SMA20 et SMA50 sont des références courantes de tendance.",
        "learn_support": "*Support*\nNiveau de prix où la demande stoppe une baisse.",
        "learn_resistance": "*Résistance*\nNiveau de prix où l'offre stoppe une hausse.",
        "learn_fibonacci": "*Fibonacci*\nNiveaux de retracement (38.2%, 50%, 61.8%) utilisés pour zones de support/résistance.",
        "learn_atr": "*ATR*\nMesure de la volatilité moyenne. Utilisé pour placer des stop-loss.",
        "learn_adx": "*ADX*\nMesure la force d'une tendance (>25 = tendance forte).",
        "learn_stochastic": "*Stochastic*\nCompare le prix de clôture à la fourchette de prix. >80 surachat, <20 survente.",
        "learn_spread": "*Spread*\nDifférence entre prix acheteur (bid) et vendeur (ask).",

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
        "setlanguage_success_en": "✅ Langue définie sur Anglais.",
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
        "stats_info": "📊 *STATISTIQUES*\n👥 Total: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro)",
        "setrole_invalid_id": "❌ USER_ID invalide.",
        "setrole_invalid_role": "❌ Rôle invalide. Utilisez free ou pro.",
        "setrole_success": "✅ Rôle de l'utilisateur {target_id} mis à jour : *{role}*",
        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro)",
        "gift_success": "✅ Rôle {role} offert à {target_id} pour {days} jours.",
        "invalid_days": "❌ Nombre de jours invalide.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ Rôle de l'utilisateur {target_id} révoqué (free).",
        "revoke_confirm": "⚠️ Révoquer l'accès de {target_id} ?",
        "action_cancelled": "Action annulée.",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Code promo appliqué : {message}",
        "redeem_invalid": "❌ Code promo invalide ou expiré.",
        "redeem_already_used": "❌ Vous avez déjà utilisé ce code promo.",
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nL'application est en cours de développement. Restez à l'écoute ! 🧸",
        "gift_notification": "🎁 Vous avez reçu un accès {role} gratuit pour {days} jours !",

        # ----- Challenge / Snapshot / Verify -----
        "challenge_start": "🔥 *DÉFI SCALPING LANCÉ* 🔥\nAnalyse de 5 trades consécutifs sur EURUSD...",
        "challenge_trade": "📊 *Trade {n}/5* – {signal} à {price}\nRésultat : {result} ({pips} pips)",
        "challenge_score": "🏆 *SCORE FINAL* : {wins}/5 gagnés\n{summary}",
        "win": "Gagné",
        "loss": "Perdu",
        "pending": "En attente",
        "net_pips": "Pips nets",
        "snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nTeddy Score: {score}/100\nPrix: {price}",
        "verify_not_found": "❌ Aucun signal trouvé avec l'ID `{signal_id}`.",
        "verify_result": "🔍 *Signal #{signal_id}*\nÉmis le : {timestamp}\nSymbole : {symbol}\nSignal : {signal}\nPrix d'entrée : {price}\nRésultat : {result}",
        "verify_usage": "Usage: /verify SIGNAL_ID",
        "history_title": "📜 *Historique des signaux*\n",
        "history_empty": "Aucun signal enregistré.",
        "no_recent_analysis": "Aucune analyse récente.",

        # ----- Signal Engine -----
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
        "signal_buy": "ACHETER",
        "signal_sell": "VENDRE",
        "signal_wait": "ATTENDRE",
        "na": "N/A",

        # ----- Menu interactif -----
        "menu_title": "🧸 *MENU PRINCIPAL*\nSélectionnez une catégorie :",
        "menu_analyse": "📊 Analyse",
        "menu_scalping": "⚡ Scalping",
        "menu_alertes": "🚨 Alertes",
        "menu_watchlist": "📋 Watchlist",
        "menu_parametres": "⚙️ Paramètres",
                        "back": "⬅️ Retour",
        "menu_choose_command": "Choisissez une commande :",
        "menu_upgrade": "💎 Upgrade",
        "btn_analyse": "📊 Analyse",
        "btn_price": "💰 Prix",
        "btn_scalp": "⚡ Scalping",
        "btn_watchlist": "📋 Watchlist",
        "btn_settings": "⚙️ Paramètres",
        "btn_upgrade": "💎 Upgrade",
        "btn_historique": "📜 Historique",
        "btn_support": "📞 Support",
        "btn_trend": "📈 Tendance",
        "btn_volatility": "🌪 Volatilité",
        "btn_levels": "📍 Niveaux",
        "btn_symbolinfo": "ℹ️ Symbole",
        "btn_check": "✅ Check trade",
        "btn_paper": "📈 Paper Trading",
        "btn_tick": "🕒 Tick",
        "btn_spread": "↔️ Spread",
        "btn_alert": "➕ Alerte",
        "btn_alerts": "📑 Alertes",
        "btn_delalert": "➖ Supprimer alerte",
        "btn_clearalerts": "🧹 Effacer alertes",
        "btn_addwatch": "➕ Ajouter",
        "btn_removewatch": "➖ Retirer",
        "btn_scan": "🔎 Scanner",
        "btn_settimeframe": "⏱ Timeframe",
        "btn_setlanguage": "🌐 Langue",
        "btn_usage": "📊 Usage",
        "help_redirect": "Utilisez /menu pour accéder au menu interactif.",
        "trial_days_left": "Essai gratuit : {days} jours restants",
        "btn_upgrade_stars": "Telegram Stars (19,99€/mois)",
        "btn_upgrade_binance": "Binance Junior (USDC)",
        "settimeframe_choose": "Choisissez un timeframe :",
        "setlanguage_choose": "Choisissez une langue :",
        "delalert_pick": "Choisissez une alerte à supprimer :",
        "scalp_choose_duration": "Choisissez une durée :",
        "cond_above": "Au-dessus",
        "cond_below": "En-dessous",
        "alert_choose_condition": "Choisissez une condition :",
        "alert_enter_price": "Entrez le prix cible après la condition.",
        "alert_price_invalid_retry": "Prix invalide, réessayez.",
        "watchlist_already": "ℹ️ {symbol} est déjà dans ta watchlist.",
        "watchlist_missing": "ℹ️ {symbol} n'est pas dans ta watchlist.",
        "watchlist_added_styled": "✅ {symbol} ajouté à ta watchlist",
        "watchlist_removed_styled": "🗑️ {symbol} retiré de ta watchlist",
        "scalp_wait_reason": "Tous les indicateurs sont neutres, aucun edge détecté.",
        "scalp_fallback_buy": "RSI survendu fort détecté (fallback).",
        "scalp_fallback_sell": "RSI suracheté fort détecté (fallback).",
        "use_command": "Utilisez la commande /{cmd} pour plus d'informations.",
        "unknown_command": "Commande non reconnue : /{cmd}",
        "unknown_option": "Option non reconnue.",
        "unsupported_command": "Commande non supportée : /{command}",

        # ----- Backtest -----
        "backtest_start": "🚀 Lancement du backtest (peut prendre quelques instants)...",
        "backtest_no_data": "⚠️ Pas de données pour {symbol}",
        "backtest_no_trades": "ℹ️ {symbol}: Aucun trade.",
        "backtest_title": "📊 {symbol} – Résultats du backtest",
        "separator_line": "━━━━━━━━━━━━━━━━━━━━━━━━",
        "backtest_trades": "🔢 Trades        : {total}",
        "backtest_wins": "✅ Gagnants      : {wins} ({win_rate:.1f}%)",
        "backtest_losses": "❌ Perdants      : {losses}",
        "backtest_avg_gain": "📈 Gain moyen    : {avg_pnl:.4f}%",
        "backtest_total_gain": "💰 Gain total    : {total_pnl:.2f}%",
        "backtest_best": "🏆 Meilleur      : {best:.4f}%",
        "backtest_worst": "📉 Pire          : {worst:.4f}%",
        "backtest_drawdown": "📊 Max drawdown  : {max_drawdown:.2f}%",
        "backtest_avg_duration": "⏳ Durée moyenne : {avg_bars:.0f} bougies",

        # ----- Paper Trading -----
        "paper_usage": "Usage: /paper start|buy <symbole>|sell <symbole>|status|history|stats",
        "paper_started": "✅ Paper trading activé avec {capital}$ virtuels.",
        "paper_status": "📊 CAPITAL: {capital}$ | ÉQUITÉ: {equity}$ | PnL: {total_pnl}$ | Ouvertes: {open_positions}",
        "paper_buy_usage": "Usage: /paper buy <symbole>",
        "paper_no_signal": "Aucun signal actif pour ce symbole.",
        "paper_opened": "✅ Position ouverte sur {symbol} à {price}$ | SL: {sl}$ | TP: {tp}$",
        "paper_sell_usage": "Usage: /paper sell <symbole>",
        "paper_closed": "✅ Position fermée sur {symbol}.",
        "paper_no_open_position": "Aucune position ouverte sur {symbol}.",
        "paper_history_empty": "Aucun trade fermé.",
        "paper_history_title": "📋 HISTORIQUE PAPER TRADING",
        "paper_stats": "📊 STATS PAPER TRADING\n💰 Capital: {capital}$\n📈 Équité: {equity}$\n💵 PnL: {total_pnl}$\n🔢 Trades: {total_trades}\n✅ Wins: {wins}\n❌ Losses: {losses}\n📊 Win rate: {win_rate:.1f}%",

        # ----- Sélection de symboles -----
        "select_symbol": "Sélectionnez un symbole :",
        "category_crypto": "🪙 Cryptos",
        "category_forex": "💱 Forex",
        "category_commodities": "✨ Matières premières",
        "category_stocks": "📈 Actions",
        "category_fav": "⭐ Favoris",
        "prev_page": "⬅️",
        "next_page": "➡️",
    },

    "en": {
        # ----- Welcome / Status -----
        "start": (
            "🐻 *Bitsure Teddy* – Your smart trading assistant\n\n"
            "📊 Advanced technical analysis (crypto, forex, stocks, commodities)\n"
            "⚡ Real‑time scalping signals\n"
            "🚨 Custom price alerts\n"
            "*Current status:* {status}\n\n"
            "🔹 /menu – Main menu\n"
            "🔹 /upgrade – Upgrade to PRO\n\n"
            "Happy trading! 🧸"
        ),
        "start_disclaimer": "",
        "status_free_trial": "🆓 Free trial (3 days)",
        "status_free_ended": "🆓 Free (trial ended)",
        "status_pro": "💎 PRO",
        "international_payment_info": "",
        "terms_title": "📋 Terms of Use",
        "terms_text": (
            "Before using Bitsure Teddy, you must read and accept the following terms:\n\n"
            "1. This bot provides trading signals for informational purposes only. No financial advice is given.\n"
            "2. Past performance (backtests) does not guarantee future results.\n"
            "3. You are solely responsible for your trading decisions. Never trade more than you can afford to lose.\n"
            "4. Trading involves high risk. Bitsure Teddy and its creator cannot be held liable for your losses.\n"
            "5. By using this bot, you confirm that you have read, understood, and accepted these terms."
        ),
        "terms_accept": "✅ I Accept",
        "terms_refuse": "❌ I Refuse",
        "terms_accepted": "✅ Terms accepted. Welcome to Bitsure Teddy! Use /menu to get started.",
        "terms_refused_msg": "❌ You cannot use the bot without accepting the terms. Type /start when you are ready.",
        "terms_must_accept": "⚠️ You must first accept the terms of use. Type /start to review them.",
        "terms_button": "📋 Read Terms of Use",
        "check_usage": "Usage: /check SYMBOL BUY|SELL",
        "check_choose_direction": "📊 {symbol} – Choose direction:",
        "check": "📊 VALIDATION {symbol}\n━━━━━━━━━━━━━━━━━━━\n✅ Trend: {trend}\n✅ RSI: {rsi}\n⚠️ Volatility: {volatility}\n📈 Score: {score}/100 → {light}\n🎯 SL: {sl}\n💰 TP: {tp}",
        "check_green": "🟢 FAVORABLE",
        "check_orange": "🟡 CAUTION",
        "check_red": "🔴 RISKY",
        "check_vol_high": "High",
        "check_vol_normal": "Normal",
        "history_stats_header": "📊 YOUR HISTORY\n━━━━━━━━━━━━━━━━━━━\n📈 Signals received: {total}\n✅ Winners: {wins} ({win_rate}%)\n❌ Losers: {losses}\n\n💰 Average gain: {avg}%\n📉 Worst: {worst}%\n🏆 Best: {best}%\n\n💡 Advice: {advice}\n\n📋 LATEST SIGNALS:\n",
        "history_advice_high": "Keep going, but maintain strict risk management.",
        "history_advice_low": "Reduce risk and favor higher scores.",
        "channel_required": "⚠️ You must join T's World channel to use Bitsure Teddy.\n\n👉 https://t.me/+c_xPX-20JAo0MTE0\n\nCome back after joining!",
        "channel_verified": "✅ Subscription verified. Welcome!",
        "channel_not_joined": "❌ You haven't joined the channel yet. Join it first.",
        "check_subscription": "✅ I joined",
        "ask_usage": "Usage: /ask <your question>",
        "ask_wait": "🤔 Thinking...",
        "ask_error": "❌ Error: {error}",

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
        "button_pro_stars": "⭐ PRO €19.99/month (Telegram Stars)",
        "button_binance_usdc": "🟡 Binance USDC",
        "binance_payment_info": (
            "🟡 Binance Payment (USDC)\n\n"
            "1. Open Binance → Wallet → Send\n"
            "2. Enter Binance ID: {binance_id}\n"
            "3. Amount: {amount} USDC\n"
            "4. Verify the displayed username is correct\n\n"
            "Your transaction ID: {memo}\n\n"
            "⚠️ Copy this ID and send it to the admin after paying."
        ),
        "confirm_payment_usage": "Usage: /confirm_payment <user_id>",
        "confirm_payment_ok": "✅ Payment confirmed for user {user_id}.",
        "confirm_payment_missing": "❌ No pending Binance payment for {user_id}.",
        "premium_required": "🔒 *Premium Feature*\n\nThis command is reserved for PRO members.\nUse /upgrade to discover the offer.",
        "payment_success": "✅ *Payment successful!*\nYou are now *PRO*.\nThank you for your trust! 🧸",
        "stripe_soon": "💳 Credit card payment will be available very soon. In the meantime, you can use Telegram Stars or contact support.",
        "unavailable_option": "Unavailable option.",

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
        "addwatch_usage": "Usage: /addwatch SYMBOL",
        "removewatch_usage": "Usage: /removewatch SYMBOL",

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
        "delalert_usage": "Usage: /delalert ID",

        # ----- Symbols -----
        "symbole_invalide": "Invalid symbol.",
        "invalid_symbol": "Invalid symbol.",
        "symboles_list": (
            "📊 *POPULAR SYMBOLS*\n\n"
            "🪙 *Cryptos*\nBTCUSD – Bitcoin\nETHUSD – Ethereum\nXRPUSD – Ripple\nSOLUSD – Solana\n\n"
            "💱 *Forex*\nEURUSD – Euro/Dollar\nGBPUSD – Pound/Dollar\nUSDJPY – Dollar/Yen\n\n"
            "✨ *Commodities*\nXAUUSD – Gold\nXAGUSD – Silver\n\n"
            "📈 *Stocks*\nAAPL – Apple\nTSLA – Tesla\nMSFT – Microsoft\n\n"
            "💡 Example: /analyse BTCUSD"
        ),
        "symbol_not_found": "Symbol not found.",
        "symbolinfo_usage": "Usage: /symbolinfo SYMBOL",
        "symbolinfo_format": "*{symbol}*\nPrice: {price}\nBid/Ask: {bid} / {ask}",

        # ----- Analysis -----
        "analyse_usage": "Usage: /analyse SYMBOL",
        "analyse_wait": "🔍 Analyzing {symbol}...",
        "analyse_error": "❌ Could not retrieve data for {symbol}.",
        "analyse_caption": (
            "📊 *ANALYSIS {symbol}*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🎯 Signal    : {signal_emoji} {signal}\n"
            "📈 Score     : {teddy_score}/100 ({confidence})\n"
            "💵 Price     : {price}\n"
            "🛑 SL        : {sl}\n"
            "🎯 TP        : {tp} (RR: {rr_ratio})\n"
            "📊 RSI       : {rsi:.1f}\n"
            "📉 SMA20/50  : {sma20} / {sma50}\n"
            "📏 ADX       : {adx:.1f}\n"
            "💡 Reason    : {reason}\n"
            "⚠️ Advice    : {risk_advice}\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "price_usage": "Usage: /price SYMBOL",
        "price_error": "❌ Price not available for {symbol}.",
        "price_format": "💵 *{symbol}*\n━━━━━━━━━━━━━━━━━━━\n💰 Price : {price}\n📉 Bid   : {bid}\n📈 Ask   : {ask}",
        "price_label": "Price",

        # ----- Scalping -----
        "tick_usage": "Usage: /tick SYMBOL",
        "tick_none": "❌ No recent tick.",
        "tick_current": "🕒 Last tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOL",
        "spread_format": "📏 *SPREAD {symbol}*\n━━━━━━━━━━━━━━━━━━━\n📉 Bid    : {bid}\n📈 Ask    : {ask}\n📊 Spread : {spread}",
        "spread_unavailable": "❌ Spread unavailable.",
        "scalp_usage": "Usage: /scalp SYMBOL DURATION (3,5,10,20)",
        "scalp_invalid_duration": "Invalid duration. Choose 3, 5, 10 or 20 seconds.",
        "scalp_signal_buy": "BUY",
        "scalp_signal_sell": "SELL",
        "scalp_signal_wait": "WAIT",
        "scalp_result": (
            "⚡ *SCALPING {symbol} · {duration}s*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📊 Signal : {signal_emoji} {signal}\n"
            "💰 Price   : {price}\n"
            "📉 Bid/Ask : {bid} / {ask}\n"
            "📏 Spread  : {spread} ({spread_pct}%)\n"
            "📈 RSI     : {rsi:.1f}\n"
            "📋 Reason  : {reason}\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        "realtime_data_error": "❌ Could not retrieve real-time data.",

        # ----- Trend / Volatility / Correlation / Levels -----
        "trend_usage": "Usage: /trend SYMBOL",
        "trend_no_data": "No data available.",
        "trend_haussiere": "Bullish",
        "trend_baissiere": "Bearish",
        "trend_neutre": "Neutral",
        "trend_bullish": "Bullish",
        "trend_bearish": "Bearish",
        "trend_neutral": "Neutral",
        "trend_result": "*{symbol}* Trend: {tend}",
        "volatility_usage": "Usage: /volatility SYMBOL",
        "volatility_result": "*{symbol}* Volatility (ATR 14): {atr}",
        "correlation_usage": "Usage: /correlation SYMBOL1 SYMBOL2",
        "correlation_result": "*{symbol1} vs {symbol2}* 30d Correlation: {corr:.2f}",
        "levels_usage": "Usage: /levels SYMBOL",
        "levels_no_data": "No data available.",
        "levels_result": (
            "📏 *LEVELS {symbol}*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🟢 Support    : {support}\n"
            "🔴 Resistance : {resistance}\n"
            "📐 Fib 38.2%  : {fib382}\n"
            "📐 Fib 50.0%  : {fib500}\n"
            "📐 Fib 61.8%  : {fib618}"
        ),

        # ----- Sentiment / Compare / Top / Fav -----
        "sentiment_result": "📊 *Crypto Fear & Greed Index*\n\nCurrent value: {value}\nClassification: {classification}",
        "sentiment_error": "Could not retrieve Fear & Greed Index.",
        "compare_usage": "Usage: /compare SYM1 SYM2",
        "compare_result": "*{symbol1} vs {symbol2}*\nTrend: {trend1} vs {trend2}",
        "top_crypto": "🚀 *Top 5 Crypto Gainers (24h)*\n\n{list}",
        "fav_usage": "Usage: /fav add|remove|list [symbol]",
        "fav_add_usage": "Usage: /fav add SYMBOL",
        "fav_remove_usage": "Usage: /fav remove SYMBOL",
        "fav_added": "✅ {symbol} added to favorites.",
        "fav_removed": "✅ {symbol} removed from favorites.",
        "fav_list": "⭐ *Your favorites:*\n{symbols}",
        "fav_empty": "No favorites saved.",
        "insufficient_data": "Insufficient data.",
        "insufficient_common_data": "Not enough common data.",
        "data_unavailable": "Data unavailable.",

        # ----- Learn -----
        "learn_usage": "Usage: /learn [term]\nAvailable terms: rsi, macd, sma, support, resistance, fibonacci, atr, adx, stochastic, spread",
        "learn_rsi": "*RSI*\nMomentum indicator measuring speed and magnitude of price moves. >70 overbought, <30 oversold.",
        "learn_macd": "*MACD*\nMoving Average Convergence Divergence. Crossovers used for buy/sell signals.",
        "learn_sma": "*SMA*\nSimple Moving Average. SMA20 and SMA50 are common trend references.",
        "learn_support": "*Support*\nPrice level where demand stops a decline.",
        "learn_resistance": "*Resistance*\nPrice level where supply stops a rally.",
        "learn_fibonacci": "*Fibonacci*\nRetracement levels (38.2%, 50%, 61.8%) used for support/resistance zones.",
        "learn_atr": "*ATR*\nAverage True Range. Measures volatility, used for stop-losses.",
        "learn_adx": "*ADX*\nAverage Directional Index. Measures trend strength (>25 = strong trend).",
        "learn_stochastic": "*Stochastic*\nCompares closing price to price range. >80 overbought, <20 oversold.",
        "learn_spread": "*Spread*\nDifference between bid and ask price.",

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
        "setlanguage_success_fr": "✅ Language set to French.",
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
        "stats_info": "📊 *STATISTICS*\n👥 Total: {total}\n🆓 FREE: {free}\n💪 PRO: {pro}",
        "setrole_usage": "Usage: /setrole USER_ID ROLE (free/pro)",
        "setrole_invalid_id": "❌ Invalid USER_ID.",
        "setrole_invalid_role": "❌ Invalid role. Use free or pro.",
        "setrole_success": "✅ User {target_id} role updated: *{role}*",
        "gift_usage": "Usage: /gift USER_ID ROLE DAYS (pro)",
        "gift_success": "✅ {role} role granted to {target_id} for {days} days.",
        "invalid_days": "❌ Invalid number of days.",
        "revoke_usage": "Usage: /revoke USER_ID",
        "revoke_success": "✅ User {target_id} role revoked (free).",
        "revoke_confirm": "⚠️ Revoke access for {target_id}?",
        "action_cancelled": "❌ Action annulée.",
        "redeem_usage": "Usage: /redeem CODE",
        "redeem_success": "✅ Promo code applied: {message}",
        "redeem_invalid": "❌ Invalid or expired promo code.",
        "redeem_already_used": "❌ You have already used this promo code.",
        "app_message": "📱 *Bitsure Teddy Mobile*\n\nThe app is currently in development. Stay tuned! 🧸",
        "gift_notification": "🎁 You have been granted free {role} access for {days} days! Enjoy!",

        # ----- Challenge / Snapshot / Verify -----
        "challenge_start": "🔥 *SCALPING CHALLENGE STARTED* 🔥\nAnalyzing 5 consecutive trades on EURUSD...",
        "challenge_trade": "📊 *Trade {n}/5* – {signal} at {price}\nResult: {result} ({pips} pips)",
        "challenge_score": "🏆 *FINAL SCORE*: {wins}/5 won\n{summary}",
        "win": "Win",
        "loss": "Loss",
        "pending": "Pending",
        "net_pips": "Net pips",
        "snapshot_caption": "🐻 *Bitsure Teddy*\n{symbol} – {signal}\nTeddy Score: {score}/100\nPrice: {price}",
        "verify_not_found": "❌ No signal found with ID `{signal_id}`.",
        "verify_result": "🔍 *Signal #{signal_id}*\nIssued on: {timestamp}\nSymbol: {symbol}\nSignal: {signal}\nEntry Price: {price}\nResult: {result}",
        "verify_usage": "Usage: /verify SIGNAL_ID",
        "history_title": "📜 *Signal History*\n",
        "history_empty": "No signals recorded.",
        "no_recent_analysis": "No recent analysis.",

        # ----- Signal Engine -----
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
        "signal_buy": "BUY",
        "signal_sell": "SELL",
        "signal_wait": "WAIT",
        "na": "N/A",

        # ----- Interactive Menu -----
        "menu_title": "🧸 *MAIN MENU*\nSelect a category:",
        "menu_analyse": "📊 Analysis",
        "menu_scalping": "⚡ Scalping",
        "menu_alertes": "🚨 Alerts",
        "menu_watchlist": "📋 Watchlist",
        "menu_parametres": "⚙️ Settings",
                        "back": "⬅️ Back",
        "menu_choose_command": "Choose a command:",
        "menu_upgrade": "💎 Upgrade",
        "btn_analyse": "📊 Analysis",
        "btn_price": "💰 Price",
        "btn_scalp": "⚡ Scalping",
        "btn_watchlist": "📋 Watchlist",
        "btn_settings": "⚙️ Settings",
        "btn_upgrade": "💎 Upgrade",
        "btn_historique": "📜 History",
        "btn_support": "📞 Support",
        "btn_trend": "📈 Trend",
        "btn_volatility": "🌪 Volatility",
        "btn_levels": "📍 Levels",
        "btn_symbolinfo": "ℹ️ Symbol",
        "btn_check": "✅ Trade check",
        "btn_paper": "📈 Paper Trading",
        "btn_tick": "🕒 Tick",
        "btn_spread": "↔️ Spread",
        "btn_alert": "➕ Alert",
        "btn_alerts": "📑 Alerts",
        "btn_delalert": "➖ Delete alert",
        "btn_clearalerts": "🧹 Clear alerts",
        "btn_addwatch": "➕ Add",
        "btn_removewatch": "➖ Remove",
        "btn_scan": "🔎 Scan",
        "btn_settimeframe": "⏱ Timeframe",
        "btn_setlanguage": "🌐 Language",
        "btn_usage": "📊 Usage",
        "help_redirect": "Use /menu to access the interactive menu.",
        "trial_days_left": "Free trial: {days} days remaining",
        "btn_upgrade_stars": "Telegram Stars (19.99€/month)",
        "btn_upgrade_binance": "Binance Junior (USDC)",
        "settimeframe_choose": "Choose a timeframe:",
        "setlanguage_choose": "Choose a language:",
        "delalert_pick": "Choose an alert to delete:",
        "scalp_choose_duration": "Choose a duration:",
        "cond_above": "Above",
        "cond_below": "Below",
        "alert_choose_condition": "Choose a condition:",
        "alert_enter_price": "Enter the target price after selecting condition.",
        "alert_price_invalid_retry": "Invalid price, please try again.",
        "watchlist_already": "ℹ️ {symbol} is already in your watchlist.",
        "watchlist_missing": "ℹ️ {symbol} is not in your watchlist.",
        "watchlist_added_styled": "✅ {symbol} added to your watchlist",
        "watchlist_removed_styled": "🗑️ {symbol} removed from your watchlist",
        "scalp_wait_reason": "All indicators are neutral, no edge detected.",
        "scalp_fallback_buy": "Strong oversold RSI detected (fallback).",
        "scalp_fallback_sell": "Strong overbought RSI detected (fallback).",
        "btn_upgrade_stars_fr": "Telegram Stars (19,99€/mois)",
        "btn_upgrade_binance_fr": "Binance Junior (USDC)",
        "settimeframe_choose_fr": "Choisissez un timeframe :",
        "setlanguage_choose_fr": "Choisissez une langue :",
        "delalert_pick_fr": "Choisissez une alerte à supprimer :",
        "scalp_choose_duration_fr": "Choisissez une durée :",
        "cond_above_fr": "Au-dessus",
        "cond_below_fr": "En-dessous",
        "alert_choose_condition_fr": "Choisissez une condition :",
        "alert_enter_price_fr": "Entrez le prix cible après la condition.",
        "use_command": "Use the command /{cmd} for more information.",
        "unknown_command": "Unknown command: /{cmd}",
        "unknown_option": "Unknown option.",
        "unsupported_command": "Unsupported command: /{command}",

        # ----- Backtest -----
        "backtest_start": "🚀 Starting backtest (this may take a few moments)...",
        "backtest_no_data": "⚠️ No data available for {symbol}",
        "backtest_no_trades": "ℹ️ {symbol}: No trades.",
        "backtest_title": "📊 {symbol} – Backtest Results",
        "separator_line": "━━━━━━━━━━━━━━━━━━━━━━━━",
        "backtest_trades": "🔢 Trades        : {total}",
        "backtest_wins": "✅ Winners       : {wins} ({win_rate:.1f}%)",
        "backtest_losses": "❌ Losers        : {losses}",
        "backtest_avg_gain": "📈 Average gain  : {avg_pnl:.4f}%",
        "backtest_total_gain": "💰 Total gain    : {total_pnl:.2f}%",
        "backtest_best": "🏆 Best          : {best:.4f}%",
        "backtest_worst": "📉 Worst         : {worst:.4f}%",
        "backtest_drawdown": "📊 Max drawdown  : {max_drawdown:.2f}%",
        "backtest_avg_duration": "⏳ Avg duration  : {avg_bars:.0f} candles",

        # ----- Paper Trading -----
        "paper_usage": "Usage: /paper start|buy <symbol>|sell <symbol>|status|history|stats",
        "paper_started": "✅ Paper trading activated with ${capital} virtual.",
        "paper_status": "📊 CAPITAL: ${capital} | EQUITY: ${equity} | PnL: ${total_pnl} | Open: {open_positions}",
        "paper_buy_usage": "Usage: /paper buy <symbol>",
        "paper_no_signal": "No active signal for this symbol.",
        "paper_opened": "✅ Position opened on {symbol} at ${price} | SL: ${sl} | TP: ${tp}",
        "paper_sell_usage": "Usage: /paper sell <symbol>",
        "paper_closed": "✅ Position closed on {symbol}.",
        "paper_no_open_position": "No open position on {symbol}.",
        "paper_history_empty": "No closed trades.",
        "paper_history_title": "📋 PAPER TRADING HISTORY",
        "paper_stats": "📊 PAPER TRADING STATS\n💰 Capital: ${capital}\n📈 Equity: ${equity}\n💵 PnL: ${total_pnl}\n🔢 Trades: {total_trades}\n✅ Wins: {wins}\n❌ Losses: {losses}\n📊 Win rate: {win_rate:.1f}%",

        # ----- Symbol Selection -----
        "select_symbol": "Select a symbol:",
        "category_crypto": "🪙 Crypto",
        "category_forex": "💱 Forex",
        "category_commodities": "✨ Commodities",
        "category_stocks": "📈 Stocks",
        "category_fav": "⭐ Favorites",
        "prev_page": "⬅️",
        "next_page": "➡️",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    texts = TEXTS.get(lang, TEXTS["en"])
    text = texts.get(key, TEXTS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
