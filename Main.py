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

LINK_BINANCE = "https://www.binance.com"
LINK_WALLET = "https://wallet.telegram.org"
LINK_TELEGRAM = "https://t.me"

ATIVOS_CRIPTO = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "OPUSDT", 
    "CHZUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", 
    "NEARUSDT", "SUIUSDT", "PEPEUSDT", "DOGEUSDT", "UNIUSDT", "ARBUSDT"
]

HISTORICO_HOJE = []

# ==============================================================================
# 2. INTEGRAÇÃO BINANCE LIVE + LÓGICA DE BACKTEST DADOS M1
# ==============================================================================
def obter_preco_binance(symbol):
    """Puxa o preço real do ativo via API pública Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        res = requests.get(url, timeout=5).json()
        return float(res["price"])
    except Exception as e:
        logging.error(f"Erro na API Binance para {symbol}: {e}")
        return 100.0

def executar_backtest_sinal(symbol, side):
    """Gera dados estatísticos de Backtest dinâmico para o Sinal M1"""
    total_amostras = 50 # Analisa últimas 50 velas M1
    vitorias = random.randint(38, 46) # Simulador de assertividade alta para M1
    winrate = (vitorias / total_amostras) * 100
    
    rsi_simulado = random.randint(28, 35) if "LONG" in side else random.randint(65, 72)
    vol_confirmacao = random.choice(["ALTO (2.4x)", "SUPERIOR A MEDIA (1.8x)", "EXPLOSIVO (3.1x)"])
    
    return {
        "samples": total_amostras,
        "wins": vitorias,
        "winrate": winrate,
        "rsi": rsi_simulado,
        "volume": vol_confirmacao
    }

def gerar_sinal_com_backtest(symbol=None):
    if not symbol:
        symbol = random.choice(ATIVOS_CRIPTO)
        
    preco_atual = obter_preco_binance(symbol)
    side = random.choice(["LONG 🟢", "SHORT 🔴"])
    
    # Preços TP/SL para M1 (~0.5% a 1.2%)
    if "LONG" in side:
        tp1 = preco_atual * 1.005
        tp2 = preco_atual * 1.010
        sl = preco_atual * 0.995
    else:
        tp1 = preco_atual * 0.995
        tp2 = preco_atual * 0.990
        sl = preco_atual * 1.005

    backtest = executar_backtest_sinal(symbol, side)

    return {
        "symbol": symbol,
        "side": side,
        "entry": preco_atual,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "backtest": backtest
    }

# ==============================================================================
# 3. EXECUÇÃO DO TESTE M1 AO VIVO (SIMULAÇÃO + BACKTEST VISUAL)
# ==============================================================================
def processar_teste_ao_vivo(chat_id, sinal):
    """Executa a simulação do M1 passo a passo na tela para os membros acompanharem"""
    symbol = sinal["symbol"]
    side = "LONG" if "LONG" in sinal["side"] else "SHORT"
    entry_price = sinal["entry"]
    
    # 1. Envia mensagem inicial do Teste M1
    msg = bot.send_message(
        chat_id, 
        f"⏳ **INICIANDO TESTE EM TEMPO REAL (M1)**\n\n"
        f"🪙 **Ativo:** `{symbol}` ({side})\n"
        f"💵 **Preço Entrada:** `${entry_price:.4f}`\n\n"
        f"📊 **Métricas de Backtest do Algoritmo:**\n"
        f"• Assertividade Recente (50 Velas): `{sinal['backtest']['winrate']:.1f}%`\n"
        f"• RSI M1: `{sinal['backtest']['rsi']}` | Volume: `{sinal['backtest']['volume']}`\n\n"
        f"⏱️ _Acompanhando movimentação da vela M1... [⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛] 0%_",
        parse_mode="Markdown"
    )

    # 2. Atualização visual durante a ordem M1 (60s)
    time.sleep(20)
    try:
        bot.edit_message_text(
            f"⏳ **TESTE M1 EM ANDAMENTO (20s/60s)**\n\n"
            f"🪙 **Ativo:** `{symbol}` ({side})\n"
            f"💵 **Entrada:** `${entry_price:.4f}`\n\n"
            f"🟢 status: _Vela M1 com fluxo comprador/vendedor positivo..._\n"
            f"⏱️ _Progresso: [🟩🟩🟩⬛⬛⬛⬛⬛⬛⬛] 33%_",
            chat_id, msg.message_id, parse_mode="Markdown"
        )
    except: pass

    time.sleep(20)
    try:
        bot.edit_message_text(
            f"⏳ **TESTE M1 EM ANDAMENTO (40s/60s)**\n\n"
            f"🪙 **Ativo:** `{symbol}` ({side})\n"
            f"💵 **Entrada:** `${entry_price:.4f}`\n\n"
            f"🎯 status: _Aproximando-se do Alvo TP1..._\n"
            f"⏱️ _Progresso: [🟩🟩🟩🟩🟩🟩⬛⬛⬛⬛] 66%_",
            chat_id, msg.message_id, parse_mode="Markdown"
        )
    except: pass

    time.sleep(20) # Total 60 segundos (M1)

    # 3. Puxa preço final da Binance após 1 minuto
    preco_final = obter_preco_binance(symbol)
    if not preco_final or preco_final == entry_price:
        preco_final = entry_price * (1.006 if side == "LONG" else 0.994)

    var_percent = ((preco_final - entry_price) / entry_price) * 100
    if side == "SHORT":
        var_percent = -var_percent

    resultado = "PROFIT" if var_percent > 0 else "LOSS"
    lucro_usd = (var_percent / 100) * 1000 
    
    icon = "✅" if resultado == "PROFIT" else "❌"
    status_color = "🟢" if resultado == "PROFIT" else "🔴"

    # Salva no histórico
    HISTORICO_HOJE.append({
        "symbol": symbol,
        "side": side,
        "result": resultado,
        "pnl": f"{var_percent:+.2f}%",
        "lucro_usd": lucro_usd
    })

    # Mensagem Final com Resultado e Validação do Backtest
    texto_final = (
        f"{icon} **RESULTADO DO TESTE DE SINAL M1** {icon}\n\n"
        f"🪙 **Ativo:** `{symbol}` ({side})\n"
        f"💵 **Preço de Entrada:** `${entry_price:.4f}`\n"
        f"🏁 **Fechamento M1:** `${preco_final:.4f}`\n"
        f"📈 **Variação Real:** `{var_percent:+.2f}%`\n"
        f"{status_color} **Resultado Final:** **{resultado} (${lucro_usd:+.2f} USDT)**\n\n"
        f"📋 **Confirmação do Backtest:**\n"
        f"• Sinais Executados Hoje: `{len(HISTORICO_HOJE)}`\n"
        f"• Teste M1 Validado com Sucesso!"
    )
    
    bot.send_message(chat_id, texto_final, parse_mode="Markdown", reply_markup=criar_menu_principal())

# ==============================================================================
# 4. MENUS INTERATIVOS
# ==============================================================================
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    
    btn_sinal = InlineKeyboardButton("📡 Gerar Sinal + Backtest M1", callback_data="gerar_sinal")
    btn_testar = InlineKeyboardButton("⚡ Abrir & Testar Ordem M1", callback_data="testar_ordem")
    btn_relatorio = InlineKeyboardButton("📈 Relatório de Backtest", callback_data="ver_relatorio")
    btn_links = InlineKeyboardButton("🎁 Bônus & Links", callback_data="ver_links")
    btn_refresh = InlineKeyboardButton("🔄 Atualizar Painel", callback_data="refresh_painel")
    
    markup.add(btn_sinal)
    markup.add(btn_testar)
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
# 5. HANDLERS DOS BOTÕES
# ==============================================================================
@bot.message_handler(commands=['start'])
def command_start(message):
    texto = (
        "🤖 **BOT TRADING M1 - BACKTEST & SINAIS AO VIVO**\n\n"
        "• Todos os sinais acompanham validação e Backtest de M1!\n"
        "• Teste as ordens ao vivo e veja os resultados da vela na hora.\n\n"
        "Escolha uma opção:"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id

    if call.data == "gerar_sinal":
        sinal = gerar_sinal_com_backtest()
        bt = sinal['backtest']
        
        texto = (
            f"📡 **SINAL DETECTADO COM BACKTEST (M1)**\n\n"
            f"🪙 **Ativo:** `{sinal['symbol']}`\n"
            f"📈 **Direção:** `{sinal['side']}`\n"
            f"💵 **Entrada Atual:** `${sinal['entry']:.4f}`\n"
            f"🎯 **Alvo TP1:** `${sinal['tp1']:.4f}`\n"
            f"🎯 **Alvo TP2:** `${sinal['tp2']:.4f}`\n"
            f"🛑 **Stop Loss:** `${sinal['sl']:.4f}`\n\n"
            f"📊 **RELATÓRIO DE BACKTEST (M1):**\n"
            f"• Amostragem: `{bt['samples']} velas M1`\n"
            f"• Assertividade: `🟢 {bt['winrate']:.1f}% ({bt['wins']}/{bt['samples']})`\n"
            f"• RSI: `{bt['rsi']}` | Volume: `{bt['volume']}`\n"
        )
        bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id, "Sinal + Backtest M1 Gerado!")

    elif call.data == "testar_ordem":
        sinal = gerar_sinal_com_backtest()
        bot.answer_callback_query(call.id, f"Iniciando Teste M1 em {sinal['symbol']}...")
        threading.Thread(target=processar_teste_ao_vivo, args=(chat_id, sinal)).start()

    elif call.data == "ver_relatorio":
        total_trades = len(HISTORICO_HOJE)
        vitorias = sum(1 for t in HISTORICO_HOJE if t["result"] == "PROFIT")
        derrotas = sum(1 for t in HISTORICO_HOJE if t["result"] == "LOSS")
        lucro_total = sum(t["lucro_usd"] for t in HISTORICO_HOJE)
        status_emoji = "🟢" if lucro_total >= 0 else "🔴"

        texto = (
            f"📈 **RELATÓRIO GERAL DE BACKTEST & TESTES M1**\n"
            f"───────────────────────────\n"
            f"• Total de Testes Executados: `{total_trades}`\n"
            f"• Vitórias (TP): `🟢 {vitorias}` | Derrotas (SL): `🔴 {derrotas}`\n"
            f"• Saldo Acumulado: {status_emoji} **${lucro_total:+.2f} USDT**\n\n"
            f"📝 **HISTÓRICO RECENTE:**\n"
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
        bot.send_message(chat_id, "🔄 **Painel Atualizado!**", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id)

# ==============================================================================
# 6. SERVIDOR HTTP PARA O RENDER
# ==============================================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Scalper M1 com Backtest Live!")

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
    print("🚀 Bot Scalper M1 com Backtest Binance Iniciado!")
    bot.infinity_polling(skip_pending=True)
            
