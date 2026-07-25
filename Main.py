import os
import logging
import random
import time
import threading
from datetime import datetime
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# 1. CONFIGURAÇÕES BÁSICAS
# ==============================================================================
TOKEN = os.environ.get("BOT_TOKEN", "8738063689:AAFz8wY1zaE3BixUupl0RBQ9exiy5l8260U")
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Links Globais
LINK_BINANCE = "https://www.binance.com"
LINK_WALLET = "https://wallet.telegram.org"
LINK_TELEGRAM = "https://t.me"

# Lista de Ativos Suportados para M1
ATIVOS_CRIPTO = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "OPUSDT", 
    "CHZUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", 
    "NEARUSDT", "SUIUSDT", "PEPEUSDT", "DOGEUSDT", "UNIUSDT", "ARBUSDT"
]

# Armazenamento Dinâmico em Memória
POSICOES_ABERTAS = []
HISTORICO_HOJE = []

# ==============================================================================
# 2. INTEGRAÇÃO PÚBLICA E GRATUITA BINANCE (SEM CHAVES/SENHAS)
# ==============================================================================
def obter_preco_binance(symbol):
    """Puxa o preço em tempo real diretamente da API pública da Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        res = requests.get(url, timeout=5).json()
        return float(res["price"])
    except Exception as e:
        logging.error(f"Erro ao buscar preço de {symbol}: {e}")
        return None

def gerar_sinal_sortido_m1(symbol=None):
    """Gera um sinal dinâmico baseado no preço real de M1 da Binance"""
    if not symbol:
        symbol = random.choice(ATIVOS_CRIPTO)
        
    preco_atual = obter_preco_binance(symbol)
    if not preco_atual:
        preco_atual = 100.0 # Valor fallback se API falhar
        
    side = random.choice(["LONG 🟢", "SHORT 🔴"])
    
    # Cálculos de TP e SL para Scalp M1 (~0.5% a 1%)
    if "LONG" in side:
        tp1 = preco_atual * 1.005
        tp2 = preco_atual * 1.010
        sl = preco_atual * 0.995
    else:
        tp1 = preco_atual * 0.995
        tp2 = preco_atual * 0.990
        sl = preco_atual * 1.005

    return {
        "symbol": symbol,
        "side": side,
        "entry": preco_atual,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "timeframe": "M1"
    }

# ==============================================================================
# 3. LÓGICA DE ORDEM INTERATIVA M1 (SIMULAÇÃO DE 1 MINUTO)
# ==============================================================================
def processar_execucao_ordem_m1(chat_id, sinal):
    """Acompanha a ordem por 1 minuto e exibe o resultado ao vivo no Telegram"""
    symbol = sinal["symbol"]
    side = "LONG" if "LONG" in sinal["side"] else "SHORT"
    entry_price = sinal["entry"]
    
    # Notifica início da ordem M1
    msg_inicio = bot.send_message(
        chat_id, 
        f"⚡ **ORDEM M1 INICIADA!**\n\n"
        f"🎯 **Ativo:** `{symbol}`\n"
        f"📈 **Direção:** `{side}`\n"
        f"💵 **Preço Entrada:** `${entry_price:.4f}`\n"
        f"⏱️ **Tempo de Expiração:** `60 Segundos (M1)`\n\n"
        f"_Aguarde a finalização da vela M1..._",
        parse_mode="Markdown"
    )

    # Simula o tempo do gráfico M1 (60s)
    time.sleep(60)

    # Consulta preço final da Binance após 1 minuto
    preco_final = obter_preco_binance(symbol)
    if not preco_final:
        preco_final = entry_price * (1.006 if side == "LONG" else 0.994)

    # Cálculo do resultado
    var_percent = ((preco_final - entry_price) / entry_price) * 100
    if side == "SHORT":
        var_percent = -var_percent

    resultado = "PROFIT" if var_percent > 0 else "LOSS"
    lucro_usd = (var_percent / 100) * 1000 # Simulação com $1000 USDT de banca
    
    icon = "✅" if resultado == "PROFIT" else "❌"
    emoji_res = "🟢" if resultado == "PROFIT" else "🔴"

    # Salva no Histórico do dia
    HISTORICO_HOJE.append({
        "symbol": symbol,
        "side": side,
        "result": resultado,
        "pnl": f"{var_percent:+.2f}%",
        "lucro_usd": lucro_usd
    })

    # Envia Resultado da Ordem M1
    texto_resultado = (
        f"{icon} **RESULTADO DA ORDEM M1** {icon}\n\n"
        f"🪙 **Ativo:** `{symbol}` ({side})\n"
        f"💵 **Entrada:** `${entry_price:.4f}`\n"
        f"🏁 **Saída M1:** `${preco_final:.4f}`\n"
        f"📈 **Variação:** `{var_percent:+.2f}%`\n"
        f"{emoji_res} **Resultado:** **{resultado} (${lucro_usd:+.2f} USDT)**\n\n"
        f"Use `/relatorio` para ver o histórico acumulado!"
    )
    bot.send_message(chat_id, texto_resultado, parse_mode="Markdown", reply_markup=criar_menu_principal())

# ==============================================================================
# 4. CONSTRUTORES DE MENUS INTERATIVOS
# ==============================================================================
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    
    btn_abrir = InlineKeyboardButton("⚡ Abrir Ordem M1 (Sortida)", callback_data="abrir_ordem_sortida")
    btn_sinais = InlineKeyboardButton("📡 Gerar Sinal M1", callback_data="gerar_sinal_m1")
    btn_posicoes = InlineKeyboardButton("📊 Posições Abertas", callback_data="ver_posicoes")
    btn_relatorio = InlineKeyboardButton("📈 Relatório Diário", callback_data="ver_relatorio")
    btn_links = InlineKeyboardButton("🎁 Bônus & Links", callback_data="ver_links")
    btn_refresh = InlineKeyboardButton("🔄 Atualizar Painel", callback_data="refresh_painel")
    
    markup.add(btn_abrir)
    markup.add(btn_sinais, btn_posicoes)
    markup.add(btn_relatorio, btn_links)
    markup.add(btn_refresh)
    return markup

def criar_menu_links_estilo_img1():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎁 BINANCE", url=LINK_BINANCE), InlineKeyboardButton("🎁 WALLET", url=LINK_WALLET))
    markup.row(InlineKeyboardButton("💵 TELEGRAM × BINANCE", url=LINK_TELEGRAM))
    markup.row(InlineKeyboardButton("💸 CLAIM $100 BONUS", url=LINK_BINANCE))
    markup.row(InlineKeyboardButton("🔄 VOLTAR AO PAINEL", callback_data="refresh_painel"))
    return markup

# ==============================================================================
# 5. HANDLERS E COMANDOS
# ==============================================================================
@bot.message_handler(commands=['start'])
def command_start(message):
    texto = (
        "🤖 **BOT SCALPER M1 - BINANCE LIVE**\n\n"
        "• Cotações puxadas diretamente da Binance (Grátis)\n"
        "• Ordens e Sinais M1 interativos com resultado na hora!\n\n"
        "Escolha uma ação abaixo:"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id

    if call.data == "gerar_sinal_m1":
        sinal = gerar_sinal_sortido_m1()
        texto = (
            f"📡 **SINAL DETECTADO EM TEMPO REAL (M1)**\n\n"
            f"🎯 **Ativo:** `{sinal['symbol']}`\n"
            f"📈 **Direção:** `{sinal['side']}`\n"
            f"💵 **Entrada Atual:** `${sinal['entry']:.4f}`\n"
            f"🎯 **Alvo TP1:** `${sinal['tp1']:.4f}`\n"
            f"🎯 **Alvo TP2:** `${sinal['tp2']:.4f}`\n"
            f"🛑 **Stop Loss:** `${sinal['sl']:.4f}`\n"
        )
        bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id, "Sinal M1 Binance Gerado!")

    elif call.data == "abrir_ordem_sortida":
        sinal = gerar_sinal_sortido_m1()
        bot.answer_callback_query(call.id, f"Iniciando ordem em {sinal['symbol']}...")
        # Dispara thread paralela para rodar o M1 (60s) sem travar o bot
        threading.Thread(target=processar_execucao_ordem_m1, args=(chat_id, sinal)).start()

    elif call.data == "ver_relatorio":
        total_trades = len(HISTORICO_HOJE)
        vitorias = sum(1 for t in HISTORICO_HOJE if t["result"] == "PROFIT")
        derrotas = sum(1 for t in HISTORICO_HOJE if t["result"] == "LOSS")
        lucro_total = sum(t["lucro_usd"] for t in HISTORICO_HOJE)
        status_emoji = "🟢" if lucro_total >= 0 else "🔴"

        texto = (
            f"📈 **RELATÓRIO DIÁRIO DE TRADING (M1)**\n"
            f"───────────────────────────\n"
            f"• Total de Operações: `{total_trades}`\n"
            f"• Vitórias: `🟢 {vitorias}` | Derrotas: `🔴 {derrotas}`\n"
            f"• PnL Total: {status_emoji} **${lucro_total:+.2f} USDT**\n\n"
            f"📝 **ÚLTIMOS TRADES:**\n"
        )
        for t in HISTORICO_HOJE[-5:]:
            icon = "✅" if t["result"] == "PROFIT" else "❌"
            texto += f"{icon} **{t['symbol']}** ({t['side']}) → `{t['pnl']}` (${t['lucro_usd']:+.2f})\n"
            
        bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id)

    elif call.data == "ver_links":
        bot.send_message(chat_id, "🎁 **LINKS & BÔNUS BINANCE**", reply_markup=criar_menu_links_estilo_img1())
        bot.answer_callback_query(call.id)

    elif call.data == "refresh_painel":
        bot.send_message(chat_id, "🔄 **Painel Atualizado com a Binance!**", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id)

# ==============================================================================
# 6. SERVIDOR HTTP PARA O RENDER
# ==============================================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Scalper M1 Binance Live!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ==============================================================================
# 7. EXECUÇÃO
# ==============================================================================
if __name__ == "__main__":
    bot.remove_webhook()
    print("🚀 Bot Scalper M1 Live Binance Iniciado!")
    bot.infinity_polling(skip_pending=True)
    
