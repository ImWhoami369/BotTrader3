import os
import sys
import logging
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# 1. CREDENCIAIS E CONFIGURAÇÕES
# ==============================================================================
TOKEN = os.environ.get("BOT_TOKEN", "8822381506:AAEFA9KscOVs_xIGOV70RJeuLPggQNojYXg")
CHAT_ID = os.environ.get("CHAT_ID", "-1003966783268")

bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Links Globais
LINK_BINANCE = "https://www.binance.com"
LINK_WALLET = "https://wallet.telegram.org"
LINK_TELEGRAM = "https://t.me"
LINK_AIRDROP = "https://binance.com"

# --- LISTA EXPANDIDA DE ATIVOS NAS POSIÇÕES ABERTAS ---
POSICOES_ABERTAS = [
    {"symbol": "BTC/USDT", "side": "LONG", "entry": 64200.0, "pnl": "+4.2%", "qty": 0.05, "cat": "L1"},
    {"symbol": "ETH/USDT", "side": "SHORT", "entry": 3450.0, "pnl": "-1.1%", "qty": 0.5, "cat": "L1"},
    {"symbol": "BNB/USDT", "side": "LONG", "entry": 580.0, "pnl": "+3.4%", "qty": 2.0, "cat": "L1"},
    {"symbol": "SOL/USDT", "side": "LONG", "entry": 145.0, "pnl": "+8.5%", "qty": 10.0, "cat": "L1"},
    {"symbol": "OP/USDT", "side": "LONG", "entry": 1.75, "pnl": "+14.2%", "qty": 500.0, "cat": "L2"},
    {"symbol": "CHZ/USDT", "side": "LONG", "entry": 0.082, "pnl": "+9.8%", "qty": 10000.0, "cat": "FanTokens"},
    {"symbol": "XRP/USDT", "side": "SHORT", "entry": 0.55, "pnl": "-0.5%", "qty": 1000.0, "cat": "L1"},
    {"symbol": "ADA/USDT", "side": "LONG", "entry": 0.42, "pnl": "+1.8%", "qty": 500.0, "cat": "L1"},
    {"symbol": "AVAX/USDT", "side": "SHORT", "entry": 28.5, "pnl": "+3.0%", "qty": 15.0, "cat": "L1"},
    {"symbol": "LINK/USDT", "side": "LONG", "entry": 14.2, "pnl": "-2.4%", "qty": 30.0, "cat": "DeFi"},
    {"symbol": "NEAR/USDT", "side": "LONG", "entry": 5.1, "pnl": "+6.3%", "qty": 100.0, "cat": "L1"},
    {"symbol": "SUI/USDT", "side": "LONG", "entry": 1.15, "pnl": "+11.0%", "qty": 300.0, "cat": "L1"},
    {"symbol": "PEPE/USDT", "side": "LONG", "entry": 0.0000085, "pnl": "+22.5%", "qty": 10000000.0, "cat": "Memes"},
    {"symbol": "DOGE/USDT", "side": "LONG", "entry": 0.12, "pnl": "+15.4%", "qty": 2500.0, "cat": "Memes"},
    {"symbol": "UNI/USDT", "side": "LONG", "entry": 7.8, "pnl": "+5.1%", "qty": 60.0, "cat": "DeFi"},
    {"symbol": "ARB/USDT", "side": "LONG", "entry": 0.58, "pnl": "+2.9%", "qty": 800.0, "cat": "L2"},
]

HISTORICO_HOJE = [
    {"symbol": "SOL/USDT", "side": "LONG", "result": "PROFIT", "pnl": "+12.5%", "lucro_usd": 150.00},
    {"symbol": "OP/USDT", "side": "LONG", "result": "PROFIT", "pnl": "+8.1%", "lucro_usd": 92.40},
    {"symbol": "CHZ/USDT", "side": "LONG", "result": "PROFIT", "pnl": "+15.0%", "lucro_usd": 120.00},
    {"symbol": "BTC/USDT", "side": "SHORT", "result": "PROFIT", "pnl": "+5.2%", "lucro_usd": 80.50},
    {"symbol": "BNB/USDT", "side": "LONG", "result": "LOSS", "pnl": "-2.1%", "lucro_usd": -25.00},
]

# ==============================================================================
# 2. INICIALIZAÇÃO AUTOMÁTICA
# ==============================================================================
def inicializar_bot():
    try:
        bot.remove_webhook()
        logging.info("✅ Webhook antigo removido!")
    except Exception as e:
        logging.error(f"⚠️ Erro webhook: {e}")

    try:
        bot.set_my_commands([
            BotCommand("start", "🚀 Painel Principal"),
            BotCommand("criptos", "🪙 Lista Completa de Ativos"),
            BotCommand("links", "🎁 Menu de Links & Bônus"),
            BotCommand("posicoes", "📊 Posições Abertas"),
            BotCommand("relatorio", "📈 Relatório Diário"),
            BotCommand("sinais", "📡 ÚLTIMOS SINAIS"),
            BotCommand("ajuda", "❓ Instruções e Suporte")
        ])
        logging.info("✅ Comandos cadastrados com sucesso!")
    except Exception as e:
        logging.error(f"⚠️ Erro comandos: {e}")

# ==============================================================================
# 3. CONSTRUTORES DE MENUS INTERATIVOS
# ==============================================================================
def criar_menu_categorias_cripto():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚡ Layer 1 (BTC, ETH, BNB, SOL...)", callback_data="cat_l1"),
        InlineKeyboardButton("🚀 Layer 2 (OP, ARB...)", callback_data="cat_l2")
    )
    markup.add(
        InlineKeyboardButton("⚽ Fan Tokens (CHZ...)", callback_data="cat_chz"),
        InlineKeyboardButton("🦄 DeFi (UNI, LINK...)", callback_data="cat_defi")
    )
    markup.add(
        InlineKeyboardButton("🐸 Memes (PEPE, DOGE...)", callback_data="cat_memes"),
        InlineKeyboardButton("📋 Ver Todas as Posições", callback_data="ver_posicoes")
    )
    markup.add(InlineKeyboardButton("⬅️ Menu Principal", callback_data="refresh_painel"))
    return markup

def criar_menu_links_estilo_img1():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎁 BINANCE", url=LINK_BINANCE),
        InlineKeyboardButton("🎁 WALLET", url=LINK_WALLET)
    )
    markup.row(InlineKeyboardButton("💵 TELEGRAM × BINANCE", url=LINK_TELEGRAM))
    markup.row(InlineKeyboardButton("💸 CLAIM $100 BONUS", url=LINK_BINANCE))
    markup.row(InlineKeyboardButton("🔗 BINANCE AIRDROP", url=LINK_AIRDROP))
    markup.row(InlineKeyboardButton("💰 WELCOME BONUS 💰", url=LINK_BINANCE))
    markup.row(
        InlineKeyboardButton("📊 MINHAS POSIÇÕES", callback_data="ver_posicoes"),
        InlineKeyboardButton("🔄 ATUALIZAR", callback_data="refresh_painel")
    )
    return markup

def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    btn_criptos = InlineKeyboardButton("🪙 Categoria de Criptos", callback_data="ver_categorias")
    btn_posicoes = InlineKeyboardButton("📊 Posições Abertas", callback_data="ver_posicoes")
    btn_sinais = InlineKeyboardButton("📡 Últimos Sinais", callback_data="ver_sinais")
    btn_relatorio = InlineKeyboardButton("📈 Relatório Diário", callback_data="ver_relatorio")
    btn_links = InlineKeyboardButton("🎁 Bônus & Links", callback_data="ver_links")
    btn_abrir = InlineKeyboardButton("⚡ Abrir Ordem", callback_data="abrir_ordem")
    btn_fechar = InlineKeyboardButton("❌ Fechar Posição", callback_data="fechar_ordem")
    btn_refresh = InlineKeyboardButton("🔄 Atualizar Painel", callback_data="refresh_painel")
    
    markup.add(btn_criptos, btn_posicoes)
    markup.add(btn_sinais, btn_relatorio)
    markup.add(btn_links, btn_abrir)
    markup.add(btn_fechar, btn_refresh)
    return markup

def criar_menu_fechar_posicoes():
    markup = InlineKeyboardMarkup(row_width=1)
    for pos in POSICOES_ABERTAS[:10]:
        symbol = pos["symbol"]
        side = pos["side"]
        pnl = pos["pnl"]
        btn_text = f"❌ Fechar {symbol} ({side}) | PnL: {pnl}"
        callback = f"close_pos_{symbol.replace('/', '_')}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=callback))
    markup.add(InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="refresh_painel"))
    return markup

# ==============================================================================
# 4. LÓGICA DO RELATÓRIO DIÁRIO
# ==============================================================================
def gerar_texto_relatorio():
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    total_trades = len(HISTORICO_HOJE)
    vitorias = sum(1 for t in HISTORICO_HOJE if t["result"] == "PROFIT")
    derrotas = sum(1 for t in HISTORICO_HOJE if t["result"] == "LOSS")
    winrate = (vitorias / total_trades * 100) if total_trades > 0 else 0
    lucro_total = sum(t["lucro_usd"] for t in HISTORICO_HOJE)
    status_emoji = "🟢" if lucro_total >= 0 else "🔴"
    
    texto = (
        f"📈 **RELATÓRIO DIÁRIO DE OPERAÇÕES**\n"
        f"📅 **Data:** `{data_hoje}`\n"
        f"───────────────────────────\n\n"
        f"📊 **RESUMO DA SESSÃO:**\n"
        f"• Total de Operações: `{total_trades}`\n"
        f"• Vitórias (TP): `🟢 {vitorias}`\n"
        f"• Derrotas (SL): `🔴 {derrotas}`\n"
        f"• Winrate: `{winrate:.1f}%`\n"
        f"• Resultado Financeiro: {status_emoji} **${lucro_total:+.2f} USDT**\n\n"
        f"📝 **DETALHAMENTO DOS TRADES:**\n"
    )
    for idx, trade in enumerate(HISTORICO_HOJE, 1):
        icon = "✅" if trade["result"] == "PROFIT" else "❌"
        texto += f"{idx}. {icon} **{trade['symbol']}** ({trade['side']}) → `{trade['pnl']}` (${trade['lucro_usd']:+.2f})\n"
        
    texto += "\n_Relatório gerado automaticamente pelo bot._"
    return texto

# ==============================================================================
# 5. HANDLERS DOS COMANDOS
# ==============================================================================
@bot.message_handler(commands=['start'])
def command_start(message):
    texto = (
        "🤖 **PAINEL DE TRADING MULTI-ATIVOS**\n\n"
        "Suporte a BTC, ETH, BNB, OP, CHZ, SOL e mais!\n"
        "Selecione uma ação abaixo:"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

@bot.message_handler(commands=['criptos'])
def command_criptos(message):
    bot.send_message(message.chat.id, "🪙 **SELEÇÃO DE CRIPTOATIVOS:**", reply_markup=criar_menu_categorias_cripto())

@bot.message_handler(commands=['links'])
def command_links(message):
    bot.send_message(message.chat.id, "🔥 **LINKS EXCLUSIVOS E PARCERIAS:**", reply_markup=criar_menu_links_estilo_img1())

@bot.message_handler(commands=['posicoes'])
def command_posicoes(message):
    exibir_posicoes(message.chat.id)

@bot.message_handler(commands=['relatorio'])
def command_relatorio(message):
    texto = gerar_texto_relatorio()
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

@bot.message_handler(commands=['sinais'])
def command_sinais(message):
    exibir_sinais(message.chat.id)

# ==============================================================================
# 6. HANDLER DE BOTÕES
# ==============================================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    global POSICOES_ABERTAS
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "ver_posicoes":
        exibir_posicoes(chat_id)
        bot.answer_callback_query(call.id, "Posições carregadas!")

    elif call.data == "ver_categorias":
        bot.send_message(chat_id, "🪙 **Selecione a Categoria de Cripto:**", reply_markup=criar_menu_categorias_cripto())
        bot.answer_callback_query(call.id)

    elif call.data.startswith("cat_"):
        cat = call.data.replace("cat_", "")
        exibir_posicoes_por_categoria(chat_id, cat)
        bot.answer_callback_query(call.id)

    elif call.data == "ver_links":
        bot.send_message(chat_id, "🔥 **LINKS RÁPIDOS & PROMOÇÕES**", reply_markup=criar_menu_links_estilo_img1())
        bot.answer_callback_query(call.id)

    elif call.data == "ver_relatorio":
        texto = gerar_texto_relatorio()
        bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id, "Relatório Diário Gerado!")

    elif call.data == "ver_sinais":
        exibir_sinais(chat_id)
        bot.answer_callback_query(call.id, "Sinais carregados!")

    elif call.data == "abrir_ordem":
        bot.send_message(chat_id, "⚡ **ORDEM RÁPIDA**\nExemplo:\n`COMPRA BNBUSDT 1.5` ou `COMPRA CHZUSDT 5000`", parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "fechar_ordem":
        if not POSICOES_ABERTAS:
            bot.send_message(chat_id, "ℹ️ Nenhuma posição aberta no momento.")
        else:
            bot.send_message(chat_id, "🎯 **Selecione a posição para fechar:**", reply_markup=criar_menu_fechar_posicoes())
        bot.answer_callback_query(call.id)

    elif call.data == "refresh_painel":
        texto = "🔄 **Painel Atualizado com Sucesso!**"
        try:
            bot.edit_message_text(texto, chat_id, message_id, parse_mode="Markdown", reply_markup=criar_menu_principal())
        except Exception:
            bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id)

    elif call.data.startswith("close_pos_"):
        symbol_raw = call.data.replace("close_pos_", "").replace("_", "/")
        POSICOES_ABERTAS = [p for p in POSICOES_ABERTAS if p["symbol"] != symbol_raw]
        bot.send_message(chat_id, f"✅ **Posição em {symbol_raw} encerrada com sucesso!**", parse_mode="Markdown")
        bot.answer_callback_query(call.id, f"{symbol_raw} Fechado!")

# ==============================================================================
# 7. FUNÇÕES AUXILIARES DE EXIBIÇÃO
# ==============================================================================
def exibir_posicoes(chat_id):
    if not POSICOES_ABERTAS:
        bot.send_message(chat_id, "📊 **POSIÇÕES:**\nNenhuma ordem aberta.")
        return

    texto = f"📊 **TODAS AS POSIÇÕES ABERTAS ({len(POSICOES_ABERTAS)}):**\n\n"
    for idx, pos in enumerate(POSICOES_ABERTAS, 1):
        emoji = "🟢" if pos["side"] == "LONG" else "🔴"
        texto += f"{idx}. {emoji} **{pos['symbol']}** ({pos['side']}) | PnL: **{pos['pnl']}**\n"
    
    bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

def exibir_posicoes_por_categoria(chat_id, categoria):
    filtradas = [p for p in POSICOES_ABERTAS if p.get("cat", "").lower() == categoria.lower()]
    if not filtradas:
        bot.send_message(chat_id, f"ℹ️ Nenhuma posição aberta na categoria `{categoria.upper()}` no momento.", parse_mode="Markdown")
        return

    texto = f"🪙 **ATIVOS EM CATEGORIA ({categoria.upper()}):**\n\n"
    for idx, pos in enumerate(filtradas, 1):
        emoji = "🟢" if pos["side"] == "LONG" else "🔴"
        texto += (
            f"{idx}. {emoji} **{pos['symbol']}** ({pos['side']})\n"
            f"   • Entrada: `${pos['entry']}` | Qtd: `{pos['qty']}`\n"
            f"   • PnL: **{pos['pnl']}**\n\n"
        )
    bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_categorias_cripto())

def exibir_sinais(chat_id):
    texto = (
        "📡 **ÚLTIMOS SINAIS DETECTADOS**\n\n"
        "1. 🎯 **CHZ/USDT** (LONG)\n   💵 Entrada: 0.0815 | TP: 0.0920 | SL: 0.0780\n\n"
        "2. 🎯 **OP/USDT** (LONG)\n   💵 Entrada: 1.74 | TP: 1.95 | SL: 1.62\n\n"
        "3. 🎯 **BNB/USDT** (LONG)\n   💵 Entrada: 578.0 | TP: 610.0 | SL: 560.0\n"
    )
    bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

# ==============================================================================
# 8. SERVIDOR DUMMY PARA O RENDER
# ==============================================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Trading Multi-Ativos Online!")

    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ==============================================================================
# 9. EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("🤖 Bot Multi-Cripto Iniciado no Render...")
    inicializar_bot()
    bot.infinity_polling(skip_pending=True)
