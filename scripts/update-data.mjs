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

const VALID_TEAMS = new Set(Object.values(TEAM_CN));

function cn(name) {
  const n = decodeHtml(name);
  return TEAM_CN[n] || n;
}

function decodeHtml(text) {
  return text
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;|&#160;/gi, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function isKnownTeam(name) {
  return VALID_TEAMS.has(name);
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

const WIKI_UA = 'worldcup.xiandan.me/1.0 (data sync; +https://worldcup.xiandan.me)';

async function fetchWikiHtml() {
  const url = 'https://en.wikipedia.org/w/api.php?action=parse&page=2026_FIFA_World_Cup_knockout_stage&prop=text&formatversion=2&format=json';
  const res = await fetch(url, {
    headers: { 'User-Agent': WIKI_UA },
    signal: AbortSignal.timeout(45000),
  });
  if (!res.ok) throw new Error('Wikipedia HTTP ' + res.status);
  const json = await res.json();
  return json.parse?.text || '';
}

function stripHtml(text) {
  return decodeHtml(text);
}

function parseScoreCell(text) {
  const plain = decodeHtml(text);
  const m = plain.match(/^(\d+)\s*[–—-]\s*(\d+)$/);
  if (!m) return null;
  return `${m[1]}-${m[2]}`;
}

function teamsFromTitle(title) {
  const parts = title.split(/\bvs\.?\b/i).map(s => s.trim()).filter(Boolean);
  if (parts.length !== 2) return null;
  const a = cn(parts[0]);
  const b = cn(parts[1]);
  if (!isKnownTeam(a) || !isKnownTeam(b) || a === b) return null;
  return [a, b];
}

/** 从各场比赛的 h3 小节里解析比分，跳过对阵图里的脏数据 */
function parseKnockoutFromHtml(html, stage) {
  const STAGES = {
    r32: { start: /id="Round_of_32"/i, end: /id="Round_of_16"/i, g: '32强' },
    r16: { start: /id="Round_of_16"/i, end: /id="Quarterfinals"/i, g: '16强' },
    qf: { start: /id="Quarterfinals"/i, end: /id="Semifinals"/i, g: '8强' },
  };
  const cfg = STAGES[stage];
  if (!cfg) return [];
  const { start: startRe, end: endRe, g } = cfg;

  const found = [];
  const start = html.search(startRe);
  if (start < 0) return found;
  const end = html.search(endRe, start + 1);
  const slice = html.slice(start, end > start ? end : start + 300000);

  const sectionRe = /<h3[^>]*>([\s\S]*?)<\/h3>([\s\S]*?)(?=<h3|<h2[^>]*>|$)/gi;
  let section;
  while ((section = sectionRe.exec(slice)) !== null) {
    const title = decodeHtml(section[1]);
    if (!/\bvs\.?\b/i.test(title)) continue;
    const titleTeams = teamsFromTitle(title);
    let fallbackScore = null;

    const rowRe = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    let row;
    while ((row = rowRe.exec(section[2])) !== null) {
      const cells = [...row[1].matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(m => m[1]);
      if (cells.length !== 3) continue;

      const score = parseScoreCell(cells[1]);
      if (!score) continue;
      fallbackScore = score;

      const a = cn(cells[0]);
      const b = cn(cells[2]);
      if (!isKnownTeam(a) || !isKnownTeam(b) || a === b) continue;

      found.push({ a, b, s: score, g, d: '', t: '' });
      break;
    }

    // 有些场次的表格会把球队名拆成球员/事件行，导致无法从单行拿到队名；
    // 此时使用 h3 标题中的 "A vs B" 作为球队名兜底，比分取该小节内最后一个合法比分。
    if (titleTeams && fallbackScore && !found.some(m => m.g === g && ((m.a === titleTeams[0] && m.b === titleTeams[1]) || (m.a === titleTeams[1] && m.b === titleTeams[0])))) {
      found.push({ a: titleTeams[0], b: titleTeams[1], s: fallbackScore, g, d: '', t: '' });
    }
  }
  return found;
}

function flipScore(score) {
  const parts = score.split('-');
  return parts.length === 2 ? `${parts[1]}-${parts[0]}` : score;
}

function mergeMatches(existing, incoming) {
  const map = new Map(existing.map(m => [matchKey(m), { ...m }]));
  let added = 0;
  for (const m of incoming) {
    if (!isKnownTeam(m.a) || !isKnownTeam(m.b)) continue;
    const k1 = matchKey(m);
    const k2 = `${m.b}|${m.a}|${m.g}`;
    const hit = map.get(k1) || map.get(k2);
    const reversed = hit && hit.a === m.b && hit.b === m.a;
    const newScore = reversed ? flipScore(m.s) : m.s;
    if (hit) {
      if (hit.s !== newScore) {
        hit.s = newScore;
        added++;
      }
    } else {
      map.set(k1, { ...m });
      added++;
    }
  }
  return { matches: [...map.values()], added };
}

function sanitizeMatches(matches) {
  return matches.filter(m => isKnownTeam(m.a) && isKnownTeam(m.b));
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
  const base = score.split('(')[0].replace(/[–—]/g, '-');
  const suffix = score.includes('(') ? score.slice(score.indexOf('(')) : '';
  const [x, y] = base.split('-').map(Number);
  if (isNaN(x) || isNaN(y)) return `${a} vs ${b}`;
  const win = x > y ? a : y > x ? b : prefer;
  const winGoals = win === a ? x : y;
  const losGoals = win === a ? y : x;
  const displayScore = `${winGoals}-${losGoals}${suffix}`;
  const e = emoji(win);
  return e ? `${e} ${win} ${displayScore}` : `${win} ${displayScore}`;
}

/** 对阵图拓扑：每对相邻 R32 格子汇入一场 R16（与 index.html 连线一致） */
const BRACKET = {
  left: [
    { r16: ['摩洛哥', '加拿大'], r32: [['摩洛哥', '荷兰'], ['加拿大', '南非']] },
    { r16: ['法国', '巴拉圭'], r32: [['法国', '瑞典'], ['巴拉圭', '德国']] },
    { r16: ['挪威', '巴西'], r32: [['挪威', '科特迪瓦'], ['巴西', '日本']] },
    { r16: ['英格兰', '墨西哥'], r32: [['英格兰', '刚果(金)'], ['墨西哥', '厄瓜多尔']] },
  ],
  right: [
    { r16: ['西班牙', '葡萄牙'], r32: [['西班牙', '奥地利'], ['葡萄牙', '克罗地亚']] },
    { r16: ['美国', '比利时'], r32: [['美国', '波黑'], ['比利时', '塞内加尔']] },
    { r16: ['阿根廷', '埃及'], r32: [['阿根廷', '佛得角'], ['埃及', '澳大利亚']] },
    { r16: ['瑞士', '哥伦比亚'], r32: [['瑞士', '阿尔及利亚'], ['哥伦比亚', '加纳']] },
  ],
};

function findMatch(matches, stage, a, b) {
  return matches.find(m => m.g === stage && ((m.a === a && m.b === b) || (m.a === b && m.b === a)));
}

function r16WinnerTeam(matches, a, b) {
  const m = findMatch(matches, '16强', a, b);
  if (!m?.s || m.s.includes('vs')) return null;
  const base = m.s.split('(')[0].replace(/[–—]/g, '-');
  const [x, y] = base.split('-').map(Number);
  if (isNaN(x) || isNaN(y)) return null;
  if (x > y) return m.a;
  if (y > x) return m.b;
  return null;
}

function r32SlotLabel(matches, team, opp) {
  const m = findMatch(matches, '32强', team, opp);
  if (!m) return team;
  return winnerLabel(m.a, m.b, m.s, team);
}

function r16SlotLabel(matches, a, b) {
  const m = findMatch(matches, '16强', a, b);
  if (!m?.s || m.s.includes('vs')) return `${a} vs ${b}`;
  return winnerLabel(m.a, m.b, m.s, a);
}

function qfLabel(matches, pairA, pairB) {
  const wA = r16WinnerTeam(matches, pairA[0], pairA[1]);
  const wB = r16WinnerTeam(matches, pairB[0], pairB[1]);
  if (!wA || !wB) return '待定';
  const m = findMatch(matches, '8强', wA, wB);
  if (!m?.s || m.s.includes('vs')) return `${wA} vs ${wB}`;
  return winnerLabel(m.a, m.b, m.s, wA);
}

function rebuildKnockout(ko, matches) {
  const leftR32 = [];
  const leftR16 = [];
  for (const slot of BRACKET.left) {
    for (const [team, opp] of slot.r32) leftR32.push(r32SlotLabel(matches, team, opp));
    leftR16.push(r16SlotLabel(matches, slot.r16[0], slot.r16[1]));
  }

  const rightR32 = [];
  const rightR16 = [];
  for (const slot of BRACKET.right) {
    for (const [team, opp] of slot.r32) rightR32.push(r32SlotLabel(matches, team, opp));
    rightR16.push(r16SlotLabel(matches, slot.r16[0], slot.r16[1]));
  }

  ko.leftR32 = leftR32;
  ko.leftR16 = leftR16;
  ko.rightR32 = rightR32;
  ko.rightR16 = rightR16;
  ko.leftQF = [
    qfLabel(matches, BRACKET.left[0].r16, BRACKET.left[1].r16),
    qfLabel(matches, BRACKET.left[2].r16, BRACKET.left[3].r16),
  ];
  ko.rightQF = [
    qfLabel(matches, BRACKET.right[0].r16, BRACKET.right[1].r16),
    qfLabel(matches, BRACKET.right[2].r16, BRACKET.right[3].r16),
  ];
  return ko;
}

function inferLiveBadge(matches, upcoming) {
  const r16Done = matches.filter(m => m.g === '16强' && m.s && !m.s.includes('vs')).length;
  if (r16Done < 8) return '16强进行中';
  const qfDone = matches.filter(m => m.g === '8强' && m.s && !m.s.includes('vs')).length;
  if (qfDone < 4) return qfDone > 0 ? '8强进行中' : '8强即将开打';
  const sfUp = upcoming.some(u => u.g === '半决赛');
  if (sfUp) return '半决赛即将开打';
  return '淘汰赛进行中';
}

const QF_SCHEDULE = [
  { side: 'left', idx: 0, d: '7.9', t: '04:00' },
  { side: 'right', idx: 0, d: '7.10', t: '03:00' },
  { side: 'left', idx: 1, d: '7.11', t: '05:00' },
  { side: 'right', idx: 1, d: '7.11', t: '09:00' },
];

function upcomingMatchLabel(text) {
  if (!text || text === '待定' || !text.includes(' vs ')) return null;
  const parts = text.split(/\s+vs\s+/i);
  if (parts.length !== 2) return null;
  const a = parts[0].trim();
  const b = parts[1].trim();
  const ea = emoji(a);
  const eb = emoji(b);
  return `${ea ? ea + ' ' : ''}${a} vs ${eb ? eb + ' ' : ''}${b}`.replace(/\s+/g, ' ').trim();
}

/** 根据对阵图 8 强格子重建预告（替换 A/B 占位文案） */
function rebuildUpcoming(upcoming, ko) {
  const rest = upcoming.filter(u => u.g !== '8强');
  const qf = [];
  for (const { side, idx, d, t } of QF_SCHEDULE) {
    const label = side === 'left' ? ko.leftQF[idx] : ko.rightQF[idx];
    const m = upcomingMatchLabel(label);
    if (m) qf.push({ d, m, t, g: '8强' });
  }
  return [...qf, ...rest];
}

async function main() {
  const raw = readFileSync(DATA_PATH, 'utf8');
  const data = JSON.parse(raw);
  let changed = false;
  let log = [];

  const cleaned = sanitizeMatches(data.matches);
  if (cleaned.length !== data.matches.length) {
    log.push(`matches cleaned -${data.matches.length - cleaned.length}`);
    data.matches = cleaned;
    changed = true;
  }

  try {
    const html = await fetchWikiHtml();
    for (const stage of ['r16', 'qf']) {
      const parsed = parseKnockoutFromHtml(html, stage);
      if (!parsed.length) continue;
      const { matches, added } = mergeMatches(data.matches, parsed);
      if (added) {
        data.matches = matches;
        changed = true;
        log.push(`${stage} +${added}`);
      }
    }
  } catch (e) {
    console.error('[warn] Wikipedia:', e.message);
  }

  const koBefore = JSON.stringify(data.knockout);
  data.knockout = rebuildKnockout(data.knockout, data.matches);
  if (JSON.stringify(data.knockout) !== koBefore) {
    changed = true;
    log.push('knockout updated');
  }

  const upcomingBefore = JSON.stringify(data.upcoming);
  data.upcoming = rebuildUpcoming(data.upcoming, data.knockout);
  const { upcoming, removed } = removeCompletedFromUpcoming(data.upcoming, data.matches);
  data.upcoming = upcoming;
  if (removed) log.push(`upcoming -${removed}`);
  if (JSON.stringify(data.upcoming) !== upcomingBefore) {
    changed = true;
    log.push('upcoming rebuilt');
  }

  const badge = inferLiveBadge(data.matches, data.upcoming);
  if (data.liveBadge !== badge) {
    data.liveBadge = badge;
    changed = true;
  }

  if (changed) {
    data.updatedAt = new Date().toISOString();
    writeFileSync(DATA_PATH, JSON.stringify(data, null, 2) + '\n');
    console.log('[ok]', data.updatedAt, log.join(', ') || 'content changed');
  } else {
    console.log('[skip] no content change (updatedAt stays', data.updatedAt + ')');
  }
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
