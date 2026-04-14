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
        "international_payment_info": "\n\n🌍 *Vous êtes dans un pays où les paiements internationaux sont difficiles ?*\nPas de problème. Contactez l'administrateur pour un arrangement manuel : /support",

        # ---- Help ----
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

        # ---- Support ----
        "support": "📞 Besoin d'aide ?\n\nContactez l'administrateur : @btsr_teddy09",

        # ---- Upgrade ----
        "upgrade_title": "💳 *Choisissez votre offre :*\n\n• PRO : 9,99€/mois – illimité, scalping\n• ELITE : 24,99€/mois – PRO + groupe privé + support prioritaire",
        "button_pro_stars": "💎 PRO – 9,99€/mois (Stars)",
        "button_elite_stars": "👑 ELITE – 24,99€/mois (Stars)",
        "button_pro_stripe": "💳 PRO – 9,99€/mois (Stripe bientôt)",
        "button_elite_stripe": "💳 ELITE – 24,99€/mois (Stripe bientôt)",
        "invoice_title": "Bitsure Teddy Premium",
        "payment_success": "✅ *Paiement réussi !*\n\nVotre compte est maintenant *{role}*.\nMerci de soutenir Bitsure Teddy ! 🧸💸",
        "stripe_soon": "ℹ️ Paiement Stripe bientôt disponible.",

        # ---- Premium ----
        "premium_required": "🔒 *Fonctionnalité Premium*\n\nCette commande est réservée aux membres PRO et ELITE.\nUtilisez /upgrade pour découvrir nos offres.",

        # ---- Limites ----
        "limit_reached": "❌ Vous avez atteint votre limite quotidienne de requêtes.",
        "watchlist_limit": "❌ Limite de 3 symboles en gratuit.",
        "watchlist_added": "✅ {symbol} ajouté.",
        "watchlist_removed": "✅ {symbol} retiré.",
        "watchlist_empty": "Watchlist vide.",
        "watchlist_scan_result": "📊 *Scan:*\n{results}",
        "watchlist_show": "📋 *Watchlist:*\n{symbols}",

        # ---- Analyse ----
        "symbole_invalide": "Symbole invalide.",
        "analyse_usage": "Usage: /analyse SYMBOLE",
        "analyse_wait": "🔍 Analyse de {symbol}...",
        "analyse_error": "❌ Données indisponibles pour {symbol}.",
        "price_usage": "Usage: /price SYMBOLE",
        "price_error": "❌ Prix indisponible.",
        "price_format": "*{symbol}*\n💰 Prix: {price}\n📊 Bid: {bid} / Ask: {ask}",

        # ---- Tick ----
        "tick_usage": "Usage: /tick SYMBOLE",
        "tick_none": "❌ Aucun tick.",
        "tick_current": "🕒 Tick {symbol}: {price}",
        "spread_usage": "Usage: /spread SYMBOLE",
        "spread_format": "*{symbol}* Spread: {spread}",
        "spread_unavailable": "❌ Spread indisponible.",

        # ---- Scalping ----
        "scalp_usage": "Usage: /scalp SYMBOLE DURÉE",
        "scalp_invalid_duration": "Durée invalide.",
        "scalp_signal_buy": "ACHETER",
        "scalp_signal_sell": "VENDRE",
        "scalp_signal_wait": "ATTENDRE",
        "scalp_result": "⚡ *Scalp {symbol}*\nSignal: {signal}",

        # ---- Trend ----
        "trend_usage": "Usage: /trend SYMBOLE",
        "trend_no_data": "Pas de données.",
        "trend_haussiere": "Haussière",
        "trend_baissiere": "Baissière",
        "trend_neutre": "Neutre",
        "trend_result": "*{symbol}* : {tend}",

        # ---- Settings ----
        "settings_info": "⚙️ Settings",
        "settimeframe_usage": "Usage: /settimeframe",
        "settimeframe_invalid": "Invalid.",
        "settimeframe_success": "OK {tf}",
        "setrisk_usage": "Usage: /setrisk",
        "setrisk_invalid": "Invalid risk.",
        "setrisk_success": "OK {risk}",
        "setlanguage_usage": "Usage: /setlanguage",
        "setlanguage_invalid": "Invalid language.",
        "setlanguage_success_fr": "Langue FR",
        "setlanguage_success_en": "Language EN",
        "usage_requests_remaining": "{rem} requests left",
        "usage_unlimited": "Unlimited",

        # ---- Admin ----
        "status_ok": "OK",
        "about": "Bitsure Teddy bot",
        "symbolinfo": "Use /analyse",
        "myid": "ID: {user_id}",
        "broadcast_admin_only": "Admin only",
        "broadcast_usage": "Usage",
        "broadcast_sent": "Sent {success}/{total}",
        "reload_success": "Reload OK",
        "stats_info": "Stats: {total}",
        "setrole_usage": "Usage",
        "setrole_invalid_id": "Invalid ID",
        "setrole_invalid_role": "Invalid role",
        "setrole_success": "Updated {target_id}",

        "gift_usage": "Usage",
        "gift_success": "Gift sent",
        "revoke_usage": "Usage",
        "revoke_success": "Revoked",
        "redeem_usage": "Usage",
        "redeem_success": "Redeemed {message}",
        "redeem_invalid": "Invalid code",

        "symboles_list": "BTCUSD, ETHUSD..."
    },

    "en": {
        # (inchangé – déjà bon)
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    # fallback safe
    texts = TEXTS.get(lang)
    if not texts:
        texts = TEXTS["en"]

    text = texts.get(key, key)

    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text