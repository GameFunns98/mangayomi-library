const BASE_RAW = `https://raw.githubusercontent.com/GameFunns98/mangayomi-library/main`;

async function fetchCatalog() {
  const res = await fetch(`${BASE_RAW}/catalog.json`);
  if (!res.ok) throw new Error("Cannot load catalog.json");
  return await res.json();
}

async function getMangaList() {
  const catalog = await fetchCatalog();
  return catalog.manga.map(m => ({
    id: m.id,
    title: m.title,
    cover: `${BASE_RAW}/${m.cover}`
  }));
}

async function getChapters(mangaId) {
  const catalog = await fetchCatalog();
  const m = catalog.manga.find(x => x.id === mangaId);
  if (!m) return [];
  return [...m.chapters].sort((a, b) => a.number - b.number);
}

async function getPages(mangaId, chapterId) {
  const catalog = await fetchCatalog();
  const m = catalog.manga.find(x => x.id === mangaId);
  if (!m) return [];
  const ch = m.chapters.find(x => x.id === chapterId);
  if (!ch) return [];

  const res = await fetch(`${BASE_RAW}/${ch.path}pages.json`);
  if (!res.ok) throw new Error("Cannot load pages.json");
  const data = await res.json();

  return data.pages.map(name => `${BASE_RAW}/${ch.path}${name}`);
}