const BASE_RAW = "https://raw.githubusercontent.com/GameFunns98/mangayomi-library/main";

async function fetchCatalog() {
  const res = await fetch(`${BASE_RAW}/catalog.json`);
  if (!res.ok) throw new Error("Cannot load catalog.json");
  return await res.json();
}

function toMangaItem(m) {
  return {
    id: m.id,
    title: m.title,
    imageUrl: `${BASE_RAW}/${m.cover}`,
    description: m.title,
  };
}

// REQUIRED by Popular tab
async function getPopular(page) {
  const catalog = await fetchCatalog();
  const list = (catalog.manga || []).map(toMangaItem);
  return { list, hasNextPage: false };
}

// REQUIRED by Latest tab
async function getLatest(page) {
  const catalog = await fetchCatalog();
  const list = [...(catalog.manga || [])]
    .sort((a, b) => (b.chapters?.length || 0) - (a.chapters?.length || 0))
    .map(toMangaItem);
  return { list, hasNextPage: false };
}

// usually required by source detail page
async function getDetail(url) {
  const catalog = await fetchCatalog();
  const m = (catalog.manga || []).find(x => x.id === url);
  if (!m) throw new Error("Manga not found");

  return {
    id: m.id,
    title: m.title,
    imageUrl: `${BASE_RAW}/${m.cover}`,
    description: m.title,
  };
}

async function getChapters(url) {
  const catalog = await fetchCatalog();
  const m = (catalog.manga || []).find(x => x.id === url);
  if (!m) return [];

  return (m.chapters || [])
    .sort((a, b) => a.number - b.number)
    .map(ch => ({
      id: ch.id,
      title: ch.title || `Chapter ${ch.number}`,
      url: ch.id,
      chapterNumber: ch.number,
    }));
}

async function getPages(chapterUrl) {
  const catalog = await fetchCatalog();

  let found = null;
  for (const m of (catalog.manga || [])) {
    const ch = (m.chapters || []).find(c => c.id === chapterUrl);
    if (ch) {
      found = ch;
      break;
    }
  }
  if (!found) return [];

  const res = await fetch(`${BASE_RAW}/${found.path}pages.json`);
  if (!res.ok) throw new Error("Cannot load pages.json");
  const data = await res.json();

  return (data.pages || []).map((name, i) => ({
    index: i,
    url: `${BASE_RAW}/${found.path}${name}`
  }));
}