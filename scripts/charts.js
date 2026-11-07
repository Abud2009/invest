// Render 4 charts with ECharts SSR -> SVG -> PNG via resvg (English labels)
const echarts = require('echarts');
const { Resvg } = require('@resvg/resvg-js');
const fs = require('fs');

const FONT = 'Segoe UI, Microsoft YaHei, sans-serif';
const C = { blue: '#2f6fed', red: '#d64545', green: '#2e9e6b', amber: '#e8a13a', gray: '#8a94a6', dark: '#22293a', purple: '#7b5cd6' };
const baseText = { fontFamily: FONT, color: C.dark };

function render(option, file, w = 980, h = 540) {
  const chart = echarts.init(null, null, { renderer: 'svg', ssr: true, width: w, height: h });
  chart.setOption(option);
  const svg = chart.renderToSVGString();
  const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: w * 2 }, font: { loadSystemFonts: true } });
  fs.writeFileSync(file, resvg.render().asPng());
  chart.dispose();
  console.log('wrote', file);
}
const axisStyle = () => ({ axisLabel: { ...baseText, fontSize: 13 }, axisLine: { lineStyle: { color: '#c8cfdb' } }, splitLine: { lineStyle: { color: '#eceff4' } } });
const yStyle = (yname) => ({ ...axisStyle(), name: yname, nameTextStyle: { ...baseText, fontSize: 13 }, nameLocation: 'middle', nameGap: 50 });
const tip = { trigger: 'axis', textStyle: { fontFamily: FONT } };

// ---- Chart 1: BTC hourly mean return profile (CET) ----
const hours = [...Array(24).keys()];
const btcMeanBp = [-3.66,0.08,-3.28,-4.64,-0.27,2.01,2.7,-0.91,-0.17,0.6,3.26,-1.29,-0.67,1.66,-1.0,-6.12,3.29,2.47,1.04,1.36,-3.9,-1.09,5.85,0.87];
render({
  backgroundColor: '#fff',
  title: { text: 'Bitcoin average hourly return by time of day (CET)', subtext: '~6 months of hourly data (May–November 2026) · mean return per hour in basis points', left: 'center', textStyle: { ...baseText, fontSize: 17 }, subtextStyle: baseText },
  grid: { left: 70, right: 40, top: 90, bottom: 60 },
  xAxis: { type: 'category', data: hours.map(h => h + ':00'), ...axisStyle() },
  yAxis: { type: 'value', ...yStyle('mean return (bp)'), axisLine: { show: false } },
  series: [{
    type: 'bar', data: btcMeanBp.map(v => ({ value: v, itemStyle: { color: v >= 0 ? C.green : C.red, opacity: 0.85 } })),
    barWidth: '62%',
    markLine: { silent: true, symbol: 'none', lineStyle: { color: C.dark, width: 1.5 }, label: { ...baseText, formatter: '0 bp', position: 'insideStartTop' }, data: [{ yAxis: 0 }] },
    markArea: { silent: true, itemStyle: { color: 'rgba(47,111,237,0.07)' }, label: { ...baseText, fontSize: 12, color: C.blue }, data: [[{ name: 'sleep window 0:00–8:00', xAxis: '0:00' }, { xAxis: '7:00' }]] },
  }],
  tooltip: tip,
}, 'chart1_btc_hourly.png');

// ---- Chart 2: BTC overnight (00-08 CET) return distribution ----
const edges = [-2.75,-2.25,-1.75,-1.25,-0.75,-0.25,0.25,0.75,1.25,1.75,2.25,2.75,3.25,3.75];
const labels = edges.slice(0,-1).map((e,i)=>`${e}…${edges[i+1]}%`);
const freq = [1, 3, 8, 18, 38, 51, 34, 18, 6, 3, 1, 0, 1];
render({
  backgroundColor: '#fff',
  title: { text: 'BTC overnight returns: buy 0:00 → sell 8:00 (182 nights)', subtext: 'Price moves both ways while you sleep; trading costs swallow most small moves', left: 'center', textStyle: { ...baseText, fontSize: 17 }, subtextStyle: baseText },
  grid: { left: 70, right: 40, top: 90, bottom: 60 },
  xAxis: { type: 'category', data: labels, ...axisStyle() },
  yAxis: { type: 'value', ...yStyle('number of nights') },
  series: [{
    type: 'bar', barWidth: '62%',
    data: freq.map((v,i) => ({ value: v, itemStyle: { color: i < 6 ? C.red : C.green, opacity: 0.85 } })),
    markLine: { silent: true, symbol: 'none', data: [
      { xAxis: '-0.25…0.25%', lineStyle: { color: C.dark, width: 1 }, label: { show: false } },
      { xAxis: '-0.75…-0.25%', lineStyle: { color: C.amber, width: 2, type: 'dashed' }, label: { ...baseText, formatter: 'costs ~0.25%\n(Binance)', position: 'insideEndTop' } },
      { xAxis: '-1.75…-1.25%', lineStyle: { color: C.purple, width: 2, type: 'dashed' }, label: { ...baseText, formatter: 'costs ~1%\n(Kraken Pro)', position: 'insideEndTop' } },
    ]},
  }],
  tooltip: tip,
}, 'chart2_btc_distribution.png');

// ---- Chart 3: overnight P&L trajectory 0-8 CET ----
const trajWd = [0, -0.8, -1.0, -1.7, -2.6, -2.8, -2.4, -1.9, -2.0];
const trajWe = [0, -0.3, 0.2, 0.4, -0.1, 0.2, 0.3, 0.2, 0.1];
render({
  backgroundColor: '#fff',
  title: { text: 'Average overnight P&L path: 2,000 Kč in BTC from 0:00 to 8:00', subtext: 'Weekend nights are calmer; weekday nights drift slightly down until ~5 AM', left: 'center', textStyle: { ...baseText, fontSize: 17 }, subtextStyle: baseText },
  grid: { left: 70, right: 40, top: 90, bottom: 60 },
  xAxis: { type: 'category', data: ['0:00','1:00','2:00','3:00','4:00','5:00','6:00','7:00','8:00'], ...axisStyle() },
  yAxis: { type: 'value', ...yStyle('average P&L (Kč)'), axisLine: { show: false } },
  series: [
    { name: 'weekday night (n=130)', type: 'line', data: trajWd, smooth: true, symbolSize: 7, lineStyle: { width: 3, color: C.red }, itemStyle: { color: C.red } },
    { name: 'weekend night (n=52)', type: 'line', data: trajWe, smooth: true, symbolSize: 7, lineStyle: { width: 3, color: C.blue }, itemStyle: { color: C.blue } },
    { name: 'break-even', type: 'line', data: [0,0,0,0,0,0,0,0,0], symbol: 'none', lineStyle: { color: C.gray, type: 'dashed', width: 1.5 }, tooltip: { show: false } },
  ],
  legend: { bottom: 5, textStyle: baseText },
  tooltip: tip,
}, 'chart3_overnight_path.png');

// ---- Chart 4: expected overnight drift vs round-trip costs ----
render({
  backgroundColor: '#fff',
  title: { text: 'Expected overnight move vs. round-trip trading costs (2,000 Kč)', subtext: 'Unleveraged. At this size, fees outweigh any statistical edge almost every night', left: 'center', textStyle: { ...baseText, fontSize: 17 }, subtextStyle: baseText },
  grid: { left: 70, right: 40, top: 90, bottom: 60 },
  xAxis: { type: 'category', data: ['BTC','ETH','Gold (GC)','EUR/USD','Savings account'], ...axisStyle() },
  yAxis: { type: 'value', ...yStyle('Kč per night (on 2,000 Kč)'), axisLine: { show: false } },
  series: [
    { name: 'average overnight move', type: 'bar', barWidth: '30%', data: [
      { value: -1.4, itemStyle: { color: C.red } }, { value: -3.2, itemStyle: { color: C.red } },
      { value: -1.7, itemStyle: { color: C.red } }, { value: -0.2, itemStyle: { color: C.red } },
      { value: 0.19, itemStyle: { color: C.green } },
    ] },
    { name: 'costs: Binance 0.25%', type: 'bar', barWidth: '18%', data: [-5,-5,-5,-5,0], itemStyle: { color: C.amber } },
    { name: 'costs: Kraken Pro 1%', type: 'bar', barWidth: '18%', data: [-20,-20,-20,-20,0], itemStyle: { color: C.purple } },
  ],
  legend: { bottom: 5, textStyle: baseText },
  tooltip: tip,
}, 'chart4_drift_vs_fees.png');
