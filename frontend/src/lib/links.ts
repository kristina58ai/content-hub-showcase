// Doc links: GitHub when NEXT_PUBLIC_REPO_URL is set (production), otherwise
// the local /docs viewer so the links work before the repo is published.

const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL;

export const DOC_LINKS = REPO_URL
  ? {
      readme: `${REPO_URL}#readme`,
      decisions: `${REPO_URL}/blob/main/DECISIONS.md`,
      examples: `${REPO_URL}/blob/main/EXAMPLES.md`,
      github: REPO_URL,
    }
  : {
      readme: "/docs/readme",
      decisions: "/docs/decisions",
      examples: "/docs/examples",
      github: "/docs/readme",
    };
