#!/usr/bin/env node
/**
 * 从 Wikipedia 拉取最新赛果，合并写入 site/data.json
 * 用法：node scripts/update-data.mjs
 * 建议 cron：每 15 分钟执行一次（见 scripts/install-cron.sh）
 */
import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const DATA_PATH = join(__dir, '../site/data.json');

const TEAM_CN = {
  Mexico: '墨西哥', 'South Africa': '南非', 'South Korea': '韩国', 'Korea Republic': '韩国',
  Czechia: '捷克', 'Czech Republic': '捷克', Switzerland: '瑞士', Canada: '加拿大',
  'Bosnia and Herzegovina': '波黑', Qatar: '卡塔尔', Brazil: '巴西', Morocco: '摩洛哥',
  Scotland: '苏格兰', Haiti: '海地', 'United States': '美国', USMNT: '美国',
  Australia: '澳大利亚', Paraguay: '巴拉圭', Turkey: '土耳其', Türkiye: '土耳其',
  Germany: '德国', 'Ivory Coast': '科特迪瓦', "Côte d'Ivoire": '科特迪瓦',
  Ecuador: '厄瓜多尔', Curaçao: '库拉索', Curacao: '库拉索',
  Netherlands: '荷兰', Japan: '日本', Sweden: '瑞典', Tunisia: '突尼斯',
  Belgium: '比利时', Egypt: '埃及', Iran: '伊朗', 'New Zealand': '新西兰',
  Spain: '西班牙', 'Cape Verde': '佛得角', Uruguay: '乌拉圭', 'Saudi Arabia': '沙特阿拉伯',
  France: '法国', Senegal: '塞内加尔', Norway: '挪威', Iraq: '伊拉克',
  Argentina: '阿根廷', Austria: '奥地利', Algeria: '阿尔及利亚', Jordan: '约旦',
  Portugal: '葡萄牙', 'DR Congo': '刚果(金)', Colombia: '哥伦比亚',
  Uzbekistan: '乌兹别克斯坦', England: '英格兰', Croatia: '克罗地亚',
  Ghana: '加纳', Panama: '巴拿马',
};

const EMOJI = {
  墨西哥: '🇲🇽', 法国: '🇫🇷', 挪威: '🇳🇴', 英格兰: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 摩洛哥: '🇲🇦',
  巴西: '🇧🇷', 西班牙: '🇪🇸', 葡萄牙: '🇵🇹', 美国: '🇺🇸', 比利时: '🇧🇪',
  阿根廷: '🇦🇷', 埃及: '🇪🇬', 瑞士: '🇨🇭', 哥伦比亚: '🇨🇴', 加拿大: '🇨🇦',
  巴拉圭: '🇵🇾', 墨西哥: '🇲🇽',
};

function cn(name) {
  const n = name.replace(/<[^>]+>/g, '').replace(/\[[^\]]*\]/g, '').trim();
  return TEAM_CN[n] || n;
}

function emoji(t) {
  return EMOJI[t] || '';
}

function normScore(s) {
  return s.replace(/[–—]/g, '-').replace(/\s+/g, '').trim();
}

function matchKey(m) {
  return `${m.a}|${m.b}|${m.g}`;
}

async function fetchWikiHtml() {
  const url = 'https://en.wikipedia.org/w/api.php?action=parse&page=2026_FIFA_World_Cup&prop=text&formatversion=2&format=json';
  const res = await fetch(url, {
    headers: { 'User-Agent': 'worldcup.xiandan.me/1.0 (data sync; +https://worldcup.xiandan.me)' },
  });
  if (!res.ok) throw new Error('Wikipedia HTTP ' + res.status);
  const json = await res.json();
  return json.parse?.text || '';
}

/** 从淘汰赛表格行解析比分 */
function parseKnockoutFromHtml(html, stage) {
  const found = [];
  const marker = stage === 'r16' ? /Round of 16/i : stage === 'r32' ? /Round of 32/i : null;
  if (!marker) return found;

  const idx = html.search(marker);
  if (idx < 0) return found;
  const slice = html.slice(idx, idx + 120000);

  // 典型 wikitext 行：| Team A | score | Team B |
  const rowRe = /\|\s*([A-Za-z][^|\n]{1,35})\s*\|\s*(\d+)\s*[–—-]\s*(\d+)(?:\s*\([^)]*\))?\s*\|\s*([A-Za-z][^|\n]{1,35})\s*\|/g;
  let m;
  while ((m = rowRe.exec(slice)) !== null) {
    const a = cn(m[1]);
    const b = cn(m[4]);
    const score = `${m[2]}-${m[3]}`;
    if (!a || !b || a === b) continue;
    found.push({ a, b, s: score, g: stage === 'r16' ? '16强' : '32强', d: '', t: '' });
  }
  return found;
}

function mergeMatches(existing, incoming) {
  const map = new Map(existing.map(m => [matchKey(m), { ...m }]));
  let added = 0;
  for (const m of incoming) {
    const k1 = matchKey(m);
    const k2 = `${m.b}|${m.a}|${m.g}`;
    const hit = map.get(k1) || map.get(k2);
    if (hit) {
      if (hit.s !== m.s) {
        hit.s = m.s;
        added++;
      }
    } else {
      map.set(k1, { ...m });
      added++;
    }
  }
  return { matches: [...map.values()], added };
}

function stripFlags(s) {
  return s.replace(/[\u{1F1E6}-\u{1F1FF}]{2}/gu, '').replace(/🏴[\u{E0061}-\u{E007A}]+/gu, '').trim();
}

function teamsFromUpcoming(u) {
  const plain = stripFlags(u.m).replace(/\s+/g, ' ');
  const vs = plain.split(/\s+vs\s+/i);
  if (vs.length === 2) return [vs[0].trim(), vs[1].trim()];
  return null;
}

function removeCompletedFromUpcoming(upcoming, matches) {
  const done = new Set();
  for (const m of matches) {
    if (!m.s || m.s.includes('vs')) continue;
    done.add(`${m.a}|${m.b}`);
    done.add(`${m.b}|${m.a}`);
  }
  const before = upcoming.length;
  const next = upcoming.filter(u => {
    const pair = teamsFromUpcoming(u);
    if (!pair) return true;
    return !done.has(`${pair[0]}|${pair[1]}`) && !done.has(`${pair[1]}|${pair[0]}`);
  });
  return { upcoming: next, removed: before - next.length };
}

function winnerLabel(a, b, score, prefer) {
  const [x, y] = score.split('-').map(Number);
  if (isNaN(x) || isNaN(y)) return `${a} vs ${b}`;
  const win = x > y ? a : y > x ? b : prefer;
  const e = emoji(win);
  return e ? `${e} ${win} ${score}` : `${win} ${score}`;
}

function updateKnockoutFromMatches(ko, matches) {
  const r16 = matches.filter(m => m.g === '16强' && m.s && !m.s.includes('vs'));
  const find = (a, b) => r16.find(m => (m.a === a && m.b === b) || (m.a === b && m.b === a));

  const leftPairs = [['摩洛哥', '加拿大'], ['法国', '巴拉圭'], ['挪威', '巴西'], ['英格兰', '墨西哥']];
  const rightPairs = [['西班牙', '葡萄牙'], ['美国', '比利时'], ['阿根廷', '埃及'], ['瑞士', '哥伦比亚']];

  for (let i = 0; i < leftPairs.length; i++) {
    const [a, b] = leftPairs[i];
    const m = find(a, b);
    if (m) ko.leftR16[i] = winnerLabel(a, b, m.s, a);
    else if (!ko.leftR16[i]) ko.leftR16[i] = `${a} vs ${b}`;
  }
  for (let i = 0; i < rightPairs.length; i++) {
    const [a, b] = rightPairs[i];
    const m = find(a, b);
    if (m) ko.rightR16[i] = winnerLabel(a, b, m.s, a);
    else if (!ko.rightR16[i]?.includes(' ')) ko.rightR16[i] = `${a} vs ${b}`;
  }
  return ko;
}

function inferLiveBadge(matches, upcoming) {
  const r16Done = matches.filter(m => m.g === '16强').length;
  const r16Total = 8;
  if (r16Done < r16Total) return '16强进行中';
  const qfUp = upcoming.some(u => u.g === '8强');
  if (qfUp) return '8强即将开打';
  return '淘汰赛进行中';
}

async function main() {
  const raw = readFileSync(DATA_PATH, 'utf8');
  const data = JSON.parse(raw);
  let changed = false;
  let log = [];

  try {
    const html = await fetchWikiHtml();
    const r16 = parseKnockoutFromHtml(html, 'r16');
    if (r16.length) {
      const { matches, added } = mergeMatches(data.matches, r16);
      if (added) {
        data.matches = matches;
        changed = true;
        log.push(`matches +${added}`);
      }
    }
  } catch (e) {
    console.error('[warn] Wikipedia:', e.message);
  }

  const koBefore = JSON.stringify(data.knockout);
  data.knockout = updateKnockoutFromMatches(data.knockout, data.matches);
  if (JSON.stringify(data.knockout) !== koBefore) {
    changed = true;
    log.push('knockout updated');
  }

  const { upcoming, removed } = removeCompletedFromUpcoming(data.upcoming, data.matches);
  if (removed) {
    data.upcoming = upcoming;
    changed = true;
    log.push(`upcoming -${removed}`);
  }

  const badge = inferLiveBadge(data.matches, data.upcoming);
  if (data.liveBadge !== badge) {
    data.liveBadge = badge;
    changed = true;
  }

  const prev = data.updatedAt;
  data.updatedAt = new Date().toISOString();
  writeFileSync(DATA_PATH, JSON.stringify(data, null, 2) + '\n');
  console.log('[ok]', data.updatedAt, changed ? log.join(', ') || 'content changed' : 'timestamp refresh');
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
