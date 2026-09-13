const BASE_RAW = "https://raw.githubusercontent.com/GameFunns98/mangayomi-library/main";

async function fetchCatalog() {
  const res = await fetch(`${BASE_RAW}/catalog.json`);
  if (!res.ok) throw new Error(`Cannot load catalog.json (${res.status})`);
  return await res.json();
}

function toManga(m) {
  return {
    name: m.title,
    url: m.id,
    imageUrl: `${BASE_RAW}/${m.cover}`,
  };
}

async function getPopular(page) {
  const c = await fetchCatalog();
  return { list: (c.manga || []).map(toManga), hasNextPage: false };
}

async function getLatest(page) {
  const c = await fetchCatalog();
  return { list: (c.manga || []).map(toManga), hasNextPage: false };
}

async function search(query, page) {
  const c = await fetchCatalog();
  const q = (query || "").toLowerCase();
  const list = (c.manga || [])
    .filter(m => !q || (m.title || "").toLowerCase().includes(q))
    .map(toManga);
  return { list, hasNextPage: false };
}

async function detail(url) {
  const c = await fetchCatalog();
  const m = (c.manga || []).find(x => x.id === url);
  if (!m) throw new Error("Manga not found");
  return {
    name: m.title,
    url: m.id,
    imageUrl: `${BASE_RAW}/${m.cover}`,
    description: m.title
  };
}

async function getChapters(url) {
  const c = await fetchCatalog();
  const m = (c.manga || []).find(x => x.id === url);
  if (!m) return [];
  return (m.chapters || []).map(ch => ({
    name: ch.title || `Chapter ${ch.number}`,
    url: ch.id,
    chapterNumber: Number(ch.number) || 0
  }));
}

async function getPages(chapterUrl) {
  const c = await fetchCatalog();
  for (const m of (c.manga || [])) {
    const ch = (m.chapters || []).find(x => x.id === chapterUrl);
    if (!ch) continue;

    const res = await fetch(`${BASE_RAW}/${ch.path}pages.json`);
    if (!res.ok) throw new Error(`Cannot load pages.json (${res.status})`);
    const data = await res.json();

    return (data.pages || []).map((p, i) => ({
      index: i,
      url: `${BASE_RAW}/${ch.path}${p}`,
    }));
  }
  return [];
}