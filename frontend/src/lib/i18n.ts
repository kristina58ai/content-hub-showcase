// RU/EN interface dictionary + persisted language store (design handoff: i18n).
// Numbers, platform names and timings are never translated.

import { create } from "zustand";

export type Lang = "ru" | "en";

const STORAGE_KEY = "ch-lang";

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

export const useLangStore = create<LangState>((set) => ({
  lang: "ru",
  setLang: (lang) => {
    set({ lang });
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* private mode */
    }
  },
}));

/** Read the persisted language after mount (avoids SSR hydration mismatch). */
export function hydrateLang(): void {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "ru" || saved === "en") {
      useLangStore.setState({ lang: saved });
    }
  } catch {
    /* private mode */
  }
}

interface ArchetypeCopy {
  name: string;
  tag: string;
}

export interface Dict {
  navAbout: string;
  navArch: string;
  navAdr: string;
  heroSub: string;
  heroLead: string;
  cta: string;
  openDemo: string;
  footProof: string;
  cardMeta: string;
  backHome: string;
  backAll: string;
  inputPh: string;
  generate: string;
  generating: string;
  planTitle: string;
  planCount: (n: number) => string;
  collapse: string;
  expand: string;
  day: string;
  fromPlan: string;
  moreTopics: (n: number) => string;
  graphLabel: string;
  outputsLabel: string;
  waiting: string;
  runHint: string;
  ms: string;
  statusQueued: string;
  statusWorking: string;
  statusFailed: string;
  draftLabel: string;
  copy: string;
  copied: string;
  overLimit: string;
  ingestTitle: string;
  ingestDesc: string;
  views: string;
  likes: string;
  ingestPh: string;
  ingestBtn: string;
  ingestBusy: string;
  ingestOk: string;
  learnTitle: string;
  learnDesc: string;
  learnBtn: string;
  learnBusy: string;
  patternsLabel: string;
  memoryLabel: string;
  planSuggestLabel: string;
  analyzed: (exemplars: number, ingested: number) => string;
  metaLine: (facts: number, posts: number, topics: number) => string;
  loading: string;
  errArchetypes: string;
  errArchetype: string;
  errFallbackHint: string;
  aboutCrumb: string;
  aboutH1: string;
  aboutP1: string;
  aboutP2: string;
  aboutStack: string;
  aboutDeeper: string;
  aboutLinks: { name: string; desc: string }[];
  agents: Record<string, string>;
  archetypes: Record<string, ArchetypeCopy>;
}

const ru: Dict = {
  navAbout: "О проекте",
  navArch: "Архитектура",
  navAdr: "Решения",
  heroSub: "мультиагентная генерация контента",
  heroLead:
    "Выберите архетип автора — и смотрите вживую, как конвейер агентов исследует тему, пишет черновик и адаптирует его под пять платформ.",
  cta: "Смотреть демо",
  openDemo: "Открыть демо",
  footProof: "66 тестов · 93% покрытия · 17 ADR",
  cardMeta: "50 фактов · 10 постов",
  backHome: "На главную",
  backAll: "Все архетипы",
  inputPh: "О чём написать пост?",
  generate: "Сгенерировать",
  generating: "Генерация…",
  planTitle: "Контент-план",
  planCount: (n) => `${n} тем`,
  collapse: "СВЕРНУТЬ",
  expand: "РАЗВЕРНУТЬ",
  day: "день",
  fromPlan: "Из плана",
  moreTopics: (n) => `ещё ${n} тем…`,
  graphLabel: "Конвейер агентов — вживую",
  outputsLabel: "Выходы агентов",
  waiting: "Ждём первого агента…",
  runHint: "Запустите генерацию — и смотрите, как работают агенты.",
  ms: "МС",
  statusQueued: "ожидает",
  statusWorking: "работает…",
  statusFailed: "сбой",
  draftLabel: "Нейтральный черновик",
  copy: "Копировать",
  copied: "Скопировано ✓",
  overLimit: "сверх лимита!",
  ingestTitle: "Свои данные",
  ingestDesc:
    "Вставьте пост с метриками — он попадёт в память сессии и в следующий цикл обучения. Данные — внутрь, видимо.",
  views: "просмотры",
  likes: "лайки",
  ingestPh: "Текст поста (минимум 10 символов)…",
  ingestBtn: "В память сессии",
  ingestBusy: "Добавляем…",
  ingestOk: "добавлено — войдёт в следующий цикл",
  learnTitle: "Цикл обучения",
  learnDesc: "Analyzer разбирает посты архетипа на паттерны и предлагает обновления плана.",
  learnBtn: "Запустить цикл",
  learnBusy: "Анализ…",
  patternsLabel: "Найденные паттерны",
  memoryLabel: "Предложения для памяти",
  planSuggestLabel: "Предложения в план",
  analyzed: (exemplars, ingested) =>
    `Разобрано ${exemplars} постов` +
    (ingested > 0 ? ` + ${ingested} добавлено в этой сессии` : ""),
  metaLine: (facts, posts, topics) =>
    `${facts} фактов · ${posts} постов · ${topics} тем`,
  loading: "Будим агентов (~20 сек)",
  errArchetypes: "Не удалось загрузить архетипы — бэкенд, возможно, просыпается.",
  errArchetype: "Не удалось загрузить архетип.",
  errFallbackHint: "Если живое демо недоступно — примеры в EXAMPLES.md.",
  aboutCrumb: "О проекте",
  aboutH1: "О проекте",
  aboutP1:
    "Content-hub Showcase — живое демо мультиагентной AI-системы генерации контента. Выберите одну из трёх демо-личностей, дайте агентам тему — и смотрите, как сеть LangGraph работает в реальном времени: Брифер достаёт персону из векторной памяти, Ресёрчер собирает углы, Райтер пишет нейтральный черновик, а пять Соц-райтеров параллельно адаптируют его под платформы.",
  aboutP2:
    "Всё, что вы видите, — настоящее: реальные вызовы LLM, реальный RAG поверх локально посчитанных эмбеддингов, реальное durable-состояние воркфлоу в Redis. Единственная выдумка — личности: они вымышлены намеренно.",
  aboutStack: "Стек",
  aboutDeeper: "Глубже",
  aboutLinks: [
    { name: "README", desc: "Архитектура, quick start и честный AI-collaboration disclosure." },
    { name: "DECISIONS.md", desc: "17 архитектурных решений (ADR) с трейд-оффами и альтернативами." },
    { name: "EXAMPLES.md", desc: "Скриншоты и GIF полного флоу — на случай, если живое демо спит." },
  ],
  agents: {
    briefer: "Брифер",
    researcher: "Ресёрчер",
    writer: "Райтер",
    social_writer: "Соц-райтер ×5",
    finalizer: "Финализатор",
  },
  archetypes: {
    ai_engineer: {
      name: "AI-инженер",
      tag: "LLM-системы, которые переживают контакт с продакшеном. Военные истории из реальных деплоев, а не keynote-демо.",
    },
    doctor: {
      name: "Врач-просветитель",
      tag: "Мифы заходят — доказательства выходят. Исследования, переведённые в истории, которые может понять каждый.",
    },
    marketer: {
      name: "Growth-маркетолог",
      tag: "Честные цифры, проваленные A/B-тесты и «грязная середина» роста — без снейк-ойла.",
    },
  },
};

const en: Dict = {
  navAbout: "About",
  navArch: "Architecture",
  navAdr: "Decisions",
  heroSub: "multi-agent content generation",
  heroLead:
    "Pick an author archetype — and watch live as the agent pipeline researches the topic, drafts a post and adapts it for five platforms.",
  cta: "Watch the demo",
  openDemo: "Open demo",
  footProof: "66 tests · 93% coverage · 17 ADR",
  cardMeta: "50 facts · 10 posts",
  backHome: "Home",
  backAll: "All archetypes",
  inputPh: "What should the post be about?",
  generate: "Generate",
  generating: "Generating…",
  planTitle: "Content plan",
  planCount: (n) => `${n} topics`,
  collapse: "COLLAPSE",
  expand: "EXPAND",
  day: "day",
  fromPlan: "From plan",
  moreTopics: (n) => `${n} more topics…`,
  graphLabel: "Agent pipeline — live",
  outputsLabel: "Agent outputs",
  waiting: "Waiting for the first agent…",
  runHint: "Run a generation to watch the agents work.",
  ms: "MS",
  statusQueued: "queued",
  statusWorking: "working…",
  statusFailed: "failed",
  draftLabel: "Neutral draft",
  copy: "Copy",
  copied: "Copied ✓",
  overLimit: "over limit!",
  ingestTitle: "Your own data",
  ingestDesc:
    "Paste a post with its metrics — it joins this session's memory and the next learning cycle. Data in, visibly.",
  views: "views",
  likes: "likes",
  ingestPh: "Post text (min 10 characters)…",
  ingestBtn: "Add to session memory",
  ingestBusy: "Adding…",
  ingestOk: "added — it will join the next cycle",
  learnTitle: "Learning cycle",
  learnDesc: "The Analyzer mines the archetype's posts for patterns and suggests plan updates.",
  learnBtn: "Run cycle",
  learnBusy: "Analyzing…",
  patternsLabel: "Patterns found",
  memoryLabel: "Suggested memory updates",
  planSuggestLabel: "Suggested plan additions",
  analyzed: (exemplars, ingested) =>
    `Analyzed ${exemplars} posts` +
    (ingested > 0 ? ` + ${ingested} ingested this session` : ""),
  metaLine: (facts, posts, topics) => `${facts} facts · ${posts} posts · ${topics} topics`,
  loading: "Warming up the agents (~20 sec)",
  errArchetypes: "Couldn't load archetypes — the backend may be waking up.",
  errArchetype: "Couldn't load this archetype.",
  errFallbackHint: "If the live demo is unavailable, see EXAMPLES.md for samples.",
  aboutCrumb: "About",
  aboutH1: "About",
  aboutP1:
    "Content-hub Showcase is a live demo of a multi-agent AI content system. Pick one of three demo personalities, give the agents a topic — and watch the LangGraph network work in real time: a Briefer pulls the persona from vector memory, a Researcher gathers angles, a Writer drafts a neutral post, and five Social Writers adapt it per platform — in parallel.",
  aboutP2:
    "Everything you see is real: real LLM calls, real RAG over locally-computed embeddings, real durable workflow state in Redis. The only fake thing is the personalities — they're fictional by design.",
  aboutStack: "Tech stack",
  aboutDeeper: "Go deeper",
  aboutLinks: [
    { name: "README", desc: "Architecture, quick start and an honest AI-collaboration disclosure." },
    { name: "DECISIONS.md", desc: "17 architecture decision records with trade-offs and alternatives." },
    { name: "EXAMPLES.md", desc: "Screenshots and a GIF of the full flow — in case the live demo is asleep." },
  ],
  agents: {
    briefer: "Briefer",
    researcher: "Researcher",
    writer: "Writer",
    social_writer: "Social Writer ×5",
    finalizer: "Finalizer",
  },
  archetypes: {
    ai_engineer: {
      name: "AI Engineer",
      tag: "LLM systems that survive contact with production. War stories from real deployments, not keynote demos.",
    },
    doctor: {
      name: "Physician Educator",
      tag: "Myths walk in — evidence walks out. Studies translated into stories anyone can follow.",
    },
    marketer: {
      name: "Growth Marketer",
      tag: "Real numbers, failed A/B tests and the messy middle of growth — zero snake oil.",
    },
  },
};

const dictionaries: Record<Lang, Dict> = { ru, en };

export function useLang(): Lang {
  return useLangStore((state) => state.lang);
}

export function useT(): Dict {
  return dictionaries[useLangStore((state) => state.lang)];
}

/** Localized archetype copy with API fallback for unknown ids. */
export function archetypeCopy(
  dict: Dict,
  id: string,
  fallback: { name: string; tag: string },
): ArchetypeCopy {
  return dict.archetypes[id] ?? fallback;
}
