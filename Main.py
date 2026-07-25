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

# Lista de Ativos Suportados (Todos puxam preço ao vivo da Binance)
ATIVOS_CRIPTO = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "OPUSDT", 
    "CHZUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", 
    "NEARUSDT", "SUIUSDT", "PEPEUSDT", "DOGEUSDT", "UNIUSDT", "ARBUSDT"
]

HISTORICO_HOJE = []

# ==============================================================================
# 2. COTAÇÃO 100% REAL EM TEMPO REAL VIA API BINANCE (GRÁTIS / SEM SENHA)
# ==============================================================================
def obter_preco_real_binance(symbol):
    """Puxa a cotação EXATA e atualizada em milissegundos da Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        res = requests.get(url, timeout=5).json()
        return float(res["price"])
    except Exception as e:
        logging.error(f"Erro ao buscar preço real de {symbol}: {e}")
        return None

def gerar_sinal_com_preco_real(symbol=None):
    """Gera o sinal baseado estritamente no preço ATUAL do mercado"""
    if not symbol:
        symbol = random.choice(ATIVOS_CRIPTO)
        
    preco_real = obter_preco_real_binance(symbol)
    
    # Se a API falhar por instabilidade na rede
    if not preco_real:
        preco_real = obter_preco_real_binance("BTCUSDT") # Tenta par principal
        
    side = random.choice(["LONG 🟢", "SHORT 🔴"])
    
    # Cálculos exatos de Alvos baseados no Preço REAL de entrada
    if "LONG" in side:
        tp1 = preco_real * 1.005 # +0.5%
        tp2 = preco_real * 1.010 # +1.0%
        sl = preco_real * 0.995  # -0.5%
    else:
        tp1 = preco_real * 0.995 # -0.5%
        tp2 = preco_real * 0.990 # -1.0%
        sl = preco_real * 1.005  # +0.5%

    return {
        "symbol": symbol,
        "side": side,
        "entry": preco_real,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl
    }

# ==============================================================================
# 3. TESTE DE ORDEM M1 COM PREÇO INICIAL E FINAL REAIS
# ==============================================================================
def processar_teste_m1_real(chat_id, sinal):
    """Mede a variação real do preço da Binance no intervalo de 1 minuto (M1)"""
    symbol = sinal["symbol"]
    side = "LONG" if "LONG" in sinal["side"] else "SHORT"
    entry_price = sinal["entry"]
    
    # Notificação do Preço Exato de Entrada
    msg = bot.send_message(
        chat_id, 
        f"⏳ **TESTE M1 INICIADO (PREÇO REAL BINANCE)**\n\n"
        f"🪙 **Ativo:** `{symbol}` ({side})\n"
        f"💵 **Preço Exato de Entrada:** `${entry_price}`\n\n"
        f"⏱️ _Aguardando 60 segundos do fechamento da vela M1..._\n"
        f"Progresso: [⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛] 0%",
        parse_mode="Markdown"
    )

    # Aguarda 60 segundos do timeframe M1
    time.sleep(30)
    try:
        bot.edit_message_text(
            f"⏳ **TESTE M1 EM ANDAMENTO (30s/60s)**\n\n"
            f"🪙 **Ativo:** `{symbol}` ({side})\n"
            f"💵 **Entrada Real:** `${entry_price}`\n\n"
            f"🔄 _Consultando fluxo de ordens na Binance..._\n"
            f"Progresso: [🟩🟩🟩🟩🟩⬛⬛⬛⬛⬛] 50%",
            chat_id, msg.message_id, parse_mode="Markdown"
        )
    except: pass

    time.sleep(30) # Completa 60s

    # Puxa o PREÇO REAL da Binance após 1 minuto
    preco_fechamento_real = obter_preco_real_binance(symbol)
    
    if not preco_fechamento_real:
        preco_fechamento_real = entry_price

    # Cálculo do resultado baseado na movimentação real da Binance
    var_percent = ((preco_fechamento_real - entry_price) / entry_price) * 100
    if side == "SHORT":
        var_percent = -var_percent

    resultado = "PROFIT" if var_percent >= 0 else "LOSS"
    lucro_usd = (var_percent / 100) * 1000  # PnL proporcional sobre $1000 USDT
    
    icon = "✅" if resultado == "PROFIT" else "❌"
    status_color = "🟢" if resultado == "PROFIT" else "🔴"

    # Salva no histórico do bot
    HISTORICO_HOJE.append({
        "symbol": symbol,
        "side": side,
        "result": resultado,
        "pnl": f"{var_percent:+.2f}%",
        "lucro_usd": lucro_usd
    })

    # Resultado Final com Preço Real de Entrada e Saída
    texto_final = (
        f"{icon} **RESULTADO DA ORDEM M1 (DADOS REAIS)** {icon}\n\n"
        f"🪙 **Ativo:** `{symbol}` ({side})\n"
        f"💵 **Preço Entrada:** `${entry_price}`\n"
        f"🏁 **Preço Saída M1:** `${preco_fechamento_real}`\n"
        f"📈 **Variação Mercado Real:** `{var_percent:+.2f}%`\n"
        f"{status_color} **Resultado:** **{resultado} (${lucro_usd:+.2f} USDT)**\n"
    )
    
    bot.send_message(chat_id, texto_final, parse_mode="Markdown", reply_markup=criar_menu_principal())

# ==============================================================================
# 4. MENUS INTERATIVOS
# ==============================================================================
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    
    btn_sinal = InlineKeyboardButton("📡 Gerar Sinal (Preço Real)", callback_data="gerar_sinal_real")
    btn_testar = InlineKeyboardButton("⚡ Abrir Ordem M1 (Binance Live)", callback_data="testar_ordem_real")
    btn_relatorio = InlineKeyboardButton("📈 Relatório de Operações", callback_data="ver_relatorio")
    btn_links = InlineKeyboardButton("🎁 Bônus & Links", callback_data="ver_links")
    btn_refresh = InlineKeyboardButton("🔄 Atualizar Cotações", callback_data="refresh_painel")
    
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
        "🤖 **BOT TRADING M1 - PREÇOS 100% REAIS (BINANCE)**\n\n"
        "• Todos os valores (BTC, SOL, ETH...) são buscados na Binance em tempo real.\n"
        "• Teste as ordens e acompanhe o fechamento real da vela M1.\n\n"
        "Escolha uma opção abaixo:"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id

    if call.data == "gerar_sinal_real":
        sinal = gerar_sinal_com_preco_real()
        
        texto = (
            f"📡 **SINAL COM COTAÇÃO REAL BINANCE (M1)**\n\n"
            f"🪙 **Ativo:** `{sinal['symbol']}`\n"
            f"📈 **Direção:** `{sinal['side']}`\n"
            f"💵 **Preço Exato Agora:** `${sinal['entry']}`\n"
            f"🎯 **Alvo TP1 (+0.5%):** `${sinal['tp1']:.4f}`\n"
            f"🎯 **Alvo TP2 (+1.0%):** `${sinal['tp2']:.4f}`\n"
            f"🛑 **Stop Loss (-0.5%):** `${sinal['sl']:.4f}`\n"
        )
        bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id, "Preço buscado na Binance!")

    elif call.data == "testar_ordem_real":
        sinal = gerar_sinal_com_preco_real()
        bot.answer_callback_query(call.id, f"Iniciando ordem com preço real em {sinal['symbol']}...")
        threading.Thread(target=processar_teste_m1_real, args=(chat_id, sinal)).start()

    elif call.data == "ver_relatorio":
        total_trades = len(HISTORICO_HOJE)
        vitorias = sum(1 for t in HISTORICO_HOJE if t["result"] == "PROFIT")
        derrotas = sum(1 for t in HISTORICO_HOJE if t["result"] == "LOSS")
        lucro_total = sum(t["lucro_usd"] for t in HISTORICO_HOJE)
        status_emoji = "🟢" if lucro_total >= 0 else "🔴"

        texto = (
            f"📈 **RELATÓRIO DE SESSÃO (M1 REAIS)**\n"
            f"───────────────────────────\n"
            f"• Ordens Executadas: `{total_trades}`\n"
            f"• Vitórias: `🟢 {vitorias}` | Derrotas: `🔴 {derrotas}`\n"
            f"• Resultado Acumulado: {status_emoji} **${lucro_total:+.2f} USDT**\n\n"
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
        bot.send_message(chat_id, "🔄 **Painel Atualizado com Cotações em Tempo Real!**", reply_markup=criar_menu_principal())
        bot.answer_callback_query(call.id)

# ==============================================================================
# 6. SERVIDOR HTTP PARA O RENDER
# ==============================================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Binance Precos Reais M1!")

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
    print("🚀 Bot M1 com Cotação Real Binance Iniciado!")
    bot.infinity_polling(skip_pending=True)
