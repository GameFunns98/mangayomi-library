// Basic custom source helper for your own GitHub-backed catalog.
// Adjust REPO_OWNER / REPO_NAME / BRANCH if needed.

const REPO_OWNER = "GameFunns98";
const REPO_NAME = "mangayomi-library";
const BRANCH = "main";

const BASE_RAW = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}`;

async function fetchCatalog() {
  const res = await fetch(`${BASE_RAW}/catalog.json`);
  if (!res.ok) throw new Error("Cannot load catalog.json");
  return await res.json();
}

// Example utility methods your extension runtime can call:
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
  return m.chapters.map(ch => ({
    id: ch.id,
    number: ch.number,
    title: ch.title,
    path: ch.path
  }));
}

async function getPages(mangaId, chapterId) {
  const catalog = await fetchCatalog();
  const m = catalog.manga.find(x => x.id === mangaId);
  if (!m) return [];
  const ch = m.chapters.find(x => x.id === chapterId);
  if (!ch) return [];

  // If you want strict page list, generate pages.json per chapter in ingest.py later.
  // For now this assumes sequential jpg names until missing.
  const pages = [];
  for (let i = 1; i <= 500; i++) {
    const file = `${String(i).padStart(3, "0")}.jpg`;
    const url = `${BASE_RAW}/${ch.path}${file}`;
    pages.push(url);
  }
  return pages;
}