# strategies/session_configs.py
# Configurações de killzone para cada sessão — reutiliza as classes existentes de forma modular

from datetime import time
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
from strategies.silver_bullet_xau import SilverBulletXAU, SilverBulletXAUConfig
from strategies.breaker_block_xau import BreakerBlockXAU, BreakerBlockXAUConfig
from strategies.breaker_block_nq import BreakerBlockNQ, BreakerBlockNQConfig

# ─────────────────────────────────────────────────────────────────
# NDX / NQ — Silver Bullet: NY AM (existente, referência)
# ─────────────────────────────────────────────────────────────────
def make_sb_nq_am() -> SilverBulletNQ:
    return SilverBulletNQ(SilverBulletConfig(
        killzone_start=time(10, 0),
        killzone_end=time(11, 0),
        min_sl_distance_pts=25.0,
        require_premium_discount=True,
        pd_threshold=0.50,
        session_name="ny_am"
    ))

# ─────────────────────────────────────────────────────────────────
# NDX / NQ — Silver Bullet: NY Lunch
# ─────────────────────────────────────────────────────────────────
def make_sb_nq_lunch() -> SilverBulletNQ:
    return SilverBulletNQ(SilverBulletConfig(
        killzone_start=time(13, 0),
        killzone_end=time(14, 0),
        min_sl_distance_pts=20.0,
        require_premium_discount=True,
        pd_threshold=0.25,
        session_name="ny_lunch"
    ))

# ─────────────────────────────────────────────────────────────────
# NDX / NQ — Silver Bullet: NY PM / Close
# ─────────────────────────────────────────────────────────────────
def make_sb_nq_close() -> SilverBulletNQ:
    return SilverBulletNQ(SilverBulletConfig(
        killzone_start=time(15, 0),
        killzone_end=time(16, 0),
        min_sl_distance_pts=25.0,
        require_premium_discount=True,
        pd_threshold=0.50,
        session_name="ny_close"
    ))

# ─────────────────────────────────────────────────────────────────
# XAUUSD — Silver Bullet: NY AM
# ─────────────────────────────────────────────────────────────────
def make_sb_xau_am() -> SilverBulletXAU:
    return SilverBulletXAU(SilverBulletXAUConfig(
        killzone_start=time(10, 0),
        killzone_end=time(11, 0),
        min_sl_distance_usd=8.0,
        require_premium_discount=True,
        pd_threshold=0.50,
        session_name="ny_am"
    ))

# ─────────────────────────────────────────────────────────────────
# XAUUSD — Silver Bullet: NY Lunch
# ─────────────────────────────────────────────────────────────────
def make_sb_xau_lunch() -> SilverBulletXAU:
    return SilverBulletXAU(SilverBulletXAUConfig(
        killzone_start=time(13, 0),
        killzone_end=time(14, 0),
        min_sl_distance_usd=6.0,
        require_premium_discount=True,
        pd_threshold=0.25,
        session_name="ny_lunch"
    ))

# ─────────────────────────────────────────────────────────────────
# XAUUSD — Silver Bullet: NY PM / Close
# ─────────────────────────────────────────────────────────────────
def make_sb_xau_close() -> SilverBulletXAU:
    return SilverBulletXAU(SilverBulletXAUConfig(
        killzone_start=time(15, 0),
        killzone_end=time(16, 0),
        min_sl_distance_usd=8.0,
        require_premium_discount=True,
        pd_threshold=0.50,
        session_name="ny_close"
    ))

# ─────────────────────────────────────────────────────────────────
# XAUUSD — Breaker Block: NY Lunch (NOVO)
# ─────────────────────────────────────────────────────────────────
def make_bb_xau_lunch() -> BreakerBlockXAU:
    return BreakerBlockXAU(BreakerBlockXAUConfig(
        killzone_start=time(13, 0),
        killzone_end=time(14, 0),
        min_sl_distance_usd=6.0,
        min_rr=2.0,
        atr_multiplier=1.2,
        breaker_lookback=40,
        session_name="ny_lunch"
    ))

# ─────────────────────────────────────────────────────────────────
# XAUUSD — Breaker Block: NY Close (NOVO)
# ─────────────────────────────────────────────────────────────────
def make_bb_xau_close() -> BreakerBlockXAU:
    return BreakerBlockXAU(BreakerBlockXAUConfig(
        killzone_start=time(15, 0),
        killzone_end=time(16, 0),
        min_sl_distance_usd=8.0,
        min_rr=2.0,
        atr_multiplier=1.2,
        breaker_lookback=40,
        session_name="ny_close"
    ))

# ─────────────────────────────────────────────────────────────────
# NDX / NQ — Breaker Block: NY Lunch (NOVO)
# ─────────────────────────────────────────────────────────────────
def make_bb_nq_lunch() -> BreakerBlockNQ:
    return BreakerBlockNQ(BreakerBlockNQConfig(
        killzone_start=time(13, 0),
        killzone_end=time(14, 0),
        min_sl_distance_pts=20.0,
        min_rr=2.0,
        atr_multiplier=1.2,
        breaker_lookback=40,
        session_name="ny_lunch"
    ))

# ─────────────────────────────────────────────────────────────────
# NDX / NQ — Breaker Block: NY Close (NOVO)
# ─────────────────────────────────────────────────────────────────
def make_bb_nq_close() -> BreakerBlockNQ:
    return BreakerBlockNQ(BreakerBlockNQConfig(
        killzone_start=time(15, 0),
        killzone_end=time(16, 0),
        min_sl_distance_pts=25.0,
        min_rr=2.0,
        atr_multiplier=1.2,
        breaker_lookback=40,
        session_name="ny_close"
    ))
