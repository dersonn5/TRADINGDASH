"""
Embedder de Dados para TradingView Cockpit HTML (Sem Dependência de CORS)
========================================================================
Lê 'research/trade_1_data.json' e injeta o objeto JSON diretamente como uma
variável JavaScript 'const tradeData = {...};' dentro de
'research/plots_html/tradingview_cockpit_trade_1.html'.
Isso garante que o arquivo HTML abra perfeitamente em QUALQUER navegador local
sem bloqueios de segurança (CORS).
"""

import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

JSON_PATH = os.path.join(os.path.dirname(__file__), "trade_1_data.json")
HTML_PATH = os.path.join(os.path.dirname(__file__), "plots_html", "tradingview_cockpit_trade_1.html")


def main():
    if not os.path.exists(JSON_PATH):
        print(f"[ERRO] {JSON_PATH} não existe. Rode export_tradingview_data primeiro.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    json_str = json.dumps(data)

    html_code = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TradingView Cockpit — ICT Trade #1 Review</title>
  <!-- TradingView Official Lightweight Charts CDN -->
  <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
  <!-- Google Fonts: Inter -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    body {{
      background-color: #131722;
      color: #d1d4dc;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    /* Header Bar */
    header {{
      background-color: #1e222d;
      border-bottom: 1px solid #2a2e39;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 10;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .logo-badge {{
      background: linear-gradient(135deg, #2962ff, #1e88e5);
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }}
    .asset-title {{
      font-size: 15px;
      font-weight: 600;
      color: #ffffff;
    }}
    /* Timeframe Selector Buttons */
    .tf-selector {{
      display: flex;
      background-color: #131722;
      border-radius: 6px;
      padding: 3px;
      gap: 2px;
      border: 1px solid #2a2e39;
    }}
    .tf-btn {{
      background: none;
      border: none;
      color: #787b86;
      font-size: 12px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .tf-btn:hover {{
      color: #d1d4dc;
      background-color: rgba(255, 255, 255, 0.05);
    }}
    .tf-btn.active {{
      color: #ffffff;
      background-color: #2962ff;
    }}
    /* Trade Status Badge */
    .trade-status-hud {{
      display: flex;
      align-items: center;
      gap: 16px;
      background-color: #131722;
      border: 1px solid #2a2e39;
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
    }}
    .hud-item {{
      display: flex;
      gap: 6px;
    }}
    .hud-label {{
      color: #787b86;
    }}
    .hud-val {{
      font-weight: 600;
    }}
    .val-loss {{ color: #f23645; }}
    .val-win {{ color: #089981; }}
    .val-entry {{ color: #2962ff; }}

    /* Floating Tool Overlay Info Panel */
    .ict-overlay-legend {{
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(19, 23, 34, 0.88);
      backdrop-filter: blur(8px);
      border: 1px solid #2a2e39;
      border-radius: 8px;
      padding: 12px 16px;
      z-index: 5;
      pointer-events: none;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}
    .legend-title {{
      font-size: 13px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .legend-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      margin-bottom: 4px;
    }}
    .color-swatch {{
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }}
    
    /* Drawing Tools Overlay */
    #drawing-canvas {{
      position: absolute;
      top: 0; left: 48px; /* Offset for toolbar */
      width: calc(100% - 48px); height: 100%;
      z-index: 20;
      pointer-events: none;
      cursor: crosshair;
    }}
    #drawing-canvas.active {{
      pointer-events: auto;
    }}
    
    /* Left Vertical Toolbar (TradingView Style) */
    .drawing-toolbar {{
      position: absolute;
      top: 56px; /* Below header */
      left: 0;
      bottom: 0;
      width: 52px;
      z-index: 30;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      background: #ffffff; /* Tema Claro igual o print */
      padding: 12px 0;
      border-right: 1px solid #e0e3eb;
      overflow-y: auto;
    }}
    /* Scrollbar oculta */
    .drawing-toolbar::-webkit-scrollbar {{ display: none; }}
    
    .tool-btn {{
      background: transparent;
      border: none;
      color: #131722;
      width: 38px;
      height: 38px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }}
    .tool-btn svg {{
      width: 22px;
      height: 22px;
      stroke: #131722;
      stroke-width: 1.5;
      fill: none;
    }}
    .tool-btn:hover {{ background: #f0f3fa; }}
    .tool-btn.active {{ background: #e0e3eb; }}
    
    .toolbar-separator {{
      width: 32px;
      height: 1px;
      background: #e0e3eb;
      margin: 4px 0;
    }}
    
    /* Main Chart Container */
    #chart-container {{
      flex: 1;
      width: 100%;
      position: relative;
      margin-left: 52px; /* Space for the left toolbar */
    }}
  </style>
</head>
<body>

  <!-- Header Section -->
  <header>
    <div class="brand">
      <span class="logo-badge">TRADINGVIEW ENGINE</span>
      <span class="asset-title">NQ1! — Nasdaq Futures (Trade #1 Audit)</span>
    </div>

    <!-- Timeframe Buttons -->
    <div class="tf-selector">
      <button class="tf-btn active" id="btn-1m" onclick="switchTF('1m')">1M</button>
      <button class="tf-btn" id="btn-5m" onclick="switchTF('5m')">5M</button>
      <button class="tf-btn" id="btn-1h" onclick="switchTF('1h')">1H</button>
    </div>

    <!-- Trade Status HUD -->
    <div class="trade-status-hud">
      <div class="hud-item">
        <span class="hud-label">Tipo:</span>
        <span class="hud-val val-entry" id="hud-side">{data['action']}</span>
      </div>
      <div class="hud-item">
        <span class="hud-label">Entrada:</span>
        <span class="hud-val" id="hud-entry">{data['entry_price']:.2f}</span>
      </div>
      <div class="hud-item">
        <span class="hud-label">Resultado:</span>
        <span class="hud-val {'val-win' if data['pnl_usd'] > 0 else 'val-loss'}" id="hud-pnl">${data['pnl_usd']:+.2f} ({data['reason']})</span>
      </div>
    </div>
  </header>

  <!-- Main Chart Canvas Container -->
  <div id="chart-container">
    <!-- ICT Annotation Legend -->
    <div class="ict-overlay-legend">
      <div class="legend-title">
        <span>📍 MARCAÇÕES CANÔNICAS ICT</span>
      </div>
      <div class="legend-row">
        <div class="color-swatch" style="background: #ff9800;"></div>
        <span>1M IFVG Zone [{data['ifvg_bottom']:.2f} - {data['ifvg_top']:.2f}]</span>
      </div>
      <div class="legend-row">
        <div class="color-swatch" style="background: #ffffff; border: 1px solid #787b86;"></div>
        <span>RTH ORG High [{data['rth_high']:.2f}]</span>
      </div>
      <div class="legend-row">
        <div class="color-swatch" style="background: #f23645;"></div>
        <span>Sellside Liquidity [{data['sellside_low']:.2f}]</span>
      </div>
      <div class="legend-row">
        <div class="color-swatch" style="background: rgba(8,153,129,0.5);"></div>
        <span>Indicador Risco/Ganho: Alvo 3:1</span>
      </div>
    </div>
    
    <!-- Drawing Canvas -->
    <canvas id="drawing-canvas"></canvas>
  </div>
  
  <div class="drawing-toolbar">
    <!-- 1. Crosshair -->
    <button class="tool-btn active" title="Crosshair">
      <svg viewBox="0 0 24 24"><path d="M12 4v16M4 12h16" stroke-dasharray="4 2"/></svg>
    </button>
    <!-- 2. Trend Line -->
    <button class="tool-btn" id="tool-draw" onclick="toggleTool('draw')" title="Trend Line">
      <svg viewBox="0 0 24 24"><circle cx="5" cy="19" r="1.5"/><circle cx="19" cy="5" r="1.5"/><path d="M6 18L18 6"/></svg>
    </button>
    <!-- 3. Fib -->
    <button class="tool-btn" title="Fib Retracement">
      <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="1.5"/><circle cx="16" cy="18" r="1.5"/></svg>
    </button>
    <!-- 4. Brush/Path -->
    <button class="tool-btn" title="Brush">
      <svg viewBox="0 0 24 24"><circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="7" r="1.5"/><circle cx="18" cy="14" r="1.5"/><path d="M6.5 11l4.5-3.5L17 13"/></svg>
    </button>
    <!-- 5. Long/Short Position -->
    <button class="tool-btn" title="Long Position">
      <svg viewBox="0 0 24 24"><path d="M4 12h16M7 12v-4M17 12v4"/><circle cx="7" cy="8" r="1.5"/><circle cx="17" cy="16" r="1.5"/></svg>
    </button>
    <!-- 6. Rectangle -->
    <button class="tool-btn" title="Rectangle">
      <svg viewBox="0 0 24 24"><rect x="5" y="7" width="14" height="10"/><circle cx="5" cy="7" r="1"/><circle cx="19" cy="7" r="1"/><circle cx="5" cy="17" r="1"/><circle cx="19" cy="17" r="1"/></svg>
    </button>
    <!-- 7. Text -->
    <button class="tool-btn" id="tool-text" onclick="toggleTool('text')" title="Text">
      <svg viewBox="0 0 24 24"><path d="M5 7h14M12 7v11M10 18h4"/></svg>
    </button>
    <!-- 8. Smiley -->
    <button class="tool-btn" title="Icon">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M9 10h.01M15 10h.01M9 15a4 4 0 0 0 6 0"/></svg>
    </button>
    
    <div class="toolbar-separator"></div>
    
    <!-- 9. Ruler -->
    <button class="tool-btn" title="Measure">
      <svg viewBox="0 0 24 24"><path d="M6 18L18 6M8 16l2 2M10 14l2 2M12 12l2 2M14 10l2 2M16 8l2 2" stroke-width="2"/></svg>
    </button>
    <!-- 10. Zoom -->
    <button class="tool-btn" title="Zoom In">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="5"/><path d="M15 15l4 4M9 11h4M11 9v4"/></svg>
    </button>
    
    <div class="toolbar-separator"></div>
    
    <!-- 11. Magnet -->
    <button class="tool-btn" title="Magnet Mode">
      <svg viewBox="0 0 24 24"><path d="M6 10v4a6 6 0 0 0 12 0v-4M6 10h3v-2H6zM15 10h3v-2h-3z"/></svg>
    </button>
    <!-- 12. Lock Drawing -->
    <button class="tool-btn" title="Stay in Drawing Mode">
      <svg viewBox="0 0 24 24"><path d="M14 4l4 4-9 9H5v-4l9-9z"/><rect x="13" y="15" width="6" height="4" rx="1"/><path d="M14 15v-2a2 2 0 0 1 4 0v2"/></svg>
    </button>
    <!-- 13. Lock All -->
    <button class="tool-btn" title="Lock All Drawing Tools">
      <svg viewBox="0 0 24 24"><rect x="7" y="11" width="10" height="8" rx="2"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/></svg>
    </button>
    <!-- 14. Hide -->
    <button class="tool-btn" title="Hide All Drawings">
      <svg viewBox="0 0 24 24"><path d="M3 12c0 0 4-7 9-7s9 7 9 7-4 7-9 7-9-7-9-7z"/><circle cx="12" cy="12" r="3"/><path d="M4 20l4-4"/></svg>
    </button>
    <!-- 15. Object Tree -->
    <button class="tool-btn" title="Object Tree">
      <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
    </button>
    
    <div class="toolbar-separator"></div>
    
    <!-- 16. Trash -->
    <button class="tool-btn" onclick="clearCanvas()" title="Remove Drawings">
      <svg viewBox="0 0 24 24"><path d="M4 6h16M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M10 11v6M14 11v6M5 6l1 14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-14"/></svg>
    </button>
  </div>

  <script>
    // Injeção Direta dos Dados (Sem bloqueio de CORS local)
    const tradeData = {json_str};

    let chart;
    let candlestickSeries;
    let currentTF = '1m';

    // Variáveis do Drawing
    let canvas, ctx;
    let isDrawing = false;
    let currentTool = null; // 'draw', 'text', null
    
    // Armazena as linhas de preço ativas para remover ao trocar o timeframe
    let currentPriceLines = [];
    
    window.onload = function() {{
      initChart();
      initDrawing();
    }};

    function initChart() {{
      const container = document.getElementById('chart-container');
      chart = LightweightCharts.createChart(container, {{
        width: container.clientWidth,
        height: container.clientHeight,
        layout: {{
          background: {{ type: 'solid', color: '#131722' }},
          textColor: '#d1d4dc',
          fontFamily: "'Inter', sans-serif"
        }},
        grid: {{
          vertLines: {{ color: '#1f2430' }},
          horzLines: {{ color: '#1f2430' }}
        }},
        crosshair: {{
          mode: LightweightCharts.CrosshairMode.Normal,
          vertLine: {{ color: '#787b86', width: 1, style: 1, labelBackgroundColor: '#2962ff' }},
          horzLine: {{ color: '#787b86', width: 1, style: 1, labelBackgroundColor: '#2962ff' }}
        }},
        rightPriceScale: {{
          borderColor: '#2a2e39',
          autoScale: true,
          borderVisible: true
        }},
        timeScale: {{
          borderColor: '#2a2e39',
          timeVisible: true,
          secondsVisible: false
        }}
      }});

      candlestickSeries = chart.addCandlestickSeries({{
        upColor: '#089981',
        downColor: '#f23645',
        borderUpColor: '#089981',
        borderDownColor: '#f23645',
        wickUpColor: '#089981',
        wickDownColor: '#f23645'
      }});

      loadTimeframe('1m');

      window.addEventListener('resize', () => {{
        chart.applyOptions({{
          width: container.clientWidth,
          height: container.clientHeight
        }});
      }});
    }}

    function loadTimeframe(tf) {{
      if (!tradeData) return;
      currentTF = tf;

      const candleKey = `candles_${{tf}}`;
      const candles = tradeData[candleKey] || [];
      candlestickSeries.setData(candles);

      // Limpar marcadores anteriores
      candlestickSeries.setMarkers([]);

      // Desenhar Níveis do TradingView
      drawICTLevels();

      // Ajustar Zoom Automaticamente
      chart.timeScale().fitContent();
    }}

    function drawICTLevels() {{
      if (!tradeData) return;
      
      // Limpar price lines anteriores para evitar duplicação ao clicar nos botões de Timeframe
      currentPriceLines.forEach(line => candlestickSeries.removePriceLine(line));
      currentPriceLines = [];

      // 1. Linha do RTH High (Branca Sólida)
      currentPriceLines.push(candlestickSeries.createPriceLine({{
        price: tradeData.rth_high,
        color: '#ffffff',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: 'RTH ORG High'
      }}));

      // 2. Linha da Liquidez de Venda (Vermelha)
      currentPriceLines.push(candlestickSeries.createPriceLine({{
        price: tradeData.sellside_low,
        color: '#f23645',
        lineWidth: 1.5,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: 'Sellside Liquidity'
      }}));

      // 3. Linha de Entrada (Azul)
      currentPriceLines.push(candlestickSeries.createPriceLine({{
        price: tradeData.entry_price,
        color: '#2962ff',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: `ENTRADA ${{tradeData.action}}`
      }}));

      // 4. Linha de Stop Loss (Vermelha Trastejada)
      currentPriceLines.push(candlestickSeries.createPriceLine({{
        price: tradeData.stop_loss,
        color: '#f23645',
        lineWidth: 1.5,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'STOP LOSS'
      }}));

      // 5. Linha de Take Profit (Verde Trastejada)
      currentPriceLines.push(candlestickSeries.createPriceLine({{
        price: tradeData.take_profit,
        color: '#089981',
        lineWidth: 1.5,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'TAKE PROFIT (3:1)'
      }}));

      // 6. Linhas do FVG (Topo e Fundo)
      if (tradeData.ifvg_top && tradeData.ifvg_bottom) {{
        currentPriceLines.push(candlestickSeries.createPriceLine({{
          price: tradeData.ifvg_top,
          color: '#ff9800',
          lineWidth: 2,
          lineStyle: LightweightCharts.LineStyle.Solid,
          axisLabelVisible: true,
          title: 'FVG TOP'
        }}));
        currentPriceLines.push(candlestickSeries.createPriceLine({{
          price: tradeData.ifvg_bottom,
          color: '#ff9800',
          lineWidth: 2,
          lineStyle: LightweightCharts.LineStyle.Solid,
          axisLabelVisible: true,
          title: 'FVG BOT'
        }}));
      }}

      // Marcadores de Ordem
      if (tradeData.entry_timestamp) {{
        candlestickSeries.setMarkers([
          {{
            time: tradeData.entry_timestamp,
            position: tradeData.action === 'BUY' ? 'belowBar' : 'aboveBar',
            color: '#2962ff',
            shape: tradeData.action === 'BUY' ? 'arrowUp' : 'arrowDown',
            text: `ENTRADA ${{tradeData.action}} @ ${{tradeData.entry_price}}`
          }},
          {{
            time: tradeData.exit_timestamp,
            position: tradeData.pnl_usd > 0 ? 'aboveBar' : 'belowBar',
            color: tradeData.pnl_usd > 0 ? '#089981' : '#f23645',
            shape: 'square',
            text: `SAÍDA: ${{tradeData.reason}}`
          }}
        ]);
      }}
    }}

    function switchTF(tf) {{
      document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(`btn-${{tf}}`).classList.add('active');
      loadTimeframe(tf);
    }}

    // --- Lógica de Desenho e Texto ---
    function initDrawing() {{
      canvas = document.getElementById('drawing-canvas');
      ctx = canvas.getContext('2d');
      resizeCanvas();
      
      window.addEventListener('resize', resizeCanvas);
      
      canvas.addEventListener('mousedown', startDrawing);
      canvas.addEventListener('mousemove', draw);
      canvas.addEventListener('mouseup', stopDrawing);
      canvas.addEventListener('mouseout', stopDrawing);
    }}

    function resizeCanvas() {{
      const container = document.getElementById('chart-container');
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }}

    function toggleTool(tool) {{
      if (currentTool === tool) {{
        currentTool = null;
        document.getElementById(`tool-${{tool}}`).classList.remove('active');
        canvas.classList.remove('active');
      }} else {{
        currentTool = tool;
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(`tool-${{tool}}`).classList.add('active');
        canvas.classList.add('active');
      }}
    }}

    function clearCanvas() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }}

    function startDrawing(e) {{
      // Corrigir offset do mouse relativo ao canvas (pois o canvas ta offset)
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      if (currentTool === 'draw') {{
        isDrawing = true;
        ctx.beginPath();
        ctx.moveTo(mouseX, mouseY);
      }} else if (currentTool === 'text') {{
        const text = prompt("Digite o texto:");
        if (text) {{
          ctx.font = "bold 14px Inter";
          ctx.fillStyle = "#ffeb3b";
          ctx.fillText(text, mouseX, mouseY);
        }}
        toggleTool('text');
      }}
    }}

    function draw(e) {{
      if (!isDrawing || currentTool !== 'draw') return;
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      ctx.strokeStyle = "#ffeb3b";
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.lineTo(mouseX, mouseY);
      ctx.stroke();
    }}

    function stopDrawing() {{
      if (isDrawing) {{
        isDrawing = false;
        ctx.closePath();
      }}
    }}
  </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(HTML_PATH), exist_ok=True)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_code)

    print(f"✅ HTML compilado com dados embutidos (Zero CORS error): {HTML_PATH}")


if __name__ == "__main__":
    main()
